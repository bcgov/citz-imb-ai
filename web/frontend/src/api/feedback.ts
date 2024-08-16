// Function to send user feedback to the server
const sendFeedback = async (
  feedbackType: 'up_vote' | 'down_vote' | 'no_vote',
  recordingHash: string,
): Promise<string> => {
  // Send a POST request to the feedback endpoint
  const response = await fetch('/api/feedbackrag/', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/x-www-form-urlencoded',
      Authorization: `Bearer ${localStorage.getItem('keycloak-token')}`,
    },
    body: `feedback=${encodeURIComponent(feedbackType)}&recording_id=${encodeURIComponent(recordingHash)}`,
  });

  // Throw an error if the response is not successful
  if (!response.ok) {
    throw new Error('Failed to send feedback');
  }

  // Parse and return the response data
  const data = await response.json();
  return data.message;
};

export default sendFeedback;
