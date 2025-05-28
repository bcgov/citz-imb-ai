import { useContext, useState } from 'react';

import CopyButton from '@/components/FeedbackBar/CopyButton/CopyButton';
import RegenerateButton from '@/components/FeedbackBar/RegenerateButton/RegenerateButton';
import ThumbButtons from '@/components/FeedbackBar/ThumbButtons/ThumbButtons';
import { Context } from '@/context/Context';
import { VoteType } from '@/types';

import './FeedbackBar.scss';

const FeedbackBar = () => {
  const context = useContext(Context);
  const { sendUserFeedback } = context || {};

  // Track which feedback button (thumbs up/down) is currently selected
  const [activeButton, setActiveButton] = useState<string | null>(null);

  // Handle user voting - toggles vote if same button is clicked twice
  const handleVote = (type: VoteType, comment?: string) => {
    if (activeButton === type && !comment) {
      // If clicking the same button without comment, remove vote
      setActiveButton(null);
      sendUserFeedback?.(VoteType.novote);
    } else {
      // Set new vote
      setActiveButton(type);
      sendUserFeedback?.(type, comment);
    }
  };

  return (
    <div className='feedback-bar'>
      <ThumbButtons activeButton={activeButton} onVote={handleVote} />
      <CopyButton />
      <RegenerateButton />
    </div>
  );
};

export default FeedbackBar;
