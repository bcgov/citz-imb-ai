import {
  AnalyticsData,
  ChatInteraction,
  TopKItem,
  AnalyticsUpdate,
} from '@/types';
import {
  sendFullAnalyticsDataToBackend,
  sendAnalyticsUpdatesToBackend,
} from '@/api/analytics';
import { generateUUID } from './uuidUtil';
import { debounce } from './debounceUtil';

// Key for storing analytics data in session storage
const ANALYTICS_STORAGE_KEY = 'analyticsData';
// Flag to check if this is the first analytics send
let isFirstAnalyticsSend = true;
// Queue for storing analytics updates
let updateQueue: AnalyticsUpdate[] = [];

// Retrieves analytics data from session storage
export const getAnalyticsData = (): AnalyticsData => {
  const data = sessionStorage.getItem(ANALYTICS_STORAGE_KEY);
  return data
    ? JSON.parse(data)
    : { sessionTimestamp: '', sessionId: '', userId: '', chats: [] };
};

// Saves analytics data to session storage
const setAnalyticsData = (data: AnalyticsData): void => {
  sessionStorage.setItem(ANALYTICS_STORAGE_KEY, JSON.stringify(data));
};

// Queues an analytics update to be sent to the backend
const queueUpdate = (update: AnalyticsUpdate): void => {
  updateQueue.push(update);
  debouncedSendAnalytics();
};

// Updates analytics data and saves it to session storage
const updateAnalyticsData = (
  updater: (data: AnalyticsData) => void,
  generationComplete?: boolean,
): void => {
  const data = getAnalyticsData();
  updater(data);
  setAnalyticsData(data);

  if (generationComplete) {
    sendAnalyticsImmediately();
  } else {
    debouncedSendAnalytics();
  }
};

// Debounced function to send analytics data to the backend every 30 seconds
const debouncedSendAnalytics = debounce(() => {
  if (updateQueue.length > 0) {
    sendAnalyticsUpdatesToBackend(updateQueue, true);
    updateQueue = [];
  }
}, 30000);

// Function to send analytics data immediately
const sendAnalyticsImmediately = (): void => {
  const data = getAnalyticsData();
  if (data.chats.length === 0) {
    // No analytics data, don't send anything
    return;
  }

  if (isFirstAnalyticsSend) {
    // This is the first analytics send, always use POST
    sendFullAnalyticsDataToBackend(data, true);
    updateQueue = []; // Clear the update queue
    isFirstAnalyticsSend = false; // Set the flag to false after first send
  } else if (updateQueue.length > 0) {
    // Send only updates using PATCH for subsequent sends
    sendAnalyticsUpdatesToBackend(updateQueue, true);
    updateQueue = [];
  }
};

// Function to send analytics data when the page visibility changes or before unload
export const sendAnalyticsImmediatelyOnLeave = (): (() => void) => {
  const handleVisibilityChange = () => {
    if (document.hidden) {
      sendAnalyticsImmediately();
    }
  };

  const handleBeforeUnload = () => {
    sendAnalyticsImmediately();
  };

  document.addEventListener('visibilitychange', handleVisibilityChange);
  window.addEventListener('beforeunload', handleBeforeUnload);

  return () => {
    document.removeEventListener('visibilitychange', handleVisibilityChange);
    window.removeEventListener('beforeunload', handleBeforeUnload);
  };
};

// Initialize analytics data for a new user session
export const initAnalytics = (userId: string): void => {
  const existingData = getAnalyticsData();
  if (existingData.userId) return;

  const newData = {
    sessionTimestamp: new Date().toISOString(),
    sessionId: generateUUID(),
    userId,
    chats: [],
  };
  setAnalyticsData(newData);
};

// Record a new chat interaction and return its index
export const addChatInteraction = (
  recording_id: string,
  topk: TopKItem[] | undefined,
  generationComplete: boolean,
): number => {
  const data = getAnalyticsData();
  const chatIndex = data.chats.length;
  const newChat: ChatInteraction = {
    llmResponseId: generateUUID(),
    timestamp: new Date().toISOString(),
    recording_id,
    llmResponseInteraction: {
      hoverDuration: 0,
      clicks: 0,
      lastClickTimestamp: '',
      chatIndex,
    },
    sources:
      topk?.map((_item, index) => ({
        sourceKey: index,
        response: `response_${index + 1}`,
        clicks: 0,
        lastClickTimestamp: '',
        chatIndex,
      })) || [],
  };
  data.chats.push(newChat);
  setAnalyticsData(data);

  queueUpdate({
    sessionId: data.sessionId,
    chatIndex,
    newChat,
  });

  if (generationComplete) {
    sendAnalyticsImmediately();
  } else {
    debouncedSendAnalytics();
  }

  return chatIndex;
};

// Track when a user clicks on a source
export const trackSourceClick = (
  chatIndex: number,
  sourceKey: number,
): void => {
  updateAnalyticsData((data) => {
    const source = data.chats[chatIndex]?.sources.find(
      (s) => s.sourceKey === sourceKey,
    );
    if (source) {
      source.clicks++;
      source.lastClickTimestamp = new Date().toISOString();
      queueUpdate({
        sessionId: data.sessionId,
        sourceUpdate: {
          chatIndex,
          sourceKey,
          clicks: source.clicks,
          lastClickTimestamp: source.lastClickTimestamp,
        },
      });
    }
  });
};

// Track user interactions with the LLM response (hover or click)
export const trackLLMResponseInteraction = (
  chatIndex: number,
  interactionType: 'hover' | 'click',
  duration?: number,
): void => {
  updateAnalyticsData((data) => {
    const interaction = data.chats[chatIndex]?.llmResponseInteraction;
    if (interaction) {
      if (interactionType === 'hover' && duration) {
        interaction.hoverDuration += duration;
        queueUpdate({
          sessionId: data.sessionId,
          llmResponseUpdate: {
            chatIndex,
            hoverDuration: interaction.hoverDuration,
          },
        });
      } else if (interactionType === 'click') {
        interaction.clicks++;
        interaction.lastClickTimestamp = new Date().toISOString();
        queueUpdate({
          sessionId: data.sessionId,
          llmResponseUpdate: {
            chatIndex,
            clicks: interaction.clicks,
            lastClickTimestamp: interaction.lastClickTimestamp,
          },
        });
      }
    }
  });
};
