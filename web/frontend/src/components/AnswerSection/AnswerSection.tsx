import React, { useState, useEffect, useContext } from 'react';
import './AnswerSection.scss';
import ModalDialog from '@/components/Modal/ModalDialog';
import FeedbackBar from '@/components/FeedbackBar/FeedbackBar';
import { assets } from '@/assets/icons/assets';
import {
  initAnalytics,
  trackSourceClick,
  saveAnalytics,
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

const AnswerSection: React.FC = () => {
  const context = useContext(Context);
  const [selectedItem, setSelectedItem] = useState<TopKItem | null>(null);

  if (!context) {
    throw new Error('AnswerSection must be used within a ContextProvider');
  }

  const { messages, generationComplete } = context;
  const userId = getUserId();

  // Initialize analytics when the AI generation is complete
  const initializeAnalytics = () => {
    const aiMessages = messages.filter((msg) => msg.type === 'ai');
    const userMessages = messages.filter((msg) => msg.type === 'user');
    if (aiMessages.length > 0 && userMessages.length > 0) {
      const lastAiMessage = aiMessages[aiMessages.length - 1];
      const lastUserMessage = userMessages[userMessages.length - 1];
      if (lastAiMessage.topk) {
        initAnalytics(
          userId,
          lastAiMessage.topk,
          lastUserMessage.content,
          lastAiMessage.content,
        );
        saveAnalytics();
      }
    }
  };

  // Call initializeAnalytics when generation is complete
  useEffect(() => {
    if (generationComplete) {
      initializeAnalytics();
    }
  }, [generationComplete, messages, userId]);

  // Handle click on a source card
  const handleCardClick = (item: TopKItem, index: number) => {
    setSelectedItem(item);
    const promptIndex = messages.filter((msg) => msg.type === 'ai').length - 1;
    trackSourceClick(promptIndex, index);
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

  // Render the component
  return (
    <div className="answer-section">
      {/* Render AI messages and sources */}
      {messages.map(
        (message, index) =>
          message.type === 'ai' && (
            <div key={index}>
              <div className="message-title">
                <img src={assets.bc_icon} alt="BC AI" />
                <p dangerouslySetInnerHTML={{ __html: message.content }}></p>
              </div>
              {message.topk && message.topk.length > 0 && (
                <div
                  className={`sources-section ${generationComplete ? 'fade-in' : ''}`}
                >
                  <h3>Sources</h3>
                  <div className="topk-container">
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
              {index === messages.length - 1 && generationComplete && (
                <FeedbackBar />
              )}
            </div>
          ),
      )}
      {/* Render modal for selected item */}
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
