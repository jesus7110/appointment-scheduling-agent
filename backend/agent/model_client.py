"""
Provider-agnostic LLM client for the appointment scheduling agent.

This module provides a unified interface to interact with various LLM providers
(OpenAI, Google Gemini, Anthropic Claude, etc.) without vendor lock-in.

To switch providers, simply change the LLM_PROVIDER and LLM_MODEL environment variables.
"""
import os
from typing import List, Dict, Optional, Any
from dotenv import load_dotenv
import litellm
from litellm import completion

# Load environment variables
load_dotenv()

# Configure LiteLLM
litellm.set_verbose = os.getenv("LITELLM_VERBOSE", "false").lower() == "true"


class ModelClient:
    """
    Provider-agnostic LLM client wrapper.
    
    Supports multiple providers through LiteLLM:
    - OpenAI: gpt-4, gpt-3.5-turbo, etc.
    - Google AI Studio (Gemini API): gemini-2.0-flash, gemini-pro, etc.
      (Uses Google AI Studio API, NOT Vertex AI - only requires API key)
    - Anthropic: claude-3-5-sonnet, claude-3-opus, etc.
    - Groq: llama-3.3-70b-versatile, mixtral-8x7b-32768, etc.
    - And many more...
    
    Environment variables:
        LLM_PROVIDER: Provider name (e.g., "openai", "google", "anthropic", "groq")
        LLM_MODEL: Model identifier (e.g., "gpt-4o-mini", "gemini-2.0-flash", "llama-3.3-70b-versatile")
                     For Google models, the "gemini/" prefix is automatically added if missing
                     For Groq models, use "groq/" prefix (e.g., "groq/llama-3.3-70b-versatile")
        LLM_API_KEY: API key for the provider
        LLM_API_VERSION: API version for Google models (default: "v1", can be "v1beta")
        LLM_TEMPERATURE: Temperature for generation (default: 0.7)
        LLM_MAX_TOKENS: Maximum tokens to generate (default: 1000)
    """
    
    def __init__(
        self,
        provider: Optional[str] = None,
        model: Optional[str] = None,
        api_key: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ):
        """
        Initialize the model client.
        
        Args:
            provider: LLM provider (overrides LLM_PROVIDER env var)
            model: Model name (overrides LLM_MODEL env var)
            api_key: API key (overrides LLM_API_KEY env var)
            temperature: Generation temperature (overrides LLM_TEMPERATURE env var)
            max_tokens: Max tokens to generate (overrides LLM_MAX_TOKENS env var)
        """
        self.provider = provider or os.getenv("LLM_PROVIDER", "openai")
        raw_model = model or os.getenv("LLM_MODEL", "gpt-4o-mini")
        self.api_key = api_key or os.getenv("LLM_API_KEY")
        self.temperature = temperature or float(os.getenv("LLM_TEMPERATURE", "0.7"))
        self.max_tokens = max_tokens or int(os.getenv("LLM_MAX_TOKENS", "1000"))
        
        # API version configuration (default to v1 for stability)
        self.api_version = os.getenv("LLM_API_VERSION", "v1")
        
        if not self.api_key:
            raise ValueError(
                "LLM_API_KEY environment variable is required. "
                "Please set it in your .env file or pass it as a parameter."
            )
        
        # Normalize model name for Google models (Gemini or Gemma via Google AI Studio API, NOT Vertex AI)
        # LiteLLM requires "gemini/" prefix for Gemini models to use Google AI Studio API
        # Gemma models should be used as-is (no prefix needed)
        # Without proper prefix, LiteLLM tries to use Vertex AI which requires google-auth
        # We explicitly use Google AI Studio API by:
        # 1. Adding "gemini/" prefix only for Gemini models (not Gemma)
        # 2. Setting GOOGLE_API_KEY (not Vertex AI credentials)
        # 3. Setting GEMINI_API_BASE to control API version (v1 or v1beta)
        if self.provider.lower() in ["google", "gemini"]:
            # Check if it's a Gemma model (starts with "gemma")
            if raw_model.lower().startswith("gemma"):
                # Gemma models: use as-is without prefix
                self.model = raw_model
            # Check if it's a Gemini model or needs gemini/ prefix
            elif not raw_model.startswith("gemini/"):
                # Auto-add gemini/ prefix to ensure Google AI Studio API usage
                self.model = f"gemini/{raw_model}"
            else:
                # Already has gemini/ prefix, use as-is
                self.model = raw_model
            
            # Set GOOGLE_API_KEY for Google AI Studio (not Vertex AI)
            os.environ["GOOGLE_API_KEY"] = self.api_key
            # Set API base URL to control version (v1 is stable, v1beta is beta)
            # This is how LiteLLM determines which API version to use
            os.environ["GEMINI_API_BASE"] = f"https://generativelanguage.googleapis.com/{self.api_version}"
            # Explicitly disable Vertex AI to ensure we use Google AI Studio
            os.environ.pop("GOOGLE_APPLICATION_CREDENTIALS", None)  # Remove if present
        elif self.provider.lower() == "openai":
            self.model = raw_model
            os.environ["OPENAI_API_KEY"] = self.api_key
        elif self.provider.lower() == "anthropic":
            self.model = raw_model
            os.environ["ANTHROPIC_API_KEY"] = self.api_key
        elif self.provider.lower() == "groq":
            # Groq models: add groq/ prefix if not present
            if not raw_model.startswith("groq/"):
                self.model = f"groq/{raw_model}"
            else:
                self.model = raw_model
            os.environ["GROQ_API_KEY"] = self.api_key
        else:
            # For other providers, use model as-is
            self.model = raw_model
            # LiteLLM will use the model name to determine the provider
            os.environ["LITELLM_API_KEY"] = self.api_key
    
    async def generate_chat(
        self,
        messages: List[Dict[str, str]],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        **kwargs: Any
    ) -> str:
        """
        Generate a chat completion.
        
        Args:
            messages: List of message dicts with "role" and "content" keys.
                     Example: [{"role": "user", "content": "Hello"}]
            temperature: Override default temperature for this call
            max_tokens: Override default max_tokens for this call
            **kwargs: Additional parameters to pass to the LLM (e.g., top_p, stream)
        
        Returns:
            The generated text response as a string.
        
        Raises:
            Exception: If the LLM call fails
        """
        try:
            # For Google models, API version is set via GEMINI_API_BASE env var in __init__
            # No need to pass it in extra_params as it's already configured
            response = completion(
                model=self.model,
                messages=messages,
                temperature=temperature or self.temperature,
                max_tokens=max_tokens or self.max_tokens,
                **kwargs
            )
            
            # Extract the content from the response
            if hasattr(response, 'choices') and len(response.choices) > 0:
                return response.choices[0].message.content
            elif isinstance(response, dict) and "choices" in response:
                return response["choices"][0]["message"]["content"]
            else:
                raise ValueError(f"Unexpected response format: {response}")
                
        except Exception as e:
            raise Exception(f"LLM generation failed: {str(e)}") from e
    
    async def generate_chat_stream(
        self,
        messages: List[Dict[str, str]],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        **kwargs: Any
    ):
        """
        Generate a streaming chat completion (generator).
        
        Args:
            messages: List of message dicts with "role" and "content" keys
            temperature: Override default temperature for this call
            max_tokens: Override default max_tokens for this call
            **kwargs: Additional parameters to pass to the LLM
        
        Yields:
            Chunks of the generated text as they arrive.
        """
        try:
            # For Google models, API version is set via GEMINI_API_BASE env var in __init__
            # No need to pass it in extra_params as it's already configured
            response = completion(
                model=self.model,
                messages=messages,
                temperature=temperature or self.temperature,
                max_tokens=max_tokens or self.max_tokens,
                stream=True,
                **kwargs
            )
            
            for chunk in response:
                if hasattr(chunk, 'choices') and len(chunk.choices) > 0:
                    delta = chunk.choices[0].delta
                    if hasattr(delta, 'content') and delta.content:
                        yield delta.content
                elif isinstance(chunk, dict) and "choices" in chunk:
                    delta = chunk["choices"][0].get("delta", {})
                    content = delta.get("content", "")
                    if content:
                        yield content
                        
        except Exception as e:
            raise Exception(f"LLM streaming failed: {str(e)}") from e
    
    async def generate_chat_with_tools(
        self,
        messages: List[Dict[str, str]],
        tools: List[Dict[str, Any]],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        **kwargs: Any
    ) -> Dict[str, Any]:
        """
        Generate a chat completion with tool calling support.
        
        Args:
            messages: List of message dicts with "role" and "content" keys
            tools: List of tool definitions in OpenAI format
            temperature: Override default temperature
            max_tokens: Override default max_tokens
            **kwargs: Additional parameters
        
        Returns:
            Dict with 'content' (str) and optional 'tool_calls' (list)
        
        Raises:
            Exception: If the LLM call fails
        """
        try:
            response = completion(
                model=self.model,
                messages=messages,
                tools=tools,
                tool_choice="auto",  # Let LLM decide when to use tools
                temperature=temperature or self.temperature,
                max_tokens=max_tokens or self.max_tokens,
                **kwargs
            )
            
            # Extract the response
            if hasattr(response, 'choices') and len(response.choices) > 0:
                choice = response.choices[0]
                message = choice.message
                
                result = {}
                
                # Get text content
                if hasattr(message, 'content') and message.content:
                    result['content'] = message.content
                else:
                    result['content'] = ""
                
                # Get tool calls if present
                if hasattr(message, 'tool_calls') and message.tool_calls:
                    result['tool_calls'] = []
                    for tool_call in message.tool_calls:
                        result['tool_calls'].append({
                            'id': tool_call.id,
                            'type': tool_call.type,
                            'function': {
                                'name': tool_call.function.name,
                                'arguments': tool_call.function.arguments
                            }
                        })
                
                return result
                
            elif isinstance(response, dict) and "choices" in response:
                choice = response["choices"][0]
                message = choice.get("message", {})
                
                result = {
                    'content': message.get("content", "")
                }
                
                if "tool_calls" in message:
                    result['tool_calls'] = message["tool_calls"]
                
                return result
                
            else:
                raise ValueError(f"Unexpected response format: {response}")
                
        except Exception as e:
            raise Exception(f"LLM generation with tools failed: {str(e)}") from e
    
    def get_model_info(self) -> Dict[str, Any]:
        """
        Get information about the current model configuration.
        
        Returns:
            Dictionary with model configuration details.
        """
        return {
            "provider": self.provider,
            "model": self.model,
            "api_version": self.api_version if self.provider.lower() in ["google", "gemini"] else None,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "api_key_set": bool(self.api_key),
        }


# Global instance (lazy initialization)
_client_instance: Optional[ModelClient] = None


def get_model_client() -> ModelClient:
    """
    Get or create the global model client instance.
    
    Returns:
        The global ModelClient instance.
    """
    global _client_instance
    if _client_instance is None:
        _client_instance = ModelClient()
    return _client_instance


def reset_model_client():
    """Reset the global model client instance (useful for testing)."""
    global _client_instance
    _client_instance = None

