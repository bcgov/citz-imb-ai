const runChat = async (_prompt: string): Promise<string> => {
  // Mock delay of 2 seconds
  await new Promise((resolve) => setTimeout(resolve, 2000));

  // Return lorem ipsum text
  const response = `Lorem ipsum dolor sit amet, consectetur adipiscing elit. Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua.

    Lorem ipsum dolor sit amet, consectetur adipiscing elit. Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua.
    `;

  return response;
};

export default runChat;
