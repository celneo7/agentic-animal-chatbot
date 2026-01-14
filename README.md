# Animal Q&A Agentic Chatbot

An **agentic chatbot** for answering questions about animals, built with **React** (frontend) and **Flask** (backend). The system uses **LangGraph agents** and **Retrieval-Augmented Generation (RAG)** to provide accurate, context-aware responses.

## Architecture

```
React Frontend
      ↓
   Flask API
      ↓
LangGraph Agent
      ↓
Retriever (Vector DB)
      ↓
 Animal Knowledge Base
```

## 📦 Setup

1. Set up RAG 
``` bash
python3 data/web_scrape.py
python3 rag/create_rag.py
```

2. Initialise Agents

3. Run backend
``` bash
flask --app backend/app run
```

4. Run frontend
``` bash
cd frontend
npm start
```

## How It Works

1. User asks a question about animals.
2. Flask sends the query to a LangGraph agent.
3. The agent retrieves relevant documents via RAG.
4. The LLM generates a grounded, coherent answer.
5. Response is streamed back to the React UI.

## Example Questions

* “What do wolves eat in the wild?”
* “How are reptiles different from mammals?”
* “Tell me about the lifespan of elephants.”

## Future Improvements

* Streaming token-level responses
* Image + text animal queries
* More app features
