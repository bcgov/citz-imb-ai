import {
  BrowserRouter as Router,
  Route,
  Routes,
  Navigate,
} from 'react-router-dom';
import Welcome from '@/pages/Welcome/Welcome';
import Main from '@/pages/Home/Main/Main';
import Error from '@/pages/Error/Error';

const isAuthenticated = true;

const App = () => {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<Welcome />} />
        <Route
          path="/home"
          element={isAuthenticated ? <Main /> : <Navigate to="/error" />}
        />
        <Route path="/error" element={<Error />} />
      </Routes>
    </Router>
  );
};

export default App;
