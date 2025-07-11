
from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
import logging

app = Flask(__name__, static_folder='frontend', static_url_path='')
CORS(app)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# In-memory storage for messages
messages = []

@app.route('/')
def serve_index():
    return send_from_directory(app.static_folder, 'index.html')

@app.route('/log', methods=['POST'])
def log_message():
    try:
        message = request.json
        if not message or 'message' not in message or 'sender' not in message or 'receiver' not in message:
            logger.error("Invalid message format. Required fields: sender, receiver, message")
            return jsonify({"status": "error", "reason": "Invalid message format. Required fields: sender, receiver, message"}), 400

        logger.info(f"Received message from {message.get('sender')} to {message.get('receiver')}: {message.get('message')}")
        messages.append(message)
        return jsonify({"status": "success"}), 200
    except Exception as e:
        logger.exception("Error in log_message")
        return jsonify({"status": "error", "reason": str(e)}), 500

@app.route('/messages', methods=['GET'])
def get_messages():
    return jsonify(messages)

if __name__ == '__main__':
    app.run(port=10111)
