/**
 * Axiom API Client
 * Handles WebSocket and REST API communication
 */

class AxiomAPI {
    constructor() {
        this.baseUrl = window.location.origin;
        this.websocket = null;
        this.sessionId = null;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 5;
        this.reconnectDelay = 1000;
        
        // Event listeners
        this.onMessage = null;
        this.onConnectionChange = null;
        this.onTaskUpdate = null;
        this.onStageChange = null;
        this.onError = null;
    }

    /**
     * Create a new session
     */
    async createSession() {
        try {
            const response = await fetch(`${this.baseUrl}/api/sessions`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                }
            });

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            const session = await response.json();
            this.sessionId = session.id;
            return session;
        } catch (error) {
            console.error('Failed to create session:', error);
            throw error;
        }
    }

    /**
     * Get session information
     */
    async getSession(sessionId) {
        try {
            const response = await fetch(`${this.baseUrl}/api/sessions/${sessionId}`);
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            return await response.json();
        } catch (error) {
            console.error('Failed to get session:', error);
            throw error;
        }
    }

    /**
     * Connect to WebSocket
     */
    async connectWebSocket(sessionId) {
        if (this.websocket && this.websocket.readyState === WebSocket.OPEN) {
            return;
        }

        this.sessionId = sessionId;
        const wsUrl = `${window.location.protocol === 'https:' ? 'wss:' : 'ws:'}//${window.location.host}/ws/${sessionId}`;

        try {
            this.websocket = new WebSocket(wsUrl);
            
            this.websocket.onopen = () => {
                console.log('WebSocket connected');
                this.reconnectAttempts = 0;
                this.onConnectionChange?.('connected');
            };

            this.websocket.onmessage = (event) => {
                try {
                    const data = JSON.parse(event.data);
                    this.handleWebSocketMessage(data);
                } catch (error) {
                    console.error('Failed to parse WebSocket message:', error);
                }
            };

            this.websocket.onclose = (event) => {
                console.log('WebSocket disconnected:', event.code, event.reason);
                this.onConnectionChange?.('disconnected');
                
                // Attempt to reconnect
                if (this.reconnectAttempts < this.maxReconnectAttempts) {
                    this.reconnectAttempts++;
                    setTimeout(() => {
                        console.log(`Reconnecting... (${this.reconnectAttempts}/${this.maxReconnectAttempts})`);
                        this.onConnectionChange?.('connecting');
                        this.connectWebSocket(sessionId);
                    }, this.reconnectDelay * this.reconnectAttempts);
                }
            };

            this.websocket.onerror = (error) => {
                console.error('WebSocket error:', error);
                this.onError?.('WebSocket connection failed');
            };

        } catch (error) {
            console.error('Failed to connect WebSocket:', error);
            this.onError?.('Failed to connect to server');
        }
    }

    /**
     * Handle incoming WebSocket messages
     */
    handleWebSocketMessage(data) {
        switch (data.type) {
            case 'message':
                this.onMessage?.(data);
                break;
            case 'message_delta':
                this.onMessage?.(data);
                break;
            case 'task_update':
                this.onTaskUpdate?.(data.task);
                break;
            case 'stage_change':
                this.onStageChange?.(data.stage);
                break;
            case 'error':
                this.onError?.(data.content);
                break;
            default:
                console.log('Unknown message type:', data.type);
        }
    }

    /**
     * Send message via WebSocket
     */
    sendMessage(content) {
        if (!this.websocket || this.websocket.readyState !== WebSocket.OPEN) {
            throw new Error('WebSocket not connected');
        }

        this.websocket.send(JSON.stringify({
            type: 'message',
            content: content
        }));
    }

    /**
     * Interrupt a task
     */
    interruptTask(taskId) {
        if (!this.websocket || this.websocket.readyState !== WebSocket.OPEN) {
            throw new Error('WebSocket not connected');
        }

        this.websocket.send(JSON.stringify({
            type: 'interrupt_task',
            task_id: taskId
        }));
    }

    /**
     * Change collaboration stage
     */
    async changeStage(sessionId, stage) {
        try {
            const response = await fetch(`${this.baseUrl}/api/sessions/${sessionId}/stage`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ stage })
            });

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            return await response.json();
        } catch (error) {
            console.error('Failed to change stage:', error);
            throw error;
        }
    }

    /**
     * Get tasks for session
     */
    async getTasks(sessionId) {
        try {
            const response = await fetch(`${this.baseUrl}/api/sessions/${sessionId}/tasks`);
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            return await response.json();
        } catch (error) {
            console.error('Failed to get tasks:', error);
            throw error;
        }
    }

    /**
     * Send message via REST API (fallback)
     */
    async sendMessageRest(sessionId, content) {
        try {
            const response = await fetch(`${this.baseUrl}/api/messages/${sessionId}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ content })
            });

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            return await response.json();
        } catch (error) {
            console.error('Failed to send message:', error);
            throw error;
        }
    }

    /**
     * Get message history
     */
    async getMessages(sessionId) {
        try {
            const response = await fetch(`${this.baseUrl}/api/messages/${sessionId}`);
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            return await response.json();
        } catch (error) {
            console.error('Failed to get messages:', error);
            throw error;
        }
    }

    /**
     * Disconnect WebSocket
     */
    disconnect() {
        if (this.websocket) {
            this.websocket.close();
            this.websocket = null;
        }
    }

    /**
     * Check if connected
     */
    isConnected() {
        return this.websocket && this.websocket.readyState === WebSocket.OPEN;
    }
}

// Export for use in other modules
window.AxiomAPI = AxiomAPI;