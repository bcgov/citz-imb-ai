import { TopKItem } from '@/components/AnswerSection/AnswerSection';

interface AnalyticsData {
  analyticsId: string;
  userId: string;
  sources: {
    key: number;
    source: TopKItem;
    clicks: number;
  }[];
}

let analyticsData: AnalyticsData | null = null;

export const initAnalytics = (userId: string, topk: TopKItem[] | undefined) => {
  analyticsData = {
    analyticsId: `analytics_${Date.now()}`,
    userId,
    sources: topk
      ? topk.map((item, index) => ({
          key: index,
          source: item,
          clicks: 0,
        }))
      : [],
  };
};

export const trackSourceClick = (key: number) => {
  if (analyticsData) {
    const sourceIndex = analyticsData.sources.findIndex((s) => s.key === key);
    if (sourceIndex !== -1) {
      analyticsData.sources[sourceIndex].clicks++;
    }
  }
};

export const saveAnalytics = () => {
  if (analyticsData) {
    // Here you would typically send this data to your backend or analytics service
    // For now, we're just logging it to the console once
    console.log('Saving Analytics Data:', analyticsData);
  }
};

export const getAnalyticsData = () => {
  return analyticsData;
};
