export interface SourceInteraction {
  sourceKey: number;
  response: string;
  clicks: number;
  lastClickTimestamp: string;
  chatIndex: number;
}

export interface LLMResponseInteraction {
  hoverDuration: number;
  clicks: number;
  lastClickTimestamp: string;
  chatIndex: number;
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

export interface AnalyticsUpdate {
  sessionId: string;
  chatIndex?: number;
  newChat?: ChatInteraction;
  sourceUpdate?: {
    chatIndex: number;
    sourceKey: number;
    clicks: number;
    lastClickTimestamp: string;
  };
  llmResponseUpdate?: {
    chatIndex: number;
    hoverDuration?: number;
    clicks?: number;
    lastClickTimestamp?: string;
  };
}
