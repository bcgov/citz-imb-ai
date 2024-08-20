import { AnalyticsData, AnalyticsUpdate } from '@/types';

const baseUrl = '/api';

// Send full analytics data to the backend
export const sendFullAnalyticsDataToBackend = async (
  data: AnalyticsData,
  useKeepalive = false,
): Promise<void> => {
  const response = await fetch(`${baseUrl}/saveAnalytics`, {
    keepalive: useKeepalive,
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${localStorage.getItem('keycloak-token')}`,
    },
    body: JSON.stringify(data),
  });

  if (!response.ok) {
    throw new Error('Failed to send full analytics data to the backend');
  }
};

// Send partial analytics updates to the backend
export const sendAnalyticsUpdatesToBackend = async (
  updates: AnalyticsUpdate[],
  useKeepalive = false,
): Promise<void> => {
  const response = await fetch(`${baseUrl}/updateAnalytics`, {
    keepalive: useKeepalive,
    method: 'PATCH',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${localStorage.getItem('keycloak-token')}`,
    },
    body: JSON.stringify(updates),
  });

  if (!response.ok) {
    throw new Error('Failed to send analytics updates to the backend');
  }
};
