import { assets } from '@/assets/icons/assets';
import './FeedbackBar.scss';

const FeedbackBar = () => {
  const upvote = () => {
    console.log('upvote, 1');
  };

  const downvote = () => {
    console.log('downvote, 0');
  };

  return (
    <div className="feedback-bar">
      <div className="feedback-buttons">
        <button className="thumb-button" title="Good Response" onClick={upvote}>
          <img src={assets.thumbs_up} alt="Good Response" />
        </button>
        <button
          className="thumb-button"
          title="Bad Response"
          onClick={downvote}
        >
          <img src={assets.thumbs_down} alt="Bad Response" />
        </button>
      </div>
    </div>
  );
};

export default FeedbackBar;
