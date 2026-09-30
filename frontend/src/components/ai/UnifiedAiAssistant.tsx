import React, { useState, useEffect, useRef, useCallback } from 'react';
import {
  X, Send, Loader2, Sparkles, ChevronRight, History, Plus, Trash2, RotateCcw, Siren, Check, ArrowLeft,
  PhoneCall, PanelRightClose, TriangleAlert, LocateFixed,
} from 'lucide-react';
import { useAuth } from '../../context/AuthContext';
import { useLanguage } from '../../context/LanguageContext';
import { api } from '../../services/api';
import type { ApiError } from '../../services/types';
import { MicButton, SpeakButton } from './VoiceControls';
import { Button } from '../ui/button';
import { Input } from '../ui/input';
import { StatusBadge } from '../ui/status-badge';
import { Sheet, SheetContent, SheetDescription, SheetTitle } from '../ui/sheet';
import { cn } from '../../lib/utils';
import { formatRoleName } from '../../utils/formatters';
import { useShell } from '../layout/ShellContext';
import { useNavCatalogue } from '../layout/nav-catalogue';

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
  status: string;
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

let uid = 0;
const nextId = () => `m${Date.now()}_${uid++}`;

const isRetryableError = (e: ApiError) => e.status === 0 || e.status === 429 || e.status >= 500;

const primaryButton = 'bg-primary text-primary-foreground hover:bg-primary-hover';

/* ---------------------------------------------------------------------------------------------
   Safe structured rendering: headings, bullet/numbered lists, **bold**, `code`. No HTML is ever injected:
   everything becomes React text nodes.
   --------------------------------------------------------------------------------------------- */

const renderInline = (text: string, keyPrefix: string): React.ReactNode[] =>
  text.split(/(\*\*[^*]+\*\*|`[^`]+`)/g).map((part, i) => {
    if (part.startsWith('**') && part.endsWith('**') && part.length > 4) {
      return <strong key={`${keyPrefix}-${i}`} className="font-semibold text-foreground">{part.slice(2, -2)}</strong>;
    }
    if (part.startsWith('`') && part.endsWith('`') && part.length > 2) {
      return <code key={`${keyPrefix}-${i}`} className="rounded-sm bg-muted px-1 font-mono text-caption">{part.slice(1, -1)}</code>;
    }
    return <React.Fragment key={`${keyPrefix}-${i}`}>{part}</React.Fragment>;
  });

const Markdown: React.FC<{ text: string }> = ({ text }) => {
  const blocks: React.ReactNode[] = [];
  let list: { ordered: boolean; items: string[] } | null = null;
  let para: string[] = [];

  const flushPara = () => {
    if (para.length) {
      const k = `p${blocks.length}`;
      blocks.push(
        <p key={k} className="text-small leading-relaxed text-foreground">
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
        <Tag key={k} className={cn('space-y-1 pl-5 text-small leading-relaxed text-foreground', list.ordered ? 'list-decimal' : 'list-disc')}>
          {list.items.map((it, i) => <li key={i}>{renderInline(it, `${k}-${i}`)}</li>)}
        </Tag>
      );
      list = null;
    }
  };

  text.split(/\r?\n/).forEach((raw) => {
    const line = raw.trimEnd();
    const heading = /^\s*#{1,6}\s+(.*)$/.exec(line);
    const bullet = /^\s*(?:[-*•])\s+(.*)$/.exec(line);
    const numbered = /^\s*\d+[.)]\s+(.*)$/.exec(line);
    if (heading) {
      flushPara();
      flushList();
      const k = `h${blocks.length}`;
      blocks.push(
        <h3 key={k} className="pt-1 text-small font-semibold text-foreground">
          {renderInline(heading[1], k)}
        </h3>
      );
    } else if (bullet || numbered) {
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
      para.push(line);
    }
  });
  flushPara();
  flushList();
  return <div className="space-y-2 break-words">{blocks}</div>;
};

/** Quiet AI marker: small label with the ai token tint. */
const AiMarker: React.FC<{ label?: string }> = ({ label = 'AI' }) => (
  <span className="inline-flex items-center gap-1 text-caption font-semibold text-ai-text">
    <Sparkles className="size-3" aria-hidden="true" />
    {label}
  </span>
);

export const UnifiedAiAssistant: React.FC = () => {
  const { activeRole, scope } = useAuth();
  const { language, t } = useLanguage();
  const { aiOpen: isOpen, setAiOpen, aiDockable } = useShell();
  const { current } = useNavCatalogue();

  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);

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
  const epoch = useRef(0);
  const scrollRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  const wasOpen = useRef(false);

  const useCommonAi = assistantKey !== null;
  const langKey = (language as string) || 'en';

  const getInitialMessage = (): string => {
    switch (activeRole) {
      case 'PATIENT': return t('ai.initial.patient') || 'Hello! I am your Citizen Health Assistant. I can help answer questions about your health, find nearest facilities, and explain appointments.';
      case 'DOCTOR': return t('ai.initial.doctor') || 'Clinical Assistant initialized. Ready to support drug interaction reviews, ICD-10 suggestions, and protocol checks.';
      case 'NURSE': return t('ai.initial.nurse') || 'Triage Clinical Support online. Ready to assist with vitals categorization and cold chain monitoring.';
      case 'PHARMACIST':
      case 'DISTRICT_SUPPLY_OFFICER':
      case 'STATE_SUPPLY_MANAGER': return t('ai.initial.supply') || 'Supply Chain Assistant active. Tracking buffer thresholds and stockout forecasts.';
      default: return t('ai.initial.governance') || 'Public Health Governance Assistant ready for epidemiological and regional performance queries.';
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
  }, [messages, isLoading, view, isOpen]);

  // When the docked panel is opened from the top bar, put the cursor in the question field.
  useEffect(() => {
    if (isOpen && !wasOpen.current && aiDockable) {
      const id = window.setTimeout(() => inputRef.current?.focus(), 0);
      wasOpen.current = true;
      return () => window.clearTimeout(id);
    }
    wasOpen.current = isOpen;
  }, [isOpen, aiDockable]);

  const describeError = (e: ApiError): string => {
    if (e.status === 429) return t('ai.rateLimited') || 'You are sending messages too quickly. Please wait a moment and try again.';
    if (e.status === 0) return t('ai.error') || 'Assistant service is temporarily unavailable.';
    return e.detail || t('state.error') || 'An unexpected error occurred.';
  };

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
        const res = await api.post<{ response: string; error?: string }>('/ai/chat', {
          message: text,
          language: langKey,
        });
        if (epoch.current !== myEpoch) return;
        if (res.error || !res.data) {
          const err = res.error ?? ({ status: 0, title: '', detail: '' } as ApiError);
          addAssistant({ text: describeError(err), error: { retryText: text, retryable: isRetryableError(err) } });
        } else {
          addAssistant({ text: res.data.response });
        }
      }
    } finally {
      if (epoch.current === myEpoch) {
        inFlight.current = false;
        setIsLoading(false);
      }
    }
  };

  const retry = (failedId: string, retryText: string) => {
    setMessages((prev) => prev.filter((m) => m.id !== failedId));
    void send(retryText, { skipUserBubble: true });
  };

  const actionStatusText = (status: string): string => {
    if (status === 'EXECUTED') return t('ai.action.done', 'Done.');
    if (status === 'CANCELLED') return t('ai.action.cancelled', 'Cancelled. Nothing was changed.');
    if (status === 'EXPIRED') return t('ai.action.expired', 'This request expired. Nothing was changed.');
    if (status === 'FAILED') return t('ai.action.failed', 'This could not be completed. Nothing was changed.');
    return status;
  };

  const executeAction = async (actionId: string, confirm: boolean) => {
    if (actionsInFlight.current.has(actionId)) return;
    actionsInFlight.current.add(actionId);

    setMessages((prev) =>
      prev.map((m) => m.action?.id === actionId ? { ...m, action: { ...m.action, busy: true, error: undefined } } : m)
    );

    const res = await api.post<{
      status: string;
      result?: Record<string, unknown> | null;
      already_completed?: boolean;
      message?: string;
    }>(`/ai/actions/${actionId}/execute`, { confirm });

    actionsInFlight.current.delete(actionId);

    setMessages((prev) =>
      prev.map((m) => {
        if (m.action?.id !== actionId) return m;
        if (res.error || !res.data) {
          const err = res.error ?? ({ status: 0, title: '', detail: '' } as ApiError);
          return { ...m, action: { ...m.action, busy: false, error: describeError(err) } };
        }
        const data = res.data;
        return {
          ...m,
          action: {
            ...m.action,
            busy: false,
            status: data.status,
            resultMessage: data.message || actionStatusText(data.status),
          },
        };
      })
    );
  };

  const openHistory = async () => {
    if (!assistant) return;
    setView('history');
    setHistoryLoading(true);
    setHistoryError(null);
    const res = await api.get<ConversationSummary[]>(`/ai/${assistant.key}/conversations`);
    setHistoryLoading(false);
    if (res.error || !res.data) {
      setHistoryError(describeError(res.error ?? ({ status: 0, title: '', detail: '' } as ApiError)));
    } else {
      setHistory(res.data);
    }
  };

  const openConversation = async (id: string) => {
    if (!assistant) return;
    setIsLoading(true);
    const res = await api.get<ConversationDetail>(`/ai/${assistant.key}/conversations/${id}`);
    setIsLoading(false);
    if (res.error || !res.data) {
      setHistoryError(describeError(res.error ?? ({ status: 0, title: '', detail: '' } as ApiError)));
      return;
    }
    const d = res.data;
    setConversationId(d.conversation.id);
    const actionsById = new Map<string, PendingActionView>((d.pending_actions || []).map((a) => [a.id, a]));
    const rebuilt: ChatMessage[] = (d.messages || []).map((m) => {
      const isUser = m.role.toLowerCase() === 'user';
      const actionRef = m.meta?.pending_action_id ? actionsById.get(m.meta.pending_action_id) : undefined;
      return {
        id: m.id,
        sender: isUser ? 'user' : 'assistant',
        text: m.content,
        emergency: m.meta?.emergency,
        sources: m.meta?.sources,
        action: actionRef
          ? {
              id: actionRef.id,
              summary: actionRef.summary,
              status: actionRef.status,
              busy: false,
              resultMessage: actionRef.message || undefined,
            }
          : undefined,
      };
    });
    setMessages(rebuilt);
    setView('chat');
  };

  const deleteConversation = async (id: string) => {
    if (!assistant) return;
    setDeletingId(id);
    setHistoryError(null);
    const res = await api.delete(`/ai/${assistant.key}/conversations/${id}`);
    setDeletingId(null);
    if (!res.error) {
      setHistory((prev) => prev.filter((c) => c.id !== id));
      if (conversationId === id) resetConversation();
    } else {
      setHistoryError(t('ai.deleteFailed', 'Could not delete this conversation. Please try again.'));
    }
  };

  const starters: string[] = assistant?.starters?.[langKey] || assistant?.starters?.en || [];
  const notConfigured = assistant && !assistant.configured;
  const assistantBlocked = useCommonAi && assistantsState === 'error';
  const assistantPending = useCommonAi && !assistant && assistantsState !== 'error';
  const inputDisabled = isLoading || inFlight.current || assistantBlocked || assistantPending || !!notConfigured;

  const getAssistantTitle = (): string => {
    if (activeRole === 'PATIENT') return t('ai.wellnessTitle', 'Citizen Health Assistant');
    if (activeRole === 'DOCTOR') return t('ai.clinicalTitle', 'Clinical Decision Support');
    if (activeRole === 'NURSE' || activeRole === 'PHARMACIST') return t('ai.assistant', 'AI Assistant');
    return `${activeRole ? formatRoleName(activeRole, t) : 'Health'} ${t('ai.assistantSuffix', 'Assistant')}`;
  };

  const title = getAssistantTitle();
  const contextLabel = [current.sectionLabel, current.pageLabel].filter(Boolean).join(' / ');

  /* ------------------------------------ panel ------------------------------------ */

  const renderPanel = (variant: 'docked' | 'sheet') => (
    <div className="flex h-full min-h-0 flex-col bg-card">
      {/* Header */}
      <div className={cn('flex shrink-0 items-start justify-between gap-2 border-b border-border px-4 py-3', variant === 'sheet' && 'pr-12')}>
        <div className="min-w-0 space-y-0.5">
          <AiMarker label={t('ai.short', 'AI')} />
          {variant === 'sheet' ? (
            <SheetTitle className="truncate text-section-title">{title}</SheetTitle>
          ) : (
            <h2 className="truncate text-section-title text-foreground">{title}</h2>
          )}
          <p className="truncate text-caption text-muted-foreground">
            {activeRole ? formatRoleName(activeRole, t) : 'Health Network'}
            {scope ? ` · ${String(scope).toUpperCase()}` : ''}
          </p>
        </div>
        <div className="flex shrink-0 items-center gap-0.5">
          {useCommonAi && assistant && (
            <>
              <Button
                variant="ghost"
                size="icon-sm"
                onClick={view === 'history' ? () => setView('chat') : openHistory}
                aria-label={view === 'history' ? t('ai.backToChat', 'Back to chat') : t('ai.history', 'Conversation history')}
                title={view === 'history' ? t('ai.backToChat', 'Back to chat') : t('ai.history', 'Conversation history')}
              >
                {view === 'history' ? <ArrowLeft className="size-4" aria-hidden="true" /> : <History className="size-4" aria-hidden="true" />}
              </Button>
              <Button
                variant="ghost"
                size="icon-sm"
                onClick={() => { resetConversation(); setTimeout(() => inputRef.current?.focus(), 0); }}
                aria-label={t('ai.newConversation', 'New conversation')}
                title={t('ai.newConversation', 'New conversation')}
              >
                <Plus className="size-4" aria-hidden="true" />
              </Button>
            </>
          )}
          {variant === 'docked' && (
            <Button
              variant="ghost"
              size="icon-sm"
              onClick={() => setAiOpen(false)}
              aria-label={t('ai.closeAssistant', 'Close AI Assistant')}
              title={t('ai.closeAssistant', 'Close AI Assistant')}
            >
              <PanelRightClose className="size-4" aria-hidden="true" />
            </Button>
          )}
        </div>
      </div>

      {/* Context: UI only. It is NOT sent to the assistant and the assistant cannot see the page. */}
      <div className="shrink-0 border-b border-border bg-muted/50 px-4 py-2">
        <div className="flex items-center gap-1.5 text-caption font-semibold text-muted-foreground">
          <LocateFixed className="size-3.5" aria-hidden="true" />
          {t('ai.context', 'You are viewing')}
        </div>
        <p className="truncate text-small font-medium text-foreground" title={contextLabel}>{contextLabel}</p>
        <p className="text-caption text-muted-foreground">
          {t('ai.contextNote', 'For your reference only. The assistant does not see this page, so include the details it needs.')}
        </p>
      </div>

      {/* Conversation */}
      <div
        ref={scrollRef}
        role="log"
        aria-live="polite"
        aria-relevant="additions text"
        aria-label={title}
        className="min-h-0 flex-1 space-y-4 overflow-y-auto px-4 py-4"
      >
        {view === 'history' ? (
          <div className="space-y-2">
            <h3 className="text-small font-semibold text-foreground">{t('ai.history', 'Conversation history')}</h3>
            {historyLoading && (
              <div className="flex items-center gap-2 py-3 text-small text-muted-foreground" role="status">
                <Loader2 className="size-4 animate-spin" aria-hidden="true" />
                {t('state.loading', 'Loading')}
              </div>
            )}
            {historyError && <p className="text-small text-danger-text">{historyError}</p>}
            {!historyLoading && !historyError && history.length === 0 && (
              <p className="py-3 text-small text-muted-foreground">{t('ai.noConversations', 'No previous conversations yet.')}</p>
            )}
            <ul className="space-y-1.5">
              {history.map((c) => (
                <li key={c.id} className="flex items-center justify-between gap-1 rounded-lg border border-border bg-card pr-1 hover:bg-accent">
                  <button
                    type="button"
                    onClick={() => void openConversation(c.id)}
                    className="min-w-0 flex-1 cursor-pointer rounded-lg px-3 py-2 text-left focus-visible:outline-2 focus-visible:-outline-offset-2 focus-visible:outline-ring"
                  >
                    <span className="block truncate text-small font-medium text-foreground">{c.title || t('ai.untitled', 'Conversation')}</span>
                    <span className="block text-caption text-muted-foreground">{new Date(c.updated_at).toLocaleDateString()}</span>
                  </button>
                  <Button
                    variant="ghost"
                    size="icon-sm"
                    onClick={() => void deleteConversation(c.id)}
                    disabled={deletingId === c.id}
                    aria-label={t('ai.deleteConversation', 'Delete conversation')}
                    title={t('ai.deleteConversation', 'Delete conversation')}
                    className="text-muted-foreground hover:text-danger-text"
                  >
                    {deletingId === c.id ? <Loader2 className="size-3.5 animate-spin" aria-hidden="true" /> : <Trash2 className="size-3.5" aria-hidden="true" />}
                  </Button>
                </li>
              ))}
            </ul>
          </div>
        ) : (
          <>
            {/* Availability notices */}
            {assistantBlocked && (
              <div className="flex flex-wrap items-center justify-between gap-2 rounded-lg border border-warning-border bg-warning-soft p-3 text-small text-warning-text">
                <span className="flex items-center gap-2">
                  <TriangleAlert className="size-4 shrink-0" aria-hidden="true" />
                  {t('ai.unavailable', 'The AI assistant is not available right now.')}
                </span>
                <Button variant="outline" size="sm" onClick={() => void loadAssistants()}>
                  <RotateCcw className="size-3.5" aria-hidden="true" />
                  {t('ai.retry', 'Retry')}
                </Button>
              </div>
            )}
            {notConfigured && (
              <div className="flex items-center gap-2 rounded-lg border border-warning-border bg-warning-soft p-3 text-small text-warning-text">
                <TriangleAlert className="size-4 shrink-0" aria-hidden="true" />
                {t('ai.notConfigured', 'The AI service is not configured on this server yet.')}
              </div>
            )}

            {/* Empty state: what it can do + starters */}
            {messages.length === 0 && (
              <div className="space-y-3">
                <p className="text-small leading-relaxed text-foreground">{getInitialMessage()}</p>
                {starters.length > 0 && (
                  <div className="space-y-1.5">
                    <h3 className="text-caption font-semibold text-muted-foreground">{t('ai.starters', 'Suggested questions')}</h3>
                    <ul className="space-y-1.5">
                      {starters.slice(0, 4).map((s, i) => (
                        <li key={i}>
                          <button
                            type="button"
                            onClick={() => void send(s)}
                            disabled={inputDisabled}
                            className="flex w-full cursor-pointer items-center justify-between gap-2 rounded-md border border-border bg-card px-3 py-2 text-left text-small font-medium text-foreground transition-colors hover:bg-accent focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-ring disabled:cursor-not-allowed disabled:opacity-50"
                          >
                            <span>{s}</span>
                            <ChevronRight className="size-4 shrink-0 text-primary-text" aria-hidden="true" />
                          </button>
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            )}

            {/* Messages */}
            {messages.map((msg) => {
              if (msg.sender === 'user') {
                return (
                  <div key={msg.id} className="flex justify-end animate-fade-in">
                    <div className="max-w-[90%] whitespace-pre-wrap break-words rounded-lg bg-secondary px-3 py-2 text-small text-secondary-foreground">
                      {msg.text}
                    </div>
                  </div>
                );
              }
              return (
                <div key={msg.id} className="space-y-2 animate-fade-in">
                  {msg.emergency && (
                    <div role="alert" className="flex flex-wrap items-center justify-between gap-2 rounded-lg border border-danger-border bg-danger-soft p-3 text-small font-semibold text-danger-text">
                      <span className="flex items-center gap-2">
                        <Siren className="size-4 shrink-0" aria-hidden="true" />
                        {t('ai.emergency', 'This may be an emergency. Seek urgent medical help now or call 108.')}
                      </span>
                      <a
                        href="tel:108"
                        className="inline-flex items-center gap-1.5 rounded-md bg-danger px-2.5 py-1.5 text-caption font-semibold text-danger-foreground hover:bg-destructive-hover focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-ring"
                      >
                        <PhoneCall className="size-3.5" aria-hidden="true" />
                        Call 108
                      </a>
                    </div>
                  )}

                  <div
                    className={cn(
                      'space-y-2 border-l-2 pl-3',
                      msg.error ? 'border-danger-border' : msg.emergency ? 'border-danger-border' : 'border-ai-border'
                    )}
                  >
                    {!msg.error && <AiMarker label={t('ai.short', 'AI')} />}
                    {msg.error ? (
                      <p className="text-small text-danger-text">{msg.text}</p>
                    ) : (
                      <Markdown text={msg.text} />
                    )}

                    {msg.refused && (
                      <div className="flex items-start gap-2 rounded-md border border-warning-border bg-warning-soft p-2 text-caption font-medium text-warning-text">
                        <TriangleAlert className="mt-px size-3.5 shrink-0" aria-hidden="true" />
                        {t('ai.safetyWarning', 'Request outside authorized safety bounds.')}
                      </div>
                    )}

                    {/* Decision block for a proposed action */}
                    {msg.action && (
                      <div className="overflow-hidden rounded-lg border border-border bg-card">
                        <div className="border-b border-border bg-muted px-3 py-1.5 text-caption font-semibold text-muted-foreground">
                          {t('ai.action.title', 'Action awaiting your confirmation')}
                        </div>
                        <div className="space-y-3 p-3">
                          <p className="text-small font-medium text-foreground">{msg.action.summary}</p>
                          {msg.action.status === 'PENDING' ? (
                            <div className="flex flex-wrap items-center gap-2">
                              <Button
                                size="sm"
                                disabled={msg.action.busy}
                                onClick={() => void executeAction(msg.action!.id, true)}
                                className={primaryButton}
                              >
                                {msg.action.busy ? <Loader2 className="size-3.5 animate-spin" aria-hidden="true" /> : <Check className="size-3.5" aria-hidden="true" />}
                                {t('ai.action.confirm', 'Confirm')}
                              </Button>
                              <Button
                                variant="outline"
                                size="sm"
                                disabled={msg.action.busy}
                                onClick={() => void executeAction(msg.action!.id, false)}
                              >
                                {t('ai.action.cancel', 'Cancel')}
                              </Button>
                            </div>
                          ) : (
                            <div className="flex flex-wrap items-center gap-2" role="status">
                              <StatusBadge
                                status={msg.action.status === 'EXECUTED' ? 'success' : msg.action.status === 'FAILED' ? 'danger' : 'neutral'}
                                label={msg.action.status === 'EXECUTED' ? t('ai.action.confirm', 'Confirm') : msg.action.status.charAt(0) + msg.action.status.slice(1).toLowerCase()}
                              />
                              <span className="text-small text-foreground">{msg.action.resultMessage || actionStatusText(msg.action.status)}</span>
                            </div>
                          )}
                          {msg.action.error && <p className="text-small text-danger-text">{msg.action.error}</p>}
                        </div>
                      </div>
                    )}

                    {msg.error?.retryable && (
                      <Button variant="outline" size="sm" onClick={() => retry(msg.id, msg.error!.retryText)} disabled={isLoading}>
                        <RotateCcw className="size-3.5" aria-hidden="true" />
                        {t('ai.retry', 'Retry')}
                      </Button>
                    )}

                    {msg.sources && msg.sources.length > 0 && (
                      <div className="flex flex-wrap items-center gap-1.5">
                        <span className="text-caption text-muted-foreground">{t('ai.sources', 'Sources')}:</span>
                        {msg.sources.map((s, idx) => (
                          <span key={idx} className="rounded-md border border-ai-border bg-ai-soft px-1.5 py-0.5 text-caption text-ai-text">
                            {s}
                          </span>
                        ))}
                      </div>
                    )}
                  </div>
                </div>
              );
            })}

            {(isLoading || assistantPending) && view === 'chat' && (
              <div role="status" className="flex items-center gap-2 text-small text-muted-foreground">
                <Loader2 className="size-4 animate-spin text-ai-text" aria-hidden="true" />
                {t('ai.analyzing', 'Analyzing authorized data...')}
              </div>
            )}
          </>
        )}
      </div>

      {/* Input */}
      {view === 'chat' && (
        <div className="shrink-0 space-y-1.5 border-t border-border p-3">
          <form
            onSubmit={(e) => { e.preventDefault(); void send(input); }}
            className="flex items-center gap-2"
          >
            <MicButton
              language={langKey}
              disabled={assistantBlocked || !!notConfigured}
              onTranscript={(text) => setInput((prev) => (prev ? `${prev} ${text}` : text).slice(0, 4000))}
            />
            <Input
              ref={inputRef}
              type="text"
              value={input}
              maxLength={4000}
              onChange={(e) => setInput(e.target.value)}
              disabled={inputDisabled}
              aria-label={t('ai.askPlaceholder') || 'Ask health question or clinical query...'}
              placeholder={t('ai.askPlaceholder') || 'Ask health question or clinical query...'}
              className="h-10 min-w-0 flex-1"
            />
            <Button
              type="submit"
              size="icon"
              disabled={inputDisabled || !input.trim()}
              aria-label={t('ai.send', 'Send')}
              title={t('ai.send', 'Send')}
              className={cn('size-10 shrink-0', primaryButton)}
            >
              <Send className="size-4" aria-hidden="true" />
            </Button>
            <SpeakButton
              language={langKey}
              textToSpeak={[...messages].reverse().find((m) => m.sender === 'assistant' && !m.error)?.text ?? ''}
            />
          </form>
          <p className="text-caption text-muted-foreground">
            {t('ai.disclaimer') || 'Informational guidance only. For medical emergencies, consult a healthcare officer or dial 108.'}
          </p>
        </div>
      )}
    </div>
  );

  /* ------------------------------ placement ------------------------------ */

  if (!aiDockable) {
    // Below xl: bottom sheet (Radix: focus trap, Escape, scroll lock)
    return (
      <Sheet open={isOpen} onOpenChange={setAiOpen}>
        <SheetContent
          side="bottom"
          closeLabel={t('ai.closeAssistant', 'Close AI Assistant')}
          aria-describedby={undefined}
          className="h-[85dvh] max-h-[85dvh] gap-0 overflow-hidden p-0"
        >
          <SheetDescription className="sr-only">{t('ai.disclaimer', 'Decision-support assistance only.')}</SheetDescription>
          {renderPanel('sheet')}
        </SheetContent>
      </Sheet>
    );
  }

  if (!isOpen) {
    // xl, collapsed: slim tab
    return (
      <aside aria-label={title} className="flex w-10 shrink-0 flex-col items-center border-l border-border bg-card py-3">
        <button
          type="button"
          onClick={() => setAiOpen(true)}
          aria-expanded={false}
          aria-label={t('ai.openAssistant', 'Open AI Assistant')}
          title={t('ai.openAssistant', 'Open AI Assistant')}
          className="flex cursor-pointer flex-col items-center gap-3 rounded-md px-1.5 py-2 text-ai-text transition-colors hover:bg-ai-soft focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-ring"
        >
          <Sparkles className="size-4" aria-hidden="true" />
          <span className="text-caption font-semibold [writing-mode:vertical-rl]">{t('ai.assistant', 'AI Assistant')}</span>
        </button>
      </aside>
    );
  }

  // xl, open: docked column that shares the layout
  return (
    <aside aria-label={title} className="flex w-[24rem] shrink-0 flex-col border-l border-border bg-card animate-fade-in 2xl:w-[26rem]">
      {renderPanel('docked')}
    </aside>
  );
};

// X is used by Sheet's built-in close control; re-exported icon import kept out of the bundle.
void X;
