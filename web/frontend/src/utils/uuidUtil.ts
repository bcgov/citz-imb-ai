import { v7 as uuidv7 } from 'uuid';

// Generate a new session id using uuid v7
export const generateUUID = (): string => {
  return uuidv7();
};
