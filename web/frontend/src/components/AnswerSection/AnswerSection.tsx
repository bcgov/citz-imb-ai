import React, {
  useState,
  useEffect,
  useContext,
  useRef,
  useCallback,
} from 'react';
import './AnswerSection.scss';
import ModalDialog from '@/components/Modal/ModalDialog';
import FeedbackBar from '@/components/FeedbackBar/FeedbackBar';
import { assets } from '@/assets/icons/assets';
import {
  initAnalytics,
  addChatInteraction,
  trackSourceClick,
  trackLLMResponseInteraction,
} from '@/utils/analyticsUtil';
import { Context } from '@/context/Context';
import { getUserId } from '@/utils/authUtil';
import { debounce } from '@/utils/debounceUtil';
import { AnswerSectionProps, TopKItem } from '@/types';

// Component for displaying AI-generated answers and related sources
const AnswerSection: React.FC<AnswerSectionProps> = ({
  message,
  isLastMessage,
  generationComplete,
  recording_id,
}) => {
  const context = useContext(Context);
  const [selectedItem, setSelectedItem] = useState<TopKItem | null>(null);
  const [isAnswerComplete, setIsAnswerComplete] = useState(false);
  const [showSources, setShowSources] = useState(true);
  const [hoverStartTime, setHoverStartTime] = useState<number | null>(null);
  const [chatIndex, setChatIndex] = useState<number | null>(null);
  const analyticsInitialized = useRef(false);

  // Ensure the component is used within a ContextProvider
  if (!context) {
    throw new Error('AnswerSection must be used within a ContextProvider');
  }

  // Get user ID and messages from context
  const userId = getUserId();
  const { messages } = context;

  // Create a debounced version of the hover tracking function
  const debouncedTrackHover = useRef(
    debounce((chatIndex: number, duration: number) => {
      trackLLMResponseInteraction(chatIndex, 'hover', duration);
    }, 1000),
  ).current;

  // Initialize analytics on component mount
  useEffect(() => {
    if (!analyticsInitialized.current) {
      initAnalytics(userId);
      analyticsInitialized.current = true;
    }
  }, [userId]);

  // Record chat interaction when generation is complete
  useEffect(() => {
    if (generationComplete && isLastMessage) {
      const aiMessages = messages.filter((msg) => msg.type === 'ai');
      if (aiMessages.length > 0) {
        const lastAiMessage = aiMessages[aiMessages.length - 1];
        const newChatIndex = addChatInteraction(
          recording_id,
          lastAiMessage.topk,
          generationComplete
        );
        setChatIndex(newChatIndex);
      }
    }
  }, [generationComplete, isLastMessage, messages, recording_id]);

  // Show answer complete animation after a delay
  useEffect(() => {
    if (generationComplete) {
      const timer = setTimeout(() => setIsAnswerComplete(true), 500);
      return () => clearTimeout(timer);
    }
    return () => {};
  }, [generationComplete]);

  // Event handlers
  const handleCardClick = useCallback(
    (item: TopKItem, index: number) => {
      setSelectedItem(item);
      if (chatIndex !== null) {
        trackSourceClick(chatIndex, index);
      }
    },
    [chatIndex],
  );

  // Handles hover tracking for the LLM response
  const handleLLMResponseHover = useCallback(
    (isHovering: boolean) => {
      if (chatIndex === null) return;

      if (isHovering) {
        setHoverStartTime(Date.now());
      } else if (hoverStartTime !== null) {
        const hoverDuration = Date.now() - hoverStartTime;
        debouncedTrackHover(chatIndex, hoverDuration);
        setHoverStartTime(null);
      }
    },
    [chatIndex, hoverStartTime, debouncedTrackHover],
  );

  // Handles click tracking for the LLM response
  const handleLLMResponseClick = useCallback(() => {
    if (chatIndex !== null) {
      trackLLMResponseInteraction(chatIndex, 'click');
    }
  }, [chatIndex]);

  // Handles closing the modal
  const handleCloseModal = useCallback(() => {
    setSelectedItem(null);
  }, []);

  // Formats the description for the modal
  const formatDescription = useCallback(
    (item: TopKItem) => (
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
    ),
    [],
  );

  // Truncates text to a maximum length
  const truncateText = useCallback((text: string, maxLength: number) => {
    return text.length <= maxLength ? text : `${text.slice(0, maxLength)}...`;
  }, []);

  return (
    <div className="answer-section">
      {/* AI response */}
      <div
        className="message-title"
        onMouseEnter={() => handleLLMResponseHover(true)}
        onMouseLeave={() => handleLLMResponseHover(false)}
        onClick={handleLLMResponseClick}
      >
        <img src={assets.bc_icon} alt="BC AI" />
        <p dangerouslySetInnerHTML={{ __html: message.content }}></p>
      </div>

      {/* Sources section */}
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

      {/* Feedback bar */}
      {isLastMessage && generationComplete && <FeedbackBar />}

      {/* Modal for displaying source details */}
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
