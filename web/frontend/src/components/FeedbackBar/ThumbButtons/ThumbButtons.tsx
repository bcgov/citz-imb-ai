import { VoteType } from '@/types';
import { ThumbButtonsProps } from '@/types/types/feedback.types';
import { ThumbsUp, ThumbsDown } from '@phosphor-icons/react';

const ThumbButtons = ({ activeButton, onVote }: ThumbButtonsProps) => {
  return (
    <div className="feedback-buttons">
      <button
        className={`feedback-action-button ${activeButton === VoteType.upvote ? 'active' : ''}`}
        title="Good Response"
        onClick={() => onVote(VoteType.upvote)}
      >
        <ThumbsUp size={20} />
      </button>
      <button
        className={`feedback-action-button ${activeButton === VoteType.downvote ? 'active' : ''}`}
        title="Bad Response"
        onClick={() => onVote(VoteType.downvote)}
      >
        <ThumbsDown size={20} />
      </button>
    </div>
  );
};

export default ThumbButtons;
