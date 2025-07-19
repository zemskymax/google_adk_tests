const App = () => {
    const [messages, setMessages] = React.useState([]);
    const [agentColors, setAgentColors] = React.useState({});
    const colorPalette = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#FED766', '#247BA0', '#F25F5C', '#70C1B3', '#FFE066', '#F45B69'];
    const nextColorIndex = React.useRef(0);
    const messagesEndRef = React.useRef(null);

    const scrollToBottom = () => {
        messagesEndRef.current && messagesEndRef.current.scrollIntoView({ behavior: "smooth" });
    };

    React.useEffect(() => {
        const interval = setInterval(() => {
            fetch('http://localhost:10111/messages')
                .then(response => response.json())
                .then(data => {
                    setMessages(data);

                    setAgentColors(currentColors => {
                        const newColors = { ...currentColors };
                        let updated = false;
                        data.forEach(msg => {
                            if (msg.sender && !newColors[msg.sender]) {
                                newColors[msg.sender] = colorPalette[nextColorIndex.current % colorPalette.length];
                                nextColorIndex.current++;
                                updated = true;
                            }
                            if (msg.receiver && !newColors[msg.receiver]) {
                                newColors[msg.receiver] = colorPalette[nextColorIndex.current % colorPalette.length];
                                nextColorIndex.current++;
                                updated = true;
                            }
                        });
                        return updated ? newColors : currentColors;
                    });
                })
                .catch(error => console.error('Error fetching messages:', error));
        }, 1000);
        return () => clearInterval(interval);
    }, []);

    React.useEffect(() => {
        scrollToBottom();
    }, [messages]);

    return (
        <div className="container">
            <header className="header">
                <h1>* Agent 2 Agent Communication Monitor *</h1>
            </header>
            <div id="message-container">
                {messages.map((msg, index) => (
                    <div key={index} className="message" style={{ borderLeftColor: agentColors[msg.sender] }}>
                        <div className="agent-name">
                            <span style={{ color: agentColors[msg.sender] }}>{msg.sender}</span>
                            {' -> '}
                            <span style={{ color: agentColors[msg.receiver] }}>{msg.receiver}</span>
                        </div>
                        <div>{msg.message}</div>
                    </div>
                ))}
                <div ref={messagesEndRef} />
            </div>
        </div>
    );
};

ReactDOM.render(<App />, document.getElementById('root'));
