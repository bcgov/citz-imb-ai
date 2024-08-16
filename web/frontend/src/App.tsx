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
  // Check if the user is authenticated
  const Authenticated = isAuthenticated();

  return (
    <Router>
      <Routes>
        {/* Route for the home page, conditionally rendering Main or Welcome based on authentication */}
        <Route path="/" element={Authenticated ? <Main /> : <Welcome />} />
        {/* Route for the error page */}
        <Route path="/error" element={<Error />} />
        {/* Catch-all route that redirects to the error page */}
        <Route path="*" element={<Navigate to="/error" />} />
        {/* Route for the safety page */}
        <Route path="/safety" element={<Safety />} />
      </Routes>
    </Router>
  );
};

export default App;
