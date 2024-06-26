import "./style.scss";
import bclogo from "../assets/BC_logo.jpg";
import { setupCounter } from "../counter.js";

document.querySelector("#app").innerHTML = `
  <div>
    <a href="" target="_blank">
      <img src="${bclogo}" class="logo vanilla" alt="B.C logo" />
    </a>
    <h1>A.I Dashboard</h1>
    <div style="display:flex; justify-content:space-evenly; align-items:center;">
    <button class="button" onclick="window.location.href = '/login.html'">Login</button>
    <button class="button small" onclick="window.location.href = 'https://citz-imb-ai-frontend-route-b875cc-dev.apps.silver.devops.gov.bc.ca/'">B.C Gov A.I</button>
    </div>
  </div>
`;

setupCounter(document.querySelector("#counter"));
