import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import './App.css';

const API_URL = 'http://localhost:10003';

function App() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const [sessionId, setSessionId] = useState(null);
  const messagesEndRef = useRef(null);

  useEffect(() => {
    // Generate a unique session ID when the component mounts
    setSessionId(`session-${Date.now()}-${Math.random().toString(36).substring(2, 9)}`);
    setMessages([]);
  }, []);

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  const pollTask = async (taskUrl) => {
    setIsTyping(true);
    try {
      const response = await axios.get(taskUrl);
      const { status, artifacts } = response.data;

      if (status === 'completed') {
        setIsTyping(false);
        const botResponse = artifacts[0].parts[0].text;
        setMessages(prev => [...prev, { sender: 'bot', text: botResponse }]);
      } else if (status === 'failed') {
        setIsTyping(false);
        setMessages(prev => [...prev, { sender: 'bot', text: 'Sorry, something went wrong.' }]);
      } else {
        // If still working, poll again after a short delay
        setTimeout(() => pollTask(taskUrl), 1000);
      }
    } catch (error) {
      setIsTyping(false);
      console.error('Error polling task:', error);
      setMessages(prev => [...prev, { sender: 'bot', text: 'Sorry, I had trouble getting the response.' }]);
    }
  };

  const handleSend = async () => {
    if (input.trim() === '') return;

    const userMessage = { sender: 'user', text: input };
    setMessages(prev => [...prev, userMessage]);
    setInput('');

    try {
      const requestBody = {
        context_id: sessionId,
        message: {
          parts: [{ text: input }],
        },
      };
      
      // The proxy in package.json will forward this to http://localhost:10003
      const response = await axios.post('/apps/pizza_house_worker/tasks', requestBody);
      
      if (response.status === 202 && response.headers.location) {
        const location = response.headers.location;
        // The location header can be relative or absolute.
        // The proxy is only for the initial request, polling is done directly.
        const taskUrl = location.startsWith('http') ? location : API_URL + location;
        pollTask(taskUrl);
      } else {
         setMessages(prev => [...prev, { sender: 'bot', text: "Sorry, I couldn't start the request." }]);
      }
    } catch (error) {
      console.error('Error sending message:', error);
      let errorMessage = 'Sorry, something went wrong on my end.';
      if (error.response) {
        errorMessage = `Error: ${error.response.status} - ${error.response.data.error?.message || 'Could not connect to the agent.'}`;
      } else if (error.request) {
        errorMessage = 'I could not reach my server. Is it running?';
      }
      setMessages(prev => [...prev, { sender: 'bot', text: errorMessage }]);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter') {
      handleSend();
    }
  };

  return (
    <div className="App">
      <header className="App-header">
        <h1>Luigi's PizzaBot</h1>
      </header>
      <div className="chat-window">
        {messages.map((msg, index) => (
          <div key={index} className={`message ${msg.sender}`}>
            <div className="bubble">{msg.text}</div>
          </div>
        ))}
        {isTyping && (
          <div className="message bot">
            <div className="bubble typing-indicator">
              <span></span><span></span><span></span>
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>
      <div className="input-area">
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyPress={handleKeyPress}
          placeholder="Type your message..."
          disabled={isTyping}
        />
        <button onClick={handleSend} disabled={isTyping}>Send</button>
      </div>
    </div>
  );
}

export default App;