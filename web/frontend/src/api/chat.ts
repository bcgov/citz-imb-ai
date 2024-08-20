import { ChatHistory, ApiResponse } from '@/types';

// Function to run a chat interaction with the API
const runChat = async (
  _prompt: string,
  chatHistory: ChatHistory[],
): Promise<{ response: ApiResponse; recordingHash: string }> => {
  try {
    // Send a POST request to the chat endpoint
    const response = await fetch('/api/chat/', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${localStorage.getItem('keycloak-token')}`,
      },
      body: JSON.stringify({
        prompt: _prompt,
        chatHistory: chatHistory,
      }),
    });

    // Throw an error if the response is not successful
    if (!response.ok) {
      throw new Error(`${response.status}`);
    }

    // Parse the response data
    const data = await response.json();
    const responses: ApiResponse = JSON.parse(data.responses);

    // Return the API response and recording hash
    return {
      response: responses,
      recordingHash: data.recording,
    };
  } catch (error) {
    throw error;
  }
};

export default runChat;
