import Error from '@/pages/Error/Error';
import Main from '@/pages/Home/Main/Main';
import Safety from '@/pages/Safety/Safety';
import Welcome from '@/pages/Welcome/Welcome';
import { isAuthenticated } from '@/utils/authUtil';

import {
  Navigate,
  Route,
  BrowserRouter as Router,
  Routes,
} from 'react-router-dom';

const App = () => {
  // Check if the user is authenticated
  const Authenticated = isAuthenticated();

  return (
    <Router>
      <Routes>
        {/* Route for the home page, conditionally rendering Main or Welcome based on authentication */}
        <Route path='/' element={Authenticated ? <Main /> : <Welcome />} />
        {/* Route for the error page */}
        <Route path='/error' element={<Error />} />
        {/* Catch-all route that redirects to the error page */}
        <Route path='*' element={<Navigate to='/error' />} />
        {/* Route for the safety page */}
        <Route path='/safety' element={<Safety />} />
      </Routes>
    </Router>
  );
};

export default App;
