import { useState, useContext } from 'react';
import { Copy } from '@phosphor-icons/react';
import { Context } from '@/context/Context';

const CopyButton = () => {
  const [copied, setCopied] = useState(false);
  const context = useContext(Context);

  if (!context) {
    throw new Error('CopyButton must be used within a ContextProvider');
  }

  const { messages } = context;

  const handleCopy = async () => {
    try {
      // Get the last AI message content
      const lastAiMessage = [...messages]
        .reverse()
        .find((message) => message.type === 'ai');

      if (lastAiMessage) {
        // Remove HTML tags from the content
        const cleanContent = lastAiMessage.content.replace(/<[^>]*>/g, '');
        await navigator.clipboard.writeText(cleanContent);
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
