import React, { useEffect, useRef, useState, useContext } from 'react';
import './Main.scss';
import Sidebar from '@/pages/Home/Sidebar/Sidebar';
import ModalDialog from '@/components/Modal/ModalDialog';
import FeedbackBar from '@/components/FeedbackBar/FeedbackBar';
import ScrollButton from '@/components/ScrollButton/ScrollButton';
import { assets } from '@/assets/icons/assets';
import { Context } from '@/context/Context';

const Main = () => {
  const context = useContext(Context);
  const [isModalVisible, setIsModalVisible] = useState(true);
  const [userScrolled, setUserScrolled] = useState(false);

  if (!context) {
    throw new Error('Main must be used within a ContextProvider');
  }

  const {
    onSent,
    recentPrompt,
    showResult,
    loading,
    resultData,
    setInput,
    input,
    resetContext,
    KeycloakLogout,
    generationComplete,
  } = context;

  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const scrollableSectionRef = useRef<HTMLDivElement>(null);

  const adjustTextareaHeight = () => {
    const textarea = textareaRef.current;
    if (textarea) {
      textarea.style.height = 'auto';
      textarea.style.height = `${textarea.scrollHeight}px`;
    }
  };

  useEffect(() => {
    adjustTextareaHeight();
  }, [input]);

  useEffect(() => {
    const element = scrollableSectionRef.current;
    if (element && !userScrolled) {
      element.scrollTo({
        top: element.scrollHeight,
        behavior: 'auto',
      });
    }
  }, [resultData, userScrolled]);

  const handleScroll = () => {
    const element = scrollableSectionRef.current;
    if (element) {
      const isNearBottom =
        element.scrollHeight - element.scrollTop - element.clientHeight < 50;
      setUserScrolled(!isNearBottom);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleSend = async () => {
    await onSent();
    setInput('');
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
    }
  };

  const handleCardClick = async (text: string) => {
    setInput(text);
    if (textareaRef.current) {
      textareaRef.current.focus();
    }
  };

  const cardContents = [
    `How much notice do I need to give to end my rental lease in BC?`,
    `Do I need to wear a seatbelt in BC?`,
    `How many breaks do I get during a workday in BC?`,
    `How do I dispute a traffic ticket in BC?`,
  ];

  const handleModalYes = () => {
    setIsModalVisible(false);
  };

  const handleModalNo = () => {
    resetContext();
    KeycloakLogout();
  };

  return (
    <div className="main-page">
      <Sidebar />
      <div className="content">
        <div className="nav">
          <p>BC AI</p>
        </div>
        <div className="main-container">
          {showResult ? (
            <div>
              <div
                className="result"
                id="scrollable-section"
                ref={scrollableSectionRef}
                onScroll={handleScroll}
              >
                <div className="result-title">
                  <img src={assets.user_icon} alt="" />
                  <p>{recentPrompt}</p>
                </div>
                <div className="result-data">
                  <img src={assets.bc_icon} alt="" />
                  {loading ? (
                    <div className="loader">
                      <hr className="animated-bg" />
                      <hr className="animated-bg" />
                      <hr className="animated-bg" />
                    </div>
                  ) : (
                    <p
                      dangerouslySetInnerHTML={{
                        __html: resultData,
                      }}
                    ></p>
                  )}
                </div>
                <FeedbackBar />
              </div>
              <ScrollButton
                scrollableElementId="scrollable-section"
                generationComplete={generationComplete}
              />
            </div>
          ) : (
            <>
              <div className="greet">
                <p>
                  <span>Hello,</span>
                </p>
                <p>How can I help you today?</p>
              </div>
              <div className="cards">
                {cardContents.map((content, index) => (
                  <div
                    className="card"
                    key={index}
                    onClick={() => handleCardClick(content)}
                  >
                    <p>{content}</p>
                  </div>
                ))}
              </div>
            </>
          )}

          <div className="main-bottom">
            <div className="search-box">
              <textarea
                value={input}
                onChange={(e) => setInput(e.target.value)}
                className="textarea"
                autoComplete="on"
                spellCheck={true}
                autoFocus={true}
                placeholder="Enter a prompt here"
                onInput={adjustTextareaHeight}
                onKeyDown={handleKeyDown}
                ref={textareaRef}
                rows={1}
                id="prompt-input"
              />
              <div>
                {input ? (
                  <div className="send-button" title="Send">
                    <img
                      onClick={handleSend}
                      src={assets.send_icon}
                      alt="send icon"
                    />
                  </div>
                ) : null}
              </div>
            </div>
            <p className="bottom-info">
              BC AI may display inaccurate info and responses may take up to 2
              minutes. Please double-check its responses.
            </p>
          </div>
        </div>
      </div>
      {isModalVisible && (
        <ModalDialog
          title="Notice"
          description={
            <>
              <p>
                This application is in beta mode, and answers may be inaccurate.
                Please double-check the validity of the information.
              </p>
              <p>Answers may take up to 2 minutes to generate.</p>
              <p>By agreeing to use BC AI, you accept our terms of service.</p>
              <p>Do you agree to proceed?</p>
            </>
          }
          option1={{
            text: 'Yes, I Agree',
            onClick: handleModalYes,
          }}
          option2={{
            text: 'No, Take Me Back',
            onClick: handleModalNo,
          }}
        />
      )}
    </div>
  );
};

export default Main;
