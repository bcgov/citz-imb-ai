interface ChatHistory {
  prompt: string;
  response: string;
}

const runChat = async (
  _prompt: string,
  chatHistory: ChatHistory[]
): Promise<{ response: string; recordingHash: string }> => {
  try {
    const response = await fetch('/api/chat/', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${localStorage.getItem('keycloak-token')}`,
      },
      body: JSON.stringify({
        prompt: _prompt,
        chatHistory: chatHistory
      }),
    });

    if (!response.ok) {
      throw new Error(`${response.status}`);
    }

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
    return {
      response: prettier,
      recordingHash: data.recording,
    };
  } catch (error) {
    throw error;
  }
};

export default runChat;