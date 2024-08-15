import { Context } from '@/context/Context';
import { useContext } from 'react';

export const isAuthenticated = (): boolean => {
  const context = useContext(Context);
  const isAuthenticated = context ? context.isAuthenticated : false;
  return isAuthenticated;
};

export const getUserId = (): string => {
  const userInfo = localStorage.getItem('keycloak-user-id') || '';
  return userInfo;
};
