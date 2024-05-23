import { createContext, useState } from 'react';
import runChat from '@/config/config';

export const Context = createContext();

const ContextProvider = (props) => {
  const [prevPrompts, setPrevPrompts] = useState([]);
  const [input, setInput] = useState('');
  const [recentPrompt, setRecentPrompt] = useState('');
  const [showResult, setShowResult] = useState(false);
  const [loading, setLoading] = useState(false);
  const [resultData, setResultData] = useState('');

  function delayPara(index, nextWord) {
    setTimeout(function () {
      setResultData((prev) => prev + nextWord);
    }, 75 * index);
  }

  const onSent = async (prompt) => {
    setResultData('');
    setLoading(true);
    setShowResult(true);
    let response;
    if (prompt !== undefined) {
      response = await runChat(prompt);
      setRecentPrompt(prompt);
    } else {
      setPrevPrompts((prev) => [...prev, input]);
      setRecentPrompt(input);
      response = await runChat(input);
    }
    let responseArray = response.split('**');
    let newArray = '';
    for (let i = 0; i < responseArray.length; i++) {
      if (i === 0 || i % 2 !== 1) {
        newArray += responseArray[i];
      } else {
        newArray += '<b>' + responseArray[i] + '</b>';
      }
    }
    console.log(newArray);
    responseArray = newArray.split('*').join('</br>').split(' ');
    for (let i = 0; i < responseArray.length; i++) {
      const nextWord = responseArray[i];
      delayPara(i, nextWord + ' ');
    }
    setLoading(false);
    setInput('');
  };

  const newChat = async () => {
    setLoading(false);
    setShowResult(false);
  };

  const contextValue = {
    prevPrompts,
    setPrevPrompts,
    onSent,
    setRecentPrompt,
    recentPrompt,
    showResult,
    loading,
    resultData,
    input,
    setInput,
    newChat,
  };

  return (
    <Context.Provider value={contextValue}>{props.children}</Context.Provider>
  );
};

export default ContextProvider;
