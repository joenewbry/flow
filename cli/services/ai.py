"""AI service for chat with tool use and streaming."""

import json
from datetime import datetime, timedelta
from typing import Optional, Generator, Callable, Any
from dataclasses import dataclass
from enum import Enum

from cli.config import get_settings
from cli.config.credentials import get_api_key, get_default_provider
from cli.services.database import DatabaseService


class MessageRole(Enum):
    USER = "user"
    ASSISTANT = "assistant"
    TOOL = "tool"


@dataclass
class ToolCall:
    """Represents a tool call from the AI."""
    id: str
    name: str
    arguments: dict


@dataclass
class StreamEvent:
    """Event from streaming response."""
    type: str  # "text", "tool_call", "tool_result", "done", "error"
    content: str = ""
    tool_call: Optional[ToolCall] = None
    tool_result: Optional[str] = None


# Define the tools available to the AI
MEMEX_TOOLS = [
    {
        "name": "search_screenshots",
        "description": "Search through screen capture history using semantic search. Returns OCR text from screenshots that match the query.",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "The search query to find relevant screenshots",
                },
                "start_date": {
                    "type": "string",
                    "description": "Start date for search (ISO format or 'today', 'yesterday', 'last week')",
                },
                "end_date": {
                    "type": "string",
                    "description": "End date for search (ISO format)",
                },
                "limit": {
                    "type": "integer",
                    "description": "Maximum number of results to return (default 10)",
                },
            },
            "required": ["query"],
        },
    },
    {
        "name": "get_activity_stats",
        "description": "Get statistics about screen capture activity for a time period.",
        "input_schema": {
            "type": "object",
            "properties": {
                "period": {
                    "type": "string",
                    "enum": ["today", "yesterday", "week", "month"],
                    "description": "Time period for stats",
                },
            },
            "required": ["period"],
        },
    },
]

# OpenAI format tools
OPENAI_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": tool["name"],
            "description": tool["description"],
            "parameters": tool["input_schema"],
        },
    }
    for tool in MEMEX_TOOLS
]


def parse_date(date_str: str) -> Optional[datetime]:
    """Parse a date string."""
    if not date_str:
        return None

    date_str = date_str.lower().strip()
    now = datetime.now()

    if date_str == "today":
        return now.replace(hour=0, minute=0, second=0, microsecond=0)
    elif date_str == "yesterday":
        return (now - timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
    elif date_str in ["last week", "week"]:
        return now - timedelta(days=7)
    elif date_str in ["last month", "month"]:
        return now - timedelta(days=30)

    try:
        return datetime.fromisoformat(date_str)
    except ValueError:
        return None


def execute_tool(name: str, arguments: dict) -> str:
    """Execute a tool and return the result as a string."""
    db = DatabaseService()

    if name == "search_screenshots":
        query = arguments.get("query", "")
        limit = arguments.get("limit", 10)
        start_date = parse_date(arguments.get("start_date", ""))
        end_date = parse_date(arguments.get("end_date", ""))

        results = db.search(
            query=query,
            limit=limit,
            start_date=start_date,
            end_date=end_date,
        )

        if not results:
            return "No matching screenshots found."

        output = f"Found {len(results)} results:\n\n"
        for i, r in enumerate(results, 1):
            ts = r.timestamp.strftime("%Y-%m-%d %H:%M")
            # Truncate text for readability
            text = r.text[:500] + "..." if len(r.text) > 500 else r.text
            output += f"[{i}] {ts} ({r.screen_name})\n{text}\n\n"

        return output

    elif name == "get_activity_stats":
        period = arguments.get("period", "today")
        now = datetime.now()

        if period == "today":
            start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        elif period == "yesterday":
            start = (now - timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
            now = start + timedelta(days=1)
        elif period == "week":
            start = now - timedelta(days=7)
        elif period == "month":
            start = now - timedelta(days=30)
        else:
            start = now.replace(hour=0, minute=0, second=0, microsecond=0)

        stats = db.get_stats(start_date=start, end_date=now)

        return f"""Activity Stats ({period}):
- Screenshots captured: {stats['captures']}
- Total words extracted: {stats['words']:,}
- Screens used: {', '.join(stats['screens']) if stats['screens'] else 'None'}
- Active hours: {len(stats['hours'])}"""

    return f"Unknown tool: {name}"


class AIService:
    """Service for AI chat with tool use."""

    def __init__(self):
        self.settings = get_settings()
        self.provider = get_default_provider()
        self.messages = []

    def is_configured(self) -> bool:
        """Check if AI is configured."""
        return self.provider is not None

    def get_provider_name(self) -> str:
        """Get human-readable provider name."""
        if self.provider == "anthropic":
            return "Claude"
        elif self.provider == "openai":
            return "GPT-4"
        return "AI"

    def chat_stream(
        self,
        user_message: str,
        on_tool_call: Optional[Callable[[ToolCall], None]] = None,
        on_tool_result: Optional[Callable[[str, str], None]] = None,
    ) -> Generator[StreamEvent, None, None]:
        """Stream a chat response with tool use.

        Args:
            user_message: The user's message
            on_tool_call: Callback when a tool is called
            on_tool_result: Callback when a tool returns (tool_name, result)

        Yields:
            StreamEvent objects for text chunks, tool calls, and completion
        """
        if not self.is_configured():
            yield StreamEvent(type="error", content="No AI provider configured. Run 'memex auth login' first.")
            return

        self.messages.append({"role": "user", "content": user_message})

        try:
            if self.provider == "anthropic":
                yield from self._stream_anthropic(on_tool_call, on_tool_result)
            elif self.provider == "openai":
                yield from self._stream_openai(on_tool_call, on_tool_result)
        except Exception as e:
            yield StreamEvent(type="error", content=str(e))

    def _stream_anthropic(
        self,
        on_tool_call: Optional[Callable],
        on_tool_result: Optional[Callable],
    ) -> Generator[StreamEvent, None, None]:
        """Stream response from Anthropic."""
        import anthropic

        api_key = get_api_key("anthropic")
        client = anthropic.Anthropic(api_key=api_key)

        system_prompt = """You are Memex, a helpful AI assistant with access to the user's screen capture history.
You can search through their screenshots (which have been OCR'd) to help them find information about what they were working on.

When answering questions about the user's activity or trying to find information:
1. Use the search_screenshots tool to find relevant content
2. Use get_activity_stats for general activity questions
3. Summarize findings clearly and cite specific times when relevant

Be concise but thorough. If you can't find something, say so."""

        while True:
            # Convert messages to Anthropic format
            anthropic_messages = []
            for msg in self.messages:
                if msg["role"] == "user":
                    anthropic_messages.append({"role": "user", "content": msg["content"]})
                elif msg["role"] == "assistant":
                    if "tool_calls" in msg:
                        # Message with tool use
                        content = []
                        if msg.get("content"):
                            content.append({"type": "text", "text": msg["content"]})
                        for tc in msg["tool_calls"]:
                            content.append({
                                "type": "tool_use",
                                "id": tc["id"],
                                "name": tc["name"],
                                "input": tc["arguments"],
                            })
                        anthropic_messages.append({"role": "assistant", "content": content})
                    else:
                        anthropic_messages.append({"role": "assistant", "content": msg["content"]})
                elif msg["role"] == "tool":
                    anthropic_messages.append({
                        "role": "user",
                        "content": [{
                            "type": "tool_result",
                            "tool_use_id": msg["tool_call_id"],
                            "content": msg["content"],
                        }],
                    })

            # Stream the response
            collected_text = ""
            tool_calls = []

            with client.messages.stream(
                model=self.settings.anthropic_model,
                max_tokens=4096,
                system=system_prompt,
                messages=anthropic_messages,
                tools=MEMEX_TOOLS,
            ) as stream:
                current_tool_id = None
                current_tool_name = None
                current_tool_input = ""

                for event in stream:
                    if event.type == "content_block_start":
                        if hasattr(event.content_block, "type"):
                            if event.content_block.type == "tool_use":
                                current_tool_id = event.content_block.id
                                current_tool_name = event.content_block.name
                                current_tool_input = ""

                    elif event.type == "content_block_delta":
                        if hasattr(event.delta, "text"):
                            collected_text += event.delta.text
                            yield StreamEvent(type="text", content=event.delta.text)
                        elif hasattr(event.delta, "partial_json"):
                            current_tool_input += event.delta.partial_json

                    elif event.type == "content_block_stop":
                        if current_tool_id and current_tool_name:
                            try:
                                args = json.loads(current_tool_input) if current_tool_input else {}
                            except json.JSONDecodeError:
                                args = {}

                            tool_call = ToolCall(
                                id=current_tool_id,
                                name=current_tool_name,
                                arguments=args,
                            )
                            tool_calls.append(tool_call)
                            yield StreamEvent(type="tool_call", tool_call=tool_call)

                            if on_tool_call:
                                on_tool_call(tool_call)

                            current_tool_id = None
                            current_tool_name = None
                            current_tool_input = ""

            # Save assistant message
            if tool_calls:
                self.messages.append({
                    "role": "assistant",
                    "content": collected_text,
                    "tool_calls": [
                        {"id": tc.id, "name": tc.name, "arguments": tc.arguments}
                        for tc in tool_calls
                    ],
                })

                # Execute tools and add results
                for tc in tool_calls:
                    result = execute_tool(tc.name, tc.arguments)
                    yield StreamEvent(type="tool_result", tool_call=tc, tool_result=result)

                    if on_tool_result:
                        on_tool_result(tc.name, result)

                    self.messages.append({
                        "role": "tool",
                        "tool_call_id": tc.id,
                        "content": result,
                    })

                # Continue the loop to get the final response
                continue
            else:
                self.messages.append({"role": "assistant", "content": collected_text})
                yield StreamEvent(type="done")
                break

    def _stream_openai(
        self,
        on_tool_call: Optional[Callable],
        on_tool_result: Optional[Callable],
    ) -> Generator[StreamEvent, None, None]:
        """Stream response from OpenAI."""
        import openai

        api_key = get_api_key("openai")
        client = openai.OpenAI(api_key=api_key)

        system_prompt = """You are Memex, a helpful AI assistant with access to the user's screen capture history.
You can search through their screenshots (which have been OCR'd) to help them find information about what they were working on.

When answering questions about the user's activity or trying to find information:
1. Use the search_screenshots function to find relevant content
2. Use get_activity_stats for general activity questions
3. Summarize findings clearly and cite specific times when relevant

Be concise but thorough. If you can't find something, say so."""

        while True:
            # Convert messages to OpenAI format
            openai_messages = [{"role": "system", "content": system_prompt}]
            for msg in self.messages:
                if msg["role"] == "user":
                    openai_messages.append({"role": "user", "content": msg["content"]})
                elif msg["role"] == "assistant":
                    if "tool_calls" in msg:
                        openai_messages.append({
                            "role": "assistant",
                            "content": msg.get("content") or None,
                            "tool_calls": [
                                {
                                    "id": tc["id"],
                                    "type": "function",
                                    "function": {
                                        "name": tc["name"],
                                        "arguments": json.dumps(tc["arguments"]),
                                    },
                                }
                                for tc in msg["tool_calls"]
                            ],
                        })
                    else:
                        openai_messages.append({"role": "assistant", "content": msg["content"]})
                elif msg["role"] == "tool":
                    openai_messages.append({
                        "role": "tool",
                        "tool_call_id": msg["tool_call_id"],
                        "content": msg["content"],
                    })

            # Stream the response
            collected_text = ""
            tool_calls = []
            current_tool_calls = {}

            stream = client.chat.completions.create(
                model=self.settings.openai_model,
                messages=openai_messages,
                tools=OPENAI_TOOLS,
                stream=True,
            )

            for chunk in stream:
                delta = chunk.choices[0].delta if chunk.choices else None
                if not delta:
                    continue

                # Handle text content
                if delta.content:
                    collected_text += delta.content
                    yield StreamEvent(type="text", content=delta.content)

                # Handle tool calls
                if delta.tool_calls:
                    for tc in delta.tool_calls:
                        idx = tc.index
                        if idx not in current_tool_calls:
                            current_tool_calls[idx] = {
                                "id": tc.id or "",
                                "name": "",
                                "arguments": "",
                            }

                        if tc.id:
                            current_tool_calls[idx]["id"] = tc.id
                        if tc.function:
                            if tc.function.name:
                                current_tool_calls[idx]["name"] = tc.function.name
                            if tc.function.arguments:
                                current_tool_calls[idx]["arguments"] += tc.function.arguments

            # Process completed tool calls
            for idx in sorted(current_tool_calls.keys()):
                tc_data = current_tool_calls[idx]
                try:
                    args = json.loads(tc_data["arguments"]) if tc_data["arguments"] else {}
                except json.JSONDecodeError:
                    args = {}

                tool_call = ToolCall(
                    id=tc_data["id"],
                    name=tc_data["name"],
                    arguments=args,
                )
                tool_calls.append(tool_call)
                yield StreamEvent(type="tool_call", tool_call=tool_call)

                if on_tool_call:
                    on_tool_call(tool_call)

            # Save assistant message
            if tool_calls:
                self.messages.append({
                    "role": "assistant",
                    "content": collected_text,
                    "tool_calls": [
                        {"id": tc.id, "name": tc.name, "arguments": tc.arguments}
                        for tc in tool_calls
                    ],
                })

                # Execute tools and add results
                for tc in tool_calls:
                    result = execute_tool(tc.name, tc.arguments)
                    yield StreamEvent(type="tool_result", tool_call=tc, tool_result=result)

                    if on_tool_result:
                        on_tool_result(tc.name, result)

                    self.messages.append({
                        "role": "tool",
                        "tool_call_id": tc.id,
                        "content": result,
                    })

                # Continue the loop to get the final response
                continue
            else:
                self.messages.append({"role": "assistant", "content": collected_text})
                yield StreamEvent(type="done")
                break
