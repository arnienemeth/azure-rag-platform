# azure-rag-platform

# ☁️ Azure Serverless RAG Platform

![Azure](https://img.shields.io/badge/azure-%230072C6.svg?style=for-the-badge&logo=microsoftazure&logoColor=white)
![Python](https://img.shields.io/badge/python-3670A0?style=for-the-badge&logo=python&logoColor=ffdd54)
![Streamlit](https://img.shields.io/badge/Streamlit-FF4B4B?style=for-the-badge&logo=Streamlit&logoColor=white)
![LangChain](https://img.shields.io/badge/LangChain-1C3C3C?style=for-the-badge&logo=langchain&logoColor=white)

An Event-Driven **Retrieval-Augmented Generation (RAG)** platform built on Microsoft Azure. This project demonstrates a serverless architecture that automatically processes uploaded PDF documents, converts them into vector embeddings, and enables users to chat with their knowledge base in natural language.

---

## 🏗️ Architecture

The solution uses a **Hub-and-Spoke** event-driven pattern to ensure scalability and cost-efficiency.

```mermaid
graph LR
    User[User] -- Upload PDF --> FE[Streamlit Frontend]
    FE -- Store Blob --> Storage[Azure Blob Storage]
    Storage -- Event Trigger --> Func[Azure Function (Python)]
    Func -- 1. Extract Text --> LangChain[LangChain Splitter]
    LangChain -- 2. Generate Vectors --> Embed[HuggingFace Model]
    Embed -- 3. Index Data --> Search[Azure AI Search]
    User -- Ask Question --> FE
    FE -- Query Vector Index --> Search
    Search -- Return Context --> FE

```

### 🔄 Data Flow

1. **Ingestion:** User uploads a PDF via the Streamlit Interface.
2. **Storage:** The file is saved to an **Azure Storage** container (`documents`).
3. **Trigger:** An **Azure Function** (`blob_trigger`) detects the new file instantly.
4. **Processing:**
* Text is extracted using `PyPDFLoader`.
* Content is chunked into manageable segments.
* Vector embeddings are generated using `sentence-transformers/all-MiniLM-L6-v2`.


5. **Indexing:** The vectors and metadata are stored in **Azure AI Search**.
6. **Retrieval:** The user asks a question, and the system performs a vector search to find the most relevant document sections.

---

## 🛠️ Tech Stack

* **Cloud Provider:** Microsoft Azure
* **Compute:** Azure Functions (Consumption Plan - Serverless)
* **Storage:** Azure Blob Storage (Standard LRS)
* **Database / Search:** Azure AI Search (Vector Store)
* **Backend Logic:** Python 3.x
* **AI Frameworks:** LangChain, HuggingFace Embeddings
* **Frontend:** Streamlit
* **Infrastructure:** Azure CLI

---

## 🚀 Getting Started

Follow these instructions to run the project locally.

### Prerequisites

* Python 3.10+
* [Azure Functions Core Tools](https://github.com/Azure/azure-functions-core-tools)
* [Azure CLI](https://learn.microsoft.com/en-us/cli/azure/install-azure-cli)
* An active Azure Subscription

### 1. Clone the Repository

```bash
git clone [https://github.com/your-username/azure-rag-platform.git](https://github.com/your-username/azure-rag-platform.git)
cd azure-rag-platform/src

```

### 2. Environment Setup

Create a virtual environment and install dependencies:

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt

```

### 3. Azure Configuration

You need to create the following resources in Azure:

1. **Storage Account** (Create a container named `documents`).
2. **Azure AI Search Service**.

Create a `local.settings.json` file in the `src` folder with your credentials:

```json
{
  "IsEncrypted": false,
  "Values": {
    "AzureWebJobsStorage": "YOUR_STORAGE_CONNECTION_STRING",
    "FUNCTIONS_WORKER_RUNTIME": "python",
    "AZURE_SEARCH_ENDPOINT": "YOUR_SEARCH_SERVICE_URL",
    "AZURE_SEARCH_KEY": "YOUR_SEARCH_ADMIN_KEY"
  }
}

```

### 4. Running the Backend (Azure Functions)

Start the local serverless runtime:

```bash
func start

```

*You should see the `blob_ingestion_trigger` loaded successfully.*

### 5. Running the Frontend (Streamlit)

Open a new terminal window and launch the UI:

```bash
streamlit run frontend.py

```

*The application will open in your browser at `http://localhost:8501`.*

---

## 📂 Project Structure

```bash
azure-rag-platform/
│
├── src/
│   ├── function_app.py       # Main Azure Function (Blob Trigger & Logic)
│   ├── frontend.py           # Streamlit UI (Upload & Chat)
│   ├── test_search.py        # Script for testing search queries manually
│   ├── requirements.txt      # Python dependencies
│   └── local.settings.json   # Environment variables (Ignored by Git)
│
└── README.md                 # Project Documentation

```

---

## 🔮 Future Improvements

* [ ] Add OpenAI (GPT-4) integration for summarizing the retrieved answer.
* [ ] Implement "Delete" functionality to remove vectors when a file is deleted.
* [ ] Add Azure Managed Identity for passwordless security.
* [ ] Deploy to Azure Container Apps.

---

## 👤 Author

**Arnold Nemeth**

* LinkedIn:https://www.linkedin.com/in/arnold-n%C3%A9meth-3b482597/
* GitHub: https://github.com/arnienemeth

*Built with ❤️ using Azure & Python.*

```

```
