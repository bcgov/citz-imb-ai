import { ArrowClockwise } from '@phosphor-icons/react';

const RegenerateButton = () => {
  const handleRegenerate = () => {
    console.log('Regenerate');
  };

  return (
    <button
      className='feedback-action-button'
      onClick={handleRegenerate}
      title='Regenerate Response'>
      <ArrowClockwise size={20} />
    </button>
  );
};

export default RegenerateButton;
