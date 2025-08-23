/**
 * Axiom UI Manager
 * Handles DOM manipulation and user interface updates
 */

class AxiomUI {
    constructor() {
        this.elements = {};
        this.currentMessageElement = null;
        this.messageCount = 0;
        
        this.initializeElements();
        this.setupEventListeners();
    }

    /**
     * Initialize DOM element references
     */
    initializeElements() {
        this.elements = {
            // Header elements
            connectionIndicator: document.getElementById('connection-indicator'),
            connectionText: document.getElementById('connection-text'),
            stageSelect: document.getElementById('stage-select'),
            currentStageInfo: document.getElementById('current-stage-info'),
            
            // Chat elements
            messages: document.getElementById('messages'),
            messageInput: document.getElementById('message-input'),
            sendButton: document.getElementById('send-button'),
            charCount: document.getElementById('char-count'),
            
            // Sidebar elements
            tasksList: document.getElementById('tasks-list'),
            sessionId: document.getElementById('session-id'),
            messageCount: document.getElementById('message-count'),
            sessionStart: document.getElementById('session-start'),
            newSessionButton: document.getElementById('new-session-button'),
            
            // Overlay elements
            loadingOverlay: document.getElementById('loading-overlay'),
            errorToast: document.getElementById('error-toast'),
            errorMessage: document.getElementById('error-message'),
            closeToast: document.getElementById('close-toast')
        };
    }

    /**
     * Setup event listeners
     */
    setupEventListeners() {
        // Message input events
        this.elements.messageInput.addEventListener('input', () => {
            this.updateCharCount();
            this.updateSendButton();
        });

        this.elements.messageInput.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && (e.ctrlKey || e.metaKey)) {
                e.preventDefault();
                this.sendMessage();
            }
        });

        // Send button
        this.elements.sendButton.addEventListener('click', () => {
            this.sendMessage();
        });

        // Stage selector
        this.elements.stageSelect.addEventListener('change', (e) => {
            this.onStageChange?.(e.target.value);
        });

        // New session button
        this.elements.newSessionButton.addEventListener('click', () => {
            this.onNewSession?.();
        });

        // Error toast close
        this.elements.closeToast.addEventListener('click', () => {
            this.hideError();
        });

        // Auto-hide error toast
        setTimeout(() => {
            if (!this.elements.errorToast.classList.contains('hidden')) {
                this.hideError();
            }
        }, 5000);
    }

    /**
     * Update character count
     */
    updateCharCount() {
        const count = this.elements.messageInput.value.length;
        this.elements.charCount.textContent = count;
        
        if (count > 3800) {
            this.elements.charCount.style.color = 'var(--error-color)';
        } else if (count > 3500) {
            this.elements.charCount.style.color = 'var(--warning-color)';
        } else {
            this.elements.charCount.style.color = 'var(--text-muted)';
        }
    }

    /**
     * Update send button state
     */
    updateSendButton() {
        const hasContent = this.elements.messageInput.value.trim().length > 0;
        this.elements.sendButton.disabled = !hasContent;
    }

    /**
     * Send message (to be connected to API)
     */
    sendMessage() {
        const content = this.elements.messageInput.value.trim();
        if (!content) return;

        // Add user message to UI
        this.addMessage('user', content);
        
        // Clear input
        this.elements.messageInput.value = '';
        this.updateCharCount();
        this.updateSendButton();

        // Call external handler
        this.onSendMessage?.(content);
    }

    /**
     * Add message to chat
     */
    addMessage(role, content, toolCalls = []) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${role}`;

        const avatar = document.createElement('div');
        avatar.className = 'message-avatar';
        avatar.textContent = role === 'user' ? 'U' : '⚡';

        const messageContent = document.createElement('div');
        messageContent.className = 'message-content';

        const bubble = document.createElement('div');
        bubble.className = 'message-bubble';
        bubble.textContent = content;

        const time = document.createElement('div');
        time.className = 'message-time';
        time.textContent = new Date().toLocaleTimeString();

        messageContent.appendChild(bubble);
        messageContent.appendChild(time);

        // Add tool calls if any
        if (toolCalls.length > 0) {
            const toolCallsDiv = document.createElement('div');
            toolCallsDiv.className = 'tool-calls';
            
            toolCalls.forEach(call => {
                const callDiv = document.createElement('div');
                callDiv.className = 'tool-call';
                callDiv.textContent = call;
                toolCallsDiv.appendChild(callDiv);
            });
            
            messageContent.appendChild(toolCallsDiv);
        }

        messageDiv.appendChild(avatar);
        messageDiv.appendChild(messageContent);

        // Remove welcome message if it exists
        const welcomeMessage = this.elements.messages.querySelector('.welcome-message');
        if (welcomeMessage) {
            welcomeMessage.remove();
        }

        this.elements.messages.appendChild(messageDiv);
        this.scrollToBottom();
        
        this.messageCount++;
        this.updateMessageCount();

        return messageDiv;
    }

    /**
     * Start streaming message (for real-time updates)
     */
    startStreamingMessage() {
        this.currentMessageElement = this.addMessage('assistant', '');
        const bubble = this.currentMessageElement.querySelector('.message-bubble');
        bubble.innerHTML = '<span class="typing-indicator">●●●</span>';
        return this.currentMessageElement;
    }

    /**
     * Update streaming message content
     */
    updateStreamingMessage(content) {
        if (!this.currentMessageElement) return;
        
        const bubble = this.currentMessageElement.querySelector('.message-bubble');
        bubble.textContent = content;
        this.scrollToBottom();
    }

    /**
     * Finish streaming message
     */
    finishStreamingMessage(toolCalls = []) {
        if (!this.currentMessageElement) return;

        // Add tool calls if any
        if (toolCalls.length > 0) {
            const messageContent = this.currentMessageElement.querySelector('.message-content');
            const toolCallsDiv = document.createElement('div');
            toolCallsDiv.className = 'tool-calls';
            
            toolCalls.forEach(call => {
                const callDiv = document.createElement('div');
                callDiv.className = 'tool-call';
                callDiv.textContent = call;
                toolCallsDiv.appendChild(callDiv);
            });
            
            messageContent.appendChild(toolCallsDiv);
        }

        this.currentMessageElement = null;
        this.scrollToBottom();
    }

    /**
     * Update connection status
     */
    updateConnectionStatus(status) {
        this.elements.connectionIndicator.className = `status-indicator ${status}`;
        
        const statusText = {
            connected: 'Connected',
            connecting: 'Connecting...',
            disconnected: 'Disconnected'
        };
        
        this.elements.connectionText.textContent = statusText[status] || status;
    }

    /**
     * Update collaboration stage
     */
    updateStage(stage) {
        this.elements.stageSelect.value = stage;
        
        const stageNames = {
            vision: 'Vision',
            architecture: 'Architecture',
            implementation: 'Implementation',
            review: 'Review'
        };
        
        this.elements.currentStageInfo.textContent = stageNames[stage] || stage;
    }

    /**
     * Update tasks list
     */
    updateTasks(tasks) {
        if (!tasks || tasks.length === 0) {
            this.elements.tasksList.innerHTML = '<div class="no-tasks">No active tasks</div>';
            return;
        }

        this.elements.tasksList.innerHTML = '';
        
        tasks.forEach(task => {
            const taskDiv = document.createElement('div');
            taskDiv.className = 'task-item';
            
            taskDiv.innerHTML = `
                <div class="task-header">
                    <span class="task-status ${task.status}">${task.status}</span>
                </div>
                <div class="task-description">${task.description}</div>
                <div class="task-progress">
                    <div class="task-progress-bar" style="width: ${task.progress}%"></div>
                </div>
            `;
            
            this.elements.tasksList.appendChild(taskDiv);
        });
    }

    /**
     * Update session information
     */
    updateSessionInfo(session) {
        this.elements.sessionId.textContent = session.id.substring(0, 8) + '...';
        this.elements.sessionStart.textContent = new Date(session.created_at).toLocaleString();
        this.messageCount = session.message_count;
        this.updateMessageCount();
    }

    /**
     * Update message count
     */
    updateMessageCount() {
        this.elements.messageCount.textContent = this.messageCount;
    }

    /**
     * Show loading overlay
     */
    showLoading() {
        this.elements.loadingOverlay.classList.remove('hidden');
    }

    /**
     * Hide loading overlay
     */
    hideLoading() {
        this.elements.loadingOverlay.classList.add('hidden');
    }

    /**
     * Show error message
     */
    showError(message) {
        this.elements.errorMessage.textContent = message;
        this.elements.errorToast.classList.remove('hidden');
        
        // Auto-hide after 5 seconds
        setTimeout(() => {
            this.hideError();
        }, 5000);
    }

    /**
     * Hide error message
     */
    hideError() {
        this.elements.errorToast.classList.add('hidden');
    }

    /**
     * Scroll messages to bottom
     */
    scrollToBottom() {
        this.elements.messages.scrollTop = this.elements.messages.scrollHeight;
    }

    /**
     * Clear all messages
     */
    clearMessages() {
        this.elements.messages.innerHTML = `
            <div class="welcome-message">
                <div class="welcome-content">
                    <h2>Welcome to Axiom</h2>
                    <p>Your coherent AI collaboration partner. Start by describing what you'd like to build.</p>
                    <div class="stage-info">
                        <strong>Current Stage:</strong> <span id="current-stage-info">Vision</span>
                    </div>
                </div>
            </div>
        `;
        this.messageCount = 0;
        this.updateMessageCount();
    }

    /**
     * Focus message input
     */
    focusInput() {
        this.elements.messageInput.focus();
    }
}

// Export for use in other modules
window.AxiomUI = AxiomUI;