import asyncio
import logging
from typing import List, Dict, Any, Optional
import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)


class OllamaClient:
    def __init__(
        self,
        base_url: Optional[str] = None,
        chat_model: Optional[str] = None,
        embed_model: Optional[str] = None,
        timeout: float = 120.0,
    ):
        self.base_url = (base_url or settings.ollama_base_url).rstrip("/")
        self.chat_model = chat_model or settings.ollama_chat_model
        self.embed_model = embed_model or settings.ollama_embed_model
        self.timeout = timeout
        self._async_client: Optional[httpx.AsyncClient] = None
        self._client_loop: Optional[asyncio.AbstractEventLoop] = None
        self._sync_client: Optional[httpx.Client] = None

    def _get_sync_client(self) -> httpx.Client:
        if self._sync_client is None or self._sync_client.is_closed:
            self._sync_client = httpx.Client(
                base_url=self.base_url,
                timeout=self.timeout,
                limits=httpx.Limits(max_keepalive_connections=10, max_connections=20),
            )
        return self._sync_client

    def _get_async_client(self) -> httpx.AsyncClient:
        try:
            current_loop = asyncio.get_running_loop()
        except RuntimeError:
            current_loop = None

        if (
            self._async_client is None
            or self._async_client.is_closed
            or self._client_loop != current_loop
        ):
            self._client_loop = current_loop
            self._async_client = httpx.AsyncClient(
                base_url=self.base_url,
                timeout=self.timeout,
                limits=httpx.Limits(max_keepalive_connections=10, max_connections=20),
            )
        return self._async_client

    def check_health(self) -> Dict[str, Any]:
        """Check if Ollama server is reachable and list models."""
        try:
            client = self._get_sync_client()
            resp = client.get("/api/tags", timeout=5.0)
            if resp.status_code == 200:
                models = [m.get("name") for m in resp.json().get("models", [])]
                return {
                    "status": "healthy",
                    "base_url": self.base_url,
                    "chat_model": self.chat_model,
                    "embed_model": self.embed_model,
                    "available_models": models,
                }
            return {
                "status": "unhealthy",
                "error": f"HTTP {resp.status_code}",
                "base_url": self.base_url,
            }
        except Exception as e:
            logger.warning(f"Ollama health check failed: {e}")
            return {
                "status": "unreachable",
                "error": str(e),
                "base_url": self.base_url,
            }

    async def acheck_health(self) -> Dict[str, Any]:
        """Async check if Ollama server is reachable."""
        try:
            client = self._get_async_client()
            resp = await client.get("/api/tags", timeout=5.0)
            if resp.status_code == 200:
                models = [m.get("name") for m in resp.json().get("models", [])]
                return {
                    "status": "healthy",
                    "base_url": self.base_url,
                    "chat_model": self.chat_model,
                    "embed_model": self.embed_model,
                    "available_models": models,
                }
            return {
                "status": "unhealthy",
                "error": f"HTTP {resp.status_code}",
                "base_url": self.base_url,
            }
        except Exception as e:
            return {
                "status": "unreachable",
                "error": str(e),
                "base_url": self.base_url,
            }

    def generate_embedding(self, text: str, model: Optional[str] = None) -> List[float]:
        """Generate vector embedding for a single text chunk."""
        model_name = model or self.embed_model
        try:
            client = self._get_sync_client()
            payload = {
                "model": model_name,
                "prompt": text,
                "keep_alive": "15m",
            }
            resp = client.post("/api/embeddings", json=payload)
            resp.raise_for_status()
            data = resp.json()
            embedding = data.get("embedding")
            if not embedding:
                raise ValueError(f"No embedding returned for model {model_name}")
            return embedding
        except Exception as e:
            logger.error(f"Error generating embedding with {model_name}: {e}")
            raise

    async def agenerate_embedding(self, text: str, model: Optional[str] = None) -> List[float]:
        """Async generate vector embedding for a single text chunk."""
        model_name = model or self.embed_model
        try:
            client = self._get_async_client()
            payload = {
                "model": model_name,
                "prompt": text,
                "keep_alive": "15m",
            }
            resp = await client.post("/api/embeddings", json=payload)
            resp.raise_for_status()
            data = resp.json()
            embedding = data.get("embedding")
            if not embedding:
                raise ValueError(f"No embedding returned for model {model_name}")
            return embedding
        except Exception as e:
            logger.error(f"Async error generating embedding with {model_name}: {e}")
            raise

    def chat_completion(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: float = 0.2,
        max_tokens: int = 384,
    ) -> Dict[str, Any]:
        """Execute chat completion with Ollama."""
        model_name = model or self.chat_model
        try:
            client = self._get_sync_client()
            payload = {
                "model": model_name,
                "messages": messages,
                "options": {
                    "temperature": temperature,
                    "num_ctx": 2048,
                    "num_predict": max_tokens,
                    "num_thread": 6,
                },
                "keep_alive": "15m",
                "stream": False,
            }
            resp = client.post("/api/chat", json=payload)
            resp.raise_for_status()
            data = resp.json()
            message_data = data.get("message", {})
            return {
                "role": message_data.get("role", "assistant"),
                "content": message_data.get("content", ""),
                "total_duration": data.get("total_duration", 0),
                "eval_count": data.get("eval_count", 0),
            }
        except Exception as e:
            logger.error(f"Error generating chat completion with {model_name}: {e}")
            raise

    async def achat_completion(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: float = 0.2,
        max_tokens: int = 384,
    ) -> Dict[str, Any]:
        """Async chat completion with Ollama."""
        model_name = model or self.chat_model
        try:
            client = self._get_async_client()
            payload = {
                "model": model_name,
                "messages": messages,
                "options": {
                    "temperature": temperature,
                    "num_ctx": 2048,
                    "num_predict": max_tokens,
                    "num_thread": 6,
                },
                "keep_alive": "15m",
                "stream": False,
            }
            resp = await client.post("/api/chat", json=payload)
            resp.raise_for_status()
            data = resp.json()
            message_data = data.get("message", {})
            return {
                "role": message_data.get("role", "assistant"),
                "content": message_data.get("content", ""),
                "total_duration": data.get("total_duration", 0),
                "eval_count": data.get("eval_count", 0),
            }
        except Exception as e:
            logger.error(f"Async error in chat completion with {model_name}: {e}")
            raise


ollama_client = OllamaClient()
