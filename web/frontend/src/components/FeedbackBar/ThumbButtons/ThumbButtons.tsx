import { useState } from 'react';
import { VoteType } from '@/types';
import { ThumbButtonsProps } from '@/types/types/feedback.types';
import { ThumbsUp, ThumbsDown } from '@phosphor-icons/react';
import FeedbackTooltip from '@/components/FeedbackBar/FeedbackTooltip/FeedbackTooltip';

const ThumbButtons = ({ activeButton, onVote }: ThumbButtonsProps) => {
  const [showTooltip, setShowTooltip] = useState(false);
  const [selectedRating, setSelectedRating] = useState<VoteType | null>(null);

  const handleVoteClick = (type: VoteType) => {
    setSelectedRating(type);
    setShowTooltip(true);
    onVote(type);
  };

  const handleSubmitFeedback = (comment: string) => {
    console.log('Feedback:', comment);
    setShowTooltip(false);
  };

  const handleCloseTooltip = () => {
    setShowTooltip(false);
  };

  return (
    <div className="feedback-buttons " style={{ position: 'relative' }}>
      <button
        className={`feedback-action-button ${activeButton === VoteType.upvote ? 'active' : ''}`}
        title="Good Response"
        onClick={() => handleVoteClick(VoteType.upvote)}
      >
        <ThumbsUp size={20} />
      </button>
      <button
        className={`feedback-action-button ${activeButton === VoteType.downvote ? 'active' : ''}`}
        title="Bad Response"
        onClick={() => handleVoteClick(VoteType.downvote)}
      >
        <ThumbsDown size={20} />
      </button>
      {showTooltip && selectedRating && (
        <FeedbackTooltip
          isOpen={showTooltip}
          onSubmit={handleSubmitFeedback}
          onClose={handleCloseTooltip}
          rating={selectedRating}
        />
      )}
    </div>
  );
};

export default ThumbButtons;
