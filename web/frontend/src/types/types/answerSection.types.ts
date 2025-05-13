import type { TopKItem } from "./chat.types";

export interface AnswerSectionProps {
	message: {
		content: string;
		topk?: TopKItem[];
	};
	isLastMessage: boolean;
	generationComplete: boolean;
	recording_id: string;
}
