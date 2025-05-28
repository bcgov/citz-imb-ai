import ModalDialog from '@/components/Modal/ModalDialog';
import type {
  ImageItem,
  ImagesSectionProps,
} from '@/types/types/answerSection.types';
import { useState } from 'react';
import './ImageSection.scss';

const ImagesSection = ({
  showSources,
  images,
  onImageClick,
}: ImagesSectionProps) => {
  const [selectedImage, setSelectedImage] = useState<ImageItem | null>(null);

  const handleImageClick = (image: ImageItem, index: number) => {
    // Only track analytics, don't trigger parent modal
    if (onImageClick) {
      // Create a new image object without the topkItem property
      const { topkItem, ...analyticsImage } = image;
      onImageClick(analyticsImage as ImageItem, index);
    }

    // Set the selected image for our own modal
    setSelectedImage(image);
  };

  const handleCloseModal = () => {
    setSelectedImage(null);
  };

  const handleImagePreviewClick = () => {
    if (selectedImage) {
      window.open(selectedImage.url, '_blank', 'noopener,noreferrer');
    }
  };

  const handleImagePreviewKeyDown = (event: React.KeyboardEvent) => {
    if (event.key === 'Enter' || event.key === ' ') {
      event.preventDefault();
      handleImagePreviewClick();
    }
  };

  const imagePreview = selectedImage ? (
    <div className="image-preview-container">
      <button
        type="button"
        className="image-preview-button"
        onClick={handleImagePreviewClick}
        onKeyDown={handleImagePreviewKeyDown}
        title="Click to open image in new tab"
      >
        <img
          src={selectedImage.url}
          alt={selectedImage.alt}
          className="image-preview clickable-image"
        />
      </button>
    </div>
  ) : null;

  return (
    <>
      <div className={`topk-container ${showSources ? 'show' : 'hide'}`}>
        <div className="topk-cards">
          {images.map((image, index) => (
            <button
              type="button"
              key={`image-${image.url}-${image.alt}`}
              className="topk-card"
              onClick={() => handleImageClick(image, index)}
            >
              <img src={image.url} alt={image.alt} className="topk-card-img" />
              <span className="card-number">{index + 1}</span>
            </button>
          ))}
        </div>
      </div>

      {selectedImage && (
        <ModalDialog
          title={selectedImage.filename || selectedImage.alt}
          description={imagePreview}
          option1={{
            text: 'Close',
            onClick: handleCloseModal,
          }}
          closeOnOutsideClick={true}
        />
      )}
    </>
  );
};

export default ImagesSection;
