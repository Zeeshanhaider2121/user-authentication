from datetime import datetime
from typing import List, Set
from langchain.docstore.document import Document
from langchain_community.document_loaders import DirectoryLoader
from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_ollama import OllamaEmbeddings
from langchain_community.vectorstores.neo4j_vector import Neo4jVector
from neo4j import GraphDatabase
from dotenv import load_dotenv
import hashlib
import os
from langchain_experimental.llms.ollama_functions import OllamaFunctions
from langchain_experimental.graph_transformers import LLMGraphTransformer
from langchain_community.graphs.graph_document import Node, Relationship
from langchain_community.graphs import Neo4jGraph
import logging

# Initialize logger
logger = logging.getLogger(__name__)
load_dotenv()




from datetime import datetime
from typing import List, Set
from langchain.docstore.document import Document
from langchain_community.document_loaders import DirectoryLoader
from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_ollama import OllamaEmbeddings
from langchain_community.vectorstores.neo4j_vector import Neo4jVector
from neo4j import GraphDatabase
from dotenv import load_dotenv
import hashlib
import os
from langchain_experimental.llms.ollama_functions import OllamaFunctions
from langchain_experimental.graph_transformers import LLMGraphTransformer
from langchain_community.graphs.graph_document import Node, Relationship
# Load environment variables (e.g., Neo4j credentials)
from langchain_community.graphs import Neo4jGraph
import logging
logger = logging.getLogger(__name__)
load_dotenv()
def get_graph_connection():
    """Get Neo4j connection when needed"""
    try:
        return Neo4jGraph(
            url=os.getenv('NEO4J_URI'),
            username=os.getenv('NEO4J_USERNAME'),
            password=os.getenv('NEO4J_PASSWORD')
        )
    except Exception as e:
        logger.error(f"Failed to connect to Neo4j: {e}")
        raise

def clean_text(text: str) -> str:
    """
    Clean text by ensuring only single spaces between words.
    """
    return ' '.join(text.split())
def setup_vector_index(graph):
    """Initialize vector index for document chunks"""
    try:
        graph.query("""
            CREATE VECTOR INDEX `chunkVector`
            IF NOT EXISTS
            FOR (c: Chunk) ON (c.textEmbedding)
            OPTIONS {indexConfig: {
            `vector.dimensions`: 1024,  
            `vector.similarity_function`: 'cosine'
            }};""")
        
        logger.info("Vector index created successfully")
    except Exception as e:
        logger.error(f"Error creating vector index: {e}")
        raise




class DocumentProcessor:
    def __init__(self, graph,llm):
        self.graph = graph
        self.llm=llm
       

    def get_existing_document_hashes(self) -> Set[str]:
        """Retrieve content hashes of documents already in the graph"""
        try:
            result = self.graph.query("""
                MATCH (c:Chunk)
                WHERE c.content_hash IS NOT NULL
                RETURN c.content_hash as hash
            """)
            existing_hashes = {record['hash'] for record in result if record.get('hash')}
            print(f"Found {len(existing_hashes)} existing document hashes")
            return existing_hashes
        except Exception as e:
            print(f"Error fetching existing hashes: {e}")
            return set()

    def process_new_documents(self, user_directory: str) -> List[Document]:
        """Process only new documents from the directory"""
        try:
            existing_hashes = self.get_existing_document_hashes()
            print(f"Retrieved {len(existing_hashes)} existing hashes")

            # Load documents
            documents = load_documents(user_directory)
            new_documents = []

            text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=750,
                chunk_overlap=100,
                length_function=len,
                separators=["\n\n", "\n", " ", ""]
            )

            for doc in documents:
                doc.page_content = clean_text(doc.page_content)
                chunks = text_splitter.create_documents([doc.page_content])

                for i, chunk in enumerate(chunks):
                    chunk_hash = generate_content_hash(chunk.page_content, i)

                    if chunk_hash in existing_hashes:
                        print(f"Skipping existing chunk with hash: {chunk_hash}")
                        continue

                    timestamp = datetime.now().strftime('%Y%m%d%H%M%S%f')
                    document_id = f"{os.path.splitext(doc.metadata['source'])[0]}_{chunk_hash}_{timestamp}_{i}"

                    chunk.metadata = {
                        'id': sanitize_string(document_id),
                        'filename': doc.metadata.get('source', 'untitled'),
                        'page_number': doc.metadata.get('page', 1),
                        'content_hash': chunk_hash,
                        'chunk_index': i,
                        'is_new': True
                    }
                    new_documents.append(chunk)

            print(f"Found {len(new_documents)} new chunks to process")
            return new_documents

        except Exception as e:
            print(f"Error in process_new_documents: {e}")
            raise

    def update_graph_with_new_documents(self, new_documents: List[Document]):
        """Update graph with only new documents and their relationships"""
        try:
            setup_vector_index(self.graph) 
            #embeddings = OllamaEmbeddings(model="mxbai-embed-large")
            #llm = OllamaFunctions(model="llama3.1", temperature=0, format="json")
            #embeddings = OllamaEmbeddings(model="mxbai-embed-large")
            embeddings = OllamaEmbeddings( model="mxbai-embed-large", base_url="https://9655-2407-d000-1a-1595-b0db-fb0b-65ed-a470.ngrok-free.app/")
            
            #llm = OllamaFunctions(model="llama3.1", temperature=0, format="json")
            llm = OllamaFunctions(model="llama3.1", temperature=0, format="json", base_url="https://9655-2407-d000-1a-1595-b0db-fb0b-65ed-a470.ngrok-free.app/")

            transformer = LLMGraphTransformer(llm=llm, node_properties=True)
            processed_count = 0 
            for chunk in new_documents:
                if not chunk.metadata.get('is_new', False):
                    continue

                text = clean_text(chunk.page_content)
            
            # 2️⃣ Generate embeddings using the cleaned text
                chunk_embedding = embeddings.embed_query(text)
                chunk_id = chunk.metadata['id']

                # Insert chunk into the Neo4j graph
                properties = {
                    "filename": chunk.metadata['filename'],
                    "chunk_id": chunk_id,
                    "text":text,
                    "embedding": chunk_embedding,
                    "content_hash": chunk.metadata['content_hash']
                }

                self.graph.query("""
                        MERGE (d:Document {id: $filename})
                        MERGE (c:Chunk {id: $chunk_id})
                        SET c.text = $text,
                            c.content_hash = $content_hash
                        MERGE (d)<-[:PART_OF]-(c)
                        WITH c
                        CALL db.create.setNodeVectorProperty(c, 'textEmbedding', $embedding)
                        RETURN c
                        """, 
                        properties
                    )

                print(f"Extracting graph data for chunk: {chunk_id}")
                text = clean_text(chunk.page_content)
                documents = [Document(page_content=text)]
                print("these are documents bullaaaa" , documents)

                # Process relationships using LLM
                graph_docs = transformer.convert_to_graph_documents(documents)
                print("these are graph_docs bullaaaa" , graph_docs)
                #self.graph.add_graph_documents(graph_docs, baseEntityLabel=True, include_source=True)
                    
                for graph_doc in graph_docs:
                        chunk_node = Node(
                            id=chunk_id,
                            type="Chunk"
                        )
                        
                        for node in graph_doc.nodes:
                            graph_doc.relationships.append(
                                Relationship(
                                    source=chunk_node,
                                    target=node,
                                    type="HAS_ENTITY"
                                )
                            )
                        
                        self.graph.add_graph_documents([graph_doc])
                        print(f"Added graph relationships for chunk: {chunk_id}")

                chunk.metadata['is_new'] = False
                processed_count += 1
                if processed_count % 10 == 0:
                        print(f"Progress: Processed {processed_count}/{len(new_documents)} chunks")                
        except Exception as e:
            print(f"Error updating graph: {e}")
            raise


def load_documents(user_directory: str) -> List[Document]:
    """Load PDF documents from the directory"""
    try:
        loader = DirectoryLoader(user_directory, glob="*.pdf", loader_cls=PyPDFLoader)
        documents = loader.load()
        print(f"Loaded {len(documents)} documents from {user_directory}")
        return documents
    except Exception as e:
        print(f"Error loading documents: {e}")
        raise


def generate_content_hash(content: str, chunk_index: int) -> str:
    """Generate a unique hash for the document content"""
    unique_content = f"{content}{chunk_index}"
    return hashlib.sha256(unique_content.encode()).hexdigest()[:16]


def sanitize_string(value: str) -> str:
    """Sanitize a string to remove special characters"""
    return ''.join(e for e in value if e.isalnum() or e in ("_", "-"))

