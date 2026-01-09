from langchain_ollama import ChatOllama
from langchain_core.tools import tool, Tool
from typing import TypedDict, Annotated, Sequence, Literal
from langchain_core.messages import BaseMessage, SystemMessage, HumanMessage, ToolMessage, AIMessage
from langgraph.graph.message import add_messages
import requests
from langchain_chroma import Chroma
import sys
sys.path.insert(1, 'C:/Users/Celeste/Documents/Data Science/1-project/agentic-animal-chatbot/') # Add the folder path
from langchain_community.utilities import GoogleSerperAPIWrapper
from dotenv import load_dotenv
from langgraph.graph import StateGraph, END
from langchain_ollama import OllamaEmbeddings
import os
from langchain.agents import create_agent
from pydantic import BaseModel, Field



load_dotenv()

from langchain_community.agent_toolkits.load_tools import load_tools
tools = load_tools(["google-serper"])

# Define API tools
@tool
def get_dog_facts() -> str:
   """
   Get Dog facts (only 5 random facts at a time).
   """ 
   data = requests.get("https://dogapi.dog/api/v2/facts?limit=5").json()['data']
   res = []
   for f in data:
       res.append(f['attributes']['body'])
   return ('\n'.join(res))

# web search API
search = GoogleSerperAPIWrapper()

tools = tools + [get_dog_facts]



class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], add_messages]
    context: str
    question: str
    decision: str

def api_agent(state: AgentState) -> AgentState:
    """Function for executing API tool"""

    system_prompt = f"""
    You are an intelligent AI assistant excellent at identify relevant information and researching for additional information in regards to user's question about an animal.
    Use either Dog Fact API or Web Search tool to provide additional information required.
    You can make multiple tool calls if needed to gather all necessary information.

    Question: {state['question']}
    """

    message = ChatOllama(model='llama3.1', temperature=0.7).bind_tools(tools).invoke([SystemMessage(content=system_prompt), HumanMessage(content=str(state['question']))] )

    tools_dict = {our_tool.name: our_tool for our_tool in tools}

    tool_msg = []

    for m in message.tool_calls:
        if m['name'] not in tools_dict:
            print(f"\nTool: {m['name']} does not exist.")
        else:
            result = tools_dict[m['name']].invoke(m['args'].get('query', ''))
            tool_msg.append(ToolMessage(tool_call_id=m['id'], name=m['name'], content=str(result)))
            #print(f"Result : {(str(result))}")

    return {'messages': [message] + tool_msg}


graph = StateGraph(AgentState)
graph.add_node('api', api_agent)

graph.set_entry_point('api')
graph.set_finish_point('api')


msg = "what are dogs typically like?"

for event in (graph.compile().stream({'question': msg})):
    for node, update in (event.items()):

        response = update['messages']
        for msg in response:
            if isinstance(msg, ToolMessage):
                print(f'Tool Response: {msg.content}\n\n')
            if isinstance(msg, AIMessage):
                if msg.content:
                    print(f'Agent Answer: {msg.content}\n\n')
                if msg.tool_calls:
                    print(f'Tool Called: {msg.tool_calls}\n\n')




