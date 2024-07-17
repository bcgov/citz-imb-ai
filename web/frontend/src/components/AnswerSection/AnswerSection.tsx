import React, { useState, useEffect } from 'react';
import './AnswerSection.scss';
import ModalDialog from '@/components/Modal/ModalDialog';
import FeedbackBar from '@/components/FeedbackBar/FeedbackBar';
import { assets } from '@/assets/icons/assets';

interface TopKItem {
  ActId: string;
  Regulations: string | null;
  score: number;
  sectionId: string;
  sectionName: string;
  text: string;
  url: string | null;
}

interface Message {
  type: 'user' | 'ai';
  content: string;
  topk?: TopKItem[];
}

interface AnswerSectionProps {
  message: Message;
  isLastMessage: boolean;
  generationComplete: boolean;
}

const AnswerSection: React.FC<AnswerSectionProps> = ({
  message,
  isLastMessage,
  generationComplete,
}) => {
  const [selectedItem, setSelectedItem] = useState<TopKItem | null>(null);
  const [isAnswerComplete, setIsAnswerComplete] = useState(false);
  const [showSources, setShowSources] = useState(true);

  useEffect(() => {
    let timer: NodeJS.Timeout;
    if (generationComplete) {
      timer = setTimeout(() => {
        setIsAnswerComplete(true);
      }, 500);
    }
    return () => clearTimeout(timer);
  }, [generationComplete]);

  const handleCardClick = (item: TopKItem) => {
    setSelectedItem(item);
  };

  const handleCloseModal = () => {
    setSelectedItem(null);
  };

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

  const truncateText = (text: string, maxLength: number) => {
    if (text.length <= maxLength) return text;
    return text.slice(0, maxLength) + '...';
  };

  return (
    <div className="answer-section">
      <div className="message-title">
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
                  onClick={() => handleCardClick(item)}
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
