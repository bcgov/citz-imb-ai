import { useState } from 'react';
import './FeedbackTooltip.scss';
import { FeedbackTooltipProps, VoteType } from '@/types';

const FeedbackTooltip = ({
  isOpen,
  onSubmit,
  onClose,
  rating,
}: FeedbackTooltipProps) => {
  // Track the user's feedback text
  const [comment, setComment] = useState('');

  // Don't show anything if tooltip is closed
  if (!isOpen) return null;

  // Handle form submission and reset comment
  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSubmit(comment);
    setComment('');
  };

  return (
    <div className="feedback-tooltip">
      <form onSubmit={handleSubmit}>
        {/* Feedback input field */}
        <textarea
          placeholder={`Tell us why you ${rating === VoteType.upvote ? 'liked' : "didn't like"} this response...`}
          value={comment}
          onChange={(e) => setComment(e.target.value)}
          autoFocus
        />
        {/* Submit and cancel buttons */}
        <div className="tooltip-buttons">
          <button type="submit" onClick={handleSubmit}>
            Submit
          </button>
          <button type="button" onClick={onClose}>
            Cancel
          </button>
        </div>
      </form>
    </div>
  );
};

export default FeedbackTooltip;
