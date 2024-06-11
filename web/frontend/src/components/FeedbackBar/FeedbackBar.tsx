import { assets } from '@/assets/icons/assets';
import './FeedbackBar.scss';
import { useContext, useState } from 'react';
import { Context } from '@/context/Context';

const FeedbackBar = () => {
  const context = useContext(Context);
  const { sendUserFeedback } = context || {};
  const [activeButton, setActiveButton] = useState<string | null>(null);

  const handleVote = (type: 'up_vote' | 'down_vote') => {
    if (activeButton === type) {
      setActiveButton(null);
      sendUserFeedback?.('no_vote');
    } else {
      setActiveButton(type);
      sendUserFeedback?.(type);
    }
  };

  return (
    <div className="feedback-bar">
      <div className="feedback-buttons">
        <button
          className={`thumb-button ${activeButton === 'up_vote' ? 'active' : ''}`}
          title="Good Response"
          onClick={() => handleVote('up_vote')}
        >
          <img src={assets.thumbs_up} alt="Good Response" />
        </button>
        <button
          className={`thumb-button ${activeButton === 'down_vote' ? 'active' : ''}`}
          title="Bad Response"
          onClick={() => handleVote('down_vote')}
        >
          <img src={assets.thumbs_down} alt="Bad Response" />
        </button>
      </div>
    </div>
  );
};

export default FeedbackBar;
