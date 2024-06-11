import { useState, useEffect } from 'react';
import './ScrollButton.scss';
import { assets } from '@/assets/icons/assets';

const ScrollButton = () => {
  const [atBottom, setAtBottom] = useState(false);

  const handleScroll = () => {
    const isBottom =
      window.innerHeight + window.scrollY >= document.body.offsetHeight;
    setAtBottom(isBottom);
  };

  const scrollTo = () => {
    window.scrollTo({
      top: atBottom ? 0 : document.body.scrollHeight,
      behavior: 'smooth',
    });
  };

  useEffect(() => {
    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

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
