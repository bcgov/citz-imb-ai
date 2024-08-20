export interface ChatHistory {
  prompt: string;
  response: string;
}

export interface TopKItem {
  ActId: string;
  Regulations: string | null;
  score: number;
  sectionId: string;
  sectionName: string;
  text: string;
  url: string | null;
}

export interface ApiResponse {
  llm: string;
  topk: TopKItem[];
}

export interface Message {
  type: 'user' | 'ai';
  content: string;
  topk?: TopKItem[];
}
