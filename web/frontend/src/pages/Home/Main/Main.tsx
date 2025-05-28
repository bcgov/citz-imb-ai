import type React from "react";
import { useContext, useEffect, useRef, useState } from "react";

import { assets } from "@/assets/icons/assets";
import AnswerSection from "@/components/AnswerSection/AnswerSection";
import ModalDialog from "@/components/Modal/ModalDialog";
import ScrollButton from "@/components/ScrollButton/ScrollButton";
import { Context } from "@/context/Context";
import Sidebar from "@/pages/Home/Sidebar/Sidebar";
import { sendAnalyticsImmediatelyOnLeave } from "@/utils/analyticsUtil";
import { PaperPlaneRight, UserCircle } from "@phosphor-icons/react";

import "./Main.scss";
import { Link } from "react-router-dom";

// Main component for the chat interface
const Main = () => {
  // Use context for global state management
  const context = useContext(Context);

  // State variables for UI control
  const [isModalVisible, setIsModalVisible] = useState(true);
  const [userScrolled, setUserScrolled] = useState(false);
  const [isWaitingForResponse, setIsWaitingForResponse] = useState(false);

  // Error handling for context
  if (!context) {
    throw new Error("Main must be used within a ContextProvider");
  }

  // Destructure context values
  const {
    onSent,
    showResult,
    messages,
    setInput,
    input,
    resetContext,
    KeycloakLogout,
    generationComplete,
    errorState,
    resetError,
    recordingHash,
    isRegenerating,
    pendingMessage,
    setPendingMessage,
  } = context;

  // Refs for DOM elements
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const scrollableSectionRef = useRef<HTMLDivElement>(null);

  // Function to adjust textarea height based on content
  const adjustTextareaHeight = () => {
    const textarea = textareaRef.current;
    if (textarea) {
      textarea.style.height = "auto";
      textarea.style.height = `${textarea.scrollHeight}px`;
    }
  };

  // Effect to adjust textarea height when input changes
  useEffect(() => {
    adjustTextareaHeight();
  }, [input]);

  // Effect to send analytics data immediately when the user tries to leave the page
  useEffect(() => {
    const cleanup = sendAnalyticsImmediatelyOnLeave();

    return cleanup;
  }, []);

  // Effect to handle scrolling behavior
  useEffect(() => {
    const element = scrollableSectionRef.current;
    if (element && !userScrolled) {
      element.scrollTo({
        top: element.scrollHeight,
        behavior: "auto",
      });
    }
  }, [messages, userScrolled, pendingMessage, isWaitingForResponse]);

  // Function to handle scroll events
  const handleScroll = () => {
    const element = scrollableSectionRef.current;
    if (element) {
      const isNearBottom =
        element.scrollHeight - element.scrollTop - element.clientHeight < 50;
      setUserScrolled(!isNearBottom);
    }
  };

  // Function to handle key press events in the textarea
  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  // Function to handle sending a message
  const handleSend = async () => {
    if (input.trim() && !isWaitingForResponse) {
      setPendingMessage(input);
      setInput("");
      setIsWaitingForResponse(true);
      if (textareaRef.current) {
        textareaRef.current.style.height = "auto";
      }
      await onSent();
      setPendingMessage(null);
      setIsWaitingForResponse(false);
    }
  };

  // Function to handle clicking on a suggestion card
  const handleCardClick = async (text: string) => {
    setInput(text);
    if (textareaRef.current) {
      textareaRef.current.focus();
    }
  };

  // Sample card contents for suggestions
  const cardContents = [
    "How much notice do I need to give to end my rental lease in BC?",
    "Do I need to wear a seatbelt in BC?",
    "How many breaks do I get during a workday in BC?",
    "How do I dispute a traffic ticket in BC?",
  ];

  // Functions to handle modal actions
  const handleModalYes = () => {
    setIsModalVisible(false);
  };

  const handleModalNo = () => {
    resetContext();
    KeycloakLogout();
  };

  const handleErrorModalRefresh = () => {
    window.location.reload();
  };

  const handleErrorModalCancel = () => {
    resetError();
  };

  // Function to render chat messages
  const renderMessages = () => {
    const allMessages = [
      ...messages,
      ...(pendingMessage
        ? [{ type: "user" as const, content: pendingMessage }]
        : []),
    ];

    return allMessages.map((message, index) => (
      <div key={index} className={`message ${message.type}`}>
        {message.type === "user" ? (
          <div className="message-title">
            <UserCircle size={40} />
            <p>{message.content}</p>
          </div>
        ) : (
          <AnswerSection
            message={message}
            key={`ai-${index}`}
            isLastMessage={index === allMessages.length - 1}
            generationComplete={generationComplete}
            recording_id={recordingHash}
          />
        )}
      </div>
    ));
  };

  // Main component render
  return (
    <div className="main-page">
      <Sidebar />
      <div className="content">
        <div className="nav">
          <p>BC AI</p>
        </div>
        <div className="main-container">
          {showResult ? (
            // Render chat messages and input area
            <div>
              <div
                className="result"
                id="scrollable-section"
                ref={scrollableSectionRef}
                onScroll={handleScroll}
              >
                {renderMessages()}
                {(isWaitingForResponse || isRegenerating) && (
                  <div className="message ai">
                    <div className="message-title">
                      <img src={assets.bc_icon} alt="" />
                      <div className="loader">
                        <hr className="animated-bg" />
                        <hr className="animated-bg" />
                        <hr className="animated-bg" />
                      </div>
                    </div>
                  </div>
                )}
              </div>
              <ScrollButton
                scrollableElementId="scrollable-section"
                generationComplete={generationComplete}
              />
            </div>
          ) : (
            // Render welcome screen with suggestion cards
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
            {/* Input area for user messages */}
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
                disabled={isWaitingForResponse || isRegenerating}
              />
              <div>
                {input && !(isWaitingForResponse || isRegenerating) ? (
                  <div
                    className="send-button"
                    title="Send"
                    onClick={handleSend}
                  >
                    <PaperPlaneRight size={24} />
                  </div>
                ) : null}
              </div>
            </div>
            {/* Disclaimer and safety link */}
            <p className="bottom-info">
              BC AI may provide inaccurate info. Responses can take up to 2
              minutes. Please verify all outputs. Learn about our{" "}
              <Link to="/safety" className="safety-link">
                AI safety measures.
              </Link>
            </p>
          </div>
        </div>
      </div>
      {/* Modal for terms agreement */}
      {isModalVisible && (
        <ModalDialog
          title="Notice"
          description={
            <div className="modal-content">
              <p>Before proceeding, please note the following:</p>
              <ul>
                <li>
                  This application is in beta mode. Answers may be inaccurate or
                  incomplete. Always verify information independently.
                </li>
                <li>Response generation may take up to 2 minutes.</li>
                <li>By using BC Laws AI, you agree to our terms of service.</li>
                <li>
                  We are committed to AI safety. Learn more about our{" "}
                  <Link to="/safety" className="safety-link">
                    AI safety practices.
                  </Link>
                </li>
              </ul>
              <p className="agreement-text">
                Do you understand and agree to proceed?
              </p>
            </div>
          }
          option1={{
            text: "Yes, I Agree",
            onClick: handleModalYes,
          }}
          option2={{
            text: "No, Take Me Back",
            onClick: handleModalNo,
          }}
        />
      )}
      {/* Error modal */}
      {errorState.hasError && (
        <ModalDialog
          title="Error Occurred"
          description={
            <>
              <p>An error occurred while processing your request.</p>
              <p>Please refresh the page and try again.</p>
              <p>
                Status: <b>{errorState.errorMessage}</b>
              </p>
            </>
          }
          option1={{
            text: "Refresh Page",
            onClick: handleErrorModalRefresh,
          }}
          option2={{
            text: "Cancel",
            onClick: handleErrorModalCancel,
          }}
        />
      )}
    </div>
  );
};

export default Main;
