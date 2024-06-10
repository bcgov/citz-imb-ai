import { assets } from '@/assets/icons/assets';
import './FeedbackBar.scss';
import { useContext, useState } from 'react';
import { Context } from '@/context/Context';

const FeedbackBar = () => {
  const context = useContext(Context);
  const { sendUserFeedback } = context || {};
  const [activeButton, setActiveButton] = useState<string | null>(null);

  const handleVote = (type: string) => {
    setActiveButton(type);
    sendUserFeedback?.(type as 'upvote' | 'downvote');
  };

  return (
    <div className="feedback-bar">
      <div className="feedback-buttons">
        <button
          className={`thumb-button ${activeButton === 'upvote' ? 'active' : ''}`}
          title="Good Response"
          onClick={() => handleVote('upvote')}
        >
          <img src={assets.thumbs_up} alt="Good Response" />
        </button>
        <button
          className={`thumb-button ${activeButton === 'downvote' ? 'active' : ''}`}
          title="Bad Response"
          onClick={() => handleVote('downvote')}
        >
          <img src={assets.thumbs_down} alt="Bad Response" />
        </button>
      </div>
    </div>
  );
};

export default FeedbackBar;
