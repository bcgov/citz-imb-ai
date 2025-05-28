export interface ChatHistory {
  prompt: string;
  response: string;
}

export interface references {
  refSectionId: string;
  refActId: string;
  refText: string;
}

export interface TopKItem {
  ActId: string;
  Regulations: string | null;
  score: number;
  sectionId: string;
  sectionName: string;
  text: string;
  url: string | null;
  references: references[];
  ImageUrl?: string;
  file_name?: string;
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

export interface ChatState {
  key: string;
  description: string;
  trulens_id: string;
}
