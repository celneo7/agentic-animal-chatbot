from langchain_ollama import ChatOllama
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from langchain_core.tools import tool
from typing import TypedDict, Annotated, Sequence, Literal
from langchain_core.messages import BaseMessage, SystemMessage, HumanMessage, ToolMessage, AIMessage
from langgraph.graph.message import add_messages
import requests
from langchain_chroma import Chroma
from dotenv import load_dotenv
from langchain_community.agent_toolkits.load_tools import load_tools
from langgraph.graph import StateGraph, END
from langchain_ollama import OllamaEmbeddings
import os
from pydantic import BaseModel, Field

load_dotenv()


class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], add_messages]
    context: str
    question: str
    decision: str

llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash-lite", temperature=0.7)
embed_model = GoogleGenerativeAIEmbeddings(model="gemini-embedding-001")


# llm = ChatOllama(model="llama3.1", temperature=0.7)


# load RAG
vectorstore = Chroma(persist_directory=os.curdir + '/rag/rag_db2', embedding_function=embed_model,
        collection_name="animals")

retriever = vectorstore.as_retriever(
    search_type="similarity",
    search_kwargs={"k": 3} # amount of chunks to return
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



def rag_agent(state: AgentState) -> AgentState:
    """Function for calling RAG agent and executing tools"""

    system_prompt = f"""
    You are an intelligent AI assistant who answers questions about animals possibly loaded into your knowledge base.
    Use the retriever tool available to answer questions about animal. You can make multiple calls if needed.
    If you need to look up some information before asking a follow up question, you are allowed to do that!
    Please always cite the specific parts of the documents you use in your answers.

    Question: {state['question']}
    """
    rag_agent = llm.bind_tools([retriever_tool])
    
    message = rag_agent.invoke([SystemMessage(content=system_prompt), HumanMessage(content=str(state['question']))])

    #print(f"\n===== RAG Agent =====\n\n{message.content}\n\n{'='*50}\n\n")

    tool_msg = []
    context = ''

    for m in message.tool_calls:
        if m['name'] != retriever_tool.name: # Checks if a valid tool is present
            print(f"\nTool: {m['name']} does not exist.")
        else:
            result = retriever_tool.invoke(m['args'].get('query', ''))
            context += str(result) + '\n'
            tool_msg.append(ToolMessage(tool_call_id=m['id'], name=m['name'], content=str(result)))
            #print(f"Result : {(str(result))}")

    return {'messages': [message] + tool_msg, 'context': context, 'question': state['question']}



class NextStep(BaseModel):
    '''Next action chosen given current information retrieved'''

    decision: Literal["answer", "api"] = Field(
        description="Next action chosen",
    )
    justification: str = Field(
        description="Reason for action chosen, and what to do next",
    )



def deciding_agent(state: AgentState) -> AgentState:
    """Function to evaluate current context needs additional information"""

    system_prompt = f"""
        You are an intelligent decision maker and evaluator. Your job is to determine the next action needed to answer the user's question.

        Review the user's question and the retrieved context or information carefully. Then decide:

        1. 'answer': Choose this ONLY if the current context contains sufficient, relevant information that directly addresses the user's question.

        2. 'api': Choose this if:
        - The context is relevant but incomplete/insufficient to fully answer the question
        - The context is irrelevant or off-topic (e.g., context about cats when the question is about monkeys)
        - No context has been retrieved yet
        - Additional information is needed from external sources

        When choosing 'api', clearly specify:
        - What information is missing or why current context is insufficient
        - What specific information needs to be retrieved
        - Any search terms or parameters that would help get relevant information

        You can make multiple tool calls if needed to gather all necessary information.

        **Important**: If the current context is completely irrelevant to the question (wrong topic entirely), you MUST choose 'api' to retrieve appropriate information rather than 'answer'.

        Question: {state['question']}
        Current information: {state['context']}
    """
    message = llm.with_structured_output(NextStep).invoke([SystemMessage(content=system_prompt), HumanMessage(content=str(state['question']))])

    # print(f"===== Deciding Agent =====\n\n{message}\n\n{'='*50}\n\n")

    res = f'Decision: {message.decision}.\nJustification & next action: {message.justification}'

    return {'messages': [AIMessage(content=res)], 'decision': message.decision, 'context': state['context'], 'question': state['question']}


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
tools = load_tools(["google-serper"]) + [get_dog_facts]

def api_agent(state: AgentState) -> AgentState:
    """Function for executing API tool"""

    system_prompt = f"""
    You are an intelligent AI assistant excellent at identify relevant information and researching for additional information in regards to user's question about an animal.
    Use either Dog Fact API or Web Search tool to provide additional information required.
    You can make multiple tool calls if needed to gather all necessary information.

    Question: {state['question']}
    Current information: {state['context']}
    """

    message = llm.bind_tools(tools).invoke([SystemMessage(content=system_prompt), HumanMessage(content=str(state['question']))] )

    tools_dict = {our_tool.name: our_tool for our_tool in tools}

    tool_msg = []

    for m in message.tool_calls:
        if m['name'] not in tools_dict:
            print(f"\nTool: {m['name']} does not exist.")
        else:
            result = tools_dict[m['name']].invoke(m['args'].get('query', ''))
            tool_msg.append(ToolMessage(tool_call_id=m['id'], name=m['name'], content=str(result)))
            #print(f"Result : {(str(result))}")

    return {'messages': [message] + tool_msg, 'context': state['context'], 'question': state['question']}



def answering_agent(state: AgentState) -> AgentState:
    """Function for calling LLM agent to answer question given relevant context"""

    system_prompt = f"""
    You are a helpful AI assistant answering a user's question about animals. 

    Use this information: {state['context']}
    """  
    message = llm.invoke([SystemMessage(content=system_prompt), HumanMessage(content=str(state['question']))] )

    # print(f"===== Answering Agent =====\n\n{message.content}\n\n{'='*50}\n\n")

    return {'messages': [message]}



def next_step(state: AgentState):
    return state['decision']


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

msg = "what are cat claws?"
# input("Enter your question on an animal: ")




# for event in (agent_workflow.stream({'question': msg}, stream_mode ='updates')):
#     for node, update in (event.items()):
#         print(node)
#         print(update)

#         response = update['messages']
#         print('='*50)
#         for msg in response:
#             if isinstance(msg, ToolMessage):
#                 print(msg)
#                 print(f'Tool Response: {msg.content}\n\n')
#             if isinstance(msg, AIMessage):
#                 if msg.content:
#                     print(f'Agent Answer: {msg.content}\n\n')


#         print('='*50)