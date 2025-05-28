import { useContext } from 'react';

import { Context } from '@/context/Context';

import './Welcome.scss';
import { Link } from 'react-router-dom';

// Welcome component for the landing page
const Welcome = () => {
  // Use context for global state management
  const context = useContext(Context);

  // Function to handle login button click
  const handleLogin = () => {
    context?.KeycloakLogin();
  };

  // Render the welcome page
  return (
    <div className="welcome-page">
      <div className="heading">
        <h1>
          Chat with <span>BC Laws</span>
        </h1>
        <h3>Experience BC Laws AI chat model in your browser.</h3>
        <button className="start-button" onClick={handleLogin}>
          Login
        </button>
      </div>
      <div className="bottom">
        <p>
          Learn more about our{' '}
          <Link to="/safety" className="safety-link">
            commitment to AI safety.
          </Link>
        </p>
      </div>
    </div>
  );
};

export default Welcome;
