const App = () => {
    const [messages, setMessages] = React.useState([]);

    React.useEffect(() => {
        const interval = setInterval(() => {
            fetch('http://localhost:10111/messages')
                .then(response => response.json())
                .then(data => setMessages(data))
                .catch(error => console.error('Error fetching messages:', error));
        }, 1000);
        return () => clearInterval(interval);
    }, []);

    return (
        <div>
            <h1>Agent to Agent Communication</h1>
            <div id="message-container">
                {messages.map((msg, index) => (
                    <div key={index} className="message">
                        <strong>{msg.agent}:</strong> {msg.message}
                    </div>
                ))}
            </div>
        </div>
    );
};

ReactDOM.render(<App />, document.getElementById('root'));
