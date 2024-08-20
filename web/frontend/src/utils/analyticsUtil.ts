import { AnalyticsData, ChatInteraction, TopKItem } from '@/types';
import { sendAnalyticsDataToBackend } from '@/api/analytics';
import { generateUUID } from './uuidUtil';
import { debounce } from './debounceUtil';

// Key for storing analytics data in session storage
const ANALYTICS_STORAGE_KEY = 'analyticsData';

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

// Updates analytics data and saves it to session storage
const updateAnalyticsData = (updater: (data: AnalyticsData) => void): void => {
  const data = getAnalyticsData();
  updater(data);
  setAnalyticsData(data);
  debouncedSendAnalytics();
};

let isAnalyticsSendingActive = false;

const debouncedSendAnalytics = debounce(() => {
  if (!isAnalyticsSendingActive) {
    isAnalyticsSendingActive = true;
    const intervalId = setInterval(() => {
      const data = getAnalyticsData();
      sendAnalyticsDataToBackend(data);
    }, 5000);

    // Stop sending after 5 minutes of inactivity
    setTimeout(() => {
      clearInterval(intervalId);
      isAnalyticsSendingActive = false;
    }, 300000);
  }
}, 1000);

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

  // Send initial analytics data immediately
  sendAnalyticsDataToBackend(newData);

  // Start the debounced sending process
  debouncedSendAnalytics();
};

// Record a new chat interaction and return its index
export const addChatInteraction = (
  userPrompt: string,
  llmResponse: string,
  recording_id: string,
  topk: TopKItem[] | undefined,
): number => {
  let newChatIndex = -1;
  updateAnalyticsData((data) => {
    const newChat: ChatInteraction = {
      llmResponseId: generateUUID(),
      timestamp: new Date().toISOString(),
      userPrompt,
      llmResponse,
      recording_id,
      llmResponseInteraction: {
        hoverDuration: 0,
        clicks: 0,
        lastClickTimestamp: '',
      },
      sources:
        topk?.map((item, index) => ({
          key: index,
          source: item,
          clicks: 0,
          lastClickTimestamp: '',
        })) || [],
    };
    data.chats.push(newChat);
    newChatIndex = data.chats.length - 1;
  });
  return newChatIndex;
};

// Track when a user clicks on a source
export const trackSourceClick = (
  chatIndex: number,
  sourceKey: number,
): void => {
  updateAnalyticsData((data) => {
    const source = data.chats[chatIndex]?.sources.find(
      (s) => s.key === sourceKey,
    );
    if (source) {
      source.clicks++;
      source.lastClickTimestamp = new Date().toISOString();
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
      } else if (interactionType === 'click') {
        interaction.clicks++;
        interaction.lastClickTimestamp = new Date().toISOString();
      }
    }
  });
};
