import React, { useState, useEffect, useRef, useCallback } from 'react';
import {
  Bot, X, Send, Loader2, Sparkles, AlertCircle, ChevronRight,
  History, Plus, Trash2, RotateCcw, Siren, Check, ArrowLeft,
  Volume2, ShieldAlert, MessageSquare, PhoneCall
} from 'lucide-react';
import { useAuth } from '../../context/AuthContext';
import { useLanguage } from '../../context/LanguageContext';
import { api } from '../../services/api';
import type { ApiError } from '../../services/types';
import { MicButton, SpeakButton } from './VoiceControls';
import { Button } from '../ui/button';
import { Badge } from '../ui/badge';
import { Card } from '../ui/card';
import { cn } from '../../lib/utils';
import { formatRoleName } from '../../utils/formatters';

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
const TERMINAL_STATUSES = ['EXECUTED', 'FAILED', 'CANCELLED', 'EXPIRED'];

let uid = 0;
const nextId = () => `m${Date.now()}_${uid++}`;

const isRetryableError = (e: ApiError) => e.status === 0 || e.status === 429 || e.status >= 500;

const renderInline = (text: string, keyPrefix: string): React.ReactNode[] =>
  text.split(/(\*\*[^*]+\*\*)/g).map((part, i) =>
    part.startsWith('**') && part.endsWith('**') && part.length > 4
      ? <strong key={`${keyPrefix}-${i}`} className="font-bold text-slate-900">{part.slice(2, -2)}</strong>
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
        <p key={k} className="mb-2 leading-relaxed text-slate-800 text-xs sm:text-sm">
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
        <Tag key={k} className="mb-2 pl-4 text-xs sm:text-sm leading-relaxed text-slate-800 list-disc space-y-1">
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
  return <div className="break-words space-y-1">{blocks}</div>;
};

export interface UnifiedAiAssistantProps {
  isOpen?: boolean;
  onClose?: () => void;
  onOpen?: () => void;
  docked?: boolean;
}

export const UnifiedAiAssistant: React.FC<UnifiedAiAssistantProps> = ({
  isOpen: controlledIsOpen,
  onClose,
  onOpen,
  docked = false,
}) => {
  const { activeRole, scope } = useAuth();
  const { language, t } = useLanguage();
  const [internalIsOpen, setInternalIsOpen] = useState(false);
  const isOpen = controlledIsOpen !== undefined ? controlledIsOpen : internalIsOpen;

  const setIsOpen = (val: boolean) => {
    if (val) {
      onOpen?.();
      setInternalIsOpen(true);
    } else {
      onClose?.();
      setInternalIsOpen(false);
    }
  };

  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [isModalActive, setIsModalActive] = useState(false);

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

  const useCommonAi = assistantKey !== null;
  const langKey = (language as string) || 'en';

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
  }, [messages, isLoading, view]);

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
            resultMessage: data.message || (data.status === 'EXECUTED' ? t('ai.actionExecuted') : t('ai.actionCancelled')),
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
    const res = await api.delete(`/ai/${assistant.key}/conversations/${id}`);
    setDeletingId(null);
    if (!res.error) {
      setHistory((prev) => prev.filter((c) => c.id !== id));
      if (conversationId === id) resetConversation();
    }
  };

  const starters: string[] = assistant?.starters?.[langKey] || assistant?.starters?.en || [];
  const notConfigured = assistant && !assistant.configured;
  const assistantBlocked = useCommonAi && assistantsState === 'error';
  const inputDisabled = isLoading || inFlight.current || assistantBlocked || !!notConfigured;

  const getAssistantTitle = (): string => {
    if (activeRole === 'PATIENT') return 'Citizen Health Assistant';
    if (activeRole === 'DOCTOR') return 'Clinical Decision Support';
    if (activeRole === 'NURSE') return 'Triage Clinical Assistant';
    if (activeRole === 'PHARMACIST') return 'Formulary & Dispensary Assistant';
    return `${activeRole ? formatRoleName(activeRole, t) : 'Health'} Assistant`;
  };

  return (
    <>
      {/* Floating Assistant Trigger Pill (Only if uncontrolled and not docked) */}
      {!isOpen && !isModalActive && !docked && controlledIsOpen === undefined && (
        <button
          type="button"
          onClick={() => setIsOpen(true)}
          aria-label={t('ai.openAssistant') || 'Open Health Assistant'}
          className="fixed bottom-5 right-5 z-40 flex items-center gap-2.5 px-4 py-3 bg-gradient-to-r from-sky-600 to-teal-600 text-white font-bold text-xs rounded-full shadow-lg hover:shadow-xl hover:scale-105 active:scale-95 transition-all duration-200 cursor-pointer"
        >
          <div className="w-6 h-6 rounded-full bg-white/20 flex items-center justify-center">
            <Bot className="w-4 h-4 text-white" />
          </div>
          <span>{getAssistantTitle()}</span>
          <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
        </button>
      )}

      {/* Backdrop for Slide-over Drawer (when controlled and not docked) */}
      {isOpen && controlledIsOpen !== undefined && !docked && (
        <div
          className="fixed inset-0 z-40 bg-slate-950/40 backdrop-blur-xs animate-fade-in"
          onClick={() => setIsOpen(false)}
        />
      )}

      {/* Assistant Container (Docked Rail, Slide-over Drawer, or Floating Card) */}
      {isOpen && (
        <div
          data-assistant="true"
          role={docked ? "region" : "dialog"}
          aria-label={getAssistantTitle()}
          className={
            docked
              ? "w-full h-full bg-white flex flex-col overflow-hidden"
              : controlledIsOpen !== undefined
              ? "fixed inset-y-0 right-0 z-50 w-full sm:w-[420px] bg-white border-l border-slate-200/90 shadow-2xl flex flex-col overflow-hidden animate-slide-left"
              : "fixed bottom-4 right-4 z-50 w-full sm:w-[420px] h-[85vh] sm:h-[620px] max-h-[92vh] bg-white border border-slate-200/90 rounded-2xl shadow-2xl flex flex-col overflow-hidden animate-scale-in"
          }
        >
          {/* Header */}
          <div className="px-4 py-3.5 bg-gradient-to-r from-sky-600 to-teal-600 text-white flex items-center justify-between gap-3 shrink-0">
            <div className="flex items-center gap-2.5 min-w-0">
              <div className="w-8 h-8 rounded-lg bg-white/20 flex items-center justify-center shrink-0">
                <Bot className="w-5 h-5" />
              </div>
              <div className="min-w-0">
                <h4 className="text-sm font-extrabold truncate leading-tight">
                  {getAssistantTitle()}
                </h4>
                <div className="flex items-center gap-1.5 text-[10px] text-sky-100 font-medium truncate">
                  <span>{activeRole ? formatRoleName(activeRole, t) : 'Health Network'}</span>
                  {scope && <span>• {scope} Scope</span>}
                </div>
              </div>
            </div>

            <div className="flex items-center gap-1 shrink-0">
              {useCommonAi && assistant && (
                <>
                  <Button
                    variant="ghost"
                    size="icon-sm"
                    onClick={view === 'history' ? () => setView('chat') : openHistory}
                    title={view === 'history' ? 'Back to chat' : 'Conversation history'}
                    className="text-white hover:bg-white/20"
                  >
                    {view === 'history' ? <ArrowLeft className="w-4 h-4" /> : <History className="w-4 h-4" />}
                  </Button>
                  <Button
                    variant="ghost"
                    size="icon-sm"
                    onClick={() => { resetConversation(); setTimeout(() => inputRef.current?.focus(), 0); }}
                    title="New conversation"
                    className="text-white hover:bg-white/20"
                  >
                    <Plus className="w-4 h-4" />
                  </Button>
                </>
              )}
              <Button
                variant="ghost"
                size="icon-sm"
                onClick={() => setIsOpen(false)}
                title="Close assistant"
                className="text-white hover:bg-white/20"
              >
                <X className="w-4 h-4" />
              </Button>
            </div>
          </div>

          {/* Context banner */}
          <div className="px-3.5 py-1.5 bg-sky-50 border-b border-sky-100 flex items-center justify-between text-[11px] text-sky-900 font-medium">
            <span className="truncate">Context: {scope || 'Local Facility'} • {language.toUpperCase()}</span>
            <span className="text-[10px] text-sky-600 font-bold uppercase tracking-wider">AI Verified</span>
          </div>

          {/* Chat Body */}
          <div
            ref={scrollRef}
            className="flex-1 overflow-y-auto p-4 space-y-3.5 bg-slate-50/50"
            aria-live="polite"
          >
            {view === 'history' ? (
              <div className="space-y-2">
                <div className="text-xs font-bold text-slate-700 uppercase tracking-wider mb-2">
                  Conversation History
                </div>
                {historyLoading && (
                  <div className="flex items-center gap-2 text-xs text-slate-500 py-4 justify-center">
                    <Loader2 className="w-4 h-4 animate-spin text-sky-600" />
                    Loading past sessions...
                  </div>
                )}
                {!historyLoading && history.length === 0 && (
                  <div className="text-xs text-slate-400 py-6 text-center">
                    No previous conversations found.
                  </div>
                )}
                {history.map((c) => (
                  <div
                    key={c.id}
                    className="flex items-center justify-between p-2.5 rounded-xl border border-slate-200 bg-white hover:border-slate-300 shadow-2xs transition"
                  >
                    <button
                      type="button"
                      onClick={() => void openConversation(c.id)}
                      className="flex-1 text-left min-w-0 pr-2 cursor-pointer"
                    >
                      <div className="text-xs font-bold text-slate-900 truncate">
                        {c.title || 'Health Conversation'}
                      </div>
                      <div className="text-[10px] text-slate-400 mt-0.5">
                        {new Date(c.updated_at).toLocaleDateString()}
                      </div>
                    </button>
                    <Button
                      variant="ghost"
                      size="icon-sm"
                      onClick={() => void deleteConversation(c.id)}
                      disabled={deletingId === c.id}
                      className="text-slate-400 hover:text-red-600"
                    >
                      {deletingId === c.id ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Trash2 className="w-3.5 h-3.5" />}
                    </Button>
                  </div>
                ))}
              </div>
            ) : (
              <>
                {/* Initial Assistant greeting */}
                {messages.length === 0 && (
                  <div className="space-y-3">
                    <div className="p-3.5 rounded-xl bg-white border border-slate-200 text-xs text-slate-700 leading-relaxed shadow-2xs">
                      <div className="flex items-center gap-2 mb-1.5 font-bold text-sky-900">
                        <Sparkles className="w-4 h-4 text-sky-600" />
                        <span>Welcome to Med2Us Copilot</span>
                      </div>
                      <p>{getInitialMessage()}</p>
                    </div>

                    {starters.length > 0 && (
                      <div className="space-y-1.5">
                        <span className="text-[11px] font-bold text-slate-500 uppercase tracking-wider">
                          Suggested questions
                        </span>
                        <div className="flex flex-col gap-1.5">
                          {starters.slice(0, 4).map((s, i) => (
                            <button
                              key={i}
                              type="button"
                              onClick={() => void send(s)}
                              disabled={inputDisabled}
                              className="text-left px-3 py-2 rounded-lg border border-sky-100 bg-sky-50/70 hover:bg-sky-100 hover:border-sky-200 text-xs font-semibold text-sky-900 transition cursor-pointer flex items-center justify-between"
                            >
                              <span className="truncate">{s}</span>
                              <ChevronRight className="w-3.5 h-3.5 text-sky-600 shrink-0" />
                            </button>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                )}

                {/* Message bubbles */}
                {messages.map((msg) => {
                  const isUser = msg.sender === 'user';
                  return (
                    <div
                      key={msg.id}
                      className={cn('flex flex-col gap-1', isUser ? 'items-end' : 'items-start')}
                    >
                      {/* Emergency Alert Header */}
                      {msg.emergency && (
                        <div className="w-full p-2.5 rounded-xl bg-red-600 text-white text-xs font-bold flex items-center justify-between gap-2 shadow-xs animate-fade-in">
                          <div className="flex items-center gap-2">
                            <Siren className="w-4 h-4 animate-bounce shrink-0" />
                            <span>URGENT: Immediate Medical Attention Needed</span>
                          </div>
                          <a
                            href="tel:108"
                            className="inline-flex items-center gap-1 px-2.5 py-1 rounded bg-white text-red-700 font-extrabold text-[11px] hover:bg-red-50 shrink-0"
                          >
                            <PhoneCall className="w-3 h-3" />
                            Call 108
                          </a>
                        </div>
                      )}

                      {/* Bubble */}
                      <div
                        className={cn(
                          'p-3 rounded-2xl text-xs sm:text-sm max-w-[88%] shadow-2xs leading-relaxed',
                          isUser
                            ? 'bg-sky-600 text-white rounded-br-xs'
                            : msg.error
                            ? 'bg-red-50 text-red-900 border border-red-200 rounded-bl-xs'
                            : msg.emergency
                            ? 'bg-white text-slate-900 border-2 border-red-500 rounded-bl-xs'
                            : 'bg-white text-slate-900 border border-slate-200/90 rounded-bl-xs'
                        )}
                      >
                        {isUser || msg.error ? msg.text : <Markdown text={msg.text} />}

                        {/* Safety Notice */}
                        {msg.refused && (
                          <div className="mt-2 p-2 rounded-lg bg-red-50 border border-red-200 text-red-700 text-[11px] flex items-center gap-1.5 font-semibold">
                            <AlertCircle className="w-3.5 h-3.5 shrink-0" />
                            Clinical Safety Warning: Medical consultation required.
                          </div>
                        )}

                        {/* Pending Action Confirmation */}
                        {msg.action && (
                          <div className="mt-2.5 p-2.5 rounded-xl bg-slate-50 border border-slate-200 space-y-2">
                            <div className="text-[11px] font-bold text-slate-700">
                              Proposed Action: {msg.action.summary}
                            </div>
                            {msg.action.status === 'PENDING' ? (
                              <div className="flex items-center gap-2">
                                <Button
                                  variant="emerald"
                                  size="sm"
                                  disabled={msg.action.busy}
                                  onClick={() => executeAction(msg.action!.id, true)}
                                  className="h-7 text-xs px-2.5"
                                >
                                  <Check className="w-3 h-3 mr-1" />
                                  Confirm &amp; Proceed
                                </Button>
                                <Button
                                  variant="outline"
                                  size="sm"
                                  disabled={msg.action.busy}
                                  onClick={() => executeAction(msg.action!.id, false)}
                                  className="h-7 text-xs px-2.5 text-red-600 hover:bg-red-50"
                                >
                                  Cancel
                                </Button>
                              </div>
                            ) : (
                              <div className="text-[11px] font-semibold text-emerald-700 flex items-center gap-1">
                                <Check className="w-3 h-3" />
                                {msg.action.resultMessage || `Action status: ${msg.action.status}`}
                              </div>
                            )}
                          </div>
                        )}

                        {/* Retry */}
                        {msg.error?.retryable && (
                          <Button
                            variant="destructive"
                            size="sm"
                            onClick={() => retry(msg.id, msg.error!.retryText)}
                            disabled={isLoading}
                            className="h-7 text-[11px] mt-2 px-2.5"
                          >
                            <RotateCcw className="w-3 h-3 mr-1" />
                            Retry
                          </Button>
                        )}
                      </div>

                      {/* Evidence Citations / Sources */}
                      {msg.sources && msg.sources.length > 0 && (
                        <div className="flex flex-wrap gap-1 px-1 mt-0.5">
                          <span className="text-[10px] text-slate-400">Sources:</span>
                          {msg.sources.map((s, idx) => (
                            <span
                              key={idx}
                              className="text-[10px] px-1.5 py-0.5 rounded bg-sky-50 border border-sky-100 text-sky-700 font-medium"
                            >
                              {s}
                            </span>
                          ))}
                        </div>
                      )}
                    </div>
                  );
                })}

                {/* Loading indicator */}
                {isLoading && (
                  <div className="flex items-center gap-2 p-2.5 rounded-xl bg-white border border-slate-200 text-xs text-slate-500 w-fit">
                    <Loader2 className="w-3.5 h-3.5 animate-spin text-sky-600" />
                    <span>Analyzing health context...</span>
                  </div>
                )}
              </>
            )}
          </div>

          {/* Clinical Disclaimer */}
          <div className="px-3 py-1 bg-slate-100/90 border-t border-slate-200 text-[10px] text-slate-500 text-center">
            {t('ai.disclaimer') || 'Informational guidance only. For medical emergencies, consult a healthcare officer or dial 108.'}
          </div>

          {/* Input Footer */}
          {view === 'chat' && (
            <form
              onSubmit={(e) => { e.preventDefault(); void send(input); }}
              className="p-3 border-t border-slate-200 bg-white flex items-center gap-2 shrink-0"
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
                disabled={inputDisabled}
                aria-label={t('ai.askPlaceholder') || 'Ask health question or clinical query...'}
                placeholder={t('ai.askPlaceholder') || 'Ask health question or clinical query...'}
                className="flex-1 min-w-0 h-9 px-3 text-xs bg-slate-50 border border-slate-200 rounded-lg outline-none focus:border-sky-500 focus:bg-white text-slate-900 transition"
              />
              <Button
                type="submit"
                variant="primary"
                size="icon"
                disabled={inputDisabled || !input.trim()}
                title="Send message"
                className="h-9 w-9 shrink-0"
              >
                <Send className="w-4 h-4" />
              </Button>
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
