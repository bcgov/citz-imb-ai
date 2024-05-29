import Keycloak from 'keycloak-js';

// Keycloak configuration
const keycloakConfig = {
  realm: 'standard',
  url: 'https://dev.loginproxy.gov.bc.ca/auth',
  'ssl-required': 'external',
  clientId: 'a-i-pathfinding-project-5449',
  'enable-pkce': true,
};

const keycloak = new Keycloak(keycloakConfig);

// Initialize Keycloak
const initKeycloak = () => {
  return keycloak.init({
    pkceMethod: 'S256',
  });
};

// Check if the user is authenticated
const isAuthenticated = () => {
  return !!keycloak.authenticated;
};

// Get the Keycloak token
const getToken = () => {
  if (keycloak.token) {
    localStorage.setItem('token', keycloak.token);
  }
  return keycloak.token;
};

// Update the token
const updateToken = (minValidity: number) => {
  return keycloak.updateToken(minValidity);
};

// Login function
const KeycloakLogin = () => {
  keycloak.login();
};

// Logout function
const KeycloakLogout = () => {
  keycloak.logout();
};

// Get the user's roles
const getUserRoles = () => {
  return keycloak.realmAccess?.roles;
};

export {
  keycloak,
  initKeycloak,
  isAuthenticated,
  getToken,
  updateToken,
  KeycloakLogout,
  KeycloakLogin,
  getUserRoles,
};
