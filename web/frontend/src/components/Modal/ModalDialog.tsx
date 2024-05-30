import React from 'react';
import './ModalDialog.scss';

interface ModalDialogProps {
  title: string;
  description: React.ReactNode;
  option1: {
    text: string;
    onClick: () => void;
  };
  option2: {
    text: string;
    onClick: () => void;
  };
}

const ModalDialog: React.FC<ModalDialogProps> = ({
  title,
  description,
  option1,
  option2,
}) => {
  return (
    <div className="modal-overlay">
      <div className="modal-dialog">
        <div className="modal-header">
          <span className="modal-title">{title}</span>
        </div>
        <div className="modal-body">
          <span className="modal-description">{description}</span>
        </div>
        <div className="modal-footer">
          <button
            className="modal-button blue-button"
            onClick={option1.onClick}
          >
            {option1.text}
          </button>
          <button className="modal-button red-button" onClick={option2.onClick}>
            {option2.text}
          </button>
        </div>
      </div>
    </div>
  );
};

export default ModalDialog;
