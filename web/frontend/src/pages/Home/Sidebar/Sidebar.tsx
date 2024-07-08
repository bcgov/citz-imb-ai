import { useState, useContext, Key } from 'react';
import { assets } from '@/assets/icons/assets';
import { Context } from '@/context/Context';
import ModalDialog from '@/components/Modal/ModalDialog';
import './Sidebar.scss';

const Sidebar = () => {
  const [isCollapsed] = useState(true);
  const [isModalVisible, setIsModalVisible] = useState(false);
  const context = useContext(Context);

  if (!context) {
    throw new Error('Sidebar must be used within a ContextProvider');
  }

  const {
    onSent,
    prevPrompts,
    setRecentPrompt,
    newChat,
    resetContext,
    KeycloakLogout,
  } = context;

  const loadPrompt = async (prompt: string) => {
    await onSent(prompt);
    setRecentPrompt(prompt);
  };

  // const toggleSidebar = () => {
  //   setIsCollapsed(!isCollapsed);
  // };

  const handleLogout = () => {
    resetContext();
    KeycloakLogout();
  };

  const openModal = () => {
    setIsModalVisible(true);
  };

  const closeModal = () => {
    setIsModalVisible(false);
  };

  return (
    <div className={`sidebar ${isCollapsed ? 'collapsed' : 'expanded'}`}>
      {/* <div className="sidebar-header" title="Menu" onClick={toggleSidebar}>
        <img src={assets.menu_icon} className="menu-icon" alt="menu icon" />
      </div> */}

      <div onClick={() => newChat()} className="new-chat" title="New Chat">
        <img src={assets.plus_icon} alt="new chat" />
        {!isCollapsed ? <p>New Chat</p> : null}
      </div>

      {!isCollapsed ? (
        <div className="recent">
          <p className="recent-title">Recent</p>
          <div className="recent-entries">
            {prevPrompts.map((item: string, index: Key) => (
              <div
                key={index}
                onClick={() => loadPrompt(item)}
                className="recent-entry"
              >
                <img src={assets.message_icon} alt="" />
                <p>
                  {item.slice(0, 18)} {'...'}
                </p>
              </div>
            ))}
          </div>
        </div>
      ) : null}

      <div onClick={openModal} className="bottom" title="Logout">
        <img src={assets.user_icon} alt="user" />
        {!isCollapsed ? <p>Logout</p> : null}
      </div>

      {isModalVisible && (
        <ModalDialog
          title="Logout"
          description={
            <>
              <p>Do you really want to log out?</p>
              <br />
              <p>This will clear your chat history.</p>
            </>
          }
          option1={{
            text: 'Yes, Logout',
            onClick: handleLogout,
          }}
          option2={{
            text: 'No, Take Me Back',
            onClick: closeModal,
          }}
        />
      )}
    </div>
  );
};

export default Sidebar;
