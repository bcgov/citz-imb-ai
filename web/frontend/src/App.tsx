import { useContext } from 'react';
import {
  BrowserRouter as Router,
  Route,
  Routes,
  Navigate,
} from 'react-router-dom';
import Welcome from '@/pages/Welcome/Welcome';
import Main from '@/pages/Home/Main/Main';
import Error from '@/pages/Error/Error';
import { Context } from '@/context/Context';

const App = () => {
  const context = useContext(Context);
  const isAuthenticated = context ? context.isAuthenticated : false;

  return (
    <Router>
      <Routes>
        <Route path="/" element={isAuthenticated ? <Main /> : <Welcome />} />
        <Route path="/error" element={<Error />} />
        <Route path="*" element={<Navigate to="/error" />} />
      </Routes>
    </Router>
  );
};

export default App;
