import { TopKItem } from '@/components/AnswerSection/AnswerSection';

// Define the structure for analytics data
interface AnalyticsData {
  timestamp: string;
  userId: string;
  userPrompt: string;
  llmResponse: string;
  sources: {
    key: number;
    source: TopKItem;
    clicks: number;
    lastClickTimestamp: string;
  }[];
}

// Store analytics data in memory
let analyticsData: AnalyticsData | null = null;

// Initialize analytics data with user interaction details
export const initAnalytics = (
  userId: string,
  topk: TopKItem[] | undefined,
  userPrompt: string,
  llmResponse: string,
) => {
  analyticsData = {
    timestamp: new Date().toISOString(),
    userId,
    userPrompt,
    llmResponse,
    sources: topk
      ? topk.map((item, index) => ({
          key: index,
          source: item,
          clicks: 0,
          lastClickTimestamp: '',
        }))
      : [],
  };
};

// Track when a user clicks on a source
export const trackSourceClick = (key: number) => {
  if (analyticsData) {
    const sourceIndex = analyticsData.sources.findIndex((s) => s.key === key);
    if (sourceIndex !== -1) {
      analyticsData.sources[sourceIndex].clicks++;
      analyticsData.sources[sourceIndex].lastClickTimestamp =
        new Date().toISOString();
    }
  }
};

// Save analytics data (currently just logs to console)
export const saveAnalytics = async () => {
  if (analyticsData) {
    try {
      // Here you would typically send this data to your backend or analytics service
      // For now, we're just logging it to the console
      console.log('Saving Analytics Data:', analyticsData);
    } catch (error) {
      console.error('Error saving analytics:', error);
    }
  }
};

// Retrieve the current analytics data
export const getAnalyticsData = () => {
  return analyticsData;
};
