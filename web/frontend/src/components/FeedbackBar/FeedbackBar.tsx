import { assets } from '@/assets/icons/assets';
import './FeedbackBar.scss';

const FeedbackBar = () => {
  return (
    <div className="feedback-bar">
      <div className="feedback-buttons">
        <button className="thumb-button" title="Thumbs Up">
          <img src={assets.thumbs_up} alt="Thumbs Up" />
        </button>
        <button className="thumb-button" title="Thumbs Down">
          <img src={assets.thumbs_down} alt="Thumbs Down" />
        </button>
      </div>
    </div>
  );
};

export default FeedbackBar;
