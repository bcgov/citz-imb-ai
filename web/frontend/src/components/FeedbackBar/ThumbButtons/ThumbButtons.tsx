import { assets } from '@/assets/icons/assets';
import { VoteType } from '@/types';
import { ThumbButtonsProps } from '@/types/types/feedback.types';

const ThumbButtons = ({ activeButton, onVote }: ThumbButtonsProps) => {
  return (
    <div className="feedback-buttons">
      <button
        className={`thumb-button ${activeButton === VoteType.upvote ? 'active' : ''}`}
        title="Good Response"
        onClick={() => onVote(VoteType.upvote)}
      >
        <img src={assets.thumbs_up} alt="Good Response" />
      </button>
      <button
        className={`thumb-button ${activeButton === VoteType.downvote ? 'active' : ''}`}
        title="Bad Response"
        onClick={() => onVote(VoteType.downvote)}
      >
        <img src={assets.thumbs_down} alt="Bad Response" />
      </button>
    </div>
  );
};

export default ThumbButtons; 
