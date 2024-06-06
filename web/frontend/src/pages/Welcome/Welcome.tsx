import './Welcome.scss';
import { useContext } from 'react';
import { Context } from '@/context/Context';

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
    </div>
  );
};

export default Welcome;
