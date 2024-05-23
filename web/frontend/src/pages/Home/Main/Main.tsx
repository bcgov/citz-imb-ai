import { useEffect, useRef } from 'react';
import './Main.scss';
import Sidebar from '@/pages/Home/Sidebar/Sidebar';
import { assets } from '@/assets/icons/assets';

const Main = () => {
  const showResult = true;
  const loading = !true;
  const resultData = `Contrary`;
  const recentPrompt = 'hello';
  const input = true;
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const onSent = () => {
    console.log('sent');
  };

  const adjustTextareaHeight = () => {
    const textarea = textareaRef.current as HTMLTextAreaElement | null;
    if (textarea) {
      textarea.style.height = 'auto';
      textarea.style.height = `${textarea.scrollHeight}px`;
    }
  };

  useEffect(() => {
    adjustTextareaHeight();
  }, []);

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      onSent();
    }
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
            <div className="result">
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
                <div className="card">
                  <p>Suggestion 1</p>
                </div>
                <div className="card">
                  <p>Suggestion 2</p>
                </div>
                <div className="card">
                  <p>Suggestion 3</p>
                </div>
                <div className="card">
                  <p>Suggestion 4</p>
                </div>
              </div>
            </>
          )}

          <div className="main-bottom">
            <div className="search-box">
              <textarea
                className="textarea"
                autoComplete="on"
                spellCheck={true}
                autoFocus={true}
                placeholder="Enter a prompt here"
                onInput={adjustTextareaHeight}
                onKeyDown={handleKeyDown}
                ref={textareaRef}
                rows={1}
              />
              <div>
                {input ? (
                  <img
                    onClick={() => onSent()}
                    src={assets.send_icon}
                    width={30}
                    alt=""
                  />
                ) : null}
              </div>
            </div>
            <p className="bottom-info">
              BC AI may display inaccurate info, please double-check its
              responses.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Main;
