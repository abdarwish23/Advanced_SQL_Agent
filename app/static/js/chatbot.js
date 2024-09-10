// static/js/chatbot.js

document.addEventListener('DOMContentLoaded', function() {
    const chatMessages = document.getElementById('chat-messages');
    const userInput = document.getElementById('user-input');
    const sendButton = document.querySelector('.chat-input button');

    function addMessage(sender, content, isImage = false) {
        const messageElement = document.createElement('div');
        messageElement.classList.add('message', sender === 'user' ? 'user-message' : 'bot-message');

        if (isImage) {
            const img = document.createElement('img');
            img.src = `data:image/png;base64,${content}`;
            img.classList.add('visualization-image');
            messageElement.appendChild(img);
        } else {
            messageElement.textContent = content;
        }

        chatMessages.appendChild(messageElement);
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }

    function sendMessage() {
        const message = userInput.value.trim();
        if (message) {
            addMessage('user', message);
            userInput.value = '';
            fetchBotResponse(message);
        }
    }

    function fetchBotResponse(message) {
        addMessage('bot', 'Processing your query...');

        fetch('/chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ query: message }),
        })
        .then(response => response.json())
        .then(data => {
            // Remove the "Processing your query..." message
            chatMessages.removeChild(chatMessages.lastChild);

            if (data.error) {
                addMessage('bot', `Error: ${data.error}`);
                return;
            }

            // Display visualization if available
            if (data.visualization && data.visualization.image) {
                addMessage('bot', data.visualization.image, true);
                if (data.visualization.description) {
                    addMessage('bot', data.visualization.description);
                }
            }

            // Always display the summary
            if (data.summary) {
                addMessage('bot', data.summary);
            } else {
                addMessage('bot', 'No summary available.');
            }
        })
        .catch(error => {
            console.error('Error:', error);
            addMessage('bot', 'Sorry, there was an error processing your request.');
        });
    }

    // Event listeners
    sendButton.addEventListener('click', sendMessage);

    userInput.addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            sendMessage();
        }
    });

    // Initial greeting
    addMessage('bot', 'Hello! How can I assist you today?');
});