import { TopKItem } from '@/components/AnswerSection/AnswerSection';

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
  llmResponseInteraction: LLMResponseInteraction;
  sources: SourceInteraction[];
}

interface AnalyticsData {
  sessionId: string;
  userId: string;
  chats: ChatInteraction[];
}

const ANALYTICS_STORAGE_KEY = 'analyticsData';

const getAnalyticsData = (): AnalyticsData => {
  const data = sessionStorage.getItem(ANALYTICS_STORAGE_KEY);
  return data ? JSON.parse(data) : { sessionId: '', userId: '', chats: [] };
};

const setAnalyticsData = (data: AnalyticsData): void => {
  sessionStorage.setItem(ANALYTICS_STORAGE_KEY, JSON.stringify(data));
};

const updateAnalyticsData = (updater: (data: AnalyticsData) => void): void => {
  const data = getAnalyticsData();
  updater(data);
  setAnalyticsData(data);
};

export const initAnalytics = (userId: string): void => {
  const existingData = getAnalyticsData();
  if (existingData.userId) return;

  setAnalyticsData({
    sessionId: new Date().toISOString(),
    userId,
    chats: [],
  });
};

export const addChatInteraction = (
  userPrompt: string,
  llmResponse: string,
  topk: TopKItem[] | undefined,
): number => {
  let newChatIndex = -1;
  updateAnalyticsData((data) => {
    const newChat: ChatInteraction = {
      timestamp: new Date().toISOString(),
      userPrompt,
      llmResponse,
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

export const trackSourceClick = (
  chatIndex: number,
  sourceKey: number,
): void => {
  updateAnalyticsData((data) => {
    const sourceIndex = data.chats[chatIndex]?.sources.findIndex(
      (s) => s.key === sourceKey,
    );
    if (sourceIndex !== -1) {
      const source = data.chats[chatIndex].sources[sourceIndex];
      source.clicks++;
      source.lastClickTimestamp = new Date().toISOString();
    }
  });
};

export const trackLLMResponseInteraction = (
  chatIndex: number,
  interactionType: 'hover' | 'click',
  duration?: number,
): void => {
  updateAnalyticsData((data) => {
    const interaction = data.chats[chatIndex]?.llmResponseInteraction;
    if (interaction) {
      if (interactionType === 'hover') {
        interaction.hoverDuration += duration || 0;
      } else if (interactionType === 'click') {
        interaction.clicks++;
        interaction.lastClickTimestamp = new Date().toISOString();
      }
    }
  });
};

export { getAnalyticsData };
