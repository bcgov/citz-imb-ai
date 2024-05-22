import './Error.scss';

const ErrorPage = () => {
  return (
    <div className="error-page">
      <div className="heading">
        <h1>
          <span>Error</span>
        </h1>
        <h3>You are not authorized to view this page.</h3>
        <button
          className="back-button"
          onClick={() => (window.location.href = '/')}
        >
          Go Back
        </button>
      </div>
    </div>
  );
};

export default ErrorPage;
