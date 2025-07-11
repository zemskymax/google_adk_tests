import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import './App.css';

function App() {
    const [messages, setMessages] = useState([]);
    const [input, setInput] = useState('');
    const [isTyping, setIsTyping] = useState(false);
    const [taskId, setTaskId] = useState(null);
    const [currentTaskId, setCurrentTaskId] = useState(null);
    const pollingInterval = useRef(null);
    const messagesEndRef = useRef(null);

    useEffect(() => {
        setTaskId(`task-${Date.now()}-${Math.random().toString(36).substring(2, 9)}`);
        setMessages([{ sender: 'bot', text: "Hi there! Welcome to Luigi's Pizza House. I’m Alex. How can I help you today?" }]);
    }, []);

    useEffect(() => {
        messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
    }, [messages]);

    const stopPolling = () => {
        if (pollingInterval.current) {
            clearInterval(pollingInterval.current);
            pollingInterval.current = null;
        }
    };

    const handleTaskResult = (result) => {
    if (result) {
      const { id, status, artifacts } = result;
      setCurrentTaskId(id);

      if (status.state === 'completed' || status.state === 'failed') {
        stopPolling();
        setIsTyping(false);
        setCurrentTaskId(null); // Reset task ID after completion/failure

        let botResponse = 'Sorry, something went wrong.';
        if (status.state === 'completed' && artifacts && artifacts.length > 0 && artifacts[0].parts && artifacts[0].parts.length > 0) {
          botResponse = artifacts[0].parts[0].text;
        }
        setMessages(prev => [...prev, { sender: 'bot', text: botResponse }]);
      } else if (status.state === 'working' && !pollingInterval.current) {
        // Start polling if not already
        pollingInterval.current = setInterval(pollTask, 2000);
      }
    } else {
      stopPolling();
      setIsTyping(false);
      setMessages(prev => [...prev, { sender: 'bot', text: 'Sorry, I received an unexpected response.' }]);
    }
  };

    const pollTask = async () => {
        if (!currentTaskId) {
            stopPolling();
            return;
        }

        const request = {
            jsonrpc: "2.0",
            method: "tasks/get",
            params: { id: currentTaskId },
            id: Date.now()
        };

        try {
            const response = await axios.post('/', request);
            if (response.data.error) {
                throw new Error(response.data.error.message);
            }
            handleTaskResult(response.data.result);
        } catch (error) {
            stopPolling();
            setIsTyping(false);
            console.error('Error polling task:', error);
            setMessages(prev => [...prev, { sender: 'bot', text: 'Sorry, I had trouble getting the response.' }]);
        }
    };

    const handleSend = async () => {
        if (input.trim() === '' || isTyping) return;

        const userMessage = { sender: 'user', text: input };
        setMessages(prev => [...prev, userMessage]);
        const messageToBeSent = input;
        setInput('');
        setIsTyping(true);

        // Stop any previous polling before starting a new task
        stopPolling();

        const request = {
            jsonrpc: "2.0",
            method: "message/send",
            params: {
                id: taskId,
                message: {
                    role: "user",
                    parts: [{ text: messageToBeSent }],
                    messageId: `msg-${Date.now()}`
                }
            },
            id: Date.now()
        };

        try {
            const response = await axios.post('/', request);
            if (response.data.error) {
                throw new Error(response.data.error.message);
            }
            handleTaskResult(response.data.result);
        } catch (error) {
            setIsTyping(false);
            console.error('Error sending message:', error);
            setMessages(prev => [...prev, { sender: 'bot', text: `Error: ${error.message}` }]);
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
