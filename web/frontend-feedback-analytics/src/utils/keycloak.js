import Keycloak from 'keycloak-js';

export function initializeKeycloak() {
  const keycloak = new Keycloak({
    realm: "standard",
    url: "https://dev.loginproxy.gov.bc.ca/auth",
    "ssl-required": "external",
    clientId: "a-i-pathfinding-project-5449",
    "enable-pkce": true,
  });

  const token = localStorage.getItem('keycloak-token');
  const refreshToken = localStorage.getItem('keycloak-refresh-token');

  if (token && refreshToken) {
    keycloak.token = token;
    keycloak.refreshToken = refreshToken;
    validateTokenWithBackend(token).then(isValid => {
      if (isValid) {
        console.log('Authenticated on dashboard');
        setInterval(refreshTokenfn, 240000);
      } else {
        redirectLogin();
      }
    }).catch(() => redirectLogin());
  } else {
    redirectLogin();
  }

  function redirectLogin() {
    console.log('Redirecting to login page');
    localStorage.removeItem('keycloak-token');
    localStorage.removeItem('keycloak-refresh-token');
    document.cookie.split("; ").forEach(cookie => {
      document.cookie = cookie.split("=")[0] + '=;expires=Thu, 01 Jan 1970 00:00:00 GMT';
    });
    window.location.href = 'login.html';
  }

  function validateTokenWithBackend(token) {
    return fetch('/api/login', {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': 'Bearer ' + token
      }
    })
    .then(response => response.ok ? response.json() : { valid: false })
    .then(data => data.valid)
    .catch(() => false);
  }

  function refreshTokenfn() {
    fetch('/api/refreshtoken', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
        'Authorization': 'Bearer ' + localStorage.getItem('keycloak-token')
      },
      body: new URLSearchParams({ refresh_token: localStorage.getItem('keycloak-refresh-token') })
    })
    .then(response => response.ok ? response.json() : null)
    .then(data => {
      if (data) {
        localStorage.setItem('keycloak-token', data.access_token);
        localStorage.setItem('keycloak-refresh-token', data.refresh_token);
      } else {
        redirectLogin();
      }
    })
    .catch(() => redirectLogin());
  }
}
