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

// Initialize analytics data with session and user details
export const initAnalytics = (userId: string) => {
  // Check if analytics data already exists in sessionStorage
  const existingData = sessionStorage.getItem('analyticsData');
  if (existingData) {
    return; // Analytics already initialized, do nothing
  }

  const sessionId = new Date().toISOString(); // Implement this function to generate a unique session ID
  const analyticsData: AnalyticsData = {
    sessionId,
    userId,
    chats: [],
  };
  sessionStorage.setItem('analyticsData', JSON.stringify(analyticsData));
};

// Add a new chat interaction
export const addChatInteraction = (
  userPrompt: string,
  llmResponse: string,
  topk: TopKItem[] | undefined,
) => {
  const analyticsData: AnalyticsData = JSON.parse(
    sessionStorage.getItem('analyticsData') || '{}',
  );

  const newChat: ChatInteraction = {
    timestamp: new Date().toISOString(),
    userPrompt,
    llmResponse,
    llmResponseInteraction: {
      hoverDuration: 0,
      clicks: 0,
      lastClickTimestamp: '',
    },
    sources: topk
      ? topk.map((item, index) => ({
          key: index,
          source: item,
          clicks: 0,
          lastClickTimestamp: '',
        }))
      : [],
  };

  analyticsData.chats.push(newChat);
  sessionStorage.setItem('analyticsData', JSON.stringify(analyticsData));
  return analyticsData.chats.length - 1; // Return the index of the new chat
};

// Track when a user clicks on a source
export const trackSourceClick = (chatIndex: number, sourceKey: number) => {
  const analyticsData: AnalyticsData = JSON.parse(
    sessionStorage.getItem('analyticsData') || '{}',
  );
  const sourceIndex = analyticsData.chats[chatIndex].sources.findIndex(
    (s) => s.key === sourceKey,
  );

  if (sourceIndex !== -1) {
    analyticsData.chats[chatIndex].sources[sourceIndex].clicks++;
    analyticsData.chats[chatIndex].sources[sourceIndex].lastClickTimestamp =
      new Date().toISOString();
    sessionStorage.setItem('analyticsData', JSON.stringify(analyticsData));
  }
};

// Track LLM response interactions
export const trackLLMResponseInteraction = (
  chatIndex: number,
  interactionType: 'hover' | 'click',
  duration?: number,
) => {
  const analyticsData: AnalyticsData = JSON.parse(
    sessionStorage.getItem('analyticsData') || '{}',
  );

  if (interactionType === 'hover') {
    analyticsData.chats[chatIndex].llmResponseInteraction.hoverDuration +=
      duration || 0;
  } else if (interactionType === 'click') {
    analyticsData.chats[chatIndex].llmResponseInteraction.clicks++;
    analyticsData.chats[chatIndex].llmResponseInteraction.lastClickTimestamp =
      new Date().toISOString();
  }

  sessionStorage.setItem('analyticsData', JSON.stringify(analyticsData));
};

// Retrieve all analytics data
export const getAnalyticsData = (): AnalyticsData => {
  return JSON.parse(sessionStorage.getItem('analyticsData') || '{}');
};
