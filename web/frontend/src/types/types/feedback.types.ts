export enum VoteType {
  upvote = 'up_vote',
  downvote = 'down_vote',
  novote = 'no_vote',
}
export type userFeedbackType = VoteType;

export interface FeedbackBarProps {
  onFeedback: (feedbackType: userFeedbackType) => void;
}

export interface ThumbButtonsProps {
  activeButton: string | null;
  onVote: (type: VoteType) => void;
}

export interface FeedbackTooltipProps {
  isOpen: boolean;
  onSubmit: (comment: string) => void;
  onClose: () => void;
  rating: VoteType;
}
