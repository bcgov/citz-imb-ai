import {
  BrowserRouter as Router,
  Route,
  Routes,
  Navigate,
} from 'react-router-dom';
import Welcome from '@/pages/Welcome/Welcome';
import Main from '@/pages/Home/Main/Main';
import Error from '@/pages/Error/Error';
import Safety from '@/pages/Safety/Safety';
import { isAuthenticated } from '@/utils/auth';

const App = () => {
  const Authenticated = isAuthenticated();

  return (
    <Router>
      <Routes>
        <Route path="/" element={Authenticated ? <Main /> : <Welcome />} />
        <Route path="/error" element={<Error />} />
        <Route path="*" element={<Navigate to="/error" />} />
        <Route path="/safety" element={<Safety />} />
      </Routes>
    </Router>
  );
};

export default App;
