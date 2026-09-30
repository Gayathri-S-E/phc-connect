import React, { useState, useEffect, useRef, useCallback } from 'react';
import {
  Bot, X, Send, Loader2, Sparkles, AlertCircle, ChevronRight,
  History, Plus, Trash2, RotateCcw, Siren, Check, ArrowLeft,
} from 'lucide-react';
import { useAuth } from '../../context/AuthContext';
import { useLanguage } from '../../context/LanguageContext';
import { api } from '../../services/api';
import type { ApiError } from '../../services/types';
import { MicButton, SpeakButton } from './VoiceControls';

/* ------------------------------ API contract ------------------------------ */

type AssistantKey = 'PATIENT' | 'DOCTOR';

interface AssistantInfo {
  key: string;
  title: string;
  starters: Record<string, string[]>;
  configured: boolean;
}

interface PendingActionView {
  id: string;
  tool: string;
  summary: string;
  status: string; // PENDING | EXECUTING | EXECUTED | FAILED | CANCELLED | EXPIRED
  expires_at: string;
  result?: Record<string, unknown> | null;
  already_completed?: boolean | null;
  message?: string | null;
}

interface ChatResponse {
  conversation_id: string;
  assistant: string;
  answer: string;
  language: string;
  emergency: boolean;
  refused: boolean;
  sources: string[];
  tools_used: string[];
  pending_action?: PendingActionView | null;
}

interface ConversationSummary {
  id: string;
  assistant: string;
  title: string;
  language: string;
  updated_at: string;
}

interface MessageView {
  id: string;
  role: string;
  content: string;
  meta?: { sources?: string[]; emergency?: boolean; pending_action_id?: string } | null;
  created_at: string;
}

interface ConversationDetail {
  conversation: ConversationSummary;
  messages: MessageView[];
  pending_actions: PendingActionView[];
}

/* ------------------------------ UI state types ----------------------------- */

interface ActionState {
  id: string;
  summary: string;
  status: string;
  busy: boolean;
  resultMessage?: string;
  error?: string;
}

interface ChatMessage {
  id: string;
  sender: 'user' | 'assistant';
  text: string;
  emergency?: boolean;
  refused?: boolean;
  sources?: string[];
  action?: ActionState;
  error?: { retryText: string; retryable: boolean };
}

const ROLE_TO_ASSISTANT: Record<string, AssistantKey> = { PATIENT: 'PATIENT', DOCTOR: 'DOCTOR' };
const TERMINAL_STATUSES = ['EXECUTED', 'FAILED', 'CANCELLED', 'EXPIRED'];

let uid = 0;
const nextId = () => `m${Date.now()}_${uid++}`;

/** The shared api service drops non-standard error fields (e.g. `retryable`), so infer it from the status. */
const isRetryableError = (e: ApiError) => e.status === 0 || e.status === 429 || e.status >= 500;

/* ------------------------- Safe minimal markdown --------------------------- */

const renderInline = (text: string, keyPrefix: string): React.ReactNode[] =>
  text.split(/(\*\*[^*]+\*\*)/g).map((part, i) =>
    part.startsWith('**') && part.endsWith('**') && part.length > 4
      ? <strong key={`${keyPrefix}-${i}`}>{part.slice(2, -2)}</strong>
      : <React.Fragment key={`${keyPrefix}-${i}`}>{part}</React.Fragment>
  );

const Markdown: React.FC<{ text: string }> = ({ text }) => {
  const blocks: React.ReactNode[] = [];
  let list: { ordered: boolean; items: string[] } | null = null;
  let para: string[] = [];

  const flushPara = () => {
    if (para.length) {
      const k = `p${blocks.length}`;
      blocks.push(
        <p key={k} style={{ margin: '0 0 0.4rem' }}>
          {para.flatMap((line, i) => [i > 0 ? <br key={`${k}-br${i}`} /> : null, ...renderInline(line, `${k}-${i}`)])}
        </p>
      );
      para = [];
    }
  };
  const flushList = () => {
    if (list) {
      const k = `l${blocks.length}`;
      const Tag = list.ordered ? 'ol' : 'ul';
      blocks.push(
        <Tag key={k} style={{ margin: '0 0 0.4rem', paddingLeft: '1.25rem' }}>
          {list.items.map((it, i) => <li key={i}>{renderInline(it, `${k}-${i}`)}</li>)}
        </Tag>
      );
      list = null;
    }
  };

  text.split(/\r?\n/).forEach((raw) => {
    const line = raw.trimEnd();
    const bullet = /^\s*(?:[-*•])\s+(.*)$/.exec(line);
    const numbered = /^\s*\d+[.)]\s+(.*)$/.exec(line);
    if (bullet || numbered) {
      flushPara();
      const ordered = !bullet;
      if (list && list.ordered !== ordered) flushList();
      if (!list) list = { ordered, items: [] };
      list.items.push((bullet || numbered)![1]);
    } else if (line.trim() === '') {
      flushPara();
      flushList();
    } else {
      flushList();
      para.push(line.replace(/^#{1,6}\s+/, ''));
    }
  });
  flushPara();
  flushList();
  return <div style={{ wordBreak: 'break-word' }}>{blocks}</div>;
};

/* -------------------------------- Component -------------------------------- */

export const UnifiedAiAssistant: React.FC = () => {
  const { activeRole } = useAuth();
  const { language, t } = useLanguage();
  const [isOpen, setIsOpen] = useState(false);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [isModalActive, setIsModalActive] = useState(false);

  // Common-AI state (PATIENT / DOCTOR)
  const assistantKey: AssistantKey | null = activeRole ? ROLE_TO_ASSISTANT[activeRole] ?? null : null;
  const [assistant, setAssistant] = useState<AssistantInfo | null>(null);
  const [assistantsState, setAssistantsState] = useState<'idle' | 'loading' | 'ready' | 'error'>('idle');
  const [conversationId, setConversationId] = useState<string | null>(null);
  const [view, setView] = useState<'chat' | 'history'>('chat');
  const [history, setHistory] = useState<ConversationSummary[]>([]);
  const [historyLoading, setHistoryLoading] = useState(false);
  const [historyError, setHistoryError] = useState<string | null>(null);
  const [deletingId, setDeletingId] = useState<string | null>(null);

  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const inFlight = useRef(false);
  const actionsInFlight = useRef<Set<string>>(new Set());
  const epoch = useRef(0); // bumped when the conversation context changes so stale replies are ignored
  const scrollRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  const useCommonAi = assistantKey !== null;
  const langKey = (language as string) || 'en';

  // Detect other open modals to avoid touch collisions
  useEffect(() => {
    const checkModal = () => {
      const modal = document.querySelector('div[role="dialog"]:not([data-assistant="true"])');
      setIsModalActive(!!modal);
    };
    checkModal();
    const observer = new MutationObserver(checkModal);
    observer.observe(document.body, { childList: true, subtree: true });
    return () => observer.disconnect();
  }, []);

  const getInitialMessage = (): string => {
    switch (activeRole) {
      case 'PATIENT': return t('ai.initial.patient');
      case 'DOCTOR': return t('ai.initial.doctor');
      case 'NURSE': return t('ai.initial.nurse');
      case 'PHARMACIST':
      case 'DISTRICT_SUPPLY_OFFICER':
      case 'STATE_SUPPLY_MANAGER': return t('ai.initial.supply');
      default: return t('ai.initial.governance');
    }
  };

  const resetConversation = useCallback(() => {
    epoch.current += 1;
    inFlight.current = false;
    setIsLoading(false);
    setConversationId(null);
    setMessages([]);
    setInput('');
    setView('chat');
  }, []);

  // Role change: drop state belonging to the previous role's assistant
  useEffect(() => {
    setAssistant(null);
    setAssistantsState('idle');
    setHistory([]);
    resetConversation();
  }, [activeRole, resetConversation]);

  const loadAssistants = useCallback(async () => {
    if (!assistantKey) return;
    setAssistantsState('loading');
    const res = await api.get<AssistantInfo[]>('/ai/assistants');
    if (res.error || !res.data) {
      setAssistantsState('error');
      return;
    }
    const found = res.data.find((a) => a.key === assistantKey) ?? null;
    setAssistant(found);
    setAssistantsState(found ? 'ready' : 'error');
  }, [assistantKey]);

  useEffect(() => {
    if (isOpen && assistantKey && assistantsState === 'idle') void loadAssistants();
  }, [isOpen, assistantKey, assistantsState, loadAssistants]);

  useEffect(() => {
    const el = scrollRef.current;
    if (el) el.scrollTop = el.scrollHeight;
  }, [messages, isLoading, view]);

  const describeError = (e: ApiError): string => {
    if (e.status === 429) return t('ai.rateLimited', 'You are sending messages too quickly. Please wait a moment and try again.');
    if (e.status === 0) return t('ai.error');
    return e.detail || t('state.error');
  };

  /* --------------------------------- Sending -------------------------------- */

  const send = async (rawText: string, opts: { skipUserBubble?: boolean } = {}) => {
    const text = rawText.trim();
    if (!text || inFlight.current) return;
    inFlight.current = true;
    const myEpoch = epoch.current;

    if (!opts.skipUserBubble) {
      setMessages((prev) => [...prev, { id: nextId(), sender: 'user', text }]);
    }
    setInput('');
    setIsLoading(true);

    const addAssistant = (m: Omit<ChatMessage, 'id' | 'sender'>) => {
      if (epoch.current !== myEpoch) return;
      setMessages((prev) => [...prev, { id: nextId(), sender: 'assistant', ...m }]);
    };

    try {
      if (useCommonAi && assistant) {
        const res = await api.post<ChatResponse>(`/ai/${assistant.key}/chat`, {
          message: text,
          conversation_id: conversationId,
          language: langKey,
        });
        if (epoch.current !== myEpoch) return;
        if (res.error || !res.data) {
          const err = res.error ?? ({ status: 0, title: '', detail: '' } as ApiError);
          addAssistant({ text: describeError(err), error: { retryText: text, retryable: isRetryableError(err) } });
        } else {
          const d = res.data;
          setConversationId(d.conversation_id);
          addAssistant({
            text: d.answer,
            emergency: d.emergency,
            refused: d.refused,
            sources: d.sources,
            action: d.pending_action && d.pending_action.status === 'PENDING'
              ? { id: d.pending_action.id, summary: d.pending_action.summary, status: d.pending_action.status, busy: false }
              : undefined,
          });
        }
      } else {
        // Legacy behaviour for all other roles
        const res = await api.post<any>('/governance/ai-assistant', { question: text, language });
        if (epoch.current !== myEpoch) return;
        if (res.data) {
          const d = res.data;
          let responseText = d.answer || d.response_text || d.response || d.advice || d.summary || JSON.stringify(d);
          if (language === 'ta' && d.answer_ta) responseText = d.answer_ta;
          addAssistant({ text: responseText, sources: d.sources, refused: d.refused });
        } else {
          addAssistant({
            text: res.error ? describeError(res.error) : t('state.error'),
            error: { retryText: text, retryable: true },
          });
        }
      }
    } catch {
      addAssistant({ text: t('ai.error'), error: { retryText: text, retryable: true } });
    } finally {
      if (epoch.current === myEpoch) {
        inFlight.current = false;
        setIsLoading(false);
      }
    }
  };

  const retry = (msgId: string, text: string) => {
    if (inFlight.current) return;
    setMessages((prev) => prev.filter((m) => m.id !== msgId));
    void send(text, { skipUserBubble: true });
  };

  /* ------------------------------ Pending actions ---------------------------- */

  const patchAction = (id: string, patch: Partial<ActionState>) =>
    setMessages((prev) => prev.map((m) => (m.action && m.action.id === id ? { ...m, action: { ...m.action, ...patch } } : m)));

  const runAction = async (id: string, kind: 'confirm' | 'cancel') => {
    if (actionsInFlight.current.has(id)) return; // double-click safe
    actionsInFlight.current.add(id);
    patchAction(id, { busy: true, error: undefined });
    try {
      const res = await api.post<PendingActionView>(`/ai/actions/${id}/${kind}`);
      if (res.error || !res.data) {
        const err = res.error ?? ({ status: 0, title: '', detail: '' } as ApiError);
        // Definitive client errors (expired, already handled, forbidden) close the card; transient ones allow retry.
        const closed = err.status >= 400 && err.status < 500 && err.status !== 429;
        patchAction(id, {
          busy: false,
          error: describeError(err),
          status: closed ? 'FAILED' : 'PENDING',
        });
      } else {
        const d = res.data;
        const fallback =
          d.status === 'EXECUTED' ? t('ai.action.done', 'Done.')
            : d.status === 'CANCELLED' ? t('ai.action.cancelled', 'Cancelled. Nothing was changed.')
              : d.status === 'EXPIRED' ? t('ai.action.expired', 'This request expired. Nothing was changed.')
                : t('ai.action.failed', 'This could not be completed. Nothing was changed.');
        patchAction(id, {
          busy: false,
          status: d.status,
          resultMessage: d.message || fallback,
          error: undefined,
        });
      }
    } catch {
      patchAction(id, { busy: false, error: t('ai.error'), status: 'PENDING' });
    } finally {
      actionsInFlight.current.delete(id);
    }
  };

  /* ------------------------------ Conversations ------------------------------ */

  const loadHistory = async () => {
    if (!assistant) return;
    setHistoryLoading(true);
    setHistoryError(null);
    const res = await api.get<ConversationSummary[]>(`/ai/${assistant.key}/conversations`);
    if (res.error || !res.data) setHistoryError(res.error ? describeError(res.error) : t('state.error'));
    else setHistory(res.data);
    setHistoryLoading(false);
  };

  const openHistory = () => {
    setView('history');
    void loadHistory();
  };

  const openConversation = async (id: string) => {
    epoch.current += 1;
    inFlight.current = false;
    setIsLoading(false);
    setHistoryLoading(true);
    setHistoryError(null);
    const res = await api.get<ConversationDetail>(`/ai/conversations/${id}`);
    setHistoryLoading(false);
    if (res.error || !res.data) {
      setHistoryError(res.error ? describeError(res.error) : t('state.error'));
      return;
    }
    const pendingById = new Map(res.data.pending_actions.map((a) => [a.id, a]));
    setMessages(
      res.data.messages.map((m): ChatMessage => {
        const pid = m.meta?.pending_action_id;
        const pa = pid ? pendingById.get(pid) : undefined;
        return {
          id: m.id,
          sender: m.role === 'user' ? 'user' : 'assistant',
          text: m.content,
          emergency: !!m.meta?.emergency,
          sources: m.meta?.sources,
          action: pa && pa.status === 'PENDING'
            ? { id: pa.id, summary: pa.summary, status: pa.status, busy: false }
            : undefined,
        };
      })
    );
    setConversationId(res.data.conversation.id);
    setView('chat');
  };

  const deleteConversation = async (id: string) => {
    if (deletingId || !assistant) return;
    setDeletingId(id);
    setHistoryError(null);
    // The shared api service cannot parse an empty 204 body, so confirm the outcome by re-listing.
    await api.delete(`/ai/conversations/${id}`);
    const list = await api.get<ConversationSummary[]>(`/ai/${assistant.key}/conversations`);
    if (list.data) {
      setHistory(list.data);
      if (list.data.some((c) => c.id === id)) {
        setHistoryError(t('ai.deleteFailed', 'Could not delete this conversation. Please try again.'));
      } else if (conversationId === id) {
        resetConversation();
        setView('history');
      }
    } else {
      setHistoryError(list.error ? describeError(list.error) : t('state.error'));
    }
    setDeletingId(null);
  };

  /* --------------------------------- Rendering ------------------------------- */

  const getAssistantTitle = () => {
    if (assistant?.title) return assistant.title;
    if (activeRole === 'PATIENT') return t('ai.wellnessTitle');
    if (activeRole === 'DOCTOR' || activeRole === 'NURSE') return t('ai.clinicalTitle');
    return t('ai.governanceTitle');
  };

  const starters = assistant ? assistant.starters[langKey] ?? assistant.starters.en ?? [] : [];
  const assistantBlocked = useCommonAi && assistantsState !== 'ready';
  const notConfigured = useCommonAi && assistant && !assistant.configured;
  const inputDisabled = isLoading || assistantBlocked || !!notConfigured;

  const headerBtn: React.CSSProperties = {
    background: 'none', border: 'none', color: '#ffffff', cursor: 'pointer',
    padding: '0.35rem', display: 'flex', borderRadius: '6px',
  };
  const chipStyle: React.CSSProperties = {
    background: 'none', border: '1px solid rgba(37, 99, 235, 0.3)', borderRadius: '6px',
    padding: '0.3rem 0.55rem', textAlign: 'left', fontSize: '0.775rem', color: 'var(--primary)',
    cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '0.25rem',
  };

  const renderAction = (a: ActionState) => {
    const done = TERMINAL_STATUSES.includes(a.status);
    const failed = a.status === 'FAILED' || a.status === 'EXPIRED';
    return (
      <div
        role="group"
        aria-label={t('ai.action.title', 'Action awaiting your confirmation')}
        style={{
          marginTop: '0.5rem', padding: '0.65rem 0.75rem', borderRadius: '10px',
          border: `1px solid ${failed ? '#fca5a5' : done ? '#86efac' : 'var(--primary)'}`,
          backgroundColor: failed ? '#fef2f2' : done ? '#f0fdf4' : '#eff6ff',
        }}
      >
        <div style={{ fontSize: '0.7rem', fontWeight: 700, textTransform: 'uppercase', opacity: 0.7, marginBottom: '0.25rem' }}>
          {t('ai.action.title', 'Action awaiting your confirmation')}
        </div>
        <div style={{ fontSize: '0.85rem', fontWeight: 600, marginBottom: '0.5rem' }}>{a.summary}</div>
        {done ? (
          <div
            role="status"
            style={{ fontSize: '0.825rem', color: failed ? '#b91c1c' : '#15803d', display: 'flex', gap: '0.35rem', alignItems: 'flex-start' }}
          >
            {failed ? <AlertCircle size={15} style={{ flexShrink: 0, marginTop: 2 }} /> : <Check size={15} style={{ flexShrink: 0, marginTop: 2 }} />}
            <span>{a.resultMessage || a.error}</span>
          </div>
        ) : (
          <>
            {a.error && (
              <div role="alert" style={{ fontSize: '0.8rem', color: '#b91c1c', marginBottom: '0.45rem' }}>{a.error}</div>
            )}
            <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap' }}>
              <button
                type="button"
                className="btn-primary"
                disabled={a.busy}
                aria-busy={a.busy}
                onClick={() => void runAction(a.id, 'confirm')}
                style={{ padding: '0.4rem 0.9rem', fontSize: '0.8rem', display: 'flex', alignItems: 'center', gap: '0.3rem' }}
              >
                {a.busy && <Loader2 size={13} className="animate-spin" />}
                {t('ai.action.confirm', 'Confirm')}
              </button>
              <button
                type="button"
                disabled={a.busy}
                onClick={() => void runAction(a.id, 'cancel')}
                style={{
                  padding: '0.4rem 0.9rem', fontSize: '0.8rem', borderRadius: '8px', cursor: a.busy ? 'not-allowed' : 'pointer',
                  border: '1px solid var(--border-color)', background: '#ffffff', color: 'var(--text-main)',
                  opacity: a.busy ? 0.6 : 1,
                }}
              >
                {t('ai.action.cancel', 'Cancel')}
              </button>
            </div>
          </>
        )}
      </div>
    );
  };

  const renderMessage = (msg: ChatMessage) => {
    const isUser = msg.sender === 'user';
    return (
      <div
        key={msg.id}
        style={{
          alignSelf: isUser ? 'flex-end' : 'flex-start', maxWidth: '88%',
          display: 'flex', flexDirection: 'column', gap: '0.35rem',
        }}
      >
        {msg.emergency && (
          <div
            role="alert"
            style={{
              padding: '0.6rem 0.8rem', borderRadius: '10px', backgroundColor: '#dc2626', color: '#ffffff',
              fontSize: '0.85rem', fontWeight: 700, display: 'flex', alignItems: 'center', gap: '0.5rem',
              boxShadow: '0 2px 6px rgba(220, 38, 38, 0.35)',
            }}
          >
            <Siren size={18} style={{ flexShrink: 0 }} />
            {t('ai.emergency', 'This may be an emergency. Seek urgent medical help now or call 108.')}
          </div>
        )}
        <div
          style={{
            padding: '0.7rem 0.95rem', borderRadius: '14px', fontSize: '0.875rem', lineHeight: 1.45,
            backgroundColor: isUser ? 'var(--primary)' : msg.error ? '#fef2f2' : '#ffffff',
            color: isUser ? '#ffffff' : msg.error ? '#991b1b' : 'var(--text-main)',
            border: isUser ? 'none' : `${msg.emergency ? '2px' : '1px'} solid ${msg.emergency ? '#dc2626' : msg.error ? '#fca5a5' : 'var(--border-color)'}`,
            boxShadow: '0 1px 2px 0 rgba(0, 0, 0, 0.05)',
          }}
        >
          {isUser || msg.error ? msg.text : <Markdown text={msg.text} />}

          {msg.refused && (
            <div
              style={{
                marginTop: '0.5rem', padding: '0.4rem 0.6rem', borderRadius: '6px',
                backgroundColor: 'rgba(239, 68, 68, 0.1)', color: '#dc2626', fontSize: '0.75rem',
                display: 'flex', alignItems: 'center', gap: '0.35rem',
              }}
            >
              <AlertCircle size={14} /> {t('ai.safetyWarning')}
            </div>
          )}

          {msg.action && renderAction(msg.action)}

          {msg.error?.retryable && (
            <button
              type="button"
              onClick={() => retry(msg.id, msg.error!.retryText)}
              disabled={isLoading}
              aria-label={t('ai.retry', 'Retry')}
              style={{
                marginTop: '0.5rem', padding: '0.3rem 0.65rem', fontSize: '0.775rem', borderRadius: '6px',
                border: '1px solid #dc2626', background: '#ffffff', color: '#b91c1c',
                cursor: isLoading ? 'not-allowed' : 'pointer', display: 'flex', alignItems: 'center', gap: '0.3rem',
              }}
            >
              <RotateCcw size={12} /> {t('ai.retry', 'Retry')}
            </button>
          )}
        </div>

        {msg.sources && msg.sources.length > 0 && (
          <div
            aria-label={t('ai.sources', 'Sources')}
            style={{ display: 'flex', flexWrap: 'wrap', gap: '0.25rem', alignItems: 'center', paddingLeft: '0.25rem' }}
          >
            <span style={{ fontSize: '0.675rem', color: 'var(--text-muted)' }}>{t('ai.basedOn', 'Based on:')}</span>
            {msg.sources.map((s, i) => (
              <span
                key={`${s}-${i}`}
                style={{
                  fontSize: '0.675rem', padding: '0.1rem 0.45rem', borderRadius: '999px',
                  backgroundColor: 'rgba(37, 99, 235, 0.08)', color: 'var(--primary)',
                  border: '1px solid rgba(37, 99, 235, 0.2)',
                }}
              >
                {s}
              </span>
            ))}
          </div>
        )}
      </div>
    );
  };

  const renderHistory = () => (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
      {historyError && (
        <div role="alert" style={{ fontSize: '0.8rem', color: '#b91c1c' }}>{historyError}</div>
      )}
      {historyLoading && (
        <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center', color: 'var(--text-muted)', fontSize: '0.825rem' }}>
          <Loader2 size={16} className="animate-spin" /> {t('state.loading', 'Loading...')}
        </div>
      )}
      {!historyLoading && history.length === 0 && !historyError && (
        <div style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>
          {t('ai.noConversations', 'No previous conversations yet.')}
        </div>
      )}
      {history.map((c) => (
        <div
          key={c.id}
          style={{
            display: 'flex', alignItems: 'stretch', border: '1px solid var(--border-color)',
            borderRadius: '10px', backgroundColor: '#ffffff', overflow: 'hidden',
          }}
        >
          <button
            type="button"
            onClick={() => void openConversation(c.id)}
            disabled={historyLoading}
            style={{
              flex: 1, textAlign: 'left', padding: '0.6rem 0.75rem', background: 'none', border: 'none',
              cursor: 'pointer', minWidth: 0, color: 'var(--text-main)',
            }}
          >
            <div style={{ fontSize: '0.85rem', fontWeight: 600, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
              {c.title || t('ai.untitled', 'Conversation')}
            </div>
            <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>
              {new Date(c.updated_at).toLocaleString()}
            </div>
          </button>
          <button
            type="button"
            onClick={() => void deleteConversation(c.id)}
            disabled={deletingId !== null}
            aria-label={t('ai.deleteConversation', 'Delete conversation')}
            title={t('ai.deleteConversation', 'Delete conversation')}
            style={{
              padding: '0 0.75rem', background: 'none', border: 'none', borderLeft: '1px solid var(--border-color)',
              color: '#b91c1c', cursor: deletingId ? 'not-allowed' : 'pointer', display: 'flex', alignItems: 'center',
            }}
          >
            {deletingId === c.id ? <Loader2 size={15} className="animate-spin" /> : <Trash2 size={15} />}
          </button>
        </div>
      ))}
    </div>
  );

  const renderChatBody = () => (
    <>
      {assistantsState === 'loading' && useCommonAi && (
        <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center', color: 'var(--text-muted)', fontSize: '0.825rem' }}>
          <Loader2 size={16} className="animate-spin" /> {t('state.loading', 'Loading...')}
        </div>
      )}
      {useCommonAi && assistantsState === 'error' && (
        <div role="alert" style={{ fontSize: '0.85rem', color: '#991b1b', display: 'flex', flexDirection: 'column', gap: '0.5rem', alignItems: 'flex-start' }}>
          {t('ai.unavailable', 'The AI assistant is not available right now.')}
          <button type="button" onClick={() => void loadAssistants()} style={chipStyle}>
            <RotateCcw size={12} /> {t('ai.retry', 'Retry')}
          </button>
        </div>
      )}
      {notConfigured && (
        <div role="status" style={{ fontSize: '0.825rem', color: '#92400e', backgroundColor: '#fffbeb', border: '1px solid #fde68a', borderRadius: '8px', padding: '0.5rem 0.7rem' }}>
          {t('ai.notConfigured', 'The AI service is not configured on this server yet.')}
        </div>
      )}

      {!assistantBlocked && messages.length === 0 && (
        <>
          <div
            style={{
              alignSelf: 'flex-start', maxWidth: '88%', padding: '0.7rem 0.95rem', borderRadius: '14px',
              fontSize: '0.875rem', lineHeight: 1.45, backgroundColor: '#ffffff', color: 'var(--text-main)',
              border: '1px solid var(--border-color)',
            }}
          >
            {getInitialMessage()}
          </div>
          {starters.length > 0 && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.3rem' }} aria-label={t('ai.starters', 'Suggested questions')}>
              {starters.map((s, i) => (
                <button
                  key={i}
                  type="button"
                  disabled={inputDisabled}
                  onClick={() => void send(s)}
                  style={{ ...chipStyle, opacity: inputDisabled ? 0.6 : 1 }}
                >
                  <ChevronRight size={12} style={{ flexShrink: 0 }} /> {s}
                </button>
              ))}
            </div>
          )}
        </>
      )}

      {messages.map(renderMessage)}

      {isLoading && (
        <div
          role="status"
          aria-live="polite"
          style={{
            alignSelf: 'flex-start', padding: '0.65rem 1rem', borderRadius: '14px', backgroundColor: '#ffffff',
            border: '1px solid var(--border-color)', display: 'flex', alignItems: 'center', gap: '0.5rem',
            color: 'var(--text-muted)', fontSize: '0.825rem',
          }}
        >
          <Loader2 size={16} className="animate-spin" style={{ color: 'var(--primary)' }} />
          {t('ai.analyzing')}
        </div>
      )}
    </>
  );

  return (
    <>
      {/* Floating Toggle Button */}
      <div
        style={{
          position: 'fixed',
          bottom: 'calc(1.5rem + env(safe-area-inset-bottom, 0px))',
          right: '1.5rem',
          zIndex: isModalActive ? 100 : 850,
          pointerEvents: isModalActive ? 'none' : 'auto',
          opacity: isModalActive ? 0.3 : 1,
          transition: 'opacity 0.2s ease, transform 0.2s ease',
        }}
      >
        <button
          onClick={() => setIsOpen(!isOpen)}
          aria-label={isOpen ? t('ai.closeAssistant') : t('ai.openAssistant')}
          title={isOpen ? t('ai.closeAssistant') : t('ai.openAssistant')}
          aria-expanded={isOpen}
          style={{
            width: '56px', height: '56px', borderRadius: '50%', backgroundColor: 'var(--primary)', color: '#ffffff',
            border: 'none',
            boxShadow: '0 10px 25px -5px rgba(37, 99, 235, 0.4), 0 8px 10px -6px rgba(37, 99, 235, 0.3)',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            cursor: isModalActive ? 'default' : 'pointer', transition: 'transform 0.2s ease',
          }}
          onMouseEnter={(e) => { if (!isModalActive) e.currentTarget.style.transform = 'scale(1.06)'; }}
          onMouseLeave={(e) => { e.currentTarget.style.transform = 'scale(1)'; }}
        >
          {isOpen ? <X size={24} /> : <Sparkles size={24} />}
        </button>
      </div>

      {isOpen && (
        <div
          role="dialog"
          data-assistant="true"
          aria-label={getAssistantTitle()}
          onKeyDown={(e) => { if (e.key === 'Escape') setIsOpen(false); }}
          style={{
            position: 'fixed',
            bottom: 'calc(5.5rem + env(safe-area-inset-bottom, 0px))',
            right: '1.5rem',
            width: 'calc(100vw - 3rem)',
            maxWidth: '420px',
            height: 'min(620px, calc(100vh - 8rem))',
            maxHeight: 'calc(100vh - 8rem)',
            backgroundColor: '#ffffff',
            borderRadius: '16px',
            boxShadow: '0 25px 50px -12px rgba(0, 0, 0, 0.25)',
            border: '1px solid var(--border-color)',
            zIndex: 900,
            display: 'flex',
            flexDirection: 'column',
            overflow: 'hidden',
          }}
        >
          {/* Header */}
          <div
            style={{
              padding: '0.75rem 1rem', backgroundColor: 'var(--primary)', color: '#ffffff',
              display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: '0.5rem',
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.65rem', minWidth: 0 }}>
              <div
                style={{
                  width: '32px', height: '32px', borderRadius: '8px', backgroundColor: 'rgba(255, 255, 255, 0.2)',
                  display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0,
                }}
              >
                <Bot size={20} />
              </div>
              <div style={{ minWidth: 0 }}>
                <h4 style={{ margin: 0, fontSize: '0.95rem', fontWeight: 700, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                  {getAssistantTitle()}
                </h4>
                <span style={{ fontSize: '0.725rem', opacity: 0.85 }}>
                  {activeRole ? t(`role.${activeRole}`, activeRole.replace(/_/g, ' ')) : t('nav.workspace')}
                </span>
              </div>
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.1rem', flexShrink: 0 }}>
              {useCommonAi && assistant && (
                <>
                  <button
                    type="button"
                    onClick={view === 'history' ? () => setView('chat') : openHistory}
                    aria-label={view === 'history' ? t('ai.backToChat', 'Back to chat') : t('ai.history', 'Conversation history')}
                    title={view === 'history' ? t('ai.backToChat', 'Back to chat') : t('ai.history', 'Conversation history')}
                    style={headerBtn}
                  >
                    {view === 'history' ? <ArrowLeft size={18} /> : <History size={18} />}
                  </button>
                  <button
                    type="button"
                    onClick={() => { resetConversation(); setTimeout(() => inputRef.current?.focus(), 0); }}
                    aria-label={t('ai.newConversation', 'New conversation')}
                    title={t('ai.newConversation', 'New conversation')}
                    style={headerBtn}
                  >
                    <Plus size={18} />
                  </button>
                </>
              )}
              {!useCommonAi && messages.length > 0 && (
                <button
                  type="button"
                  onClick={resetConversation}
                  aria-label={t('ai.newConversation', 'New conversation')}
                  title={t('ai.newConversation', 'New conversation')}
                  style={headerBtn}
                >
                  <Plus size={18} />
                </button>
              )}
              <button
                type="button"
                onClick={() => setIsOpen(false)}
                aria-label={t('ai.closeAssistant')}
                style={headerBtn}
              >
                <X size={20} />
              </button>
            </div>
          </div>

          {/* Body */}
          <div
            ref={scrollRef}
            style={{
              flex: 1, overflowY: 'auto', padding: '1rem', display: 'flex', flexDirection: 'column', gap: '0.85rem',
              backgroundColor: 'rgba(248, 250, 252, 0.5)',
            }}
            aria-live="polite"
          >
            {view === 'history' ? renderHistory() : renderChatBody()}
          </div>

          {/* Disclaimer */}
          <div
            style={{
              padding: '0.4rem 0.75rem', backgroundColor: 'rgba(241, 245, 249, 0.8)',
              borderTop: '1px solid var(--border-color)', fontSize: '0.675rem', color: 'var(--text-muted)', textAlign: 'center',
            }}
          >
            {t('ai.disclaimer')}
          </div>

          {/* Input */}
          {view === 'chat' && (
            <form
              onSubmit={(e) => { e.preventDefault(); void send(input); }}
              style={{
                padding: '0.75rem 1rem', borderTop: '1px solid var(--border-color)', display: 'flex', gap: '0.5rem',
                backgroundColor: '#ffffff',
              }}
            >
              <MicButton
                language={langKey}
                disabled={assistantBlocked || !!notConfigured}
                onTranscript={(text) => setInput((prev) => (prev ? `${prev} ${text}` : text).slice(0, 4000))}
              />
              <input
                ref={inputRef}
                type="text"
                value={input}
                maxLength={4000}
                onChange={(e) => setInput(e.target.value)}
                disabled={assistantBlocked || !!notConfigured}
                aria-label={t('ai.askPlaceholder')}
                placeholder={t('ai.askPlaceholder')}
                style={{
                  flex: 1, minWidth: 0, padding: '0.6rem 0.85rem', borderRadius: '8px',
                  border: '1px solid var(--border-color)', fontSize: '0.85rem',
                }}
              />
              <button
                type="submit"
                disabled={inputDisabled || !input.trim()}
                className="btn-primary"
                aria-label={t('ai.send')}
                title={t('ai.send')}
                style={{ padding: '0.6rem 0.85rem', display: 'flex', alignItems: 'center', justifyContent: 'center' }}
              >
                <Send size={16} />
              </button>
              <SpeakButton
                language={langKey}
                textToSpeak={[...messages].reverse().find((m) => m.sender === 'assistant' && !m.error)?.text ?? ''}
              />
            </form>
          )}
        </div>
      )}
    </>
  );
};
