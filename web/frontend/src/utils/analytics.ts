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

// Initialize analytics data with user interaction details
export const initAnalytics = (
  userId: string,
  topk: TopKItem[] | undefined,
  userPrompt: string,
  llmResponse: string,
) => {
  const analyticsData: AnalyticsData = {
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

  const existingData = sessionStorage.getItem('analyticsData');
  const dataArray = existingData ? JSON.parse(existingData) : [];
  dataArray.push(analyticsData);
  sessionStorage.setItem('analyticsData', JSON.stringify(dataArray));
};

// Track when a user clicks on a source
export const trackSourceClick = (promptIndex: number, sourceKey: number) => {
  const existingData = sessionStorage.getItem('analyticsData');
  if (existingData) {
    const dataArray = JSON.parse(existingData);
    if (dataArray[promptIndex]) {
      const sourceIndex = dataArray[promptIndex].sources.findIndex(
        (s: any) => s.key === sourceKey,
      );
      if (sourceIndex !== -1) {
        dataArray[promptIndex].sources[sourceIndex].clicks++;
        dataArray[promptIndex].sources[sourceIndex].lastClickTimestamp =
          new Date().toISOString();
        sessionStorage.setItem('analyticsData', JSON.stringify(dataArray));
      }
    }
  }
};

// Save analytics data (currently just stores in session storage)
export const saveAnalytics = async () => {
  // This function is now redundant as we're saving data immediately in initAnalytics and trackSourceClick
  // Keeping it for potential future use (e.g., sending data to a server)
};

// Retrieve all analytics data
export const getAnalyticsData = (): AnalyticsData[] => {
  const data = sessionStorage.getItem('analyticsData');
  return data ? JSON.parse(data) : [];
};
