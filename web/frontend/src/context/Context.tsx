import React, { createContext, useEffect, useState } from 'react';

import { runChat } from '@/api/chat';
import sendFeedback from '@/api/feedback';
import {
  ChatHistory,
  ContextProps,
  ContextProviderProps,
  Message,
  userFeedbackType,
} from '@/types';

import Keycloak from 'keycloak-js';

// Create a Context with ContextProps type or undefined
export const Context = createContext<ContextProps | undefined>(undefined);

// Keycloak configuration object
const keycloakConfig = {
  realm: 'standard',
  url: 'https://dev.loginproxy.gov.bc.ca/auth',
  'ssl-required': 'external',
  clientId: 'a-i-pathfinding-project-5449',
  'enable-pkce': true,
};

// Initialize Keycloak instance
const keycloak = new Keycloak(keycloakConfig);

// ContextProvider component
const ContextProvider: React.FC<ContextProviderProps> = ({ children }) => {
  // State declarations
  const [prevPrompts, setPrevPrompts] = useState<string[]>([]);
  const [input, setInput] = useState<string>('');
  const [recentPrompt, setRecentPrompt] = useState<string>('');
  const [showResult, setShowResult] = useState<boolean>(false);
  const [loading, setLoading] = useState<boolean>(false);
  const [isRegenerating, setIsRegenerating] = useState<boolean>(false);
  const [messages, setMessages] = useState<Message[]>([]);
  const [isAuthenticated, setIsAuthenticated] = useState<boolean>(false);
  const [generationComplete, setGenerationComplete] = useState<boolean>(false);
  const [pendingMessage, setPendingMessage] = useState<string | null>(null);
  const [recordingHash, setRecordingHash] = useState<string>('');
  const [errorState, setErrorState] = useState<{
    hasError: boolean;
    errorMessage: string;
  }>({
    hasError: false,
    errorMessage: '',
  });

  // Function to reset error state
  const resetError = () => {
    setErrorState({
      hasError: false,
      errorMessage: '',
    });
  };

  // Function to send user feedback
  const sendUserFeedback = async (
    feedbackType: userFeedbackType,
    comment?: string,
  ) => {
    try {
      await sendFeedback(feedbackType, recordingHash, comment);
    } catch (error) {
      console.error('Error sending feedback:', error);
    }
  };

  // Function to delay paragraph generation
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

  // Function to update session storage with chat history
  const updateSessionStorage = (prompt: string, response: string) => {
    const chatHistory: ChatHistory[] = JSON.parse(
      sessionStorage.getItem('chatHistory') || '[]',
    );
    chatHistory.push({ prompt, response });
    if (chatHistory.length > 4) {
      chatHistory.shift();
    }
    sessionStorage.setItem('chatHistory', JSON.stringify(chatHistory));
  };

  // Function to handle sending a message
  const onSent = async (prompt?: string) => {
    try {
      // Set loading state and prepare for new message
      setLoading(true);
      setShowResult(true);
      setInput('');
      setGenerationComplete(false);
      const currentPrompt = prompt !== undefined ? prompt : input;
      const chatHistory = JSON.parse(
        sessionStorage.getItem('chatHistory') || '[]',
      );
      const ragStateKey = sessionStorage.getItem('ragStateKey');
      const response = await runChat(currentPrompt, chatHistory, ragStateKey);

      // Set recording hash for feedback
      setRecordingHash(response.recordingHash);

      // Update messages state with user input
      if (prompt !== undefined) {
        setRecentPrompt(prompt);
        setMessages((prev) => [...prev, { type: 'user', content: prompt }]);
      } else {
        setPrevPrompts((prev) => [...prev, input]);
        setRecentPrompt(input);
        setMessages((prev) => [...prev, { type: 'user', content: input }]);
      }

      // Process and display AI response
      const llmResponse = response.response.llm;
      const topkData = response.response.topk;

      // Format response for display
      let responseArray = llmResponse.split('**');
      let newArray = '';
      for (let i = 0; i < responseArray.length; i++) {
        if (i === 0 || i % 2 !== 1) {
          newArray += responseArray[i];
        } else {
          newArray += '<b>' + responseArray[i] + '</b>';
        }
      }
      responseArray = newArray.split('\n').join('</br>').split(' ');

      // Add AI message to state
      setMessages((prev) => [
        ...prev,
        { type: 'ai', content: '', topk: topkData },
      ]);

      // Update session storage
      updateSessionStorage(currentPrompt, JSON.stringify(response.response));

      // Display response word by word
      for (let i = 0; i < responseArray.length; i++) {
        const nextWord = responseArray[i];
        delayPara(i, nextWord + ' ', responseArray.length);
      }
    } catch (error) {
      console.error('Error in onSent:', error);
      setErrorState({
        hasError: true,
        errorMessage: error instanceof Error ? error.message : 'Unknown error',
      });
    } finally {
      setLoading(false);
    }
  };

  // Function to start a new chat
  const newChat = async () => {
    setLoading(false);
    setShowResult(false);
    setInput('');
    setMessages([]);
    sessionStorage.removeItem('chatHistory');
  };

  // Function to reset the context
  const resetContext = () => {
    setPrevPrompts([]);
    setInput('');
    setRecentPrompt('');
    setShowResult(false);
    setLoading(false);
    setMessages([]);
    setGenerationComplete(false);
    sessionStorage.removeItem('chatHistory');
    sessionStorage.removeItem('analyticsData');
  };

  // Function to refresh the Keycloak token
  const refreshToken = () => {
    keycloak
      .updateToken(70)
      .then((refreshed) => {
        if (refreshed) {
          localStorage.setItem('keycloak-token', keycloak.token ?? '');
          localStorage.setItem(
            'keycloak-refresh-token',
            keycloak.refreshToken ?? '',
          );
        }

        return refreshed;
      })
      .catch((error) => {
        console.error('Failed to refresh token:', error);
        KeycloakLogout();
        throw error;
      });
  };

  // Effect to initialize Keycloak and set up event listeners
  useEffect(() => {
    const initKeycloak = async () => {
      if (!keycloak.authenticated) {
        const authenticated = await keycloak.init({
          onLoad: 'check-sso',
          pkceMethod: 'S256',
        });
        setIsAuthenticated(authenticated);
        if (authenticated) {
          localStorage.setItem(
            'keycloak-user-id',
            keycloak.tokenParsed?.idir_user_guid ?? '',
          );
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

  // Function to handle Keycloak login
  const KeycloakLogin = async () => {
    await keycloak.login({
      redirectUri: window.location.origin,
    });
  };

  // Function to handle Keycloak logout
  const KeycloakLogout = () => {
    keycloak.logout();
    localStorage.clear();
  };

  // Create context value object
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
    isRegenerating,
    setIsRegenerating,
    pendingMessage,
    setPendingMessage,
  };

  // Render the Context Provider with the context value
  return <Context.Provider value={contextValue}>{children}</Context.Provider>;
};

export default ContextProvider;
