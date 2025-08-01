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

# Professor persona prompt
professor_prompt = """
You are Dr. Neelam Sharma, a highly respected professor in psychology and technology. You blend knowledge and empathy to help people understand what they're going through with logic, evidence, and calm tone.

You use thoughtful language, ask meaningful follow-up questions, and cite relevant research, blogs, or news when necessary.

If the user expresses confusion or emotion, explain the psychological or sociological roots in a gentle, affirming way.
"""

# Required generate() for dynamic call from main.py
def generate(state: dict):
    """Receives a dictionary with 'messages' and returns a response in compatible format."""
    conversation_messages = [
        message
        for message in state["messages"]
        if message["role"] in ("user", "system", "assistant")
    ]

    prompt = [SystemMessage(professor_prompt)]
    for msg in conversation_messages:
        role = msg["role"]
        content = msg["content"]
        prompt.append({"type": role, "content": content})

    response = llm.invoke(prompt)

    return {"messages": [response]}
