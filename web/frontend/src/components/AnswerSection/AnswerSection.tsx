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
} from '@/utils/analytics';
import { Context } from '@/context/Context';
import { getUserId } from '@/utils/auth';

export interface TopKItem {
  ActId: string;
  Regulations: string | null;
  score: number;
  sectionId: string;
  sectionName: string;
  text: string;
  url: string | null;
}

interface AnswerSectionProps {
  message: {
    content: string;
    topk?: TopKItem[];
  };
  isLastMessage: boolean;
  generationComplete: boolean;
}

const AnswerSection: React.FC<AnswerSectionProps> = ({
  message,
  isLastMessage,
  generationComplete,
}) => {
  const context = useContext(Context);
  const [selectedItem, setSelectedItem] = useState<TopKItem | null>(null);
  const [isAnswerComplete, setIsAnswerComplete] = useState(false);
  const [showSources, setShowSources] = useState(true);
  const [hoverStartTime, setHoverStartTime] = useState<number | null>(null);
  const [chatIndex, setChatIndex] = useState<number | null>(null);
  const analyticsInitialized = useRef(false);

  if (!context) {
    throw new Error('AnswerSection must be used within a ContextProvider');
  }

  const { messages } = context;
  const userId = getUserId();

  useEffect(() => {
    if (!analyticsInitialized.current) {
      initAnalytics(userId);
      analyticsInitialized.current = true;
    }
  }, [userId]);

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

  const handleCardClick = useCallback(
    (item: TopKItem, index: number) => {
      setSelectedItem(item);
      if (chatIndex !== null) {
        trackSourceClick(chatIndex, index);
      }
    },
    [chatIndex],
  );

  const handleLLMResponseHover = useCallback(
    (isHovering: boolean) => {
      if (chatIndex === null) return;

      if (isHovering) {
        setHoverStartTime(Date.now());
      } else if (hoverStartTime !== null) {
        const hoverDuration = Date.now() - hoverStartTime;
        trackLLMResponseInteraction(chatIndex, 'hover', hoverDuration);
        setHoverStartTime(null);
      }
    },
    [chatIndex, hoverStartTime],
  );

  const handleLLMResponseClick = useCallback(() => {
    if (chatIndex !== null) {
      trackLLMResponseInteraction(chatIndex, 'click');
    }
  }, [chatIndex]);

  const handleCloseModal = useCallback(() => {
    setSelectedItem(null);
  }, []);

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

  const truncateText = useCallback((text: string, maxLength: number) => {
    return text.length <= maxLength ? text : `${text.slice(0, maxLength)}...`;
  }, []);

  useEffect(() => {
    let timer: NodeJS.Timeout;
    if (generationComplete) {
      timer = setTimeout(() => {
        setIsAnswerComplete(true);
      }, 500);
    }
    return () => clearTimeout(timer);
  }, [generationComplete]);

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
      {isLastMessage && generationComplete && <FeedbackBar />}
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
