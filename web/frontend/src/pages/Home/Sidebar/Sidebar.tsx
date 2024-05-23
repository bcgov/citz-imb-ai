import { useState, useContext, Key } from 'react';
import { useNavigate } from 'react-router-dom';
import { assets } from '@/assets/icons/assets';
import { Context } from '@/context/Context';
import './Sidebar.scss';

const Sidebar = () => {
  const [isCollapsed, setIsCollapsed] = useState(true);
  const navigate = useNavigate();
  const context = useContext(Context);

  if (!context) {
    throw new Error('Sidebar must be used within a ContextProvider');
  }

  const { onSent, prevPrompts, setRecentPrompt, newChat, resetContext } =
    context;

  const loadPrompt = async (prompt: string) => {
    await onSent(prompt);
    setRecentPrompt(prompt);
  };

  const toggleSidebar = () => {
    setIsCollapsed(!isCollapsed);
  };

  const logout = () => {
    resetContext();
    navigate('/');
  };

  return (
    <div className={`sidebar ${isCollapsed ? 'collapsed' : 'expanded'}`}>
      <div className="sidebar-header" title="Menu" onClick={toggleSidebar}>
        <img src={assets.menu_icon} className="menu-icon" alt="menu icon" />
      </div>

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

      <div onClick={logout} className="bottom" title="Logout">
        <img src={assets.user_icon} alt="user" />
        {!isCollapsed ? <p>Logout</p> : null}
      </div>
    </div>
  );
};

export default Sidebar;
