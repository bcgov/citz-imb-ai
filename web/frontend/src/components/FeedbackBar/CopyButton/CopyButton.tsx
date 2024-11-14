import { useState } from 'react';
import { Copy } from '@phosphor-icons/react';
import { CopyButtonProps } from '@/types/types/feedback.types';

const CopyButton = ({ textToCopy }: CopyButtonProps) => {
  const [copied, setCopied] = useState(false);

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(textToCopy);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
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
