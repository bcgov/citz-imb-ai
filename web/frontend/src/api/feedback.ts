const sendFeedback = async (
  feedbackType: 'up_vote' | 'down_vote' | 'no_vote',
  recordingHash: string,
): Promise<string> => {
  const response = await fetch('/api/feedbackrag/', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/x-www-form-urlencoded',
      Authorization: `Bearer ${localStorage.getItem('keycloak-token')}`,
    },
    body: `feedback=${encodeURIComponent(feedbackType)}&recording=${encodeURIComponent(recordingHash)}`,
  });
  if (!response.ok) {
    throw new Error('Failed to send feedback');
  }
  const data = await response.json();
  return data.message;
};

export default sendFeedback;
