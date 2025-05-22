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

export interface SourcesSectionProps {
	showSources: boolean;
	message: {
		content: string;
		topk?: TopKItem[];
	};
	handleCardClick: (item: TopKItem, index: number) => void;
	truncateText: (text: string, length: number) => string;
}

export interface ImageItem {
	url: string;
	alt: string;
	filename?: string; // Optional filename for display
	topkItem?: TopKItem; // Optional reference to the original topk item if needed
}

export interface ImagesSectionProps {
	showSources: boolean;
	images: ImageItem[];
	onImageClick: (image: ImageItem, index: number) => void;
}
