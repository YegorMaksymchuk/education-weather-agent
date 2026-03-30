"""MCP integration helpers (client + LangChain tools).

Важливо для розробки та навчання:

- Продакшн-агент у `agent.py` **не імпортує** цей пакет. Календар
  підключається через **LangChain Google Calendar Toolkit**
  (`calendar/google_toolkit.py`), а не через MCP.
- Модулі `mcp/client.py` та `mcp/tools.py` потрібні для **опційного** сценарію:
  LangChain tools, що ходять на ваш MCP-сервер по HTTP JSON-RPC. Щоб вони
  працювали, у `.env` має бути **`MCP_ENDPOINT`** (інакше `get_default_mcp_client()`
  поверне зрозумілу помилку `McpClientError`).
- Тести (`tests/UnitMock/test_mcp_*.py`, `integration_mcp/`) покривають цей шлях.

Якщо потрібен саме MCP-календар у агенті: додайте інструменти з
`weather_agent.mcp.tools` до списку tools у `create_agent(...)` і налаштуйте
`MCP_ENDPOINT` — або залишайте поточну схему з Google Calendar Toolkit без MCP.
"""

