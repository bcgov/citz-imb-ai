import { useState, useContext, Key } from 'react';
import { Context } from '@/context/Context';
import { Chat, Plus, UserCircle } from '@phosphor-icons/react';

import ModalDialog from '@/components/Modal/ModalDialog';
import './Sidebar.scss';

// Sidebar component
const Sidebar = () => {
  // State for sidebar collapse and modal visibility
  const [isCollapsed] = useState(true);
  const [isModalVisible, setIsModalVisible] = useState(false);

  // Use context for global state management
  const context = useContext(Context);

  // Ensure context is available
  if (!context) {
    throw new Error('Sidebar must be used within a ContextProvider');
  }

  // Destructure context values
  const {
    onSent,
    prevPrompts,
    setRecentPrompt,
    newChat,
    resetContext,
    KeycloakLogout,
  } = context;

  // Function to load a previous prompt
  const loadPrompt = async (prompt: string) => {
    await onSent(prompt);
    setRecentPrompt(prompt);
  };

  // Function to toggle sidebar
  // const toggleSidebar = () => {
  //   setIsCollapsed(!isCollapsed);
  // };

  // Function to handle user logout
  const handleLogout = () => {
    resetContext();
    KeycloakLogout();
  };

  // Functions to open and close the modal
  const openModal = () => {
    setIsModalVisible(true);
  };

  const closeModal = () => {
    setIsModalVisible(false);
  };

  // Render the sidebar component
  return (
    <div className={`sidebar ${isCollapsed ? 'collapsed' : 'expanded'}`}>
      {/* Sidebar header */}
      {/* <div className="sidebar-header" title="Menu" onClick={toggleSidebar}>
        <List size={24} />
      </div> */}

      {/* New chat button */}
      <div onClick={() => newChat()} className="new-chat" title="New Chat">
        <Plus size={24} />
        {!isCollapsed ? <p>New Chat</p> : null}
      </div>

      {/* Recent prompts section (visible when expanded) */}
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
                <Chat size={24} />
                <p>
                  {item.slice(0, 18)} {'...'}
                </p>
              </div>
            ))}
          </div>
        </div>
      ) : null}

      {/* Logout button */}
      <div onClick={openModal} className="bottom" title="Logout">
        <UserCircle size={26} />
        {!isCollapsed ? <p>Logout</p> : null}
      </div>

      {/* Logout confirmation modal */}
      {isModalVisible && (
        <ModalDialog
          title="Logout"
          description={
            <>
              <p>Do you really want to log out?</p>
              <br />
              <strong>This will clear your chat history.</strong>
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
