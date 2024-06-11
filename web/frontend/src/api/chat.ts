const runChat = async (_prompt: string): Promise<string> => {
  const response = await fetch('/api/chat/', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/x-www-form-urlencoded',
      Authorization: `Bearer ${localStorage.getItem('keycloak-token')}`,
    },
    body: `prompt=${encodeURIComponent(_prompt)}`,
  });

  const data = await response.json();
  const responses = JSON.parse(data.responses);
  let prettier = responses['llm'];
  /* format the top k */
  let topk = responses['topk'];
  let topk_str = '<br><br><p><u><small>Footnotes:</small></u></p>';
  for (let i = 0; i < topk.length; i++) {
    topk_str += '<p><small>';
    Object.keys(topk[i]).forEach(function (key) {
      if (key === 'url' && topk[i][key] !== '' && topk[i][key] !== null) {
        topk_str +=
          key +
          ': ' +
          '<a target="_blank" href="' +
          topk[i][key] +
          '"><img src="' +
          topk[i][key] +
          '" width="100" height="100"></a><br>';
      } else {
        topk_str += key + ': ' + topk[i][key] + '<br>';
      }
    });
    topk_str += '</small></p><br><hr><br>';
  }
  prettier += '\n\n' + topk_str;
  return prettier;
};

export default runChat;
