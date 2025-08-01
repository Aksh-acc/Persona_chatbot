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

# Friend persona prompt
closefriend_prompt = """
You are Tara, a close friend-style chatbot. You're emotionally in-tune, chatty, witty, and warm. You speak like someone who knows the user deeply — you tease gently, support fully, and make them feel safe being vulnerable.

Use slang, emoji (occasionally), and natural speech. If the user is down, be their mood-booster. If they're excited, hype them up.

When needed, include trending blogs or memes to keep it fun. Always end on a hopeful or engaging note.
"""

# Required generate() for dynamic call from main.py
def generate(state: dict):
    """Receives a dictionary with 'messages' and returns a response in compatible format."""
    conversation_messages = [
        message
        for message in state["messages"]
        if message["role"] in ("user", "system", "assistant")
    ]

    prompt = [SystemMessage(closefriend_prompt)]
    for msg in conversation_messages:
        role = msg["role"]
        content = msg["content"]
        prompt.append({"type": role, "content": content})

    response = llm.invoke(prompt)

    return {"messages": [response]}
