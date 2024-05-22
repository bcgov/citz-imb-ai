import { useState } from 'react';
import { assets } from '@/assets/icons/assets';

import './Sidebar.scss';

const Sidebar = () => {
  const [isCollapsed, setIsCollapsed] = useState(true);

  const toggleSidebar = () => {
    setIsCollapsed(!isCollapsed);
  };

  return (
    <div className={`sidebar ${isCollapsed ? 'collapsed' : 'expanded'}`}>
      <div className="sidebar-header" title="Menu" onClick={toggleSidebar}>
        <img src={assets.menu_icon} className="menu-icon" alt="menu icon" />
      </div>

      <div className="new-chat" title="New Chat">
        <img src={assets.plus_icon} alt="new chat" />
        {!isCollapsed ? <p>New Chat</p> : null}
      </div>

      {!isCollapsed ? (
        <div className="recent">
          <p className="recent-title">Recent</p>
          <div className="recent-entry">
            <img src={assets.message_icon} alt="" />
            <p>Chat 1</p>
          </div>
          <div className="recent-entry">
            <img src={assets.message_icon} alt="" />
            <p>Chat 2</p>
          </div>
          <div className="recent-entry">
            <img src={assets.message_icon} alt="" />
            <p>Chat 3</p>
          </div>
        </div>
      ) : null}

      <div className="bottom" title="Logout">
        <img src={assets.user_icon} alt="user" />
        {!isCollapsed ? <p>Logout</p> : null}
      </div>
    </div>
  );
};

export default Sidebar;
