import { type Key, useContext, useEffect, useState } from 'react';

import { getChatStates } from '@/api/chat';
import ModalDialog from '@/components/Modal/ModalDialog';
import { Context } from '@/context/Context';
import type { ChatState } from '@/types';
import { Chat, Gear, Plus, UserCircle } from '@phosphor-icons/react';

import './Sidebar.scss';

// Sidebar component
const Sidebar = () => {
  // Use context for global state management
  const context = useContext(Context);

  // Ensure context is available
  if (!context) {
    throw new Error('Sidebar must be used within a ContextProvider');
  }

  // State for sidebar collapse and modal visibility
  const [isCollapsed] = useState(true);
  const [isModalVisible, setIsModalVisible] = useState(false);
  const [isOptionsOpen, setIsOptionsOpen] = useState(false);

  // State control for RAG state options
  const [activeStates, setActiveStates] = useState<ChatState[]>([]);
  const defaultState =
    sessionStorage.getItem('ragStateKey') || activeStates[0]?.key;
  const [selectedState, setSelectedState] = useState<string | null>(
    defaultState,
  );

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

  // Load the RAG states from the API
  useEffect(() => {
    getChatStates()
      .then((data) => {
        setActiveStates(data);
        if (data.length) {
          const setDefaultState = () => {
            context.setChatState(data.at(0)!);
            setSelectedState(data.at(0)!.key);
            sessionStorage.setItem('ragStateKey', data.at(0)!.key);
          };
          if (!defaultState) {
            setDefaultState();
          } else {
            const foundState = data.find((state) => state.key === defaultState);
            if (foundState) {
              context.setChatState(foundState);
              setSelectedState(foundState.key);
            } else {
              setDefaultState();
            }
          }
        }

        return data;
      })
      .catch((e) => console.warn(`Active RAG states not found: ${e}`));
  }, []);

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
      <div onClick={() => newChat()} className='new-chat' title='New Chat'>
        <Plus size={24} />
        {!isCollapsed ? <p>New Chat</p> : null}
      </div>

      {/* Recent prompts section (visible when expanded) */}
      {!isCollapsed ? (
        <div className='recent'>
          <p className='recent-title'>Recent</p>
          <div className='recent-entries'>
            {prevPrompts.map((item: string, index: Key) => (
              <div
                key={index}
                onClick={() => loadPrompt(item)}
                className='recent-entry'
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

      <div className='lower-button-container'>
        {/* Options Menu */}
        <div
          className='options'
          title='Options'
          onClick={() => setIsOptionsOpen(true)}
        >
          <Gear size={26} />
          {!isCollapsed ? <p>Options</p> : null}
        </div>

        {/* Logout button */}
        <div onClick={openModal} className='bottom' title='Logout'>
          <UserCircle size={26} />
          {!isCollapsed ? <p>Logout</p> : null}
        </div>
      </div>

      {/* Options confirmation modal */}
      {isOptionsOpen && (
        <ModalDialog
          title='Options'
          description={
            <>
              <h2>Search & Query Version</h2>
              {activeStates.length ? (
                activeStates.map((state) => (
                  <div className='rag-state-option' key={state.key}>
                    <input
                      type='radio'
                      id={state.key}
                      name='index_method'
                      value={state.key}
                      checked={state.key === selectedState}
                      onChange={() => {
                        setSelectedState(state.key);
                      }}
                    />
                    <div className='rag-state-option-text'>
                      <label htmlFor={state.key}>
                        <h3>{state.key}</h3>
                        <p>{state.description}</p>
                      </label>
                    </div>
                  </div>
                ))
              ) : (
                <p>No RAG options found.</p>
              )}
            </>
          }
          option1={{
            text: 'Save',
            onClick: () => {
              // Save selected option to app context and session storage
              const selectedOption = document.querySelector(
                'input[name="index_method"]:checked',
              ) as HTMLInputElement;
              if (selectedOption) {
                sessionStorage.setItem('ragStateKey', selectedOption.value);
                context.setChatState(
                  activeStates.find(
                    (state) => state.key === selectedOption.value,
                  )!,
                );
              }
              setIsOptionsOpen(false);
            },
          }}
          option2={{
            text: 'Cancel',
            onClick: () => {
              setIsOptionsOpen(false);
            },
          }}
        />
      )}

      {/* Logout confirmation modal */}
      {isModalVisible && (
        <ModalDialog
          title='Logout'
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
