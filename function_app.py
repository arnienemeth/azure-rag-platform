import logging
import os
import tempfile
import azure.functions as func
from azure.core.credentials import AzureKeyCredential
from azure.search.documents import SearchClient
from azure.search.documents.indexes import SearchIndexClient
from azure.search.documents.indexes.models import (
    SearchIndex,
    SimpleField,
    SearchFieldDataType,
    SearchableField,
    SearchField,
    VectorSearch,
    HnswAlgorithmConfiguration,
    VectorSearchProfile
)
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings

# Initialize the Function App
app = func.FunctionApp()
SEARCH_INDEX_NAME = "rag-index"

def ensure_index_exists(endpoint, key, index_name):
    """
    Checks if the search index exists. If not, it creates a new index 
    with vector search configuration.
    """
    try:
        # Authenticate using the API Key
        credential = AzureKeyCredential(key)
        index_client = SearchIndexClient(endpoint=endpoint, credential=credential)
        
        # Check if index exists in the list of index names
        existing_indexes = list(index_client.list_index_names())
        if index_name not in existing_indexes:
            logging.info(f"🛠 Creating new index: {index_name}")
            
            # Configure Vector Search (HNSW Algorithm)
            vector_search = VectorSearch(
                algorithms=[HnswAlgorithmConfiguration(name="my-hnsw-config")],
                profiles=[VectorSearchProfile(name="my-vector-profile", algorithm_configuration_name="my-hnsw-config")]
            )
            
            # Define Index Fields
            fields = [
                SimpleField(name="id", type=SearchFieldDataType.String, key=True),
                SearchableField(name="content", type=SearchFieldDataType.String),
                SimpleField(name="source", type=SearchFieldDataType.String),
                SimpleField(name="page", type=SearchFieldDataType.Int32),
                # Vector field for embeddings (384 dimensions for all-MiniLM-L6-v2)
                SearchField(name="vector", type=SearchFieldDataType.Collection(SearchFieldDataType.Single), 
                            vector_search_dimensions=384, vector_search_profile_name="my-vector-profile")
            ]
            
            # Create the Index
            index = SearchIndex(name=index_name, fields=fields, vector_search=vector_search)
            index_client.create_index(index)
            logging.info(f"✅ Index '{index_name}' created successfully.")
            
    except Exception as e:
        logging.error(f"Error ensuring index exists: {e}")

@app.blob_trigger(arg_name="myblob", path="documents/{name}", connection="AzureWebJobsStorage")
def blob_ingestion_trigger(myblob: func.InputStream):
    """
    Triggered when a new file is uploaded to the 'documents' container.
    Processes the PDF, generates embeddings, and uploads them to Azure AI Search.
    """
    logging.info(f"🚀 Processing file: {myblob.name} ({myblob.length} bytes)")
    
    # Load Environment Variables
    SEARCH_ENDPOINT = os.environ.get("AZURE_SEARCH_ENDPOINT")
    SEARCH_KEY = os.environ.get("AZURE_SEARCH_KEY")

    if not SEARCH_ENDPOINT or not SEARCH_KEY:
        logging.error("❌ ERROR: Missing AZURE_SEARCH_ENDPOINT or AZURE_SEARCH_KEY in application settings.")
        return

    # Only process PDF files
    if not myblob.name.lower().endswith(".pdf"):
        logging.info("File is not a PDF. Skipping.")
        return

    temp_path = None
    try:
        # 1. Save Blob to a Temporary File
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_pdf:
            temp_pdf.write(myblob.read())
            temp_path = temp_pdf.name

        # 2. Load PDF Content
        loader = PyPDFLoader(temp_path)
        pages = loader.load()
        logging.info(f"📄 Loaded {len(pages)} pages.")

        # 3. Split Text into Chunks
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
        docs = text_splitter.split_documents(pages)
        logging.info(f"✂️ Created {len(docs)} text chunks.")

        # 4. Generate Embeddings
        logging.info("🧠 Generating vectors (embeddings)...")
        # Using a lightweight local model suitable for free tier/testing
        embedding_model = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
        
        search_documents = []
        for idx, doc in enumerate(docs):
            vector = embedding_model.embed_query(doc.page_content)
            
            # Create a safe ID (Azure Search keys allow limited characters)
            file_name = os.path.basename(myblob.name)
            safe_id = f"{file_name}-{idx}".replace(".", "-").replace(" ", "-").replace("_", "-")
            
            search_documents.append({
                "id": safe_id,
                "content": doc.page_content,
                "source": myblob.name,
                "page": doc.metadata.get("page", 0),
                "vector": vector
            })

        # 5. Upload to Azure AI Search
        ensure_index_exists(SEARCH_ENDPOINT, SEARCH_KEY, SEARCH_INDEX_NAME)
        
        credential = AzureKeyCredential(SEARCH_KEY)
        search_client = SearchClient(SEARCH_ENDPOINT, SEARCH_INDEX_NAME, credential=credential)
        
        result = search_client.upload_documents(documents=search_documents)
        logging.info(f"✅ Successfully uploaded {len(result)} documents to the index.")

    except Exception as e:
        logging.error(f"❌ ERROR processing blob: {str(e)}")
        
    finally:
        # Cleanup: Remove temporary file
        if temp_path and os.path.exists(temp_path):
            os.remove(temp_path)