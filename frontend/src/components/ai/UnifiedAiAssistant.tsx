import React, { useState, useEffect } from 'react';
import { 
  Bot, X, Send, Loader2, Sparkles, AlertCircle, 
  ChevronRight
} from 'lucide-react';
import { useAuth } from '../../context/AuthContext';
import { useLanguage } from '../../context/LanguageContext';
import { api } from '../../services/api';

interface ChatMessage {
  id: string;
  sender: 'user' | 'assistant';
  text: string;
  text_ta?: string | null;
  text_hi?: string | null;
  sources?: string[];
  suggestions?: string[];
  refused?: boolean;
}

export const UnifiedAiAssistant: React.FC = () => {
  const { activeRole } = useAuth();
  const { language, t } = useLanguage();
  const [isOpen, setIsOpen] = useState(false);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [isModalActive, setIsModalActive] = useState(false);

  // Monitor DOM to detect when a modal or dialog is active, to prevent touch collision
  useEffect(() => {
    const checkModal = () => {
      // Check if any modal is currently open in the DOM
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
      case 'PATIENT':
        return t('ai.initial.patient');
      case 'DOCTOR':
        return t('ai.initial.doctor');
      case 'NURSE':
        return t('ai.initial.nurse');
      case 'PHARMACIST':
      case 'DISTRICT_SUPPLY_OFFICER':
      case 'STATE_SUPPLY_MANAGER':
        return t('ai.initial.supply');
      default:
        return t('ai.initial.governance');
    }
  };

  const [messages, setMessages] = useState<ChatMessage[]>([]);

  // Update initial message whenever role or language changes
  useEffect(() => {
    setMessages([
      {
        id: 'init',
        sender: 'assistant',
        text: getInitialMessage(),
      },
    ]);
  }, [activeRole, language]);

  const handleSend = async () => {
    if (!input.trim() || isLoading) return;

    const userText = input.trim();
    const userMsg: ChatMessage = {
      id: Date.now().toString(),
      sender: 'user',
      text: userText,
    };

    setMessages((prev) => [...prev, userMsg]);
    setInput('');
    setIsLoading(true);

    try {
      let endpoint = '/governance/ai-assistant';
      let payload: any = { question: userText, language };

      if (activeRole === 'PATIENT') {
        endpoint = '/patient-portal/wellness-assistant/chat';
        payload = { message: userText, language };
      } else if (activeRole === 'DOCTOR') {
        endpoint = '/doctor-portal/clinical-assistant/advise';
        payload = { query: userText };
      } else if (activeRole === 'NURSE') {
        endpoint = '/nurse-portal/triage-assistant/score';
        payload = { symptoms: userText };
      }

      const res = await api.post<any>(endpoint, payload);

      if (res.data) {
        const d = res.data;
        let responseText = d.answer || d.response_text || d.response || d.advice || d.summary || JSON.stringify(d);
        if (language === 'ta' && d.answer_ta) {
          responseText = d.answer_ta;
        }

        const assistantMsg: ChatMessage = {
          id: (Date.now() + 1).toString(),
          sender: 'assistant',
          text: responseText,
          text_ta: d.answer_ta,
          sources: d.sources,
          suggestions: d.suggestions,
          refused: d.refused,
        };
        setMessages((prev) => [...prev, assistantMsg]);
      } else {
        setMessages((prev) => [
          ...prev,
          {
            id: (Date.now() + 1).toString(),
            sender: 'assistant',
            text: res.error?.detail || t('state.error'),
          },
        ]);
      }
    } catch {
      setMessages((prev) => [
        ...prev,
        {
          id: (Date.now() + 1).toString(),
          sender: 'assistant',
          text: t('ai.error'),
        },
      ]);
    } finally {
      setIsLoading(false);
    }
  };

  const getAssistantTitle = () => {
    if (activeRole === 'PATIENT') return t('ai.wellnessTitle');
    if (activeRole === 'DOCTOR' || activeRole === 'NURSE') return t('ai.clinicalTitle');
    return t('ai.governanceTitle');
  };

  return (
    <>
      {/* Floating Toggle Button with Safe Area Isolation */}
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
          style={{
            width: '56px',
            height: '56px',
            borderRadius: '50%',
            backgroundColor: 'var(--primary)',
            color: '#ffffff',
            border: 'none',
            boxShadow: '0 10px 25px -5px rgba(37, 99, 235, 0.4), 0 8px 10px -6px rgba(37, 99, 235, 0.3)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            cursor: isModalActive ? 'default' : 'pointer',
            transition: 'transform 0.2s ease',
          }}
          onMouseEnter={(e) => {
            if (!isModalActive) e.currentTarget.style.transform = 'scale(1.06)';
          }}
          onMouseLeave={(e) => {
            e.currentTarget.style.transform = 'scale(1)';
          }}
        >
          {isOpen ? <X size={24} /> : <Sparkles size={24} />}
        </button>
      </div>

      {/* Slide-in Assistant Drawer */}
      {isOpen && (
        <div
          role="dialog"
          data-assistant="true"
          aria-label={getAssistantTitle()}
          style={{
            position: 'fixed',
            bottom: 'calc(5.5rem + env(safe-area-inset-bottom, 0px))',
            right: '1.5rem',
            width: 'calc(100vw - 3rem)',
            maxWidth: '420px',
            height: 'min(580px, calc(100vh - 8rem))',
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
              padding: '1rem 1.25rem',
              backgroundColor: 'var(--primary)',
              color: '#ffffff',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.65rem' }}>
              <div
                style={{
                  width: '32px',
                  height: '32px',
                  borderRadius: '8px',
                  backgroundColor: 'rgba(255, 255, 255, 0.2)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                }}
              >
                <Bot size={20} />
              </div>
              <div>
                <h4 style={{ margin: 0, fontSize: '0.95rem', fontWeight: 700 }}>{getAssistantTitle()}</h4>
                <span style={{ fontSize: '0.725rem', opacity: 0.85 }}>
                  {activeRole ? t(`role.${activeRole}`, activeRole.replace(/_/g, ' ')) : t('nav.workspace')}
                </span>
              </div>
            </div>
            <button
              onClick={() => setIsOpen(false)}
              aria-label={t('ai.closeAssistant')}
              style={{
                background: 'none',
                border: 'none',
                color: '#ffffff',
                cursor: 'pointer',
                padding: '0.25rem',
                display: 'flex',
              }}
            >
              <X size={20} />
            </button>
          </div>

          {/* Messages Body */}
          <div
            style={{
              flex: 1,
              overflowY: 'auto',
              padding: '1rem',
              display: 'flex',
              flexDirection: 'column',
              gap: '0.85rem',
              backgroundColor: 'rgba(248, 250, 252, 0.5)',
            }}
          >
            {messages.map((msg) => (
              <div
                key={msg.id}
                style={{
                  alignSelf: msg.sender === 'user' ? 'flex-end' : 'flex-start',
                  maxWidth: '85%',
                  display: 'flex',
                  flexDirection: 'column',
                  gap: '0.35rem',
                }}
              >
                <div
                  style={{
                    padding: '0.75rem 1rem',
                    borderRadius: '14px',
                    fontSize: '0.875rem',
                    lineHeight: 1.45,
                    backgroundColor: msg.sender === 'user' ? 'var(--primary)' : '#ffffff',
                    color: msg.sender === 'user' ? '#ffffff' : 'var(--text-main)',
                    border: msg.sender === 'user' ? 'none' : '1px solid var(--border-color)',
                    boxShadow: '0 1px 2px 0 rgba(0, 0, 0, 0.05)',
                  }}
                >
                  {msg.text}

                  {msg.refused && (
                    <div
                      style={{
                        marginTop: '0.5rem',
                        padding: '0.4rem 0.6rem',
                        borderRadius: '6px',
                        backgroundColor: 'rgba(239, 68, 68, 0.1)',
                        color: '#dc2626',
                        fontSize: '0.75rem',
                        display: 'flex',
                        alignItems: 'center',
                        gap: '0.35rem',
                      }}
                    >
                      <AlertCircle size={14} /> {t('ai.safetyWarning')}
                    </div>
                  )}
                </div>

                {msg.suggestions && msg.suggestions.length > 0 && (
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '0.25rem', paddingLeft: '0.25rem' }}>
                    {msg.suggestions.map((sug, i) => (
                      <button
                        key={i}
                        onClick={() => {
                          setInput(sug);
                        }}
                        style={{
                          background: 'none',
                          border: '1px solid rgba(37, 99, 235, 0.3)',
                          borderRadius: '6px',
                          padding: '0.25rem 0.5rem',
                          textAlign: 'left',
                          fontSize: '0.75rem',
                          color: 'var(--primary)',
                          cursor: 'pointer',
                          display: 'flex',
                          alignItems: 'center',
                          gap: '0.25rem',
                        }}
                      >
                        <ChevronRight size={12} /> {sug}
                      </button>
                    ))}
                  </div>
                )}
              </div>
            ))}

            {isLoading && (
              <div
                style={{
                  alignSelf: 'flex-start',
                  padding: '0.65rem 1rem',
                  borderRadius: '14px',
                  backgroundColor: '#ffffff',
                  border: '1px solid var(--border-color)',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '0.5rem',
                  color: 'var(--text-muted)',
                  fontSize: '0.825rem',
                }}
              >
                <Loader2 size={16} className="animate-spin" style={{ color: 'var(--primary)' }} />
                {t('ai.analyzing')}
              </div>
            )}
          </div>

          {/* Disclaimer Footer */}
          <div
            style={{
              padding: '0.4rem 0.75rem',
              backgroundColor: 'rgba(241, 245, 249, 0.8)',
              borderTop: '1px solid var(--border-color)',
              fontSize: '0.675rem',
              color: 'var(--text-muted)',
              textAlign: 'center',
            }}
          >
            {t('ai.disclaimer')}
          </div>

          {/* Input Box */}
          <div
            style={{
              padding: '0.75rem 1rem',
              borderTop: '1px solid var(--border-color)',
              display: 'flex',
              gap: '0.5rem',
              backgroundColor: '#ffffff',
            }}
          >
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleSend()}
              placeholder={t('ai.askPlaceholder')}
              style={{
                flex: 1,
                padding: '0.6rem 0.85rem',
                borderRadius: '8px',
                border: '1px solid var(--border-color)',
                fontSize: '0.85rem',
                outline: 'none',
              }}
            />
            <button
              onClick={handleSend}
              disabled={isLoading || !input.trim()}
              className="btn-primary"
              style={{
                padding: '0.6rem 0.85rem',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
              }}
            >
              <Send size={16} />
            </button>
          </div>
        </div>
      )}
    </>
  );
};
