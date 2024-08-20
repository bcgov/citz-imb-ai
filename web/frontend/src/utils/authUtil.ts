import { Context } from '@/context/Context';
import { useContext } from 'react';

// Check if the user is authenticated
export const isAuthenticated = (): boolean => {
  const context = useContext(Context);
  const isAuthenticated = context ? context.isAuthenticated : false;
  return isAuthenticated;
};

// Get the user ID from local storage
export const getUserId = (): string => {
  const userInfo = localStorage.getItem('keycloak-user-id') || '';
  return userInfo;
};
