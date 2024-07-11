import './Welcome.scss';
import { useContext } from 'react';
import { Context } from '@/context/Context';
import { Link } from 'react-router-dom';

const Welcome = () => {
  const context = useContext(Context);
  const handleLogin = () => {
    context?.KeycloakLogin();
  };

  return (
    <div className="welcome-page">
      <div className="heading">
        <h1>
          Chat with <span>BC AI</span>
        </h1>
        <h3>Experience BC's AI model in your browser.</h3>
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
