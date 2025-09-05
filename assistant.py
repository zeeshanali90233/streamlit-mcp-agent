import asyncio
import json
from fastmcp import Client
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.prebuilt import create_react_agent
from langgraph.checkpoint.memory import InMemorySaver
from langchain.tools import BaseTool

client = Client("http://localhost:8000/mcp")

async def call_mcp_tool(tool_name: str, **kwargs):
    async with client:
        return await client.call_tool(tool_name, kwargs)

async def get_all_tools():
    async with client:
        return await client.list_tools()

# Get available tools
mcp_tools = asyncio.run(get_all_tools())
print(f"Available MCP tools: {[tool.name for tool in mcp_tools]}")

llm = ChatGoogleGenerativeAI(
    google_api_key="AIzaSyA-AxGGObm4t_2dOGhtLx5aYv6AeKjfjfY",
    model="gemini-2.5-flash",
    temperature=0,
)

memory = InMemorySaver()

class MCPTool(BaseTool):
    """Wrapper for an MCP tool to be used in LangGraph ReAct."""
    name: str
    description: str
    mcp_tool_name: str

    class Config:
        arbitrary_types_allowed = True

    def _run(self, tool_input: str) -> str:
        params = json.loads(tool_input)
        print(f"Calling MCP tool '{self.mcp_tool_name}' with params: {params}")
        result = asyncio.run(call_mcp_tool(self.mcp_tool_name, **params))
        return str(result)

    async def _arun(self, tool_input: str) -> str:
        params = json.loads(tool_input)
        result = await call_mcp_tool(self.mcp_tool_name, **params)
        return str(result)

tools = [
    MCPTool(
        name=tool.name,
        description=tool.description,
        mcp_tool_name=tool.name
    )
    for tool in mcp_tools
]

helpful_assistant = create_react_agent(
    model=llm,
    tools=tools,
    checkpointer=memory,
    prompt="You are a helpful assistant."
)
