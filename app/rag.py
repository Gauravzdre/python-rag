import os
import chromadb
from langchain_community.document_loaders import TextLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.vectorstores import Chroma
from langchain.embeddings import OpenAIEmbeddings
from langchain_openai import OpenAI
from dotenv import load_dotenv

load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

embeddings = OpenAIEmbeddings(openai_api_key=OPENAI_API_KEY)
vectorstore = Chroma(collection_name="rag-docs", embedding_function=embeddings)

def process_document_upload(file):
    loader = TextLoader(file.file)
    docs = loader.load()
    splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    chunks = splitter.split_documents(docs)
    vectorstore.add_documents(chunks)
    return len(chunks)

async def process_query(query: str):
    retriever = vectorstore.as_retriever(search_kwargs={"k": 5})
    # context = retrieval step
    matches = retriever.get_relevant_documents(query)
    llm = OpenAI(model="gpt-4", openai_api_key=OPENAI_API_KEY)
    answer = llm(question=query, context="\n\n".join(d.page_content for d in matches))
    return {"answer": answer, "sources": [d.metadata for d in matches]}
