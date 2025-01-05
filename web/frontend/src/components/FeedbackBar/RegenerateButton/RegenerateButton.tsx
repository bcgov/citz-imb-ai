import { useContext } from 'react';

import { Context } from '@/context/Context';
import { ArrowClockwise } from '@phosphor-icons/react';

const RegenerateButton = () => {
  const context = useContext(Context);

  if (!context) {
    throw new Error('RegenerateButton must be used within a ContextProvider');
  }

  const { recentPrompt, onSent, resetContext, setIsRegenerating } = context;

  const handleRegenerate = async () => {
    // Reset the context to clear previous messages
    resetContext();
    setIsRegenerating(true);
    // Send the most recent prompt again
    if (recentPrompt) {
      await onSent(recentPrompt);
      setIsRegenerating(false);
    }
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
