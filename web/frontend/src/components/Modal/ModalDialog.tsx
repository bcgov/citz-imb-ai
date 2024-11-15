import React from 'react';

import { ModalDialogProps } from '@/types';

import './ModalDialog.scss';

// ModalDialog component
const ModalDialog: React.FC<ModalDialogProps> = ({
  title,
  description,
  option1,
  option2,
  closeOnOutsideClick = false,
}) => {
  // Function to handle clicks on the overlay
  const handleOverlayClick = (e: React.MouseEvent<HTMLDivElement>) => {
    if (closeOnOutsideClick && e.target === e.currentTarget) {
      option1?.onClick();
    }
  };

  // Render the modal dialog
  return (
    <div className='modal-overlay' onClick={handleOverlayClick}>
      <div className='modal-dialog'>
        {/* Modal header */}
        <div className='modal-header'>
          <span className='modal-title'>{title}</span>
        </div>
        {/* Modal body */}
        <div className='modal-body'>
          <div className='modal-description'>{description}</div>
        </div>
        {/* Modal footer with action buttons */}
        <div className='modal-footer'>
          {option1 && (
            <button
              className='modal-button blue-button'
              onClick={option1.onClick}>
              {option1.text}
            </button>
          )}
          {option2 && (
            <button
              className='modal-button red-button'
              onClick={option2.onClick}>
              {option2.text}
            </button>
          )}
        </div>
      </div>
    </div>
  );
};

export default ModalDialog;
