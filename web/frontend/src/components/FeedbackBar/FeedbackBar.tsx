import './FeedbackBar.scss';
import { useContext, useState } from 'react';
import { Context } from '@/context/Context';
import { VoteType } from '@/types';
import ThumbButtons from '@/components/FeedbackBar/ThumbButtons/ThumbButtons';
import CopyButton from '@/components/FeedbackBar/CopyButton/CopyButton';

const FeedbackBar = () => {
  const context = useContext(Context);
  const { sendUserFeedback } = context || {};

  const [activeButton, setActiveButton] = useState<string | null>(null);

  const handleVote = (type: VoteType) => {
    if (activeButton === type) {
      setActiveButton(null);
      sendUserFeedback?.(VoteType.novote);
    } else {
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
