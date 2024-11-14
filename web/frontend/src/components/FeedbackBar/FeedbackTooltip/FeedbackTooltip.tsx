import { useState } from 'react';
import './FeedbackTooltip.scss';
import { VoteType } from '@/types';

interface FeedbackTooltipProps {
  isOpen: boolean;
  onSubmit: (comment: string) => void;
  onClose: () => void;
  rating: VoteType;
}

const FeedbackTooltip = ({
  isOpen,
  onSubmit,
  onClose,
  rating,
}: FeedbackTooltipProps) => {
  const [comment, setComment] = useState('');

  if (!isOpen) return null;

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSubmit(comment);
    setComment('');
  };

  return (
    <div className="feedback-tooltip">
      <form onSubmit={handleSubmit}>
        <textarea
          placeholder={`Tell us why you ${rating === VoteType.upvote ? 'liked' : "didn't like"} this response...`}
          value={comment}
          onChange={(e) => setComment(e.target.value)}
          autoFocus
        />
        <div className="tooltip-buttons">
          <button type="submit">Submit</button>
          <button type="button" onClick={onClose}>
            Cancel
          </button>
        </div>
      </form>
    </div>
  );
};

export default FeedbackTooltip;
