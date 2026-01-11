# agentic-animal-chatbot
Agentic RAG-based chatbot for Q&amp;A on animal facts.

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
