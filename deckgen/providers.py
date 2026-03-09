"""LLM provider abstraction — auto-detects available backends."""

import json
import os
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional


@dataclass
class Message:
    role: str  # "system", "user", "assistant"
    content: str


class LLMProvider(ABC):
    """Base class for LLM providers."""

    @abstractmethod
    def chat(self, messages: list[Message], temperature: float = 0.7) -> str:
        """Send messages and return the assistant's response text."""
        ...

    @abstractmethod
    def name(self) -> str:
        ...


class OpenAIProvider(LLMProvider):
    """OpenAI or Azure OpenAI provider."""

    def __init__(self, model: str = "gpt-4o", api_key: Optional[str] = None,
                 base_url: Optional[str] = None, api_version: Optional[str] = None,
                 use_azure_ad: bool = False):
        try:
            from openai import OpenAI, AzureOpenAI
        except ImportError:
            raise ImportError("Install openai: pip install openai")

        self.model = model

        # Azure OpenAI
        if base_url and "openai.azure.com" in base_url:
            azure_endpoint = base_url or os.getenv("AZURE_OPENAI_ENDPOINT")
            azure_api_version = api_version or os.getenv("AZURE_OPENAI_API_VERSION", "2024-10-21")
            resolved_key = api_key or os.getenv("AZURE_OPENAI_API_KEY")

            # Use Azure AD token auth if no API key or explicitly requested
            if use_azure_ad or not resolved_key:
                try:
                    from azure.identity import DefaultAzureCredential, get_bearer_token_provider
                    credential = DefaultAzureCredential()
                    token_provider = get_bearer_token_provider(
                        credential, "https://cognitiveservices.azure.com/.default"
                    )
                    self.client = AzureOpenAI(
                        azure_ad_token_provider=token_provider,
                        azure_endpoint=azure_endpoint,
                        api_version=azure_api_version,
                    )
                except ImportError:
                    raise ImportError(
                        "Install azure-identity for AAD auth: pip install azure-identity"
                    )
            else:
                self.client = AzureOpenAI(
                    api_key=resolved_key,
                    azure_endpoint=azure_endpoint,
                    api_version=azure_api_version,
                )
        else:
            # Standard OpenAI
            self.client = OpenAI(
                api_key=api_key or os.getenv("OPENAI_API_KEY"),
                base_url=base_url,
            )

    def chat(self, messages: list[Message], temperature: float = 0.7) -> str:
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": m.role, "content": m.content} for m in messages],
            temperature=temperature,
        )
        return response.choices[0].message.content

    def name(self) -> str:
        return f"OpenAI ({self.model})"


class AnthropicProvider(LLMProvider):
    """Anthropic Claude provider."""

    def __init__(self, model: str = "claude-sonnet-4-20250514", api_key: Optional[str] = None):
        try:
            import anthropic
        except ImportError:
            raise ImportError("Install anthropic: pip install anthropic")

        self.model = model
        self.client = anthropic.Anthropic(
            api_key=api_key or os.getenv("ANTHROPIC_API_KEY"),
        )

    def chat(self, messages: list[Message], temperature: float = 0.7) -> str:
        # Separate system message from conversation
        system = ""
        conversation = []
        for m in messages:
            if m.role == "system":
                system = m.content
            else:
                conversation.append({"role": m.role, "content": m.content})

        response = self.client.messages.create(
            model=self.model,
            max_tokens=8192,
            system=system,
            messages=conversation,
            temperature=temperature,
        )
        return response.content[0].text

    def name(self) -> str:
        return f"Anthropic ({self.model})"


class OllamaProvider(LLMProvider):
    """Ollama local provider — no API key needed."""

    def __init__(self, model: str = "llama3.1", base_url: str = "http://localhost:11434"):
        self.model = model
        self.base_url = base_url

    def chat(self, messages: list[Message], temperature: float = 0.7) -> str:
        import urllib.request

        payload = json.dumps({
            "model": self.model,
            "messages": [{"role": m.role, "content": m.content} for m in messages],
            "stream": False,
            "options": {"temperature": temperature},
        }).encode()

        req = urllib.request.Request(
            f"{self.base_url}/api/chat",
            data=payload,
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req, timeout=120) as resp:
            data = json.loads(resp.read())
        return data["message"]["content"]

    def name(self) -> str:
        return f"Ollama ({self.model})"


def auto_detect_provider() -> LLMProvider:
    """Auto-detect the first available LLM provider from environment."""

    # 1. Azure OpenAI (with API key)
    if os.getenv("AZURE_OPENAI_ENDPOINT") and os.getenv("AZURE_OPENAI_API_KEY"):
        model = os.getenv("AZURE_OPENAI_MODEL", "gpt-4o")
        return OpenAIProvider(
            model=model,
            base_url=os.getenv("AZURE_OPENAI_ENDPOINT"),
            api_key=os.getenv("AZURE_OPENAI_API_KEY"),
        )

    # 2. Azure OpenAI (with Azure AD / Entra ID auth — no API key needed)
    if os.getenv("AZURE_OPENAI_ENDPOINT"):
        model = os.getenv("AZURE_OPENAI_MODEL", "gpt-4o")
        return OpenAIProvider(
            model=model,
            base_url=os.getenv("AZURE_OPENAI_ENDPOINT"),
            use_azure_ad=True,
        )

    # 2. OpenAI
    if os.getenv("OPENAI_API_KEY"):
        return OpenAIProvider()

    # 3. Anthropic
    if os.getenv("ANTHROPIC_API_KEY"):
        return AnthropicProvider()

    # 4. Ollama (check if running)
    try:
        import urllib.request
        req = urllib.request.Request("http://localhost:11434/api/tags")
        with urllib.request.urlopen(req, timeout=2):
            return OllamaProvider()
    except Exception:
        pass

    raise RuntimeError(
        "No LLM provider found. Set one of:\n"
        "  AZURE_OPENAI_ENDPOINT + AZURE_OPENAI_API_KEY\n"
        "  OPENAI_API_KEY\n"
        "  ANTHROPIC_API_KEY\n"
        "  Or start Ollama: ollama serve"
    )
