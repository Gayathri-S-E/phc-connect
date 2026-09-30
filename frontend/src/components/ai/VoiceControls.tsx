import React, { useCallback, useEffect, useRef, useState } from 'react';
import { Mic, Square, Volume2, Loader2, VolumeX } from 'lucide-react';
import { api } from '../../services/api';
import { cn } from '../../lib/utils';

/* Voice controls for the AI assistants: a microphone button (record -> Google Speech-to-Text) and a speak button
   (Google Text-to-Speech). Standalone: styled with design tokens, no context dependencies. Degrades gracefully when the
   server has no Google credentials (503) or the browser/user denies the microphone. */

export type VoiceLanguage = 'en' | 'ta' | 'hi' | (string & {});

const MAX_RECORD_MS = 25_000; // keeps recordings well under the server's ~1 MB base64 limit
const MIME_CANDIDATES = ['audio/webm;codecs=opus', 'audio/webm', 'audio/ogg;codecs=opus'];

interface TranscribeResult { text: string; language: string; locale: string }
interface SpeakResult { audio_base64: string; mime: string }

const LABELS: Record<string, Record<string, string>> = {
  en: {
    record: 'Speak your message', stop: 'Stop recording', listening: 'Listening… tap to stop',
    transcribing: 'Converting speech to text…', speak: 'Read aloud', stopSpeak: 'Stop reading',
    notConfigured: 'Voice is not set up on this server', denied: 'Microphone access was denied',
    unsupported: 'Voice input is not supported in this browser', nothing: 'Could not hear anything. Please try again.',
    failed: 'Voice service is unavailable. Please try again.', limit: 'Too many voice requests. Please wait a moment.',
  },
  ta: {
    record: 'உங்கள் செய்தியைப் பேசுங்கள்', stop: 'பதிவை நிறுத்து', listening: 'கேட்கிறது… நிறுத்த தட்டவும்',
    transcribing: 'பேச்சை எழுத்தாக மாற்றுகிறது…', speak: 'உரக்கப் படி', stopSpeak: 'படிப்பதை நிறுத்து',
    notConfigured: 'இந்த சேவையகத்தில் குரல் வசதி அமைக்கப்படவில்லை', denied: 'மைக்ரோஃபோன் அனுமதி மறுக்கப்பட்டது',
    unsupported: 'இந்த உலாவியில் குரல் உள்ளீடு ஆதரிக்கப்படவில்லை', nothing: 'எதுவும் கேட்கவில்லை. மீண்டும் முயலவும்.',
    failed: 'குரல் சேவை கிடைக்கவில்லை. மீண்டும் முயலவும்.', limit: 'அதிக கோரிக்கைகள். சிறிது காத்திருக்கவும்.',
  },
  hi: {
    record: 'अपना संदेश बोलें', stop: 'रिकॉर्डिंग रोकें', listening: 'सुन रहा है… रोकने के लिए टैप करें',
    transcribing: 'आवाज़ को टेक्स्ट में बदल रहा है…', speak: 'पढ़कर सुनाएँ', stopSpeak: 'पढ़ना रोकें',
    notConfigured: 'इस सर्वर पर वॉइस सेट अप नहीं है', denied: 'माइक्रोफ़ोन की अनुमति नहीं मिली',
    unsupported: 'इस ब्राउज़र में वॉइस इनपुट समर्थित नहीं है', nothing: 'कुछ सुनाई नहीं दिया। कृपया फिर से प्रयास करें।',
    failed: 'वॉइस सेवा उपलब्ध नहीं है। कृपया फिर से प्रयास करें।', limit: 'बहुत अधिक अनुरोध। कृपया थोड़ी देर रुकें।',
  },
};
const t = (lang: string, key: string): string => (LABELS[lang] ?? LABELS.en)[key] ?? LABELS.en[key];

const blobToBase64 = (blob: Blob): Promise<string> =>
  new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onerror = () => reject(reader.error);
    reader.onload = () => resolve(String(reader.result).split(',')[1] ?? '');
    reader.readAsDataURL(blob);
  });

const pickMime = (): string | null => {
  if (typeof MediaRecorder === 'undefined') return null;
  return MIME_CANDIDATES.find((m) => MediaRecorder.isTypeSupported(m)) ?? null;
};

const baseButton =
  'inline-flex size-10 shrink-0 cursor-pointer items-center justify-center rounded-md border border-input bg-card p-0 text-foreground transition-colors hover:bg-accent disabled:cursor-not-allowed disabled:opacity-50 [touch-action:manipulation]';

/* ------------------------------ Mic button ------------------------------ */

export interface MicButtonProps {
  onTranscript: (text: string) => void;
  language?: VoiceLanguage;
  disabled?: boolean;
  onError?: (message: string) => void;
}

export const MicButton: React.FC<MicButtonProps> = ({ onTranscript, language = 'en', disabled, onError }) => {
  const [phase, setPhase] = useState<'idle' | 'recording' | 'sending'>('idle');
  const [blocked, setBlocked] = useState<string | null>(null); // permanent reason -> disabled with tooltip
  const [message, setMessage] = useState('');
  const recorder = useRef<MediaRecorder | null>(null);
  const stream = useRef<MediaStream | null>(null);
  const chunks = useRef<Blob[]>([]);
  const timer = useRef<number | null>(null);
  const mounted = useRef(true);
  const cancelled = useRef(false);

  const supported = typeof navigator !== 'undefined' && !!navigator.mediaDevices?.getUserMedia && pickMime() !== null;

  const release = useCallback(() => {
    if (timer.current) window.clearTimeout(timer.current);
    timer.current = null;
    stream.current?.getTracks().forEach((tr) => tr.stop());
    stream.current = null;
  }, []);

  useEffect(() => {
    mounted.current = true;
    return () => {
      mounted.current = false;
      cancelled.current = true;
      if (recorder.current && recorder.current.state !== 'inactive') recorder.current.stop();
      release();
    };
  }, [release]);

  const report = useCallback((msg: string) => {
    if (!mounted.current) return;
    setMessage(msg);
    onError?.(msg);
  }, [onError]);

  const send = useCallback(async (blob: Blob, mime: string) => {
    try {
      const audio_base64 = await blobToBase64(blob);
      const { data, error } = await api.post<TranscribeResult>('/ai/voice/transcribe', {
        audio_base64, mime, language,
      });
      if (!mounted.current) return;
      if (error) {
        if (error.status === 503) setBlocked(t(language, 'notConfigured'));
        else report(t(language, error.status === 429 ? 'limit' : 'failed'));
        return;
      }
      const text = data?.text?.trim();
      if (text) { setMessage(''); onTranscript(text); } else report(t(language, 'nothing'));
    } catch {
      report(t(language, 'failed'));
    } finally {
      if (mounted.current) setPhase('idle');
    }
  }, [language, onTranscript, report]);

  const start = useCallback(async () => {
    setMessage('');
    const mime = pickMime();
    if (!mime) { setBlocked(t(language, 'unsupported')); return; }
    try {
      const media = await navigator.mediaDevices.getUserMedia({ audio: { channelCount: 1, echoCancellation: true } });
      if (!mounted.current) { media.getTracks().forEach((tr) => tr.stop()); return; }
      stream.current = media;
      chunks.current = [];
      cancelled.current = false;
      const rec = new MediaRecorder(media, { mimeType: mime });
      recorder.current = rec;
      rec.ondataavailable = (e) => { if (e.data.size > 0) chunks.current.push(e.data); };
      rec.onstop = () => {
        release();
        if (cancelled.current || !mounted.current) return;
        const blob = new Blob(chunks.current, { type: mime });
        if (blob.size === 0) { setPhase('idle'); report(t(language, 'nothing')); return; }
        setPhase('sending');
        void send(blob, mime);
      };
      rec.start();
      setPhase('recording');
      timer.current = window.setTimeout(() => { if (rec.state !== 'inactive') rec.stop(); }, MAX_RECORD_MS);
    } catch (err) {
      release();
      const name = (err as DOMException)?.name;
      if (name === 'NotAllowedError' || name === 'SecurityError') setBlocked(t(language, 'denied'));
      else report(t(language, 'unsupported'));
      setPhase('idle');
    }
  }, [language, release, report, send]);

  const stop = useCallback(() => {
    if (recorder.current && recorder.current.state !== 'inactive') recorder.current.stop();
  }, []);

  const off = !!disabled || !supported || !!blocked;
  const reason = blocked ?? (!supported ? t(language, 'unsupported') : '');
  const recording = phase === 'recording';
  const label = off && reason ? reason
    : recording ? t(language, 'stop') : phase === 'sending' ? t(language, 'transcribing') : t(language, 'record');

  return (
    <span className="relative inline-flex">
      <button
        type="button"
        onClick={recording ? stop : start}
        disabled={off || phase === 'sending'}
        aria-label={label}
        aria-pressed={recording}
        title={label}
        className={cn(baseButton, recording && 'border-danger bg-danger text-danger-foreground hover:bg-destructive-hover')}
      >
        {phase === 'sending' ? <Loader2 size={18} aria-hidden="true" className="animate-spin" />
          : recording ? <Square size={18} aria-hidden="true" /> : <Mic size={20} aria-hidden="true" />}
      </button>
      <span role="status" aria-live="polite" className="sr-only">
        {recording ? t(language, 'listening') : phase === 'sending' ? t(language, 'transcribing') : message}
      </span>
    </span>
  );
};

/* ------------------------------ Speak button ------------------------------ */

export interface SpeakButtonProps {
  textToSpeak: string;
  language?: VoiceLanguage;
  disabled?: boolean;
  onError?: (message: string) => void;
}

export const SpeakButton: React.FC<SpeakButtonProps> = ({ textToSpeak, language = 'en', disabled, onError }) => {
  const [phase, setPhase] = useState<'idle' | 'loading' | 'playing'>('idle');
  const [blocked, setBlocked] = useState<string | null>(null);
  const audio = useRef<HTMLAudioElement | null>(null);
  const mounted = useRef(true);
  const requestId = useRef(0);

  const halt = useCallback(() => {
    requestId.current += 1; // invalidates any in-flight request
    if (audio.current) { audio.current.pause(); audio.current.src = ''; audio.current = null; }
  }, []);

  useEffect(() => {
    mounted.current = true;
    return () => { mounted.current = false; halt(); };
  }, [halt]);

  useEffect(() => { halt(); setPhase('idle'); }, [textToSpeak, language, halt]);

  const play = useCallback(async () => {
    if (phase === 'playing' || phase === 'loading') { halt(); setPhase('idle'); return; }
    const id = ++requestId.current;
    setPhase('loading');
    const { data, error } = await api.post<SpeakResult>('/ai/voice/speak', { text: textToSpeak, language });
    if (!mounted.current || id !== requestId.current) return;
    if (error || !data?.audio_base64) {
      setPhase('idle');
      if (error?.status === 503) setBlocked(t(language, 'notConfigured'));
      else onError?.(t(language, error?.status === 429 ? 'limit' : 'failed'));
      return;
    }
    const el = new Audio(`data:${data.mime || 'audio/mpeg'};base64,${data.audio_base64}`);
    audio.current = el;
    el.onended = () => { if (mounted.current) setPhase('idle'); };
    el.onerror = () => { if (mounted.current) { setPhase('idle'); onError?.(t(language, 'failed')); } };
    try {
      await el.play();
      if (mounted.current && id === requestId.current) setPhase('playing');
    } catch {
      if (mounted.current) { setPhase('idle'); onError?.(t(language, 'failed')); } // e.g. autoplay policy
    }
  }, [phase, halt, textToSpeak, language, onError]);

  const empty = !textToSpeak.trim();
  const off = !!disabled || empty || !!blocked;
  const label = blocked ?? (phase === 'playing' || phase === 'loading' ? t(language, 'stopSpeak') : t(language, 'speak'));

  return (
    <button
      type="button"
      onClick={play}
      disabled={off}
      aria-label={label}
      aria-pressed={phase === 'playing'}
      title={label}
      className={baseButton}
    >
      {phase === 'loading' ? <Loader2 size={18} aria-hidden="true" className="animate-spin" />
        : phase === 'playing' ? <VolumeX size={20} aria-hidden="true" /> : <Volume2 size={20} aria-hidden="true" />}
    </button>
  );
};

/* ------------------------------ Combined ------------------------------ */

export interface VoiceControlsProps {
  /** Called with the transcript once speech-to-text finishes. */
  onTranscript: (text: string) => void;
  /** Text the speak button reads aloud (e.g. the latest assistant reply). Omit to hide the speak button. */
  textToSpeak?: string;
  /** Short language code: 'en' | 'ta' | 'hi' (must be supported by the backend). */
  language?: VoiceLanguage;
  disabled?: boolean;
  onError?: (message: string) => void;
  className?: string;
}

export const VoiceControls: React.FC<VoiceControlsProps> = ({
  onTranscript, textToSpeak, language = 'en', disabled, onError, className,
}) => (
  <span className={cn('inline-flex flex-wrap items-center gap-2', className)} role="group" aria-label="Voice controls">
    <MicButton onTranscript={onTranscript} language={language} disabled={disabled} onError={onError} />
    {textToSpeak !== undefined && (
      <SpeakButton textToSpeak={textToSpeak} language={language} disabled={disabled} onError={onError} />
    )}
  </span>
);

export default VoiceControls;
