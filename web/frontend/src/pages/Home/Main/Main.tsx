import './Main.scss';
import Sidebar from '@/pages/Home/Sidebar/Sidebar';

const Main = () => {
  return (
    <div className="main-page">
      <Sidebar />
      <div className="content">
        <h1>Welcome to the Main Page</h1>
        <p>This is the main content area.</p>
      </div>
    </div>
  );
};

export default Main;
