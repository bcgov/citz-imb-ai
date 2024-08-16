import { assets } from '@/assets/icons/assets';
import './FeedbackBar.scss';
import { useContext, useState } from 'react';
import { Context } from '@/context/Context';

// FeedbackBar component
const FeedbackBar = () => {
  // Use context for global state management
  const context = useContext(Context);
  const { sendUserFeedback } = context || {};

  // State to track the active feedback button
  const [activeButton, setActiveButton] = useState<string | null>(null);

  // Function to handle user vote
  const handleVote = (type: 'up_vote' | 'down_vote') => {
    if (activeButton === type) {
      // If the same button is clicked again, reset the vote
      setActiveButton(null);
      sendUserFeedback?.('no_vote');
    } else {
      // Set the new active button and send the feedback
      setActiveButton(type);
      sendUserFeedback?.(type);
    }
  };

  // Render the feedback bar component
  return (
    <div className="feedback-bar">
      <div className="feedback-buttons">
        {/* Thumbs up button */}
        <button
          className={`thumb-button ${activeButton === 'up_vote' ? 'active' : ''}`}
          title="Good Response"
          onClick={() => handleVote('up_vote')}
        >
          <img src={assets.thumbs_up} alt="Good Response" />
        </button>
        {/* Thumbs down button */}
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
