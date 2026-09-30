import React, { createContext, useContext, useState, useEffect } from 'react';
import { type Language, translations } from '../utils/i18n';

export type TranslationParams = Record<string, string | number>;

interface LanguageContextType {
  language: Language;
  setLanguage: (lang: Language) => void;
  t: (key: string, defaultTextOrParams?: string | TranslationParams, params?: TranslationParams) => string;
}

const LanguageContext = createContext<LanguageContextType | undefined>(undefined);

export const LanguageProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [language, setLanguageState] = useState<Language>(() => {
    return (localStorage.getItem('app_lang') as Language) || 'en';
  });

  const setLanguage = (lang: Language) => {
    setLanguageState(lang);
    localStorage.setItem('app_lang', lang);
  };

  const t = (
    key: string,
    defaultTextOrParams?: string | TranslationParams,
    params?: TranslationParams
  ): string => {
    let fallbackText: string | undefined;
    let actualParams: TranslationParams | undefined;

    if (typeof defaultTextOrParams === 'object' && defaultTextOrParams !== null) {
      actualParams = defaultTextOrParams;
    } else if (typeof defaultTextOrParams === 'string') {
      fallbackText = defaultTextOrParams;
      actualParams = params;
    } else {
      actualParams = params;
    }

    let text = translations[language]?.[key] || translations['en']?.[key] || fallbackText || key;

    if (actualParams && typeof text === 'string') {
      Object.entries(actualParams).forEach(([k, v]) => {
        text = text.replace(new RegExp(`\\{${k}\\}`, 'g'), String(v));
      });
    }

    return text;
  };

  useEffect(() => {
    document.documentElement.lang = language;
  }, [language]);

  return (
    <LanguageContext.Provider value={{ language, setLanguage, t }}>
      {children}
    </LanguageContext.Provider>
  );
};

export const useLanguage = (): LanguageContextType => {
  const context = useContext(LanguageContext);
  if (!context) {
    throw new Error('useLanguage must be used within a LanguageProvider');
  }
  return context;
};
