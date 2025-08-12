"""
Prompt-toolkit styling for Momo Interactive Terminal

This module provides custom styling for the interactive terminal interface.
"""

from prompt_toolkit.styles import Style

# Define the terminal style
momo_style = Style.from_dict(
    {
        # Prompt elements
        "prompt-icon": "#e74c3c bold",  # Red robot icon
        "model-name": "#3498db bold",  # Blue model name
        "prompt-separator": "#7f8c8d",  # Gray separator
        # Completion menu
        "completion-menu.completion": "bg:#ecf0f1 #2c3e50",
        "completion-menu.completion.current": "bg:#3498db #ffffff bold",
        "completion-menu.scrollbar": "bg:#bdc3c7",
        "completion-menu.scrollbar.background": "bg:#ecf0f1",
        # Help and status
        "help": "#27ae60",
        "error": "#e74c3c bold",
        "warning": "#f39c12",
        "info": "#3498db",
        # Special elements
        "command": "#9b59b6 bold",
        "argument": "#e67e22",
        "success": "#27ae60 bold",
    }
)

# Recommended models with descriptions and use cases
RECOMMENDED_MODELS = [
    {
        "name": "llama3.2:3b",
        "description": "Fast and capable 3B model, excellent for general chat and quick responses",
        "use_case": "General purpose, fast responses",
        "size": "~2GB",
        "category": "general",
    },
    {
        "name": "llama3.2:1b",
        "description": "Ultra-fast 1B model for lightning-quick interactions",
        "use_case": "Speed-optimized chat",
        "size": "~800MB",
        "category": "general",
    },
    {
        "name": "codellama:7b",
        "description": "Specialized for code generation, debugging, and programming assistance",
        "use_case": "Code generation and debugging",
        "size": "~3.8GB",
        "category": "coding",
    },
    {
        "name": "codellama:13b",
        "description": "Larger code model with better reasoning for complex programming tasks",
        "use_case": "Complex code tasks",
        "size": "~7.3GB",
        "category": "coding",
    },
    {
        "name": "mistral:7b",
        "description": "Excellent reasoning and instruction following, great balance of speed and capability",
        "use_case": "Reasoning and analysis",
        "size": "~4.1GB",
        "category": "general",
    },
    {
        "name": "phi3:3.8b",
        "description": "Compact but powerful Microsoft model with strong performance",
        "use_case": "Efficient general purpose",
        "size": "~2.2GB",
        "category": "general",
    },
    {
        "name": "gemma2:9b",
        "description": "Google's efficient and capable model with strong reasoning",
        "use_case": "Advanced reasoning",
        "size": "~5.4GB",
        "category": "general",
    },
    {
        "name": "qwen2.5:7b",
        "description": "Alibaba's multilingual model with strong coding and reasoning abilities",
        "use_case": "Multilingual and coding",
        "size": "~4.4GB",
        "category": "general",
    },
    {
        "name": "deepseek-coder:6.7b",
        "description": "Specialized coding model with excellent programming capabilities",
        "use_case": "Advanced coding tasks",
        "size": "~3.8GB",
        "category": "coding",
    },
    {
        "name": "neural-chat:7b",
        "description": "Fine-tuned for conversational AI with natural dialogue flow",
        "use_case": "Natural conversations",
        "size": "~4.1GB",
        "category": "chat",
    },
]


def get_models_by_category():
    """Group recommended models by category."""
    categories = {}
    for model in RECOMMENDED_MODELS:
        category = model["category"]
        if category not in categories:
            categories[category] = []
        categories[category].append(model)
    return categories
