import React, { createContext, useContext, useState, useEffect } from 'react';
import { translations, languages } from './translations';

const LanguageContext = createContext();

// Map country codes to language codes
const countryToLanguage = {
  // Portuguese
  'BR': 'pt', 'PT': 'pt', 'AO': 'pt', 'MZ': 'pt', 'CV': 'pt',
  // Spanish
  'ES': 'es', 'MX': 'es', 'AR': 'es', 'CO': 'es', 'CL': 'es', 
  'PE': 'es', 'VE': 'es', 'EC': 'es', 'GT': 'es', 'CU': 'es',
  'BO': 'es', 'DO': 'es', 'HN': 'es', 'PY': 'es', 'SV': 'es',
  'NI': 'es', 'CR': 'es', 'PA': 'es', 'UY': 'es', 'PR': 'es',
  // English (default for most other countries)
};

export const LanguageProvider = ({ children }) => {
  const [language, setLanguage] = useState(() => {
    const saved = localStorage.getItem('language');
    return saved || 'pt'; // Default to Portuguese while detecting
  });
  const [isDetecting, setIsDetecting] = useState(false);

  // Detect language from IP on first visit
  useEffect(() => {
    const detectLanguageFromIP = async () => {
      const saved = localStorage.getItem('language');
      const hasDetected = localStorage.getItem('language_detected');
      
      // Only detect if never detected before
      if (!saved && !hasDetected) {
        setIsDetecting(true);
        try {
          const response = await fetch('https://ipapi.co/json/', { 
            timeout: 5000 
          });
          
          if (response.ok) {
            const data = await response.json();
            const countryCode = data.country_code;
            
            // Get language from country or default to English
            const detectedLang = countryToLanguage[countryCode] || 'en';
            
            setLanguage(detectedLang);
            localStorage.setItem('language', detectedLang);
            localStorage.setItem('language_detected', 'true');
            localStorage.setItem('detected_country', countryCode);
          }
        } catch (error) {
          // If detection fails, keep Portuguese as default
          console.log('Language detection failed, using default');
          localStorage.setItem('language_detected', 'true');
        } finally {
          setIsDetecting(false);
        }
      }
    };

    detectLanguageFromIP();
  }, []);

  // Save language changes to localStorage
  useEffect(() => {
    localStorage.setItem('language', language);
  }, [language]);

  const t = (key) => {
    const keys = key.split('.');
    let value = translations[language];
    
    for (const k of keys) {
      if (value && value[k] !== undefined) {
        value = value[k];
      } else {
        // Fallback to Portuguese
        value = translations['pt'];
        for (const k2 of keys) {
          if (value && value[k2] !== undefined) {
            value = value[k2];
          } else {
            return key; // Return key if not found
          }
        }
        break;
      }
    }
    
    return typeof value === 'string' ? value : key;
  };

  return (
    <LanguageContext.Provider value={{ language, setLanguage, t, languages, isDetecting }}>
      {children}
    </LanguageContext.Provider>
  );
};

export const useLanguage = () => {
  const context = useContext(LanguageContext);
  if (!context) {
    throw new Error('useLanguage must be used within a LanguageProvider');
  }
  return context;
};
