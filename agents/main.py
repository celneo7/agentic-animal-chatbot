from langchain_ollama import ChatOllama
from langchain_core.tools import tool, Tool
from typing import TypedDict, Annotated, Sequence
from langchain_core.messages import BaseMessage, SystemMessage, HumanMessage, ToolMessage
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

load_dotenv()


class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], add_messages]

llm = ChatOllama(model='llama3.1', temperature=0.7)
embed_model = OllamaEmbeddings(model="nomic-embed-text")


# load RAG
vectorstore = Chroma(persist_directory=os.curdir + '/rag/rag_db', embedding_function=embed_model,
        collection_name="animals")

retriever = vectorstore.as_retriever(
    search_type="similarity",
    search_kwargs={"k": 1} # amount of chunks to return
)


# define tools of RAG agent
@tool
def retriever_tool(query: str) -> str:
    """
    This tool searches and returns the relevant aspect and information about the animal inquired.
    """

    docs = retriever.invoke(query)

    if not docs:
        return "There is no relevant information regarding the aspect of animal inquired."
    
    seen = set()
    results = []

    for i, doc in enumerate(docs):
        if doc.page_content not in seen:
            results.append(f"Document {i+1}:\n{doc.page_content}")
            seen.add(doc.page_content)
    
    return "\n\n".join(results)


system_prompt = """
    You are an intelligent AI assistant who answers questions about animals possibly loaded into your knowledge base.
    Use the retriever tool available to answer questions about animal. You can make multiple calls if needed.
    If you need to look up some information before asking a follow up question, you are allowed to do that!
    Please always cite the specific parts of the documents you use in your answers.
    """

def rag_agent(state: AgentState) -> AgentState:
    """Function for calling RAG agent and executing tools"""

    curr = list(state['messages'])

    llm = ChatOllama(model='llama3.1', temperature=0.7)
    rag_agent = llm.bind_tools([retriever_tool])
    
    curr = [SystemMessage(content=system_prompt)] + curr
    message = rag_agent.invoke(curr)

    print(f"\n===== RAG Agent =====\n\n{message.content}\n\n{'='*50}\n\n")

    tool_msg = []

    for m in message.tool_calls:
        if m['name'] != retriever_tool.name: # Checks if a valid tool is present
            print(f"\nTool: {m['name']} does not exist.")
        else:
            result = retriever_tool.invoke(m['args'].get('query', ''))
            tool_msg.append(ToolMessage(tool_call_id=m['id'], name=m['name'], content=str(result)))
            print(f"Result : {(str(result))}")

    return {'messages': tool_msg}



# Define API tools
@tool
def get_dog_info() -> str:
   """
   Get Dog facts (only 5 random facts at a time).
   """ 
   data = requests.get("https://dogapi.dog/api/v2/facts?limit=5").json()['data']
   res = []
   for f in data:
       res.append(f['attributes']['body'])
   return ('\n'.join(res))

# web search API
search = GoogleSerperAPIWrapper(serper_api_key=os.environ['SERPER_API_KEY'])

from langchain_community.agent_toolkits.load_tools import load_tools
tools = load_tools(["google-serper"])
# tools = tool + [get_dog_info]

tools = [Tool(
        name="Web Search tool",
        description="Tool that can search the web for information",
        func=search.run
    )]


system_prompt = """
    You are an intelligent AI assistant who fact checks the answer given.
    Use either the Dog Fact API tool or Web Searcher tool available to obtain more information relevant to the question about animal. You can make multiple calls if needed.
    """

def deciding_agent(state: AgentState) -> AgentState:
    """Function to evaluate current context needs additional information"""

    curr = list(state['messages'])
    msgs = [SystemMessage(content=system_prompt)] + curr
    
    llm2 = ChatOllama(model='llama3.1', temperature=0.7)
    deciding_agent = llm2.bind_tools(tools)
    message = deciding_agent.invoke(msgs)

    print(f"===== Deciding Agent =====\n\n{message.content}\n\n{'='*50}\n\n")

    return {'messages': [message]}



def api_agent(state: AgentState) -> AgentState:
    """Function for executing API tool"""

    msgs = list(state['messages'])

    message = msgs[-1]

    tools_dict = {our_tool.name: our_tool for our_tool in tools}

    tool_msg = []

    for m in message.tool_calls:
        if m['name'] not in tools_dict:
            print(f"\nTool: {m['name']} does not exist.")
        else:
            result = tools_dict[m['name']].invoke(m['args'].get('query', ''))
            tool_msg.append(ToolMessage(tool_call_id=m['id'], name=m['name'], content=str(result)))
            print(f"Result : {(str(result))}")

    return {'messages': tool_msg }

system_prompt = """
    You are an AI assistant that generates accurate, concise, and helpful answers. Please give an answer even if repeating what was previously answered.
    """

def answering_agent(state: AgentState) -> AgentState:
    """Function for calling LLM agent to answer question given relevant context"""
    
    llm = ChatOllama(model='llama3.1', temperature=0.7)
    curr = list(state['messages'])    
    msgs = [SystemMessage(content=system_prompt)] + curr
    message = llm.invoke(msgs)

    print(f"===== Answering Agent =====\n\n{message.content}\n\n{'='*50}\n\n")

    return {'messages': [message]}



def next_step(state: AgentState):
    result = state['messages'][-1]
    print(result)

    if len(result.tool_calls) > 0:
   # if "API_CALL" in result.content:
        return "api"
    else:
        return "answer"
    


graph = StateGraph(AgentState)

graph.add_node("rag_agent", rag_agent)
graph.add_node("deciding_agent", deciding_agent)
graph.add_node("api_agent", api_agent)
graph.add_node("answering_agent", answering_agent)


graph.set_entry_point("rag_agent")

graph.add_edge("rag_agent", "deciding_agent")

graph.add_conditional_edges(
    "deciding_agent",
    next_step,
    {'api': "api_agent", 'answer': "answering_agent"}
)

graph.add_edge("api_agent", "deciding_agent")
graph.add_edge("answering_agent", END)


agent_workflow = graph.compile()

def print_stream(stream):
    for s in stream:
        message = s["messages"][-1]
        if isinstance(message, tuple):
            print(message)
        else:
            message.pretty_print()

agent_workflow.invoke({'messages': HumanMessage(input("Enter your question on an animal: "))})