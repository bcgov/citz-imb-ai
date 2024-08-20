import { AnalyticsData, ChatInteraction, TopKItem } from '@/types';
import { sendAnalyticsDataToBackend } from '@/api/analytics';
import { generateUUID } from './uuidUtil';
import { debounce } from './debounceUtil';

// Key for storing analytics data in session storage
const ANALYTICS_STORAGE_KEY = 'analyticsData';
// Last data sent to the backend
let lastSentData: string | null = null;
// Whether the analytics data is currently being sent to the backend
let isAnalyticsSendingActive = false;

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
  if (!isAnalyticsSendingActive) {
    isAnalyticsSendingActive = true;
    debouncedSendAnalytics();
  }
};

// Debounced function to send analytics data to the backend
const debouncedSendAnalytics = debounce(() => {
  sendAnalyticsImmediately();
  isAnalyticsSendingActive = false;
}, 10000);

// Function to send analytics data immediately
const sendAnalyticsImmediately = () => {
  const currentData = JSON.stringify(getAnalyticsData());
  if (currentData !== lastSentData) {
    sendAnalyticsDataToBackend(JSON.parse(currentData));
    lastSentData = currentData;
  }
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

  // Send initial analytics data immediately
  sendAnalyticsDataToBackend(newData);
  lastSentData = JSON.stringify(newData);

  // Add beforeunload event listener with dialog
  window.addEventListener('beforeunload', (event) => {
    sendAnalyticsImmediately();
    event.preventDefault();
    event.returnValue = '';
    return '';
  });
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
