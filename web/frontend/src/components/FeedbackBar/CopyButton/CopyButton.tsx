import { useState, useContext } from 'react';
import { Copy } from '@phosphor-icons/react';
import { Context } from '@/context/Context';

const CopyButton = () => {
  // State to track whether text has been copied
  const [copied, setCopied] = useState(false);
  const context = useContext(Context);

  if (!context) {
    throw new Error('CopyButton must be used within a ContextProvider');
  }

  const { messages } = context;

  const handleCopy = async () => {
    try {
      // Find the most recent AI message by reversing the array and finding first AI message
      const lastAiMessage = [...messages]
        .reverse()
        .find((message) => message.type === 'ai');

      if (lastAiMessage) {
        // Strip any HTML tags from the message content for clean copying
        const cleanContent = lastAiMessage.content.replace(/<[^>]*>/g, '');
        await navigator.clipboard.writeText(cleanContent);
        // Show copied state for 2 seconds
        setCopied(true);
        setTimeout(() => setCopied(false), 2000);
      }
    } catch (err) {
      console.error('Failed to copy text:', err);
    }
  };

  return (
    <button
      className={`feedback-action-button ${copied ? 'copied' : ''}`}
      onClick={handleCopy}
      title={copied ? 'Copied!' : 'Copy to clipboard'}
    >
      <Copy size={20} />
    </button>
  );
};

export default CopyButton;