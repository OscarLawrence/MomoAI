const chatForm = document.getElementById('chatForm');
const messageInput = document.getElementById('messageInput');
const chatHistory = document.getElementById('chatHistory');
const sendBtn = document.getElementById('sendBtn');
const clearBtn = document.getElementById('clearBtn');
const status = document.getElementById('status');

// Load chat history on page load
window.addEventListener('load', loadHistory);

// Handle form submission
chatForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const message = messageInput.value.trim();
    if (!message) return;
    
    // Disable form while processing
    setLoading(true);
    
    try {
        // Add user message to display
        addMessage('user', message);
        
        // Clear input
        messageInput.value = '';
        
        // Send to API
        const response = await fetch('/api/chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ message })
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        
        // Add assistant response to display
        addMessage('assistant', data.response);
        
        // Update status with token usage
        const tokens = data.token_usage;
        setStatus(`Tokens: ${tokens.input_tokens} in, ${tokens.output_tokens} out`);
        
    } catch (error) {
        console.error('Error:', error);
        setStatus(`Error: ${error.message}`, 'error');
        
    } finally {
        setLoading(false);
        messageInput.focus();
    }
});

// Clear history
clearBtn.addEventListener('click', async () => {
    try {
        await fetch('/api/history', { method: 'DELETE' });
        chatHistory.innerHTML = '';
        setStatus('History cleared');
    } catch (error) {
        setStatus(`Error clearing history: ${error.message}`, 'error');
    }
});

// Handle Ctrl+Enter to submit
messageInput.addEventListener('keydown', (e) => {
    if (e.ctrlKey && e.key === 'Enter') {
        chatForm.dispatchEvent(new Event('submit'));
    }
});

async function loadHistory() {
    try {
        const response = await fetch('/api/history');
        const data = await response.json();
        
        chatHistory.innerHTML = '';
        data.messages.forEach(msg => {
            addMessage(msg.role, msg.content);
        });
        
    } catch (error) {
        console.error('Error loading history:', error);
    }
}

function addMessage(role, content) {
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${role}`;
    
    const roleLabel = document.createElement('div');
    roleLabel.className = 'role';
    roleLabel.textContent = role === 'user' ? 'You' : 'Axiom';
    
    const contentDiv = document.createElement('div');
    contentDiv.className = 'content';
    contentDiv.textContent = content;
    
    messageDiv.appendChild(roleLabel);
    messageDiv.appendChild(contentDiv);
    
    chatHistory.appendChild(messageDiv);
    chatHistory.scrollTop = chatHistory.scrollHeight;
}

function setLoading(loading) {
    sendBtn.disabled = loading;
    messageInput.disabled = loading;
    sendBtn.textContent = loading ? 'Sending...' : 'Send';
}

function setStatus(message, type = 'info') {
    status.textContent = message;
    status.className = `status ${type}`;
    
    // Clear status after 3 seconds
    setTimeout(() => {
        status.textContent = '';
        status.className = 'status';
    }, 3000);
}