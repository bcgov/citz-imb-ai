import './style.scss';
import 'bootstrap/dist/css/bootstrap.min.css';
import { createBootstrapHeader } from './components/Header';
import { createFeedbackSystem } from './components/FeedbackSystem';
import { initializeKeycloak } from './utils/keycloak';

document.querySelector('#app').innerHTML = `
  <div>
    <div id="header"></div>
    <div id="feedback-system"></div>
  </div>
`;

document.getElementById('header').appendChild(createBootstrapHeader());
document.getElementById('feedback-system').appendChild(createFeedbackSystem());
initializeKeycloak();