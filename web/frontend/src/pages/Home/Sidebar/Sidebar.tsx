import { useState } from 'react';
import { assets } from '@/assets/icons/assets';

import './Sidebar.scss';

const Sidebar = () => {
  const [isCollapsed, setIsCollapsed] = useState(false);

  const toggleSidebar = () => {
    setIsCollapsed(!isCollapsed);
  };

  return (
    <div className={`sidebar ${isCollapsed ? 'collapsed' : ''}`}>
      <div className="sidebar-header">
        <img
          src={assets.menu_icon}
          className="menu-icon"
          alt="menu icon"
          onClick={toggleSidebar}
        />
      </div>
      <ul>
        <li>
          <p>Section 1</p>
        </li>
        <li>
          <p>Section 2</p>
        </li>
        <li>
          <p>Section 3</p>
        </li>
      </ul>
    </div>
  );
};

export default Sidebar;
