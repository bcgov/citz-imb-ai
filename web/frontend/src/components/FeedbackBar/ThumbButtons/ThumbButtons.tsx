import { useState } from 'react';

import FeedbackTooltip from '@/components/FeedbackBar/FeedbackTooltip/FeedbackTooltip';
import { VoteType } from '@/types';
import { ThumbButtonsProps } from '@/types/types/feedback.types';
import { ThumbsDown, ThumbsUp } from '@phosphor-icons/react';

const ThumbButtons = ({ activeButton, onVote }: ThumbButtonsProps) => {
  // Control visibility of feedback tooltip
  const [showTooltip, setShowTooltip] = useState(false);
  // Track which rating (thumbs up/down) was selected
  const [selectedRating, setSelectedRating] = useState<VoteType | null>(null);

  // Handle initial vote click and show tooltip for additional feedback
  const handleVoteClick = (type: VoteType) => {
    setSelectedRating(type);
    setShowTooltip(true);
    onVote(type);
  };

  // Handle submission of text feedback from tooltip
  const handleSubmitFeedback = (comment: string) => {
    if (selectedRating) {
      onVote(selectedRating, comment);
    }
    setShowTooltip(false);
  };

  // Close tooltip without submitting feedback
  const handleCloseTooltip = () => {
    setShowTooltip(false);
  };

  return (
    <div className='feedback-buttons'>
      {/* Thumbs up button - becomes active when upvoted */}
      <button
        className={`feedback-action-button ${activeButton === VoteType.upvote ? 'active' : ''}`}
        title='Good Response'
        onClick={() => handleVoteClick(VoteType.upvote)}>
        <ThumbsUp size={20} />
      </button>

      {/* Thumbs down button - becomes active when downvoted */}
      <button
        className={`feedback-action-button ${activeButton === VoteType.downvote ? 'active' : ''}`}
        title='Bad Response'
        onClick={() => handleVoteClick(VoteType.downvote)}>
        <ThumbsDown size={20} />
      </button>

      {/* Feedback tooltip - shown only after rating is selected */}
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
