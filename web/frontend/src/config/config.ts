const runChat = async (_prompt: string): Promise<string> => {
  // Mock delay of 2 seconds
    const response = await fetch("http://localhost:10000/submit/", {
    method: "POST",
    headers: {
      "Content-Type": "application/x-www-form-urlencoded",
      "Authorization": `Bearer ${localStorage.getItem("token")}`,
    },
    body: `prompt=${encodeURIComponent(_prompt)}`,
  });

      const data = await response.json();
      const responses = data.responses.map((res: any) => res.text); 
      return responses.join("\n");
  //return response;
};
 
export default runChat;
