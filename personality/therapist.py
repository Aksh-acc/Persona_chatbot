import os
from langchain.chat_models import init_chat_model
from langgraph.checkpoint.memory import MemorySaver
from langchain_tavily import TavilySearch
from langgraph.prebuilt import create_react_agent, ToolNode
from langchain_core.messages import SystemMessage
from dotenv import load_dotenv

# Load keys from .env file (RECOMMENDED)
load_dotenv()
print("Tavily key loaded:", bool(os.getenv("TAVILY_API_KEY")))

# Required env vars
os.environ["GOOGLE_API_KEY"] = os.getenv("GOOGLE_API_KEY", "")
os.environ["TAVILY_API_KEY"] = os.getenv("TAVILY_API_KEY", "")

# OPTIONAL: Disable LangSmith to avoid plugin/gRPC header issues
# os.environ["LANGSMITH_TRACING"] = "true"
# os.environ["LANGSMITH_API_KEY"] = os.getenv("LANGSMITH_API_KEY", "")

# Initialize model and tools
llm = init_chat_model("gemini-2.5-flash", model_provider="google_genai")
memory = MemorySaver()
search = TavilySearch(max_results=2)
tools = [search]

model_with_tools = llm.bind_tools(tools)
agent_executor = create_react_agent(llm, tools, checkpointer=memory)
tool_node = ToolNode(tools)

# Therapist persona prompt
therapist_prompt = """
You are Reva, a compassionate AI therapist. You are calm, intuitive, and deeply emotionally intelligent.

You never rush to solutions. Instead, you create a safe space where the user feels heard. You reflect their emotions, validate their experience, and ask reflective questions. Use trauma-informed, non-judgmental language.

When helpful, include links to mental wellness blogs, guided exercises, or affirmations. But never overwhelm — only suggest gently.
"""

# Required generate() for dynamic call from main.py
def generate(state: dict):
    """Receives a dictionary with 'messages' and returns a response in compatible format."""
    conversation_messages = [
        message
        for message in state["messages"]
        if message["role"] in ("user", "system", "assistant")
    ]

    prompt = [SystemMessage(therapist_prompt)]
    for msg in conversation_messages:
        role = msg["role"]
        content = msg["content"]
        prompt.append({"type": role, "content": content})

    response = llm.invoke(prompt)

    return {"messages": [response]}
