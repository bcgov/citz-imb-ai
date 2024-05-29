const runChat = async (_prompt: string): Promise<string> => {
  // Mock delay of 2 seconds
    const response = await fetch("http://localhost:10000/chat/", {
    method: "POST",
    headers: {
      "Content-Type": "application/x-www-form-urlencoded",
      "Authorization": `Bearer ${localStorage.getItem("token")}`,
    },
    body: `prompt=${encodeURIComponent(_prompt)}`,
  });

      const data = await response.json();
      //const responses = data.responses.map((res: any) => res.text);
      console.log(data);
      console.log(data.responses);
      const responses = JSON.parse(data.responses);
      let prettier = responses['llm'];
      /* format the top k */
      let topk = responses['topk'];
      let topk_str = '<br><br><p><u><small>Footnotes:</small></u></p>';
      for (let i = 0; i < topk.length; i++) {
        topk_str += '<p><small>' 
        Object.keys(topk[i]).forEach(function(key) {
          topk_str += key + ': ' + topk[i][key] + '<br>';
        });
        topk_str += '</small></p><br><hr><br>';
      }
      prettier += '\n\n' + topk_str;
      return prettier;
};

export default runChat;
