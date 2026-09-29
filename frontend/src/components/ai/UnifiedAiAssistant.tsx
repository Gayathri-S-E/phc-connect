import React, { useState } from 'react';
import { 
  Bot, X, Send, Loader2, Sparkles, AlertCircle, 
  MessageSquare, ChevronRight, HelpCircle 
} from 'lucide-react';
import { useAuth } from '../../context/AuthContext';
import { useLanguage } from '../../context/LanguageContext';
import { api } from '../../services/api';

interface ChatMessage {
  id: string;
  sender: 'user' | 'assistant';
  text: string;
  text_ta?: string | null;
  sources?: string[];
  suggestions?: string[];
  refused?: boolean;
}

export const UnifiedAiAssistant: React.FC = () => {
  const { activeRole, user } = useAuth();
  const { language, t } = useLanguage();
  const [isOpen, setIsOpen] = useState(false);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  const getInitialMessage = (): string => {
    switch (activeRole) {
      case 'PATIENT':
        return language === 'ta'
          ? 'வணக்கம்! நான் உங்கள் நல்வாழ்வு AI உதவியாளர். உங்கள் உடல்நலம், உணவுமுறை அல்லது மருந்து நேரம் குறித்து கேளுங்கள்.'
          : 'Hello! I am your AI Wellness Assistant. How can I help you maintain good health today?';
      case 'DOCTOR':
        return 'Clinical Decision Support active. Ask for clinical guidelines, drug contraindications, or differential summaries.';
      case 'NURSE':
        return 'Triage Assistant ready. Enter patient symptoms or vital signs for Early Warning Score evaluation.';
      case 'PHARMACIST':
      case 'DISTRICT_SUPPLY_OFFICER':
      case 'STATE_SUPPLY_MANAGER':
        return 'Supply Chain Intelligence ready. Ask for consumption trends, stockout risks, or replenishment guidance.';
      default:
        return language === 'ta'
          ? 'வணக்கம்! நான் உங்கள் நிர்வாக AI உதவியாளர். மாவட்ட/மாநில சுகாதாரத் தரவுகள் மற்றும் கண்காணிப்பு தகவல்களை கேளுங்கள்.'
          : 'Governance & Analytics Assistant ready. Ask for live aggregated metrics, disease patterns, or administrative summaries.';
    }
  };

  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      id: 'init',
      sender: 'assistant',
      text: getInitialMessage(),
    },
  ]);

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
            text: res.error?.detail || 'Sorry, I am unable to retrieve that information right now.',
          },
        ]);
      }
    } catch {
      setMessages((prev) => [
        ...prev,
        {
          id: (Date.now() + 1).toString(),
          sender: 'assistant',
          text: 'Network error connecting to the AI advisory service.',
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
      {/* Floating Toggle Button */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        aria-label="Open AI Assistant"
        style={{
          position: 'fixed',
          bottom: '1.5rem',
          right: '1.5rem',
          zIndex: 900,
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
          cursor: 'pointer',
          transition: 'transform 0.2s ease',
        }}
        onMouseEnter={(e) => (e.currentTarget.style.transform = 'scale(1.06)')}
        onMouseLeave={(e) => (e.currentTarget.style.transform = 'scale(1)')}
      >
        <Sparkles size={24} />
      </button>

      {/* Slide-in Assistant Drawer */}
      {isOpen && (
        <div
          role="dialog"
          aria-label={getAssistantTitle()}
          style={{
            position: 'fixed',
            bottom: '5.5rem',
            right: '1.5rem',
            width: '90vw',
            maxWidth: '420px',
            height: '580px',
            backgroundColor: '#ffffff',
            borderRadius: '16px',
            boxShadow: '0 25px 50px -12px rgba(0, 0, 0, 0.25)',
            border: '1px solid var(--border-color)',
            zIndex: 950,
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
                  {activeRole ? activeRole.replace(/_/g, ' ') : 'AUTHORIZED PERSPECTIVE'}
                </span>
              </div>
            </div>
            <button
              onClick={() => setIsOpen(false)}
              aria-label="Close assistant"
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
                      <AlertCircle size={14} /> Request outside authorized safety bounds.
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
                Analyzing authorized data...
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
