from langchain import hub
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_core.output_parsers import JsonOutputParser
from langchain_community.chat_models import ChatOllama
from langchain_core.tools import tool
from typing import TypedDict, Annotated, Sequence
from langchain_core.messages import BaseMessage


llm = ChatOpenAI(model="mistral", api_key="ollama", base_url="http://localhost:11434/v1",)

embed_model = OpenAIEmbeddings(model = "")

@tool
def retrieve_tool(query: str) -> str:
    """
    This tool is used to..
    """
    return


class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], add_messages]

def next_step(state: AgentState):
    return