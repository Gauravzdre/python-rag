"""
Configuration manager for multiple chatbots
"""

import os
import json
from typing import Dict, Any

class ChatbotConfig:
    def __init__(self, config_file: str = "chatbot_config.json"):
        self.config_file = config_file
        self.configs = self.load_configs()
    
    def load_configs(self) -> Dict[str, Any]:
        """Load chatbot configurations"""
        if os.path.exists(self.config_file):
            with open(self.config_file, "r") as f:
                return json.load(f)
        return {}
    
    def save_configs(self):
        """Save chatbot configurations"""
        with open(self.config_file, "w") as f:
            json.dump(self.configs, f, indent=2)
    
    def add_chatbot(self, chatbot_id: str, config: Dict[str, Any]):
        """Add a new chatbot configuration"""
        self.configs[chatbot_id] = {
            "company_name": config.get("company_name"),
            "company_domain": config.get("company_domain"),
            "api_key": config.get("api_key"),
            "jwt_secret": config.get("jwt_secret"),
            "system_prompt": config.get("system_prompt", "You are a helpful assistant."),
            "max_tokens": config.get("max_tokens", 150),
            "model": config.get("model", "meta-llama/llama-3.2-3b-instruct:free"),
            "response_style": config.get("response_style", "helpful"),
            "created_at": "2025-01-05"
        }
        self.save_configs()
        return True
    
    def get_chatbot_config(self, chatbot_id: str) -> Dict[str, Any]:
        """Get chatbot configuration"""
        return self.configs.get(chatbot_id, {})
    
    def update_chatbot_config(self, chatbot_id: str, updates: Dict[str, Any]):
        """Update chatbot configuration"""
        if chatbot_id in self.configs:
            self.configs[chatbot_id].update(updates)
            self.save_configs()
            return True
        return False
    
    def list_chatbots(self) -> List[str]:
        """List all chatbot IDs"""
        return list(self.configs.keys())
    
    def delete_chatbot(self, chatbot_id: str):
        """Delete a chatbot configuration"""
        if chatbot_id in self.configs:
            del self.configs[chatbot_id]
            self.save_configs()
            return True
        return False

# Global instance
config_manager = ChatbotConfig()

