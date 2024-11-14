import './FeedbackBar.scss';
import { useContext, useState } from 'react';
import { Context } from '@/context/Context';
import { VoteType } from '@/types';
import ThumbButtons from '@/components/FeedbackBar/ThumbButtons/ThumbButtons';
import CopyButton from '@/components/FeedbackBar/CopyButton/CopyButton';

const FeedbackBar = () => {
  const context = useContext(Context);
  const { sendUserFeedback } = context || {};

  // Track which feedback button (thumbs up/down) is currently selected
  const [activeButton, setActiveButton] = useState<string | null>(null);

  // Handle user voting - toggles vote if same button is clicked twice
  const handleVote = (type: VoteType) => {
    if (activeButton === type) {
      // If clicking the same button, remove vote
      setActiveButton(null);
      sendUserFeedback?.(VoteType.novote);
    } else {
      // Set new vote
      setActiveButton(type);
      sendUserFeedback?.(type);
    }
  };

  return (
    <div className="feedback-bar">
      <ThumbButtons activeButton={activeButton} onVote={handleVote} />
      <CopyButton />
    </div>
  );
};

export default FeedbackBar;
