"""HTTP client for Ollama API communication."""

from typing import Dict, Any, Optional, AsyncGenerator
import httpx
from app.config import settings


class OllamaProxy:
    """Proxy client for Ollama API."""

    def __init__(self):
        self.base_url = settings.ollama_base_url.rstrip("/")
        self.timeout = settings.ollama_timeout
        self.client = httpx.AsyncClient(timeout=self.timeout)

    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()

    async def chat(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Send chat request to Ollama.

        Args:
            payload: Chat request payload

        Returns:
            Ollama response
        """
        url = f"{self.base_url}/api/chat"
        response = await self.client.post(url, json=payload)
        response.raise_for_status()
        return response.json()

    async def chat_stream(self, payload: Dict[str, Any]) -> AsyncGenerator[bytes, None]:
        """
        Stream chat response from Ollama.

        Args:
            payload: Chat request payload

        Yields:
            Response chunks
        """
        url = f"{self.base_url}/api/chat"
        async with self.client.stream("POST", url, json=payload) as response:
            response.raise_for_status()
            async for chunk in response.aiter_bytes():
                yield chunk

    async def generate(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Send generation request to Ollama.

        Args:
            payload: Generation request payload

        Returns:
            Ollama response
        """
        url = f"{self.base_url}/api/generate"
        response = await self.client.post(url, json=payload)
        response.raise_for_status()
        return response.json()

    async def generate_stream(self, payload: Dict[str, Any]) -> AsyncGenerator[bytes, None]:
        """
        Stream generation response from Ollama.

        Args:
            payload: Generation request payload

        Yields:
            Response chunks
        """
        url = f"{self.base_url}/api/generate"
        async with self.client.stream("POST", url, json=payload) as response:
            response.raise_for_status()
            async for chunk in response.aiter_bytes():
                yield chunk

    async def embeddings(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate embeddings via Ollama.

        Tries /api/embed first (new API), falls back to /api/embeddings (old API).

        Args:
            payload: Embedding request payload with 'model' and 'input' or 'prompt'

        Returns:
            Ollama response with embeddings
        """
        # Convert legacy 'prompt' field to new 'input' field
        if "prompt" in payload and "input" not in payload:
            payload["input"] = payload.pop("prompt")

        # Try new /api/embed endpoint first
        try:
            url = f"{self.base_url}/api/embed"
            response = await self.client.post(url, json=payload)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                # Fall back to old /api/embeddings endpoint
                old_payload = {
                    "model": payload["model"],
                    "prompt": payload.get("input", "") if isinstance(payload.get("input"), str) else payload.get("input", [""])[0]
                }
                url = f"{self.base_url}/api/embeddings"
                response = await self.client.post(url, json=old_payload)
                response.raise_for_status()
                result = response.json()
                # Normalize old format to new format
                if "embedding" in result and "embeddings" not in result:
                    result["embeddings"] = [result.pop("embedding")]
                return result
            raise

    async def list_models(self) -> Dict[str, Any]:
        """
        List available models from Ollama.

        Returns:
            Models list
        """
        url = f"{self.base_url}/api/tags"
        response = await self.client.get(url)
        response.raise_for_status()
        return response.json()

    async def show_model(self, model_name: str) -> Dict[str, Any]:
        """
        Get model information.

        Args:
            model_name: Name of the model

        Returns:
            Model details
        """
        url = f"{self.base_url}/api/show"
        response = await self.client.post(url, json={"name": model_name})
        response.raise_for_status()
        return response.json()

    async def running_models(self) -> Dict[str, Any]:
        """
        Get currently running models.

        Returns:
            Running models list
        """
        url = f"{self.base_url}/api/ps"
        response = await self.client.get(url)
        response.raise_for_status()
        return response.json()

    async def health_check(self) -> bool:
        """
        Check if Ollama is reachable.

        Returns:
            True if healthy, False otherwise
        """
        try:
            url = f"{self.base_url}/"
            response = await self.client.get(url)
            return response.status_code == 200
        except Exception:
            return False

    async def raw_request(
            self,
            endpoint: str,
            method: str = "POST",
            payload: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Make raw request to Ollama API.

        Args:
            endpoint: API endpoint (e.g., "/api/generate")
            method: HTTP method
            payload: Request payload

        Returns:
            Ollama response
        """
        url = f"{self.base_url}{endpoint}"

        if method.upper() == "GET":
            response = await self.client.get(url)
        else:
            response = await self.client.post(url, json=payload or {})

        response.raise_for_status()
        return response.json()


# Global instance
ollama_proxy = OllamaProxy()