/**
 * AgentWatch 语言上下文
 * 支持英文/中文切换
 */

import { createContext, useContext, useState, ReactNode, useEffect } from 'react'
import { en, zh, Language } from './locales'

type LangCode = 'en' | 'zh'

const translations: Record<LangCode, Language> = { en, zh }

interface LanguageContextType {
  lang: LangCode
  t: Language
  setLang: (lang: LangCode) => void
  toggleLang: () => void
}

const LanguageContext = createContext<LanguageContextType | undefined>(undefined)

const STORAGE_KEY = 'agentwatch_lang'

export function LanguageProvider({ children }: { children: ReactNode }) {
  // 默认英文，从 localStorage 读取用户偏好
  const [lang, setLangState] = useState<LangCode>(() => {
    const stored = localStorage.getItem(STORAGE_KEY)
    if (stored === 'zh' || stored === 'en') {
      return stored
    }
    return 'en' // 默认英文
  })

  // 保存到 localStorage
  useEffect(() => {
    localStorage.setItem(STORAGE_KEY, lang)
  }, [lang])

  const setLang = (newLang: LangCode) => {
    setLangState(newLang)
  }

  const toggleLang = () => {
    setLangState(lang === 'en' ? 'zh' : 'en')
  }

  const t = translations[lang]

  return (
    <LanguageContext.Provider value={{ lang, t, setLang, toggleLang }}>
      {children}
    </LanguageContext.Provider>
  )
}

export function useLanguage() {
  const context = useContext(LanguageContext)
  if (context === undefined) {
    throw new Error('useLanguage must be used within a LanguageProvider')
  }
  return context
}

export default LanguageContext