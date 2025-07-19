import React, { useState, useEffect, useRef, useCallback } from 'react';
import axios from 'axios';
import ReactMarkdown from 'react-markdown';
import RemarkGfm from 'remark-gfm';
import './App.css';

function App() {
    const [conversations, setConversations] = useState({});
    const [activeConversationId, setActiveConversationId] = useState(null);
    const [input, setInput] = useState('');
    const [isLoaded, setIsLoaded] = useState(false);
    const [isSidebarCollapsed, setIsSidebarCollapsed] = useState(false);
    const pollingTasksRef = useRef({});
    const messagesEndRef = useRef(null);
    const inputRef = useRef(null);
    const sidebarRef = useRef(null);
    const mainContentRef = useRef(null);
    const [agentColors, setAgentColors] = useState({});
    const colorPalette = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#FED766', '#247BA0', '#F25F5C', '#70C1B3', '#FFE066', '#F45B69'];

    useEffect(() => {
        setAgentColors({
            'user': colorPalette[0],
            'bot': colorPalette[1]
        });
    // eslint-disable-next-line react-hooks/exhaustive-deps
    }, []);

    // Load conversations from localStorage on initial render
    useEffect(() => {
        try {
            const savedConversations = localStorage.getItem('personal-helper-conversations');
            if (savedConversations) {
                const parsedConvos = JSON.parse(savedConversations);
                // Ensure all conversations have a contextId for backward compatibility
                Object.values(parsedConvos).forEach(convo => {
                    if (!convo.contextId) {
                        convo.contextId = `context-${Date.now()}-${Math.random().toString(36).substring(2, 9)}`;
                    }
                });

                if (Object.keys(parsedConvos).length > 0) {
                    setConversations(parsedConvos);
                    const lastActive = localStorage.getItem('personal-helper-last-active-convo');
                    if (lastActive && parsedConvos[lastActive]) {
                        setActiveConversationId(lastActive);
                    } else {
                        setActiveConversationId(Object.keys(parsedConvos)[0]);
                    }
                } else {
                    handleNewConversation();
                }
            } else {
                handleNewConversation();
            }
        } catch (error) {
            console.error("Failed to load conversations from localStorage", error);
            handleNewConversation();
        } finally {
            setIsLoaded(true);
        }
    // eslint-disable-next-line react-hooks/exhaustive-deps
    }, []);

    // Save conversations to localStorage when they change
    useEffect(() => {
        if (!isLoaded) {
            return;
        }
        if (Object.keys(conversations).length > 0) {
            localStorage.setItem('personal-helper-conversations', JSON.stringify(conversations));
        } else {
            // If all conversations are deleted, clear from storage
            localStorage.removeItem('personal-helper-conversations');
            localStorage.removeItem('personal-helper-last-active-convo');
        }

        if (activeConversationId) {
            localStorage.setItem('personal-helper-last-active-convo', activeConversationId);
        }
    }, [conversations, activeConversationId, isLoaded]);

    useEffect(() => {
        messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
    }, [conversations, activeConversationId]);

    useEffect(() => {
        if (isLoaded && activeConversationId) {
            inputRef.current?.focus();
        }
    }, [activeConversationId, isLoaded]);

    const activeConversation = conversations[activeConversationId];

    useEffect(() => {
        // When the active conversation is done typing, re-focus the input field.
        if (activeConversation && !activeConversation.isTyping) {
            inputRef.current?.focus();
        }
    }, [activeConversation]);


    const handleNewConversation = () => {
        const newId = `convo-${Date.now()}`;
        setConversations(prev => {
            const existingNumbers = Object.values(prev)
                .map(c => c.name)
                .filter(name => name.startsWith('Order #'))
                .map(name => parseInt(name.replace('Order #', ''), 10))
                .filter(num => !isNaN(num));
            
            const newNumber = existingNumbers.length > 0 ? Math.max(...existingNumbers) + 1 : 1;

            const newConversation = {
                id: newId,
                name: `Order #${newNumber}`,
                messages: [],
                taskId: `task-${Date.now()}-${Math.random().toString(36).substring(2, 9)}`,
                contextId: `context-${Date.now()}-${Math.random().toString(36).substring(2, 9)}`,
                isTyping: false,
            };
            return { ...prev, [newId]: newConversation };
        });
        setActiveConversationId(newId);
    };

    const handleDeleteConversation = (convoIdToDelete) => {
        const newConversations = { ...conversations };
        delete newConversations[convoIdToDelete];
        setConversations(newConversations);

        if (activeConversationId === convoIdToDelete) {
            const remainingIds = Object.keys(newConversations);
            if (remainingIds.length > 0) {
                setActiveConversationId(remainingIds[0]);
            } else {
                handleNewConversation();
            }
        }
    };

    const updateConversation = useCallback((convoId, updates) => {
        setConversations(prev => {
            if (!prev[convoId]) return prev;
            return {
                ...prev,
                [convoId]: { ...prev[convoId], ...updates },
            };
        });
    }, []);

    const stopPolling = useCallback((processingTaskId) => {
        if (pollingTasksRef.current[processingTaskId]) {
            clearInterval(pollingTasksRef.current[processingTaskId].intervalId);
            delete pollingTasksRef.current[processingTaskId];
        }
    }, []);

    const handleTaskResult = useCallback((result, convoId) => {
        if (!result) {
            updateConversation(convoId, { isTyping: false });
            setConversations(prev => {
                if (!prev[convoId]) return prev;
                const newMessages = [...prev[convoId].messages, { sender: 'bot', text: 'Sorry, I received an unexpected response.' }];
                return { ...prev, [convoId]: { ...prev[convoId], messages: newMessages } };
            });
            return;
        }

        const { id: processingTaskId, status, artifacts } = result;

        if (status.state === 'completed' || status.state === 'failed') {
            stopPolling(processingTaskId);
            updateConversation(convoId, { isTyping: false });

            let botResponse = null;
            if (status.state === 'completed' && artifacts && artifacts.length > 0 && artifacts[0].parts && artifacts[0].parts.length > 0) {
                const part = artifacts[0].parts[0];
                if (part && typeof part.text === 'string') {
                    botResponse = part.text;
                } else {
                    console.log("Received non-text part in completed task, ignoring:", part);
                }
            } else if (status.state === 'failed') {
                botResponse = 'Sorry, something went wrong.';
            }

            if (botResponse) {
                setConversations(prev => {
                    if (!prev[convoId]) return prev;
                    const newMessages = [...prev[convoId].messages, { sender: 'bot', text: botResponse }];
                    return { ...prev, [convoId]: { ...prev[convoId], messages: newMessages } };
                });
            }
        }
    }, [updateConversation, stopPolling]);


    const pollTask = useCallback(async (processingTaskId, convoId) => {
        const request = {
            jsonrpc: "2.0",
            method: "tasks/get",
            params: { id: processingTaskId },
            id: Date.now()
        };

        try {
            const response = await axios.post('/', request);
            if (response.data.error) {
                throw new Error(response.data.error.message);
            }
            handleTaskResult(response.data.result, convoId);
        } catch (error) {
            stopPolling(processingTaskId);
            updateConversation(convoId, { isTyping: false });
            console.error('Error polling task:', error);
            setConversations(prev => {
                if (!prev[convoId]) return prev;
                const newMessages = [...prev[convoId].messages, { sender: 'bot', text: 'Sorry, I had trouble getting the response.' }];
                return { ...prev, [convoId]: { ...prev[convoId], messages: newMessages } };
            });
        }
    }, [handleTaskResult, stopPolling, updateConversation]);

    const handleSend = async () => {
        const activeConversation = conversations[activeConversationId];
        if (!activeConversation || input.trim() === '' || activeConversation.isTyping) return;

        const userMessage = { sender: 'user', text: input };
        const newMessages = [...activeConversation.messages, userMessage];
        updateConversation(activeConversationId, { messages: newMessages, isTyping: true });

        const messageToBeSent = input;
        setInput('');

        const request = {
            jsonrpc: "2.0",
            method: "message/send",
            params: {
                id: activeConversation.taskId,
                message: {
                    role: 'user',
                    parts: [{ text: messageToBeSent }],
                    messageId: `msg-${Date.now()}`,
                    contextId: activeConversation.contextId,
                }
            },
            id: Date.now()
        };

        try {
            const response = await axios.post('/', request);
            if (response.data.error) {
                throw new Error(response.data.error.message);
            }
            const { id: processingTaskId, status } = response.data.result;

            // Update the task ID for the next turn
            updateConversation(activeConversationId, { taskId: processingTaskId });

            if (status.state === 'working' || status.state === 'submitted') {
                const intervalId = setInterval(() => pollTask(processingTaskId, activeConversationId), 2000);
                pollingTasksRef.current[processingTaskId] = { intervalId, convoId: activeConversationId };
            }
            handleTaskResult(response.data.result, activeConversationId);

        } catch (error) {
            updateConversation(activeConversationId, { isTyping: false });
            console.error('Error sending message:', error);
            setConversations(prev => {
                if (!prev[activeConversationId]) return prev;
                const updatedMessages = [...newMessages, { sender: 'bot', text: `Error: ${error.message}` }];
                return { ...prev, [activeConversationId]: { ...prev[activeConversationId], messages: updatedMessages } };
            });
        }
    };

    const handleKeyPress = (e) => {
        if (e.key === 'Enter') {
            e.preventDefault();
            handleSend();
        }
    };

    return (
        <div className="app-layout">
            <div className={`sidebar ${isSidebarCollapsed ? 'collapsed' : ''}`} ref={sidebarRef}>
                <button className="new-chat-btn" onClick={handleNewConversation}>
                    <span className="new-chat-btn-icon">+</span>
                    <span className="new-chat-btn-text">New Order</span>
                </button>
                <div className="conversation-list">
                    {Object.values(conversations).map(convo => (
                        <div
                            key={convo.id}
                            className={`conversation-item ${convo.id === activeConversationId ? 'active' : ''}`}
                            onClick={() => setActiveConversationId(convo.id)}
                        >
                            <span className="convo-name">{convo.name}</span>
                            <button
                                className="delete-convo-btn"
                                onClick={(e) => {
                                    e.stopPropagation();
                                    handleDeleteConversation(convo.id);
                                }}
                            >
                                &#x2715;
                            </button>
                        </div>
                    ))}
                </div>
                <button className="collapse-btn" onClick={() => setIsSidebarCollapsed(!isSidebarCollapsed)}>
                    {isSidebarCollapsed ? '»' : '«'}
                </button>
            </div>
            <div className="main-content" ref={mainContentRef}>
                <header className="App-header">
                    <h1>{activeConversation ? activeConversation.name : "Food Ordering"}</h1>
                </header>
                <div className="chat-window">
                    {activeConversation?.messages.map((msg, index) => (
                        <div key={index} className={`message-wrapper ${msg.sender}`}>
                            <div className="message" style={{ borderLeftColor: agentColors[msg.sender] }}>
                                <div className="agent-name">
                                    <span style={{ color: agentColors[msg.sender] }}>{msg.sender === 'bot' ? 'Personal Helper' : 'User'}</span>
                                </div>
                                <div><ReactMarkdown remarkPlugins={[RemarkGfm]}>{msg.text}</ReactMarkdown></div>
                            </div>
                        </div>
                    ))}
                    {activeConversation?.isTyping && (
                        <div className="message-wrapper bot">
                            <div className="message" style={{ borderLeftColor: agentColors['bot'] }}>
                                <div className="agent-name">
                                    <span style={{ color: agentColors['bot'] }}>Personal Helper</span>
                                </div>
                                <div className="typing-indicator">
                                    <span></span><span></span><span></span>
                                </div>
                            </div>
                        </div>
                    )}
                    <div ref={messagesEndRef} />
                </div>
                <div className="input-area">
                    <input
                        ref={inputRef}
                        type="text"
                        value={input}
                        onChange={(e) => setInput(e.target.value)}
                        onKeyPress={handleKeyPress}
                        placeholder="Type your message..."
                        disabled={!activeConversation || activeConversation.isTyping}
                    />
                    <button onClick={handleSend} disabled={!activeConversation || activeConversation.isTyping}>Send</button>
                </div>
            </div>
        </div>
    );
}

export default App;
