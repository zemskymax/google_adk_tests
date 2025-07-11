const App = () => {
    const [messages, setMessages] = React.useState([]);
    const [agentColors, setAgentColors] = React.useState({});
    const colorPalette = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#FED766', '#247BA0', '#F25F5C', '#70C1B3', '#FFE066', '#50514F', '#F45B69'];
    const nextColorIndex = React.useRef(0);

    React.useEffect(() => {
        const interval = setInterval(() => {
            fetch('http://localhost:10111/messages')
                .then(response => response.json())
                .then(data => {
                    const parsedMessages = data.map(msg => {
                        let messageContent = msg.message;
                        const prefix = `${msg.agent}:`;
                        if (messageContent.startsWith(prefix)) {
                            messageContent = messageContent.substring(prefix.length).trim();
                        }
                        return { ...msg, messageContent: messageContent };
                    });

                    setMessages(parsedMessages);

                    setAgentColors(currentColors => {
                        const newColors = { ...currentColors };
                        let updated = false;
                        parsedMessages.forEach(msg => {
                            if (!newColors[msg.agent]) {
                                newColors[msg.agent] = colorPalette[nextColorIndex.current % colorPalette.length];
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

    return (
        <div className="container">
            <header className="header">
                <h1>Agent to Agent Communication Monitor</h1>
            </header>
            <div id="message-container">
                {messages.map((msg, index) => (
                    <div key={index} className="message" style={{ borderLeftColor: agentColors[msg.agent] }}>
                        <div className="agent-name" style={{ color: agentColors[msg.agent] }}>{msg.agent}</div>
                        <div>{msg.messageContent}</div>
                    </div>
                ))}
            </div>
        </div>
    );
};

ReactDOM.render(<App />, document.getElementById('root'));
