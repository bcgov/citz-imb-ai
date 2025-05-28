import type { SourcesSectionProps } from '@/types/types/answerSection.types';

const SourcesSection = ({
  showSources,
  message,
  handleCardClick,
  truncateText,
}: SourcesSectionProps) => {
  return (
    <div className={`topk-container ${showSources ? 'show' : 'hide'}`}>
      <div className='topk-cards'>
        {message.topk?.map((item, index) => (
          <div
            key={index}
            className='topk-card'
            onClick={() => handleCardClick(item, index)}
          >
            <h3>{item.ActId}</h3>
            <p className='truncated-text'>{truncateText(item.text, 100)}</p>
            <span className='card-number'>{index + 1}</span>
          </div>
        ))}
      </div>
    </div>
  );
};

export default SourcesSection;
