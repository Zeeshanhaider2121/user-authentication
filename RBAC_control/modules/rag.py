import os
from dotenv import load_dotenv
import logging
# Load environment variables (if needed)
load_dotenv()
# Core imports for Neo4j integration and vector stores
from langchain_community.graphs import Neo4jGraph
from langchain_community.vectorstores.neo4j_vector import Neo4jVector
# LangChain chains, prompts, and text splitters
from langchain.chains import (
    RetrievalQA,
    GraphCypherQAChain,
    RetrievalQAWithSourcesChain,
    StuffDocumentsChain,
    create_retrieval_chain
)
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.prompts import ChatPromptTemplate

# Chat models and embeddings
from langchain_ollama import OllamaEmbeddings
from langchain_community.chat_models import ChatOllama
from langchain_experimental.llms.ollama_functions import OllamaFunctions
# Document loading
from langchain_community.document_loaders import TextLoader
# Neo4j Python driver (if direct driver access is required)
from neo4j import GraphDatabase
# Set up logging
logger = logging.getLogger(__name__)
from langchain_community.chat_models import ChatOllama
from modules.doc_processing import DocumentProcessor  # Import the DocumentProcessor class
import os
#rom dotenv import load_dotenv
from langchain_experimental.llms.ollama_functions import OllamaFunctions
from langchain.chains import RetrievalQAWithSourcesChain
# Load environment variables
#oad_dotenv()

# Neo4j configurations
NEO4J_BOLT_URL = os.getenv("NEO4J_BOLT_URL")
#NEO4J_USERNAME = os.getenv("NEO4J_USERNAME")
#NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")
#NEO4J_DATABASE = os.getenv("NEO4J_DATABASE")


class RAGWithRoles:
    def __init__(self, roles,username,password,database):
        self.roles = roles
        self.username = username
        self.password = password
        self.database = database

        self.graph = Neo4jGraph(
            url=NEO4J_BOLT_URL,
            username=username,
            password=password,
            database=database,
        )

        # Instantiate the ChatOllama model with local URL
        #local_url = "http://localhost:11411"  # Change if Ollama runs on a different port
        #self.llm = OllamaFunctions(model="llama3.1", temperature=0, format="json")
        self.llm = OllamaFunctions(model="llama3.1", temperature=0, format="json", base_url="https://9655-2407-d000-1a-1595-b0db-fb0b-65ed-a470.ngrok-free.app/")

        # Initialize DocumentProcessor with the same graph and LLM
        self.document_processor = DocumentProcessor(graph=self.graph, llm=self.llm)

        # Flag to track if access is denied after querying
        self.access_denied = False

    def can_add_documents(self):
        return "admin" in self.roles

    def can_query_graph(self):
        return "reader" in self.roles or "admin" in self.roles

    def check_document_access(self, document_id):
        """Check if the user has access to a specific document."""
        if "restrictedAccessRole" in self.roles:
            return False  # Block access
        return True  # Allow access

    def add_documents(self):
        """Ingest new documents into the Neo4j graph."""
        if not self.can_add_documents():
            print("Access Denied: Insufficient permissions to add documents.")
            return

        # Delegate document ingestion to the DocumentProcessor class
        document_path = "C:\\Users\\Admin\\Downloads\\ollama\\GraphRAG-with-Llama-3.1\\documents"
        new_documents = self.document_processor.process_new_documents(document_path)

        # Update Neo4j graph with the new documents
        if new_documents:
            self.document_processor.update_graph_with_new_documents(new_documents)
        else:
            print("No new documents to process.")

    def retrieval_qa(self):
        """Perform retrieval-based QA with sources."""
        # Check if user has already been denied access before
        if self.access_denied:
            print("Access Denied: You cannot query the system after previous access denial.")
            return {"result": "Access Denied: You cannot query the system after previous access denial."}

        # Let the user enter the query
        #query = input("Enter your QA query: ")

        # If access is restricted, deny access after the query
        if "restrictedAccessRole" in self.roles:
            self.access_denied = True  # Deny access after this query
            print("Access Denied: You do not have access to this document.")
            return {"result": "Access Denied: You do not have access to this document."}

        # Initialize embeddings and Neo4j vector search
       # embeddings = OllamaEmbeddings(model="mxbai-embed-large")

        print(f"User roles for QA: {self.roles}")
        """
        print(f"User  for QA: {self.graph}")
        print("Vector Index Credentials:")   
        print("Vector Index Credentials:")
        print(f"  URL: {NEO4J_BOLT_URL}")
        print(f"  Username: {username}")
        print(f"  Password: {'*' * len(password)}")
        print(f"  Database: {database}") """
                                        
   
        embeddings = OllamaEmbeddings( model="mxbai-embed-large", base_url="https://9655-2407-d000-1a-1595-b0db-fb0b-65ed-a470.ngrok-free.app/")
        print()
        vector_index = Neo4jVector.from_existing_index(
        embeddings,
        graph=self.graph,
        index_name="chunkVector",
        embedding_node_property="textEmbedding",
        text_node_property="text",
        url=NEO4J_BOLT_URL,
        username=self.username,
        password=self.password,
        database=self.database,
    )
        # Set up the retrieval-based QA system with sources
        retrieval_qa = RetrievalQA.from_chain_type(
               llm=self.llm,  # Use the LLM (e.g., Ollama model)
               chain_type="stuff", 
               verbose=True, # You can customize this chain type
               retriever = vector_index.as_retriever(search_kwargs={"k": 5})
                )
        # Process the query
        query = input("Enter your QA query: ")
        qa_result = retrieval_qa.invoke({"query": query})
        print("QA Result:", qa_result)
        relevant_chunks = qa_result["result"]
        print(relevant_chunks)

