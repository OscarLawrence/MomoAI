/**
 * Coherence Validation UI Components
 * Real-time input validation and coherence indicators
 */

class CoherenceValidator {
    constructor() {
        this.debounceTimer = null;
        this.debounceDelay = 500; // ms
        this.currentValidation = null;
        this.enabled = true;
        this.level = 'standard';
        
        this.initializeUI();
        this.bindEvents();
    }
    
    initializeUI() {
        // Create coherence indicator
        const indicator = document.createElement('div');
        indicator.id = 'coherence-indicator';
        indicator.className = 'coherence-indicator hidden';
        indicator.innerHTML = `
            <div class="coherence-status">
                <span class="coherence-icon">🧠</span>
                <span class="coherence-level">Checking...</span>
                <span class="coherence-score"></span>
            </div>
            <div class="coherence-details hidden">
                <div class="contradictions"></div>
                <div class="suggestions"></div>
            </div>
        `;
        
        // Add to message input area
        const messageInput = document.getElementById('message-input');
        if (messageInput && messageInput.parentNode) {
            messageInput.parentNode.insertBefore(indicator, messageInput.nextSibling);
        }
        
        // Create coherence settings panel
        this.createSettingsPanel();
    }
    
    createSettingsPanel() {
        const panel = document.createElement('div');
        panel.id = 'coherence-settings';
        panel.className = 'coherence-settings hidden';
        panel.innerHTML = `
            <h3>Coherence Validation</h3>
            <div class="setting-group">
                <label>
                    <input type="checkbox" id="coherence-enabled" ${this.enabled ? 'checked' : ''}>
                    Enable coherence validation
                </label>
            </div>
            <div class="setting-group">
                <label for="coherence-level">Validation level:</label>
                <select id="coherence-level">
                    <option value="permissive" ${this.level === 'permissive' ? 'selected' : ''}>Permissive</option>
                    <option value="standard" ${this.level === 'standard' ? 'selected' : ''}>Standard</option>
                    <option value="strict" ${this.level === 'strict' ? 'selected' : ''}>Strict</option>
                </select>
            </div>
            <div class="setting-description">
                <small id="level-description">Standard: Blocks contradictory and low-coherence input</small>
            </div>
        `;
        
        document.body.appendChild(panel);
    }
    
    bindEvents() {
        // Real-time validation on input
        const messageInput = document.getElementById('message-input');
        if (messageInput) {
            messageInput.addEventListener('input', (e) => {
                if (this.enabled) {
                    this.validateInputDebounced(e.target.value);
                }
            });
            
            messageInput.addEventListener('focus', () => {
                this.showIndicator();
            });
        }
        
        // Settings panel events
        const enabledCheckbox = document.getElementById('coherence-enabled');
        if (enabledCheckbox) {
            enabledCheckbox.addEventListener('change', (e) => {
                this.enabled = e.target.checked;
                this.updateSettings();
                if (!this.enabled) {
                    this.hideIndicator();
                }
            });
        }
        
        const levelSelect = document.getElementById('coherence-level');
        if (levelSelect) {
            levelSelect.addEventListener('change', (e) => {
                this.level = e.target.value;
                this.updateLevelDescription();
                this.updateSettings();
            });
        }
        
        // Toggle settings panel
        document.addEventListener('keydown', (e) => {
            if (e.ctrlKey && e.key === 'h') {
                e.preventDefault();
                this.toggleSettingsPanel();
            }
        });
    }
    
    validateInputDebounced(input) {
        clearTimeout(this.debounceTimer);
        
        if (!input.trim()) {
            this.hideIndicator();
            return;
        }
        
        this.showIndicator();
        this.setValidationStatus('checking', 'Checking coherence...');
        
        this.debounceTimer = setTimeout(() => {
            this.validateInput(input);
        }, this.debounceDelay);
    }
    
    async validateInput(input) {
        try {
            const response = await fetch('/api/coherence/validate-input', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ content: input })
            });
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}`);
            }
            
            const result = await response.json();
            this.currentValidation = result;
            this.displayValidationResult(result);
            
        } catch (error) {
            console.error('Coherence validation error:', error);
            this.setValidationStatus('error', 'Validation error');
        }
    }
    
    displayValidationResult(result) {
        const level = result.level.toLowerCase();
        const score = Math.round(result.score * 100);
        
        // Update indicator
        this.setValidationStatus(level, this.getLevelText(level), score);
        
        // Show details if there are issues
        if (result.contradictions.length > 0 || result.suggestions.length > 0) {
            this.showValidationDetails(result);
        } else {
            this.hideValidationDetails();
        }
        
        // Block input if necessary
        if (this.shouldBlockInput(result)) {
            this.blockInput(result);
        } else {
            this.unblockInput();
        }
    }
    
    setValidationStatus(level, text, score = null) {
        const indicator = document.getElementById('coherence-indicator');
        const levelSpan = indicator.querySelector('.coherence-level');
        const scoreSpan = indicator.querySelector('.coherence-score');
        
        indicator.className = `coherence-indicator ${level}`;
        levelSpan.textContent = text;
        
        if (score !== null) {
            scoreSpan.textContent = `${score}%`;
            scoreSpan.classList.remove('hidden');
        } else {
            scoreSpan.classList.add('hidden');
        }
    }
    
    showValidationDetails(result) {
        const details = document.getElementById('coherence-indicator').querySelector('.coherence-details');
        const contradictions = details.querySelector('.contradictions');
        const suggestions = details.querySelector('.suggestions');
        
        // Show contradictions
        if (result.contradictions.length > 0) {
            contradictions.innerHTML = `
                <h4>⚠️ Contradictions:</h4>
                <ul>${result.contradictions.map(c => `<li>${c}</li>`).join('')}</ul>
            `;
        } else {
            contradictions.innerHTML = '';
        }
        
        // Show suggestions
        if (result.suggestions.length > 0) {
            suggestions.innerHTML = `
                <h4>💡 Suggestions:</h4>
                <ul>${result.suggestions.map(s => `<li class="suggestion" onclick="coherenceValidator.applySuggestion('${s}')">${s}</li>`).join('')}</ul>
            `;
        } else {
            suggestions.innerHTML = '';
        }
        
        details.classList.remove('hidden');
    }
    
    hideValidationDetails() {
        const details = document.getElementById('coherence-indicator').querySelector('.coherence-details');
        details.classList.add('hidden');
    }
    
    shouldBlockInput(result) {
        const level = result.level.toLowerCase();
        
        switch (this.level) {
            case 'permissive':
                return level === 'incoherent';
            case 'standard':
                return level === 'incoherent' || level === 'low';
            case 'strict':
                return level === 'incoherent' || level === 'low' || level === 'medium';
            default:
                return false;
        }
    }
    
    blockInput(result) {
        const messageInput = document.getElementById('message-input');
        const sendButton = document.getElementById('send-button');
        
        if (messageInput) {
            messageInput.classList.add('blocked');
            messageInput.title = 'Input blocked due to logical contradictions';
        }
        
        if (sendButton) {
            sendButton.disabled = true;
            sendButton.title = 'Fix contradictions before sending';
        }
    }
    
    unblockInput() {
        const messageInput = document.getElementById('message-input');
        const sendButton = document.getElementById('send-button');
        
        if (messageInput) {
            messageInput.classList.remove('blocked');
            messageInput.title = '';
        }
        
        if (sendButton) {
            sendButton.disabled = false;
            sendButton.title = '';
        }
    }
    
    applySuggestion(suggestion) {
        const messageInput = document.getElementById('message-input');
        if (messageInput) {
            // Simple suggestion application - replace the input
            messageInput.value = suggestion;
            messageInput.focus();
            
            // Trigger validation of new input
            this.validateInputDebounced(suggestion);
        }
    }
    
    getLevelText(level) {
        const texts = {
            'perfect': 'Perfect',
            'high': 'High coherence',
            'medium': 'Medium coherence',
            'low': 'Low coherence',
            'incoherent': 'Incoherent',
            'checking': 'Checking...',
            'error': 'Error'
        };
        return texts[level] || level;
    }
    
    showIndicator() {
        const indicator = document.getElementById('coherence-indicator');
        indicator.classList.remove('hidden');
    }
    
    hideIndicator() {
        const indicator = document.getElementById('coherence-indicator');
        indicator.classList.add('hidden');
    }
    
    toggleSettingsPanel() {
        const panel = document.getElementById('coherence-settings');
        panel.classList.toggle('hidden');
    }
    
    updateLevelDescription() {
        const descriptions = {
            'permissive': 'Permissive: Only blocks completely incoherent input',
            'standard': 'Standard: Blocks contradictory and low-coherence input',
            'strict': 'Strict: Requires high coherence for all input'
        };
        
        const desc = document.getElementById('level-description');
        if (desc) {
            desc.textContent = descriptions[this.level] || '';
        }
    }
    
    async updateSettings() {
        const sessionId = window.currentSessionId;
        if (!sessionId) return;
        
        try {
            await fetch(`/api/coherence/session/${sessionId}/settings`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    enabled: this.enabled,
                    level: this.level
                })
            });
        } catch (error) {
            console.error('Failed to update coherence settings:', error);
        }
    }
    
    // Handle WebSocket coherence events
    handleCoherenceValidation(data) {
        this.currentValidation = data;
        this.displayValidationResult(data);
    }
    
    handleInputBlocked(data) {
        this.blockInput(data);
        
        // Show notification
        this.showNotification('Input blocked due to logical contradictions', 'warning');
    }
    
    handleOutputValidation(data) {
        this.displayOutputValidation(data);
    }
    
    displayOutputValidation(data) {
        // Create output validation indicator
        let indicator = document.getElementById('output-validation-indicator');
        if (!indicator) {
            indicator = document.createElement('div');
            indicator.id = 'output-validation-indicator';
            indicator.className = 'output-validation-indicator';
            
            const messagesContainer = document.getElementById('messages');
            if (messagesContainer) {
                messagesContainer.appendChild(indicator);
            }
        }
        
        const status = data.has_contracts && data.contracts_valid && data.contracts_verified ? 'verified' : 'issues';
        const icon = status === 'verified' ? '✅' : '❌';
        
        indicator.innerHTML = `
            <div class="validation-status ${status}">
                ${icon} Contract Validation: ${status === 'verified' ? 'Verified' : 'Issues Found'}
            </div>
            ${data.violations.length > 0 ? `
                <div class="violations">
                    <strong>Violations:</strong>
                    <ul>${data.violations.map(v => `<li>${v}</li>`).join('')}</ul>
                </div>
            ` : ''}
        `;
        
        // Auto-hide after 5 seconds if verified
        if (status === 'verified') {
            setTimeout(() => {
                indicator.classList.add('fade-out');
            }, 5000);
        }
    }
    
    showNotification(message, type = 'info') {
        const notification = document.createElement('div');
        notification.className = `notification ${type}`;
        notification.textContent = message;
        
        document.body.appendChild(notification);
        
        setTimeout(() => {
            notification.classList.add('fade-out');
            setTimeout(() => {
                document.body.removeChild(notification);
            }, 300);
        }, 3000);
    }
}

// Initialize coherence validator when DOM is ready
let coherenceValidator;
document.addEventListener('DOMContentLoaded', () => {
    coherenceValidator = new CoherenceValidator();
});

// Export for use in other modules
window.CoherenceValidator = CoherenceValidator;