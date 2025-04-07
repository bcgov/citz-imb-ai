import { ApiResponse, ChatHistory, ChatState } from '@/types';

// Function to run a chat interaction with the API
export const runChat = async (
  _prompt: string,
  chatHistory: ChatHistory[],
  ragStateKey: string | null,
): Promise<{ response: ApiResponse; recordingHash: string }> => {
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
      key: ragStateKey
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
};

/**
 * Function to retrieve active RAG states from the API.
 * @returns {Promise<ChatState[]>} - Returns a promise that resolves to an array of ChatState objects.
 */
export const getChatStates = async (): Promise<ChatState[]> => {
  const response = await fetch('/api/chat/states/', {
    method: 'GET',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${localStorage.getItem('keycloak-token')}`,
    },
  });

  if (!response.ok) {
    // Return an empty array if the response is not successful. 
    // API will default if no states are found, so frontend should handle case where no states are returned.
    return []; 
  }
  const data = await response.json();

  return data as ChatState[];
}
