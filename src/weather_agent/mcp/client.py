"""Клієнт для MCP-серверів (JSON-RPC поверх HTTP).

Інкапсулює базовий протокол: list_tools та виклик окремого інструмента.
Конкретний формат методів/параметрів може відрізнятися між MCP-серверами,
тому цей модуль тримає єдиний інтерфейс McpClientBase, який легко мокати.
"""

from __future__ import annotations

import json
import uuid
from dataclasses import dataclass
from typing import Any, Mapping, Protocol

import httpx

from weather_agent.config import MCP_ENDPOINT, MCP_TIMEOUT_SECONDS


class McpClientError(RuntimeError):
    """Помилка при виклику MCP-сервера (мережа, протокол, помилка інструмента)."""


@dataclass(slots=True)
class McpClientConfig:
    """Налаштування MCP-клієнта."""

    endpoint: str
    timeout_seconds: float = MCP_TIMEOUT_SECONDS


class McpClientBase(Protocol):
    """Мінімальний інтерфейс MCP-клієнта для використання та моків у тестах."""

    def list_tools(self) -> list[dict[str, Any]]:  # pragma: no cover - протокол
        ...

    def call_tool(
        self,
        name: str,
        arguments: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:  # pragma: no cover - протокол
        ...


class HttpJsonRpcMcpClient:
    """Проста реалізація MCP-клієнта через JSON-RPC 2.0 поверх HTTP POST.

    Очікується, що MCP-сервер підтримує методи:
    - "tools/list"  без параметрів
    - "tools/call"  з параметрами {"name": <tool_name>, "arguments": {...}}
    """

    def __init__(self, config: McpClientConfig):
        self._config = config

    def _request(self, method: str, params: Mapping[str, Any] | None = None) -> Any:
        if not self._config.endpoint:
            raise McpClientError("MCP endpoint is not configured.")

        payload = {
            "jsonrpc": "2.0",
            "id": str(uuid.uuid4()),
            "method": method,
            "params": params or {},
        }

        try:
            resp = httpx.post(
                self._config.endpoint,
                content=json.dumps(payload),
                headers={"Content-Type": "application/json"},
                timeout=self._config.timeout_seconds,
            )
        except httpx.HTTPError as exc:  # pragma: no cover - мережеві збої важко відтворити
            raise McpClientError(f"MCP network error: {exc!s}") from exc

        try:
            data = resp.json()
        except ValueError as exc:
            raise McpClientError("MCP response is not valid JSON.") from exc

        if "error" in data:
            raise McpClientError(f"MCP error: {data['error']}")

        return data.get("result")

    def list_tools(self) -> list[dict[str, Any]]:
        result = self._request("tools/list")
        if not isinstance(result, list):
            raise McpClientError("MCP tools/list returned unexpected result.")
        return [t for t in result if isinstance(t, dict)]

    def call_tool(
        self,
        name: str,
        arguments: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        params = {"name": name, "arguments": dict(arguments or {})}
        result = self._request("tools/call", params=params)
        if not isinstance(result, dict):
            raise McpClientError("MCP tools/call returned unexpected result.")
        return result


_default_client: McpClientBase | None = None


def get_default_mcp_client() -> McpClientBase:
    """Лінива ініціалізація клієнта за замовчуванням.

    Використовує MCP_ENDPOINT / MCP_TIMEOUT_SECONDS з config.
    У тестах цей клієнт можна підмінити власним за допомогою монкіпатчу.
    """
    global _default_client
    if _default_client is None:
        if not MCP_ENDPOINT:
            raise McpClientError(
                "MCP_ENDPOINT не налаштований. Додайте MCP_ENDPOINT у .env, "
                "якщо хочете використовувати MCP-інструменти (наприклад календар)."
            )
        cfg = McpClientConfig(endpoint=MCP_ENDPOINT, timeout_seconds=MCP_TIMEOUT_SECONDS)
        _default_client = HttpJsonRpcMcpClient(cfg)
    return _default_client


def set_default_mcp_client(client: McpClientBase | None) -> None:
    """Підміняє клієнт за замовчуванням (зручно для тестів)."""
    global _default_client
    _default_client = client

