import './Safety.scss';
import { Link } from 'react-router-dom';

// Safety page component to display AI safety information
const SafetyPage = () => {
  return (
    <div className='safety-page'>
      <div className='safety-content'>
        {/* Back button to return to home page */}
        <Link to='/' className='safety-back-button'>
          Back to Home
        </Link>
        <div className='safety-main-container'>
          {/* Main heading */}
          <div className='safety-greet'>
            <p>
              <span>Our Commitment to Safe and Ethical AI</span>
            </p>
          </div>
          {/* Introduction to AI safety practices */}
          <div className='safety-intro-alert'>
            <h2>
              At BC Gov, we prioritize trust, safety, and effectiveness in our
              AI solutions.
            </h2>
            <p>
              Here&apos;s how we ensure our AI systems are designed and deployed
              responsibly:
            </p>
          </div>
          {/* Cards displaying various AI safety measures */}
          <div className='safety-cards'>
            {/* Human-in-the-Loop card */}
            <div className='safety-card'>
              <h3>Human-in-the-Loop (HITL)</h3>
              <p>
                We involve human reviewers in critical decision-making processes
                to ensure accuracy and accountability.
              </p>
            </div>
            {/* Ethical AI Practices card */}
            <div className='safety-card'>
              <h3>Ethical AI Practices</h3>
              <p>
                Transparency, fairness, and accountability are at the core of
                our AI practices.
              </p>
            </div>
            {/* Security and Privacy card */}
            <div className='safety-card'>
              <h3>Security and Privacy</h3>
              <p>
                Protecting sensitive data and ensuring user privacy is
                paramount.
              </p>
            </div>
            {/* Performance Monitoring card */}
            <div className='safety-card'>
              <h3>Performance Monitoring</h3>
              <p>
                Our AI infrastructure is continuously monitored using OpenShift
                to ensure high performance and reliability.
              </p>
            </div>
            {/* Continuous Improvement card */}
            <div className='safety-card'>
              <h3>Continuous Improvement</h3>
              <p>
                We use feedback loops and performance metrics to gather insights
                and continuously refine our AI models.
              </p>
            </div>
            {/* Bias Detection and Mitigation card */}
            <div className='safety-card'>
              <h3>Bias Detection and Mitigation</h3>
              <p>
                We are committed to ensuring our AI systems are fair and
                unbiased.
              </p>
            </div>
          </div>
          {/* Section for guardrails and safety measures */}
          <h2>Our Guardrails and Safety Measures</h2>
          <div className='safety-cards'>
            {/* Additional safety measure cards */}
            <div className='safety-card'>
              <h3>Transparency Reports</h3>
            </div>
            <div className='safety-card'>
              <h3>Ethical Audits</h3>
            </div>
            <div className='safety-card'>
              <h3>Security Measures</h3>
            </div>
            <div className='safety-card'>
              <h3>Human Oversight</h3>
            </div>
            <div className='safety-card'>
              <h3>User Feedback Integration</h3>
            </div>
            <div className='safety-card'>
              <h3>Regular Risk Assessments</h3>
            </div>
          </div>
          {/* Concluding section on ensuring safe AI */}
          <h2>Ensuring Safe AI</h2>
          <p>
            We are dedicated to deploying AI responsibly. Our comprehensive
            guardrails and ethical practices ensure our AI systems are safe,
            trustworthy, and effective. We are committed to continuous
            improvement and transparency, making sure our AI solutions benefit
            everyone.
          </p>
          <p>
            By demonstrating our commitment to safe AI practices, we aim to
            build trust and confidence in our AI solutions.
          </p>
        </div>
      </div>
    </div>
  );
};

export default SafetyPage;
