import React, { createContext, useState, ReactNode, useEffect } from 'react';
import runChat from '@/api/chat';
import sendFeedback from '@/api/feedback';
import Keycloak from 'keycloak-js';

interface Message {
  type: 'user' | 'ai';
  content: string;
}

interface ChatHistory {
  prompt: string;
  response: string;
}

interface ContextProps {
  prevPrompts: string[];
  setPrevPrompts: React.Dispatch<React.SetStateAction<string[]>>;
  onSent: (prompt?: string) => Promise<void>;
  setRecentPrompt: React.Dispatch<React.SetStateAction<string>>;
  recentPrompt: string;
  showResult: boolean;
  loading: boolean;
  messages: Message[];
  input: string;
  setInput: React.Dispatch<React.SetStateAction<string>>;
  newChat: () => void;
  resetContext: () => void;
  isAuthenticated: boolean;
  KeycloakLogin: () => void;
  KeycloakLogout: () => void;
  sendUserFeedback: (feedbackType: 'up_vote' | 'down_vote' | 'no_vote') => void;
  generationComplete: boolean;
  recordingHash: string;
  errorState: {
    hasError: boolean;
    errorMessage: string;
  };
  resetError: () => void;
}

export const Context = createContext<ContextProps | undefined>(undefined);

interface ContextProviderProps {
  children: ReactNode;
}

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
  const [messages, setMessages] = useState<Message[]>([]);
  const [isAuthenticated, setIsAuthenticated] = useState<boolean>(false);
  const [generationComplete, setGenerationComplete] = useState<boolean>(false);
  const [recordingHash, setRecordingHash] = useState<string>('');
  const [errorState, setErrorState] = useState<{
    hasError: boolean;
    errorMessage: string;
  }>({
    hasError: false,
    errorMessage: '',
  });

  const resetError = () => {
    setErrorState({
      hasError: false,
      errorMessage: '',
    });
  };

  const sendUserFeedback = async (
    feedbackType: 'up_vote' | 'down_vote' | 'no_vote',
  ) => {
    await sendFeedback(feedbackType, recordingHash);
  };

  const delayPara = (index: number, nextWord: string, totalWords: number) => {
    setTimeout(() => {
      setMessages((prev) => {
        const newMessages = [...prev];
        const lastMessage = newMessages[newMessages.length - 1];
        if (lastMessage && lastMessage.type === 'ai') {
          lastMessage.content += nextWord;
        }
        return newMessages;
      });
      if (index === totalWords - 1) {
        setGenerationComplete(true);
      }
    }, 15 * index);
  };

  const updateSessionStorage = (prompt: string, response: string) => {
    const chatHistory: ChatHistory[] = JSON.parse(sessionStorage.getItem('chatHistory') || '[]');
    chatHistory.push({ prompt, response });
    if (chatHistory.length > 4) {
      chatHistory.shift();
    }
    sessionStorage.setItem('chatHistory', JSON.stringify(chatHistory));
  };

  const onSent = async (prompt?: string) => {
    try {
      setLoading(true);
      setShowResult(true);
      setInput('');
      setGenerationComplete(false);
      let response;
      let currentPrompt = prompt !== undefined ? prompt : input;
      
      const chatHistory: ChatHistory[] = JSON.parse(sessionStorage.getItem('chatHistory') || '[]');
      
      response = await runChat(currentPrompt, chatHistory);

      setRecordingHash(response.recordingHash);

      if (prompt !== undefined) {
        setRecentPrompt(prompt);
        setMessages((prev) => [...prev, { type: 'user', content: prompt }]);
      } else {
        setPrevPrompts((prev) => [...prev, input]);
        setRecentPrompt(input);
        setMessages((prev) => [...prev, { type: 'user', content: input }]);
      }

      let responseArray = response.response.split('**');
      let newArray = '';
      for (let i = 0; i < responseArray.length; i++) {
        if (i === 0 || i % 2 !== 1) {
          newArray += responseArray[i];
        } else {
          newArray += '<b>' + responseArray[i] + '</b>';
        }
      }
      responseArray = newArray.split('*').join('</br>').split(' ');
      
      setMessages((prev) => [...prev, { type: 'ai', content: '' }]);
      
      updateSessionStorage(currentPrompt, response.response);

      for (let i = 0; i < responseArray.length; i++) {
        const nextWord = responseArray[i];
        delayPara(i, nextWord + ' ', responseArray.length);
      }
    } catch (error) {
      setErrorState({
        hasError: true,
        errorMessage: (error as Error).message || 'An unknown error occurred',
      });
    } finally {
      setLoading(false);
    }
  };

  const newChat = async () => {
    setLoading(false);
    setShowResult(false);
    setInput('');
    setMessages([]);
    sessionStorage.removeItem('chatHistory');
  };

  const resetContext = () => {
    setPrevPrompts([]);
    setInput('');
    setRecentPrompt('');
    setShowResult(false);
    setLoading(false);
    setMessages([]);
    setGenerationComplete(false);
    sessionStorage.removeItem('chatHistory');
  };

  const refreshToken = () => {
    keycloak.updateToken(70).then((refreshed) => {
      if (refreshed) {
        localStorage.setItem('keycloak-token', keycloak.token ?? '');
        localStorage.setItem(
          'keycloak-refresh-token',
          keycloak.refreshToken ?? '',
        );
      }
    });
  };

  useEffect(() => {
    const initKeycloak = async () => {
      if (!keycloak.authenticated) {
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
          setInterval(refreshToken, 4 * 60 * 1000);
        }
      }
    };

    initKeycloak();

    // Clear session storage on page refresh
    window.addEventListener('beforeunload', () => {
      sessionStorage.removeItem('chatHistory');
    });

    return () => {
      window.removeEventListener('beforeunload', () => {
        sessionStorage.removeItem('chatHistory');
      });
    };
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
    messages,
    input,
    setInput,
    newChat,
    resetContext,
    isAuthenticated,
    KeycloakLogin,
    KeycloakLogout,
    sendUserFeedback,
    generationComplete,
    recordingHash,
    errorState,
    resetError,
  };

  return <Context.Provider value={contextValue}>{children}</Context.Provider>;
};

export default ContextProvider;
