import { useNavigate } from 'react-router-dom';
import './Welcome.scss';

const Welcome = () => {
  const navigate = useNavigate();

  const KeycloackLogin = () => {
    console.log('login');
    navigate('/home');
  };

  return (
    <div className="welcome-page">
      <div className="heading">
        <h1>
          Chat with <span>BC AI</span>
        </h1>
        <h3>Experience BC's AI model in your browser.</h3>
        <button className="start-button" onClick={KeycloackLogin}>
          Login
        </button>
      </div>
    </div>
  );
};

export default Welcome;
