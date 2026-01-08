from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
import os
from langchain_chroma import Chroma
from langchain_ollama import OllamaEmbeddings


animals = ['cat','dog', 'elephant']

corpus = []

# get text data
for a in animals:
    for f in os.listdir(f'./data/{a}'):
        path = f'./data/{a}' + f'/{f}'
        with open(path, "r", encoding="utf-8") as f:
            text = f.read()
       
        corpus.append(
            Document(
                page_content=text,
                metadata={"animal": f'{a}', "source": f'{f}'}
            )
        )



# chunking
text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=300,
    chunk_overlap=100,
    separators=['\n']
)

split_text = text_splitter.split_documents(corpus)

embed_model = OllamaEmbeddings(model="nomic-embed-text")

persist_directory = os.curdir + '/rag/rag_db'
if not os.path.exists(persist_directory):
    os.makedirs(persist_directory)


# create rag DB
try:
    vectorstore = Chroma.from_documents(
        documents=corpus,
        embedding=embed_model,
        persist_directory=persist_directory,
        collection_name="animals"
    )
    print(f"Created ChromaDB vector store")
    
except Exception as e:
    print(f"Error setting up ChromaDB: {str(e)}")
    raise


# retriever 
retriever = vectorstore.as_retriever(
    search_type="similarity",
    search_kwargs={"k": 3} # amount of chunks to return
)
