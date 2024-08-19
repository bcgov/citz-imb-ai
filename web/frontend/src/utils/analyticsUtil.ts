import { TopKItem } from '@/components/AnswerSection/AnswerSection';
import { v7 as uuidv7 } from 'uuid';

// Interfaces
interface SourceInteraction {
  key: number;
  source: TopKItem;
  clicks: number;
  lastClickTimestamp: string;
}

interface LLMResponseInteraction {
  hoverDuration: number;
  clicks: number;
  lastClickTimestamp: string;
}

interface ChatInteraction {
  timestamp: string;
  userPrompt: string;
  llmResponse: string;
  recording_id: string;
  llmResponseInteraction: LLMResponseInteraction;
  sources: SourceInteraction[];
}

interface AnalyticsData {
  sessionTimestamp: string;
  sessionId: string;
  userId: string;
  chats: ChatInteraction[];
}

// Key for storing analytics data in session storage
const ANALYTICS_STORAGE_KEY = 'analyticsData';

// Retrieves analytics data from session storage
const getAnalyticsData = (): AnalyticsData => {
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
};

// Generate a new session id using uuid v7
const generateSessionId = (): string => {
  return uuidv7();
};

// Initialize analytics data for a new user session
export const initAnalytics = (userId: string): void => {
  const existingData = getAnalyticsData();
  if (existingData.userId) return;

  setAnalyticsData({
    sessionTimestamp: new Date().toISOString(),
    sessionId: generateSessionId(),
    userId,
    chats: [],
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

export { getAnalyticsData };
