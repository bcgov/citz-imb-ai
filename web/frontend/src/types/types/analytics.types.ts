export interface SourceInteraction {
  key: number;
  response: string;
  clicks: number;
  lastClickTimestamp: string;
}

export interface LLMResponseInteraction {
  hoverDuration: number;
  clicks: number;
  lastClickTimestamp: string;
}

export interface ChatInteraction {
  llmResponseId: string;
  timestamp: string;
  recording_id: string;
  llmResponseInteraction: LLMResponseInteraction;
  sources: SourceInteraction[];
}

export interface AnalyticsData {
  sessionTimestamp: string;
  sessionId: string;
  userId: string;
  chats: ChatInteraction[];
}
