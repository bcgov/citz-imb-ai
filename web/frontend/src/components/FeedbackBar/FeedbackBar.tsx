import { assets } from '@/assets/icons/assets';
import './FeedbackBar.scss';

const FeedbackBar = () => {
  return (
    <div className="feedback-bar">
      <div className="feedback-buttons">
        <button className="thumb-button" title="Good Response">
          <img src={assets.thumbs_up} alt="Good Response" />
        </button>
        <button className="thumb-button" title="Bad Response">
          <img src={assets.thumbs_down} alt="Bad Response" />
        </button>
      </div>
    </div>
  );
};

export default FeedbackBar;
