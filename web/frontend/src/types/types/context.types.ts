import { ReactNode } from "react";

import { ChatState, Message } from "./chat.types";
import { userFeedbackType } from "./feedback.types";

export interface ContextProps {
	prevPrompts: string[];
	setPrevPrompts: React.Dispatch<React.SetStateAction<string[]>>;
	onSent: (prompt?: string) => Promise<void>;
	setRecentPrompt: React.Dispatch<React.SetStateAction<string>>;
	recentPrompt: string;
	showResult: boolean;
	loading: boolean;
	messages: Message[];
	input: string;
	setInput: React.Dispatch<React.SetStateAction<string>>;
	newChat: () => void;
	resetContext: () => void;
	isAuthenticated: boolean;
	KeycloakLogin: () => void;
	KeycloakLogout: () => void;
	sendUserFeedback: (
		feedbackType: userFeedbackType,
		comment?: string,
	) => Promise<void>;
	generationComplete: boolean;
	recordingHash: string;
	errorState: {
		hasError: boolean;
		errorMessage: string;
	};
	resetError: () => void;
	isRegenerating: boolean;
	setIsRegenerating: React.Dispatch<React.SetStateAction<boolean>>;
	pendingMessage: string | null;
	setPendingMessage: React.Dispatch<React.SetStateAction<string | null>>;
	chatState: ChatState | null;
	setChatState: React.Dispatch<React.SetStateAction<ChatState | null>>;
}

export interface ContextProviderProps {
	children: ReactNode;
}
