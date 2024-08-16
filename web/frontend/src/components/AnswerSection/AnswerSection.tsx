import React, { useState, useEffect, useContext, useRef } from 'react';
import './AnswerSection.scss';
import ModalDialog from '@/components/Modal/ModalDialog';
import FeedbackBar from '@/components/FeedbackBar/FeedbackBar';
import { assets } from '@/assets/icons/assets';
import {
  initAnalytics,
  addChatInteraction,
  trackSourceClick,
  trackLLMResponseInteraction,
} from '@/utils/analytics';
import { Context } from '@/context/Context';
import { getUserId } from '@/utils/auth';

// Define the structure for TopKItem
export interface TopKItem {
  ActId: string;
  Regulations: string | null;
  score: number;
  sectionId: string;
  sectionName: string;
  text: string;
  url: string | null;
}

// Define props for AnswerSection component
interface AnswerSectionProps {
  message: {
    content: string;
    topk?: TopKItem[];
  };
  isLastMessage: boolean;
  generationComplete: boolean;
}

// AnswerSection component
const AnswerSection: React.FC<AnswerSectionProps> = ({
  message,
  isLastMessage,
  generationComplete,
}) => {
  // Use context and set up state
  const context = useContext(Context);
  const [selectedItem, setSelectedItem] = useState<TopKItem | null>(null);
  const [isAnswerComplete, setIsAnswerComplete] = useState(false);
  const [showSources, setShowSources] = useState(true);
  const [hoverStartTime, setHoverStartTime] = useState<number | null>(null);
  const [chatIndex, setChatIndex] = useState<number | null>(null);
  const analyticsInitialized = useRef(false);

  // Ensure context is available
  if (!context) {
    throw new Error('AnswerSection must be used within a ContextProvider');
  }

  // Destructure context values and get user ID
  const { messages } = context;
  const userId = getUserId();

  // Initialize analytics only once
  useEffect(() => {
    if (!analyticsInitialized.current) {
      initAnalytics(userId);
      analyticsInitialized.current = true;
    }
  }, []);

  // Add chat interaction when the AI generation is complete
  useEffect(() => {
    if (generationComplete && isLastMessage) {
      const aiMessages = messages.filter((msg) => msg.type === 'ai');
      const userMessages = messages.filter((msg) => msg.type === 'user');
      if (aiMessages.length > 0 && userMessages.length > 0) {
        const lastAiMessage = aiMessages[aiMessages.length - 1];
        const lastUserMessage = userMessages[userMessages.length - 1];
        const newChatIndex = addChatInteraction(
          lastUserMessage.content,
          lastAiMessage.content,
          lastAiMessage.topk,
        );
        setChatIndex(newChatIndex);
      }
    }
  }, [generationComplete, isLastMessage, messages]);

  // Handle click on a source card
  const handleCardClick = (item: TopKItem, index: number) => {
    setSelectedItem(item);
    if (chatIndex !== null) {
      trackSourceClick(chatIndex, index);
    }
  };

  // Handle hover on LLM response
  const handleLLMResponseHover = (isHovering: boolean) => {
    if (chatIndex === null) return;

    if (isHovering) {
      setHoverStartTime(Date.now());
    } else if (hoverStartTime !== null) {
      const hoverDuration = Date.now() - hoverStartTime;
      trackLLMResponseInteraction(chatIndex, 'hover', hoverDuration);
      setHoverStartTime(null);
    }
  };

  // Handle click on LLM response
  const handleLLMResponseClick = () => {
    if (chatIndex !== null) {
      trackLLMResponseInteraction(chatIndex, 'click');
    }
  };

  // Close the modal
  const handleCloseModal = () => {
    setSelectedItem(null);
  };

  // Format the description for the modal
  const formatDescription = (item: TopKItem) => (
    <div>
      <p>
        <strong>Score:</strong> {item.score || 'N/A'}
      </p>
      <p>
        <strong>Act ID:</strong> {item.ActId || 'N/A'}
      </p>
      <p>
        <strong>Section Name:</strong> {item.sectionName || 'N/A'}
      </p>
      <p>
        <strong>Section ID:</strong> {item.sectionId || 'N/A'}
      </p>
      <p>
        <strong>Regulations:</strong> {item.Regulations || 'N/A'}
      </p>
      <p>
        <strong>URL:</strong>{' '}
        {item.url ? (
          <a href={item.url} target="_blank" rel="noopener noreferrer">
            {item.url}
          </a>
        ) : (
          'N/A'
        )}
      </p>
      <p>
        <strong>Text:</strong> {item.text || 'N/A'}
      </p>
    </div>
  );

  // Truncate text to a specified length
  const truncateText = (text: string, maxLength: number) => {
    if (text.length <= maxLength) return text;
    return text.slice(0, maxLength) + '...';
  };

  useEffect(() => {
    let timer: NodeJS.Timeout;
    if (generationComplete) {
      timer = setTimeout(() => {
        setIsAnswerComplete(true);
      }, 500);
    }
    return () => clearTimeout(timer);
  }, [generationComplete]);

  // Render the component
  return (
    <div className="answer-section">
      <div
        className="message-title"
        onMouseEnter={() => handleLLMResponseHover(true)}
        onMouseLeave={() => handleLLMResponseHover(false)}
        onClick={handleLLMResponseClick}
      >
        <img src={assets.bc_icon} alt="BC AI" />
        <p dangerouslySetInnerHTML={{ __html: message.content }}></p>
      </div>
      {/* Render sources section if available */}
      {message.topk && message.topk.length > 0 && (
        <div className={`sources-section ${isAnswerComplete ? 'fade-in' : ''}`}>
          <h3
            onClick={() => setShowSources(!showSources)}
            style={{ cursor: 'pointer' }}
          >
            Sources
            <img
              src={assets.down_arrow}
              alt={showSources ? 'Hide sources' : 'Show sources'}
              className={`chevron-icon ${showSources ? '' : 'rotated'}`}
            />
          </h3>
          <div className={`topk-container ${showSources ? 'show' : 'hide'}`}>
            <div className="topk-cards">
              {message.topk.map((item, index) => (
                <div
                  key={index}
                  className="topk-card"
                  onClick={() => handleCardClick(item, index)}
                >
                  <h3>{item.ActId}</h3>
                  <p className="truncated-text">
                    {truncateText(item.text, 100)}
                  </p>
                  <span className="card-number">{index + 1}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
      {/* Render feedback bar for last message when generation is complete */}
      {isLastMessage && generationComplete && <FeedbackBar />}
      {/* Render modal dialog when a source is selected */}
      {selectedItem && (
        <ModalDialog
          title={selectedItem.ActId || 'Details'}
          description={formatDescription(selectedItem)}
          option1={{
            text: 'Close',
            onClick: handleCloseModal,
          }}
          closeOnOutsideClick={true}
        />
      )}
    </div>
  );
};

export default AnswerSection;
