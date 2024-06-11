// const sendFeedback = async (
//   feedbackType: 'up_vote' | 'down_vote' | 'no_vote',
// ): Promise<string> => {
//   const response = await fetch('/api/feedback/', {
//     method: 'POST',
//     headers: {
//       'Content-Type': 'application/x-www-form-urlencoded',
//       Authorization: `Bearer ${localStorage.getItem('keycloak-token')}`,
//     },
//     body: `feedback=${encodeURIComponent(feedbackType)}`,
//   });

//   if (!response.ok) {
//     throw new Error('Failed to send feedback');
//   }

//   const data = await response.json();
//   return data.message;
// };

// export default sendFeedback;

const sendFeedback = async (
  feedbackType: 'up_vote' | 'down_vote' | 'no_vote',
): Promise<string> => {
  return `Feedback logged: ${feedbackType}`;
};

export default sendFeedback;
