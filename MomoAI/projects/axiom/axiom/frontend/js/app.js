/**
 * Axiom PWA Main Application
 * Coordinates API, UI, and Stage management
 */

class AxiomApp {
    constructor() {
        this.api = new AxiomAPI();
        this.ui = new AxiomUI();
        this.stages = new AxiomStages();
        
        this.currentSession = null;
        this.streamingContent = '';
        
        this.initialize();
    }

    /**
     * Initialize the application
     */
    async initialize() {
        console.log('🚀 Initializing Axiom PWA...');
        
        // Setup event handlers
        this.setupEventHandlers();
        
        // Initialize stages
        this.stages.initialize();
        
        // Create initial session
        await this.createNewSession();
        
        // Focus input
        this.ui.focusInput();
        
        console.log('✅ Axiom PWA initialized');
    }

    /**
     * Setup event handlers between components
     */
    setupEventHandlers() {
        // API event handlers
        this.api.onMessage = (data) => this.handleMessage(data);
        this.api.onConnectionChange = (status) => this.handleConnectionChange(status);
        this.api.onTaskUpdate = (task) => this.handleTaskUpdate(task);
        this.api.onStageChange = (stage) => this.handleStageChange(stage);
        this.api.onError = (error) => this.handleError(error);

        // UI event handlers
        this.ui.onSendMessage = (content) => this.sendMessage(content);
        this.ui.onStageChange = (stage) => this.changeStage(stage);
        this.ui.onNewSession = () => this.createNewSession();

        // Stage event handlers
        this.stages.onStageChange = (newStage, oldStage) => {
            console.log(`Stage changed: ${oldStage} → ${newStage}`);
        };

        // Window event handlers
        window.addEventListener('beforeunload', () => {
            this.api.disconnect();
        });

        // Handle offline/online events
        window.addEventListener('online', () => {
            console.log('Back online');
            if (this.currentSession) {
                this.api.connectWebSocket(this.currentSession.id);
            }
        });

        window.addEventListener('offline', () => {
            console.log('Gone offline');
            this.ui.showError('Connection lost. Messages will be queued until reconnected.');
        });
    }

    /**
     * Create a new session
     */
    async createNewSession() {
        try {
            this.ui.showLoading();
            
            // Disconnect existing WebSocket
            this.api.disconnect();
            
            // Create new session
            this.currentSession = await this.api.createSession();
            console.log('Created session:', this.currentSession.id);
            
            // Store session ID globally for coherence validator
            window.currentSessionId = this.currentSession.id;
            
            // Update UI
            this.ui.updateSessionInfo(this.currentSession);
            this.ui.clearMessages();
            
            // Connect WebSocket
            await this.api.connectWebSocket(this.currentSession.id);
            
            // Load initial data
            await this.loadSessionData();
            
        } catch (error) {
            console.error('Failed to create session:', error);
            this.ui.showError('Failed to create new session. Please try again.');
        } finally {
            this.ui.hideLoading();
        }
    }

    /**
     * Load session data (tasks, messages, etc.)
     */
    async loadSessionData() {
        try {
            // Load tasks
            const tasksData = await this.api.getTasks(this.currentSession.id);
            this.ui.updateTasks(tasksData.tasks);
            
        } catch (error) {
            console.error('Failed to load session data:', error);
        }
    }

    /**
     * Send message to AI
     */
    async sendMessage(content) {
        if (!this.currentSession) {
            this.ui.showError('No active session. Please create a new session.');
            return;
        }

        try {
            // Check if WebSocket is connected
            if (this.api.isConnected()) {
                // Send via WebSocket for real-time streaming
                this.api.sendMessage(content);
                
                // Start streaming message in UI
                this.ui.startStreamingMessage();
                this.streamingContent = '';
                
            } else {
                // Fallback to REST API
                this.ui.showLoading();
                const response = await this.api.sendMessageRest(this.currentSession.id, content);
                this.ui.addMessage('assistant', response.content, response.tool_calls);
                this.ui.hideLoading();
            }
            
        } catch (error) {
            console.error('Failed to send message:', error);
            this.ui.showError('Failed to send message. Please try again.');
            this.ui.hideLoading();
        }
    }

    /**
     * Handle incoming messages from API
     */
    handleMessage(data) {
        if (data.type === 'message_delta') {
            // Streaming message update
            this.streamingContent += data.content;
            this.ui.updateStreamingMessage(this.streamingContent);
            
        } else if (data.type === 'message') {
            // Complete message
            if (this.ui.currentMessageElement) {
                // Finish streaming message
                this.ui.finishStreamingMessage(data.tool_calls || []);
            } else {
                // Add complete message
                this.ui.addMessage('assistant', data.content, data.tool_calls || []);
            }
            
            this.streamingContent = '';
            
        } else if (data.type === 'coherence_validation') {
            // Handle coherence validation feedback
            if (window.coherenceValidator) {
                window.coherenceValidator.handleCoherenceValidation(data);
            }
            
        } else if (data.type === 'input_blocked') {
            // Handle blocked input
            if (window.coherenceValidator) {
                window.coherenceValidator.handleInputBlocked(data);
            }
            
        } else if (data.type === 'output_validation') {
            // Handle AI output validation
            if (window.coherenceValidator) {
                window.coherenceValidator.handleOutputValidation(data);
            }
            
        } else if (data.type === 'regenerating') {
            // Show regeneration notification
            this.ui.showNotification('Regenerating response with formal contracts...', 'info');
            
        } else if (data.type === 'regeneration_delta') {
            // Handle regeneration streaming
            this.streamingContent += data.content;
            this.ui.updateStreamingMessage(this.streamingContent);
            
        } else if (data.type === 'coherence_settings_updated') {
            // Update coherence validator settings
            if (window.coherenceValidator) {
                window.coherenceValidator.enabled = data.enabled;
                window.coherenceValidator.level = data.level;
                window.coherenceValidator.updateLevelDescription();
            }
        }
    }

    /**
     * Handle connection status changes
     */
    handleConnectionChange(status) {
        this.ui.updateConnectionStatus(status);
        
        if (status === 'connected') {
            console.log('WebSocket connected');
        } else if (status === 'disconnected') {
            console.log('WebSocket disconnected');
        }
    }

    /**
     * Handle task updates
     */
    handleTaskUpdate(task) {
        console.log('Task update:', task);
        // Reload tasks to get updated list
        if (this.currentSession) {
            this.loadSessionData();
        }
    }

    /**
     * Handle stage changes from server
     */
    handleStageChange(stage) {
        this.stages.changeStage(stage);
        this.ui.updateStage(stage);
    }

    /**
     * Change collaboration stage
     */
    async changeStage(stage) {
        if (!this.currentSession) {
            this.ui.showError('No active session');
            return;
        }

        try {
            await this.api.changeStage(this.currentSession.id, stage);
            this.stages.changeStage(stage);
            this.ui.updateStage(stage);
            
        } catch (error) {
            console.error('Failed to change stage:', error);
            this.ui.showError('Failed to change stage. Please try again.');
        }
    }

    /**
     * Handle errors
     */
    handleError(error) {
        console.error('API Error:', error);
        this.ui.showError(error);
    }

    /**
     * Get application status
     */
    getStatus() {
        return {
            session: this.currentSession?.id,
            connected: this.api.isConnected(),
            stage: this.stages.currentStage,
            messageCount: this.ui.messageCount
        };
    }
}

// Initialize app when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.axiomApp = new AxiomApp();
});

// Export for debugging
window.AxiomApp = AxiomApp;