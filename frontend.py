import streamlit as st
import os
from azure.core.credentials import AzureKeyCredential
from azure.search.documents import SearchClient
from azure.storage.blob import BlobServiceClient
from dotenv import load_dotenv

# --- CONFIGURATION & ENVIRONMENT VARIABLES ---
# Load environment variables from .env file
load_dotenv()

# Retrieve keys securely from environment
STORAGE_CONNECTION_STRING = os.getenv("AZURE_STORAGE_CONNECTION_STRING")
SEARCH_KEY = os.getenv("AZURE_SEARCH_KEY")
SEARCH_ENDPOINT = os.getenv("AZURE_SEARCH_ENDPOINT")

# Constants
CONTAINER_NAME = "documents"
INDEX_NAME = "rag-index"

# --- PAGE SETUP ---
st.set_page_config(page_title="My Enterprise AI", layout="wide")

# Validate that secrets are loaded before proceeding
if not STORAGE_CONNECTION_STRING or not SEARCH_KEY or not SEARCH_ENDPOINT:
    st.error("❌ Missing environment variables! Please check your .env file.")
    st.stop()

st.title("🤖 Enterprise AI Platform")
st.markdown("Upload a document and ask questions based on its content.")

# --- SIDEBAR: DOCUMENT UPLOAD ---
with st.sidebar:
    st.header("📂 Upload Document")
    uploaded_file = st.file_uploader("Select PDF file", type=['pdf'])
    
    if uploaded_file is not None:
        if st.button("Upload to Cloud ☁️"):
            try:
                # Initialize Blob Service Client
                blob_service_client = BlobServiceClient.from_connection_string(STORAGE_CONNECTION_STRING)
                blob_client = blob_service_client.get_blob_client(container=CONTAINER_NAME, blob=uploaded_file.name)
                
                # Upload the file
                with st.spinner("Uploading file..."):
                    blob_client.upload_blob(uploaded_file, overwrite=True)
                
                st.success(f"✅ File '{uploaded_file.name}' uploaded successfully! AI is processing it now (wait ~10-20s).")
            
            except Exception as e:
                st.error(f"Upload error: {e}")

# --- MAIN SECTION: CHAT INTERFACE ---
st.subheader("💬 Chat with Documents")

query = st.text_input("What would you like to know?", placeholder="E.g.: What is TraceMonkey?")

if query:
    try:
        # Initialize Search Client
        credential = AzureKeyCredential(SEARCH_KEY)
        client = SearchClient(endpoint=SEARCH_ENDPOINT,
                              index_name=INDEX_NAME,
                              credential=credential)
        
        # Execute Vector/Hybrid Search
        # Note: Ensure your index has a semantic configuration if using semantic search
        results = client.search(search_text=query, top=3)
        
        found = False
        for result in results:
            found = True
            # Display results in an expander
            score = result.get('@search.score', 0)
            source_file = result.get('source', 'Unknown source')
            
            with st.expander(f"📄 Source: {source_file} (Relevance: {score:.2f})", expanded=True):
                st.write(result.get('content', 'No content available'))
        
        if not found:
            st.warning("❌ No relevant information found in the documents.")
            
    except Exception as e:
        st.error(f"Search error: {e}")

# --- FOOTER ---
st.markdown("---")
st.caption("Powered by Azure AI & Python Streamlit")