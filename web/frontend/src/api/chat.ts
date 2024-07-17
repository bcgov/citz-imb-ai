interface ChatHistory {
  prompt: string;
  response: string;
}

interface TopKItem {
  ActId: string;
  Regulations: string | null;
  score: number;
  sectionId: string;
  sectionName: string;
  text: string;
  url: string | null;
}

interface ApiResponse {
  llm: string;
  topk: TopKItem[];
}

const runChat = async (
  _prompt: string,
  chatHistory: ChatHistory[],
): Promise<{ response: ApiResponse; recordingHash: string }> => {
  try {
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

    if (!response.ok) {
      throw new Error(`${response.status}`);
    }

    const data = await response.json();
    const responses: ApiResponse = JSON.parse(data.responses);

    return {
      response: responses,
      recordingHash: data.recording,
    };
  } catch (error) {
    throw error;
  }
};

export default runChat;
