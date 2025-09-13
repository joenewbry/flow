"""
Ollama client for Flow CLI
Handles local LLM inference using Ollama
"""

import logging
import requests
import json
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)


class OllamaClient:
    def __init__(self, host: str = "localhost", port: int = 11434):
        self.host = host
        self.port = port
        self.base_url = f"http://{host}:{port}"
        
    def _make_request(self, endpoint: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Make a request to Ollama API."""
        try:
            url = f"{self.base_url}{endpoint}"
            response = requests.post(url, json=data, timeout=120)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Ollama API request failed: {e}")
            raise Exception(f"Ollama API error: {e}")
    
    def generate(self, model: str, prompt: str, system: str = None, stream: bool = False) -> str:
        """Generate text using Ollama model."""
        try:
            data = {
                "model": model,
                "prompt": prompt,
                "stream": stream
            }
            
            if system:
                data["system"] = system
            
            response = self._make_request("/api/generate", data)
            return response.get("response", "")
            
        except Exception as e:
            logger.error(f"Text generation failed: {e}")
            raise
    
    def chat(self, model: str, messages: List[Dict[str, str]], stream: bool = False) -> str:
        """Chat with Ollama model using messages format."""
        try:
            data = {
                "model": model,
                "messages": messages,
                "stream": stream
            }
            
            response = self._make_request("/api/chat", data)
            
            if "message" in response and "content" in response["message"]:
                return response["message"]["content"]
            else:
                return response.get("response", "")
            
        except Exception as e:
            logger.error(f"Chat generation failed: {e}")
            raise
    
    def list_models(self) -> List[Dict[str, Any]]:
        """List available models."""
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=10)
            response.raise_for_status()
            data = response.json()
            return data.get("models", [])
        except Exception as e:
            logger.error(f"Failed to list models: {e}")
            return []
    
    def is_model_available(self, model: str) -> bool:
        """Check if a model is available."""
        models = self.list_models()
        model_names = [model["name"] for model in models]
        return model in model_names or any(model in name for name in model_names)
    
    def health_check(self) -> bool:
        """Check if Ollama service is running."""
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            return response.status_code == 200
        except:
            return False


# Global instance
ollama_client = OllamaClient()
