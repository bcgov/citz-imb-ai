import { useState, useEffect } from 'react';
import './ScrollButton.scss';
import { assets } from '@/assets/icons/assets';

interface ScrollButtonProps {
  scrollableElementId: string;
  generationComplete: boolean;
}

const ScrollButton: React.FC<ScrollButtonProps> = ({
  scrollableElementId,
  generationComplete,
}) => {
  const [atBottom, setAtBottom] = useState(false);

  const handleScroll = () => {
    const element = document.getElementById(scrollableElementId);
    if (element) {
      const isBottom =
        element.scrollHeight - element.scrollTop - element.clientHeight < 1;
      setAtBottom(isBottom);
    }
  };

  const scrollTo = () => {
    const element = document.getElementById(scrollableElementId);
    if (element) {
      element.scrollTo({
        top: atBottom ? 0 : element.scrollHeight,
        behavior: generationComplete ? 'smooth' : 'auto',
      });
    }
  };

  useEffect(() => {
    const element = document.getElementById(scrollableElementId);
    if (element) {
      element.addEventListener('scroll', handleScroll);
    }
    return () => {
      if (element) {
        element.removeEventListener('scroll', handleScroll);
      }
    };
  }, [scrollableElementId]);

  return (
    <div className="scroll-button-container">
      <button
        className="scroll-button"
        onClick={scrollTo}
        title={atBottom ? 'Scroll to Top' : 'Scroll to Bottom'}
      >
        <img
          src={atBottom ? assets.up_arrow : assets.down_arrow}
          alt="scroll icon"
        />
      </button>
    </div>
  );
};

export default ScrollButton;
