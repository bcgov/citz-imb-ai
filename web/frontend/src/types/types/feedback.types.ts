export enum VoteType {
  upvote = 'up_vote',
  downvote = 'down_vote',
  novote = 'no_vote',
}
export type userFeedbackType = VoteType;

export interface FeedbackBarProps {
  onFeedback: (feedbackType: userFeedbackType) => void;
}
