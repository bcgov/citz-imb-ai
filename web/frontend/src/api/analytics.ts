import { AnalyticsData } from '@/types';

export const sendAnalyticsDataToBackend = async (
  data: AnalyticsData,
): Promise<void> => {
  try {
    const response = await fetch('/api/saveAnalytics', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${localStorage.getItem('keycloak-token')}`,
      },
      body: JSON.stringify(data),
    });

    if (!response.ok) {
      throw new Error('Failed to send analytics data to the backend');
    }

    console.log('Analytics data successfully sent to the backend');
  } catch (error) {
    console.error('Error sending analytics data:', error);
  }
};
