import React, { createContext, useState, ReactNode, useEffect } from 'react';
import runChat from '@/config/config';
import Keycloak from 'keycloak-js';

interface ContextProps {
  prevPrompts: string[];
  setPrevPrompts: React.Dispatch<React.SetStateAction<string[]>>;
  onSent: (prompt?: string) => Promise<void>;
  setRecentPrompt: React.Dispatch<React.SetStateAction<string>>;
  recentPrompt: string;
  showResult: boolean;
  loading: boolean;
  resultData: string;
  input: string;
  setInput: React.Dispatch<React.SetStateAction<string>>;
  newChat: () => void;
  resetContext: () => void;
  isAuthenticated: boolean;
  KeycloakLogin: () => void;
  KeycloakLogout: () => void;
}

export const Context = createContext<ContextProps | undefined>(undefined);

interface ContextProviderProps {
  children: ReactNode;
}

// Keycloak configuration
const keycloakConfig = {
  realm: 'standard',
  url: 'https://dev.loginproxy.gov.bc.ca/auth',
  'ssl-required': 'external',
  clientId: 'a-i-pathfinding-project-5449',
  'enable-pkce': true,
};

const keycloak = new Keycloak(keycloakConfig);

const ContextProvider: React.FC<ContextProviderProps> = ({ children }) => {
  const [prevPrompts, setPrevPrompts] = useState<string[]>([]);
  const [input, setInput] = useState<string>('');
  const [recentPrompt, setRecentPrompt] = useState<string>('');
  const [showResult, setShowResult] = useState<boolean>(false);
  const [loading, setLoading] = useState<boolean>(false);
  const [resultData, setResultData] = useState<string>('');
  const [isAuthenticated, setIsAuthenticated] = useState<boolean>(false);

  const delayPara = (index: number, nextWord: string) => {
    setTimeout(() => {
      setResultData((prev) => prev + nextWord);
    }, 15 * index);
  };

  const onSent = async (prompt?: string) => {
    setResultData('');
    setLoading(true);
    setShowResult(true);
    setInput('');
    let response;
    if (prompt !== undefined) {
      response = await runChat(prompt);
      setRecentPrompt(prompt);
    } else {
      setPrevPrompts((prev) => [...prev, input]);
      setRecentPrompt(input);
      response = await runChat(input);
    }
    let responseArray = response.split('**');
    let newArray = '';
    for (let i = 0; i < responseArray.length; i++) {
      if (i === 0 || i % 2 !== 1) {
        newArray += responseArray[i];
      } else {
        newArray += '<b>' + responseArray[i] + '</b>';
      }
    }
    console.log(newArray);
    responseArray = newArray.split('*').join('</br>').split(' ');
    for (let i = 0; i < responseArray.length; i++) {
      const nextWord = responseArray[i];
      delayPara(i, nextWord + ' ');
    }
    setLoading(false);
  };

  const newChat = async () => {
    setLoading(false);
    setShowResult(false);
    setInput('');
  };

  const resetContext = () => {
    setPrevPrompts([]);
    setInput('');
    setRecentPrompt('');
    setShowResult(false);
    setLoading(false);
    setResultData('');
  };

  useEffect(() => {
    const initKeycloak = async () => {
      const authenticated = await keycloak.init({
        onLoad: 'check-sso',
        pkceMethod: 'S256',
      });
      setIsAuthenticated(authenticated);
      if (authenticated) {
        localStorage.setItem('keycloak-token', keycloak.token ?? '');
        localStorage.setItem(
          'keycloak-refresh-token',
          keycloak.refreshToken ?? '',
        );
      }
    };

    initKeycloak();
  }, []);

  const KeycloakLogin = async () => {
    await keycloak.login({
      redirectUri: window.location.origin,
    });
  };

  const KeycloakLogout = () => {
    keycloak.logout();
    localStorage.clear();
  };

  const contextValue: ContextProps = {
    prevPrompts,
    setPrevPrompts,
    onSent,
    setRecentPrompt,
    recentPrompt,
    showResult,
    loading,
    resultData,
    input,
    setInput,
    newChat,
    resetContext,
    isAuthenticated,
    KeycloakLogin,
    KeycloakLogout,
  };

  return <Context.Provider value={contextValue}>{children}</Context.Provider>;
};

export default ContextProvider;
