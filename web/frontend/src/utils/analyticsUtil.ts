import {
  sendAnalyticsUpdatesToBackend,
  sendFullAnalyticsDataToBackend,
} from '@/api/analytics';
import {
  AnalyticsData,
  AnalyticsUpdate,
  ChatInteraction,
  TopKItem,
} from '@/types';

import { debounce } from './debounceUtil';
import { generateUUID } from './uuidUtil';

// Constants
const ANALYTICS_STORAGE_KEY = 'analyticsData';
const DEBOUNCE_DELAY = 30000; // 30 seconds

// State variables
let isFirstAnalyticsSend = true;
let updateQueue: AnalyticsUpdate[] = [];

// Helper functions
export const getAnalyticsData = (): AnalyticsData => {
  const data = sessionStorage.getItem(ANALYTICS_STORAGE_KEY);

  return data
    ? JSON.parse(data)
    : { sessionTimestamp: '', sessionId: '', userId: '', chats: [] };
};

// Retrieves analytics data from session storage or returns an empty object if not found
const setAnalyticsData = (data: AnalyticsData): void => {
  sessionStorage.setItem(ANALYTICS_STORAGE_KEY, JSON.stringify(data));
};

// Adds an update to the queue and triggers a debounced send
const queueUpdate = (update: AnalyticsUpdate): void => {
  updateQueue.push(update);
  debouncedSendAnalytics();
};

// Updates analytics data and triggers either an immediate or debounced send
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

// Sends queued analytics updates to the backend after a 30-second delay
const debouncedSendAnalytics = debounce(() => {
  if (updateQueue.length > 0) {
    sendAnalyticsUpdatesToBackend(updateQueue, true);
    updateQueue = [];
  }
}, DEBOUNCE_DELAY);

// Immediately sends analytics data, using POST for first send and PATCH for updates
const sendAnalyticsImmediately = (): void => {
  const data = getAnalyticsData();
  if (data.chats.length === 0) return;
  if (isFirstAnalyticsSend) {
    sendFullAnalyticsDataToBackend(data, true);
    updateQueue = [];
    isFirstAnalyticsSend = false;
  } else if (updateQueue.length > 0) {
    sendAnalyticsUpdatesToBackend(updateQueue, true);
    updateQueue = [];
  }
};

// Sends analytics data immediately when the user leaves the page
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

// Initializes analytics data for a new user session if it doesn't already exist
export const initAnalytics = (userId: string): void => {
  const existingData = getAnalyticsData();
  if (existingData.userId) return;

  const newData: AnalyticsData = {
    sessionTimestamp: new Date().toISOString(),
    sessionId: generateUUID(),
    userId,
    chats: [],
  };
  setAnalyticsData(newData);
};

// Records a new chat interaction and queues an update to be sent
export const addChatInteraction = (
  recording_id: string,
  topk: TopKItem[] | undefined,
  generationComplete: boolean,
): number => {
  const data = getAnalyticsData();
  const chatIndex = data.chats.length;
  const newChat: ChatInteraction = {
    llmResponseId: generateUUID(),
    recording_id,
    timestamp: new Date().toISOString(),
    llmResponseInteraction: {
      chatIndex,
      clicks: 0,
      hoverDuration: 0,
      lastClickTimestamp: '',
    },
    sources:
      topk?.map((_, index) => ({
        chatIndex,
        sourceKey: index,
        response: `response_${index + 1}`,
        clicks: 0,
        lastClickTimestamp: '',
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

// Tracks when a user clicks on a source and updates the analytics data
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

// Tracks user interactions (hover or click) with the LLM response and updates analytics
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
