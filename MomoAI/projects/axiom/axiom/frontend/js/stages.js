/**
 * Axiom Stage Manager
 * Handles collaboration stage transitions and stage-specific behavior
 */

class AxiomStages {
    constructor() {
        this.currentStage = 'vision';
        this.stageInfo = {
            vision: {
                name: 'Vision',
                icon: '🎯',
                description: 'Explore problems and define goals',
                placeholder: 'Describe what you want to build or the problem you want to solve...',
                systemPrompt: 'Focus on understanding and exploration'
            },
            architecture: {
                name: 'Architecture',
                icon: '🏗️',
                description: 'Design solutions and plan implementation',
                placeholder: 'Discuss the architecture, design patterns, or technical approach...',
                systemPrompt: 'Focus on design and planning'
            },
            implementation: {
                name: 'Implementation',
                icon: '⚙️',
                description: 'Build and execute the solution',
                placeholder: 'Request specific implementations or code changes...',
                systemPrompt: 'Focus on building and executing'
            },
            review: {
                name: 'Review',
                icon: '🔍',
                description: 'Evaluate and refine the results',
                placeholder: 'Review the implementation, suggest improvements, or test functionality...',
                systemPrompt: 'Focus on evaluation and refinement'
            }
        };
    }

    /**
     * Get information about a stage
     */
    getStageInfo(stage) {
        return this.stageInfo[stage] || this.stageInfo.vision;
    }

    /**
     * Get current stage information
     */
    getCurrentStageInfo() {
        return this.getStageInfo(this.currentStage);
    }

    /**
     * Change to a new stage
     */
    changeStage(newStage) {
        if (!this.stageInfo[newStage]) {
            console.error('Invalid stage:', newStage);
            return false;
        }

        const oldStage = this.currentStage;
        this.currentStage = newStage;

        // Update UI elements
        this.updateStageUI();

        // Trigger stage change event
        this.onStageChange?.(newStage, oldStage);

        return true;
    }

    /**
     * Update UI elements for current stage
     */
    updateStageUI() {
        const stageInfo = this.getCurrentStageInfo();
        
        // Update placeholder text
        const messageInput = document.getElementById('message-input');
        if (messageInput) {
            messageInput.placeholder = stageInfo.placeholder;
        }

        // Update stage info display
        const stageInfoElement = document.getElementById('current-stage-info');
        if (stageInfoElement) {
            stageInfoElement.textContent = stageInfo.name;
        }

        // Update stage selector
        const stageSelect = document.getElementById('stage-select');
        if (stageSelect) {
            stageSelect.value = this.currentStage;
        }

        // Update document title
        document.title = `Axiom - ${stageInfo.name}`;
    }

    /**
     * Get stage-specific suggestions
     */
    getStageSuggestions(stage) {
        const suggestions = {
            vision: [
                "I want to build a web application that...",
                "Help me understand the requirements for...",
                "What are the key challenges in building...",
                "I need to solve this problem: ..."
            ],
            architecture: [
                "What's the best architecture for...",
                "How should I structure the database for...",
                "What technologies would you recommend for...",
                "Can you design the API structure for..."
            ],
            implementation: [
                "Implement the user authentication system",
                "Create the database schema for...",
                "Write the API endpoints for...",
                "Build the frontend components for..."
            ],
            review: [
                "Review the code quality of...",
                "Test the functionality of...",
                "What improvements can be made to...",
                "Are there any security issues with..."
            ]
        };

        return suggestions[stage] || [];
    }

    /**
     * Get stage transition recommendations
     */
    getStageTransitions(currentStage) {
        const transitions = {
            vision: {
                next: 'architecture',
                reason: 'Ready to design the solution architecture'
            },
            architecture: {
                next: 'implementation',
                reason: 'Architecture is defined, ready to build'
            },
            implementation: {
                next: 'review',
                reason: 'Implementation complete, ready for review'
            },
            review: {
                next: 'vision',
                reason: 'Review complete, ready for new iteration'
            }
        };

        return transitions[currentStage];
    }

    /**
     * Check if stage transition is recommended
     */
    shouldTransitionStage(messageCount, lastMessages) {
        // Simple heuristics for stage transitions
        switch (this.currentStage) {
            case 'vision':
                // Transition to architecture after problem is well-defined
                return messageCount >= 3 && this.hasArchitecturalDiscussion(lastMessages);
            
            case 'architecture':
                // Transition to implementation when design is clear
                return messageCount >= 5 && this.hasImplementationRequests(lastMessages);
            
            case 'implementation':
                // Transition to review when implementation tasks are done
                return this.hasCompletedImplementation(lastMessages);
            
            case 'review':
                // Transition back to vision for new features/iterations
                return this.hasNewRequirements(lastMessages);
            
            default:
                return false;
        }
    }

    /**
     * Analyze messages for architectural discussion
     */
    hasArchitecturalDiscussion(messages) {
        const architecturalKeywords = [
            'architecture', 'design', 'structure', 'components',
            'database', 'api', 'frontend', 'backend', 'system'
        ];
        
        return this.containsKeywords(messages, architecturalKeywords);
    }

    /**
     * Analyze messages for implementation requests
     */
    hasImplementationRequests(messages) {
        const implementationKeywords = [
            'implement', 'build', 'create', 'write', 'code',
            'function', 'class', 'method', 'endpoint'
        ];
        
        return this.containsKeywords(messages, implementationKeywords);
    }

    /**
     * Check if implementation is completed
     */
    hasCompletedImplementation(messages) {
        const completionKeywords = [
            'done', 'complete', 'finished', 'implemented',
            'working', 'ready', 'test', 'review'
        ];
        
        return this.containsKeywords(messages, completionKeywords);
    }

    /**
     * Check for new requirements
     */
    hasNewRequirements(messages) {
        const newRequirementKeywords = [
            'new', 'add', 'feature', 'requirement', 'change',
            'improve', 'enhance', 'modify', 'update'
        ];
        
        return this.containsKeywords(messages, newRequirementKeywords);
    }

    /**
     * Helper to check if messages contain keywords
     */
    containsKeywords(messages, keywords) {
        if (!messages || messages.length === 0) return false;
        
        const recentMessages = messages.slice(-3); // Check last 3 messages
        const text = recentMessages.map(msg => msg.content.toLowerCase()).join(' ');
        
        return keywords.some(keyword => text.includes(keyword));
    }

    /**
     * Get stage-specific tips
     */
    getStageTips(stage) {
        const tips = {
            vision: [
                "Be specific about your goals and constraints",
                "Describe the problem you're trying to solve",
                "Think about who will use this solution",
                "Consider the scope and timeline"
            ],
            architecture: [
                "Focus on high-level design decisions",
                "Consider scalability and maintainability",
                "Think about data flow and system boundaries",
                "Choose appropriate technologies and patterns"
            ],
            implementation: [
                "Break down tasks into manageable pieces",
                "Start with core functionality first",
                "Write clean, well-documented code",
                "Test as you build"
            ],
            review: [
                "Test all functionality thoroughly",
                "Check for edge cases and error handling",
                "Review code quality and performance",
                "Document any issues or improvements"
            ]
        };

        return tips[stage] || [];
    }

    /**
     * Initialize stage manager
     */
    initialize(initialStage = 'vision') {
        this.currentStage = initialStage;
        this.updateStageUI();
    }
}

// Export for use in other modules
window.AxiomStages = AxiomStages;