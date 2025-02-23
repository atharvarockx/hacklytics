import re
import os
import io
import uuid
import requests
import pymongo
from urllib.parse import urlencode

from flask import Flask, request, jsonify, session, redirect
from flask_cors import CORS
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user

from azure.storage.blob import BlobServiceClient
from dotenv import load_dotenv

from google.oauth2 import id_token
from google.auth.transport import requests as google_requests

from pymongo.operations import SearchIndexModel

from llama_index.core import (
    SimpleDirectoryReader,
    VectorStoreIndex,
    StorageContext,
    ServiceContext,
    Document,
    SummaryIndex,
)
from llama_index.core.settings import Settings
from llama_index.core.retrievers import VectorIndexRetriever
from llama_index.core.vector_stores import (
    MetadataFilter,
    MetadataFilters,
    ExactMatchFilter,
    FilterOperator,
)
from llama_index.core.query_engine import (
    RetrieverQueryEngine,
    RouterQueryEngine,
)
from llama_index.core.node_parser import SentenceSplitter
from llama_index.core.tools import QueryEngineTool
from llama_index.core.selectors import (
    LLMSingleSelector,
    LLMMultiSelector,
    PydanticMultiSelector,
    PydanticSingleSelector,
)
from llama_index.llms.azure_openai import AzureOpenAI
from llama_index.embeddings.azure_openai import AzureOpenAIEmbedding
from llama_index.vector_stores.mongodb import MongoDBAtlasVectorSearch

# ============================================================================
# Environment Variables & Configurations
# ============================================================================

# Load environment variables
load_dotenv()

# Keys & API Credentials
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
AZURE_CONNECTION_STRING = os.getenv("AZURE_CONNECTION_STRING")
ATLAS_CONNECTION_STRING = os.getenv("ATLAS_CONNECTION_STRING")

# Azure Endpoint & API Version for LlamaIndex
azure_endpoint = os.getenv("AZURE_ENDPOINT")
api_version = "2023-07-01-preview"

# Flask Secret Key
FLASK_SECRET_KEY = os.getenv("FLASK_SECRET_KEY")

# Google OAuth Redirect URI
REDIRECT_URI = os.getenv("REDIRECT_URI")

# Upload Folder
UPLOAD_FOLDER = "backend/uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# ============================================================================
# Flask App & Extensions Setup
# ============================================================================

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})
app.secret_key = FLASK_SECRET_KEY

login_manager = LoginManager()
login_manager.init_app(app)

# ============================================================================
# In-Memory Stores & User Management
# ============================================================================

# In-memory chat histories and PDF indexes per user
chat_histories = {}  # Format: { user_id: [ {"role": "user"/"assistant", "content": "..."}, ... ] }
pdf_indexes = {}     # Format: { pdf_id: LlamaIndex }

# In-memory user store (for demo purposes)
users = {}

class User(UserMixin):
    def __init__(self, user_id, name, email):
        self.id = user_id
        self.name = name
        self.email = email

@login_manager.user_loader
def load_user(user_id):
    return users.get(user_id)

# Global variable for current user id
global_current_user_id = None

# ============================================================================
# Azure Blob Storage Service
# ============================================================================

class BlobStorageService:
    """Handles file upload and download from Azure Blob Storage."""
    def __init__(self, connection_string):
        if not connection_string:
            raise ValueError("Azure Storage connection string is not configured")
        
        self.blob_service_client = BlobServiceClient.from_connection_string(connection_string)
        containers = list(self.blob_service_client.list_containers())
        if not containers:
            raise ValueError("No containers found in storage account")
        
        self.container_name = containers[0].name
        self.container_client = self.blob_service_client.get_container_client(self.container_name)
        print(f"Connected to container: {self.container_name}")

    def upload_file(self, user_id, file, filename):
        """Upload a file to blob storage under the user's directory."""
        try:
            blob_path = f"{user_id}/{filename}"
            blob_client = self.container_client.get_blob_client(blob_path)
            blob_client.upload_blob(file, overwrite=True)
            return blob_client.url
        except Exception as e:
            raise Exception(f"Upload failed: {str(e)}")

    def download_file(self, user_id, filename):
        """Download a file from blob storage."""
        try:
            blob_path = f"{user_id}/{filename}"
            blob_client = self.container_client.get_blob_client(blob_path)
            if not blob_client.exists():
                raise FileNotFoundError("File not found")
            blob_data = blob_client.download_blob()
            return io.BytesIO(blob_data.readall())
        except Exception as e:
            raise Exception(f"Download failed: {str(e)}")

# Initialize Azure Blob Storage service
try:
    blob_service = BlobStorageService(AZURE_CONNECTION_STRING)
except Exception as e:
    print(f"Failed to initialize Blob Storage Service: {str(e)}")
    raise

# ============================================================================
# Llama Index & MongoDB Atlas Setup
# ============================================================================

# Configure LlamaIndex settings with Azure OpenAI and embedding
Settings.llm = AzureOpenAI(
    model="gpt-4o",
    deployment_name="gpt-4o",
    api_key=OPENAI_API_KEY,
    azure_endpoint=azure_endpoint,
    api_version=api_version,
)

Settings.embed_model = AzureOpenAIEmbedding(
    model="text-embedding-ada-002",
    deployment_name="text-embedding-ada-002",
    api_key=OPENAI_API_KEY,
    azure_endpoint=azure_endpoint,
    api_version=api_version,
)
Settings.chunk_size = 1024
Settings.chunk_overlap = 10

# MongoDB Atlas Connection and Collection
mongo_client = pymongo.MongoClient(ATLAS_CONNECTION_STRING)
atlas_collection = mongo_client["user_data"]["user_data"]

# Instantiate the vector store
atlas_vector_store = MongoDBAtlasVectorSearch(
    mongo_client,
    db_name="user_data",
    collection_name="user_data",
    vector_index_name="vector_index_hacklytics"
)
vector_store_context = StorageContext.from_defaults(vector_store=atlas_vector_store)

chat_sessions = {}

def get_vector_store_index(user_id, filename):
    """
    Fetch all documents (ingested PDFs) for the given user_id and filename from MongoDB,
    convert them into Llama Index Document objects, and rebuild the vector store index.
    """
    docs = list(atlas_collection.find({
        "metadata.user_id": user_id,
        "metadata.filename": filename
    }))
    documents = []
    for doc in docs:
        doc_text = doc.get("text", "")
        doc_metadata = doc.get("metadata", {})
        documents.append(Document(text=doc_text, metadata=doc_metadata))
    
    if documents:
        text_splitter = SentenceSplitter(chunk_size=1024)
        vector_index = VectorStoreIndex.from_documents(
            documents,
            storage_context=vector_store_context,
            text_splitter=text_splitter,
            show_progress=False
        )
        return vector_index
    else:
        return None

# ============================================================================
# API Endpoints
# ============================================================================

@app.route("/api/upload", methods=["POST"])
def upload_pdf():
    """
    Upload a PDF file, ingest it into a vector index, and return a pdf_id.
    """
    if "file" not in request.files:
        return jsonify({"error": "No file provided"}), 400
    file = request.files["file"]
    if file.filename == "":
        return jsonify({"error": "No file selected"}), 400

    # Secure filename and save it to the uploads directory
    filename = file.filename
    file_path = os.path.join(UPLOAD_FOLDER, filename)
    file.save(file_path)

    user_id = 3

    # Load the PDF using SimpleDirectoryReader
    try:
        documents = SimpleDirectoryReader(input_files=[file_path]).load_data()
    except Exception as e:
        return jsonify({"error": f"Failed to load PDF: {str(e)}"}), 500

    # Add metadata to each document
    for doc in documents:
        doc.metadata["filename"] = filename
        doc.metadata["user_id"] = user_id

    # Build the vector index from the documents
    try:
        vector_index = VectorStoreIndex.from_documents(
            documents,
            service_context=vector_store_context,
            show_progress=True
        )
    except Exception as e:
        return jsonify({"error": f"Failed to build index: {str(e)}"}), 500

    pdf_id = str(uuid.uuid4())
    pdf_indexes[pdf_id] = vector_index
    chat_histories[pdf_id] = ""  # initialize empty conversation context
    print(pdf_id)
    return jsonify({"message": "PDF uploaded and indexed successfully", "pdf_id": pdf_id}), 200

@app.route("/api/chat", methods=["POST"])
def chat_with_pdf():
    """
    Chat with the ingested PDF.
    Expected JSON payload:
    {
      "pdf_id": "<id returned by /api/upload>",
      "question": "Your question here"
    }
    """
    data = request.get_json()
    pdf_id = data.get("pdf_id")
    question = data.get("question")
    if not pdf_id or not question:
        return jsonify({"error": "pdf_id and question are required"}), 400

    vector_index = pdf_indexes.get(pdf_id)
    if not vector_index:
        return jsonify({"error": "Invalid pdf_id"}), 404
    
    documents = vector_index.storage_context.docstore.docs.values()
    nodes = Settings.node_parser.get_nodes_from_documents(documents)
    storage_context = StorageContext.from_defaults()
    storage_context.docstore.add_documents(nodes)
    summary_index = SummaryIndex(nodes, storage_context=storage_context)
    vector_query_index = VectorStoreIndex(nodes, storage_context=storage_context)
    
    list_query_engine = summary_index.as_query_engine(
        response_mode="tree_summarize",
        use_async=True,
    )
    vector_query_engine = vector_query_index.as_query_engine()

    list_tool = QueryEngineTool.from_defaults(
        query_engine=list_query_engine,
        description=(
            "Useful for summarization questions related to the bank statement that the user has uploaded."
        ),
    )

    vector_tool = QueryEngineTool.from_defaults(
        query_engine=vector_query_engine,
        description=(
            "Useful for retrieving specific context about the bank statement that the user has uploaded."
        ),
    )

    query_engine = RouterQueryEngine(
        selector=PydanticSingleSelector.from_defaults(),
        query_engine_tools=[list_tool, vector_tool],
    )

    history = chat_histories.get(pdf_id, "")
    prompt_template = """
        You are an AI assistant helping users analyze their bank statements. The user has uploaded a PDF containing their financial transactions in their bank statement. 
        Your role is to provide clear, concise, and insightful answers based on the document.
        Context:
        - The PDF contains financial transactions, including income, expenses, and other financial activities.
        - Transactions may include merchant names, dates, amounts, and categories.
        - The user may ask about their spending habits, category-wise breakdowns, unusual transactions, trends, and budget insights.
        - Ensure responses are factual, analytical, and directly based on the provided data.
        The user can ask questions such as :
        - "What was my total expenditure last month?"
        - "Break down my expenses into categories."
        - "Find unusual or large transactions."
        - "Compare my spending between two months."
        - "Identify my top 5 spending categories."
        - If a question requires comparisons, ensure that you summarize the trend based on available data.
        Response Guidelines:
        1. Be Data-Driven - Ensure that answers are only based on the bank statement data.
        2. Be Concise & Structured - If applicable, provide information in bullets or tables.
        3. Ensure Clarity - Avoid ambiguity and respond in simple, easy-to-understand language.
        4. Highlight Trends & Insights - If patterns exist in spending, mention them.
        MAKE SURE YOU PROPERLY READ THE DOCUMENT AND UNDERSTAND ALL OF THE INFORMATION.
        DO NOT HALLUCINATE OR PROVIDE FALSE INFORMATION. IF THE DATA IS NOT AVAILABLE, STATE THAT THE INFORMATION IS NOT IN THE DOCUMENT.
        YOU SHOULD SEND THE RESPONSE AS A PLAIN HTML STRING and MAKE SURE YOU INCLUDE ALL THE HTML INSIDE A <div> </div> use any headers of h3 size and lower like h4 etc. DO NOT INCLUDE ANY EXPLANATIONS OR EXTRA TEXT OUTSIDE HTML.
    """
    prompt = (prompt_template + "chat history till now : " + history +
              f"Current Question that the user is asking Q: {question}" +
              "Please provide your response in plain HTML format only inside <div> </div> and since we are displaying this on chatbot, use any headers of h3 size and lower like h4 etc. Do not include any explanations or extra text outside HTML.")

    response = query_engine.query(prompt)
    answer = re.sub(r"```[a-zA-Z]*\n?|```", "", str(response))
    answer = re.sub(r"^#+\s*", "", answer, flags=re.MULTILINE)

    history += f"Q: {question}\nA: {answer}\n"
    chat_histories[pdf_id] = history

    return jsonify({"answer": answer}), 200

@app.route("/api/insights", methods=["POST"])
def get_insights():
    """
    Extract insights from an ingested bank/credit card statement PDF.
    Expected JSON payload:
    {
      "pdf_id": "<id returned by /api/upload>"
    }
    """
    data = request.get_json()
    pdf_id = data.get("pdf_id")
    if not pdf_id:
        return jsonify({"error": "pdf_id is required"}), 400

    vector_index = pdf_indexes.get(pdf_id)
    if not vector_index:
        return jsonify({"error": "Invalid pdf_id"}), 404

    docs = vector_index.storage_context.docstore.docs.values()
    full_text = "\n".join([doc.text for doc in docs])

    prompt_template = """
    You are an expert financial analyst.
    Given the bank statement text below, extract and compute the following insights strictly in valid JSON format without any additional commentary, explanations, or extra text.
    Chart Data Format:
    Include chart data in the following format:
    The first line chart should include 12 entries, one for each month of the year.
    Each entry should have three keys: "name" (the month name), "Income" (the total income for that month), and "Expenditure" (the total expenditure for that month).
    The second bar chart should include 5 entries, where you give the top 5 categories that have the most expenses.
    Each entry should have two keys: "name" (the category name) and "amount" (the total amount spent in that particular category).
    The third pie chart should take all the expenses and then accumulate them into categories.
    Each entry should have two keys: "name" (the category name) and "amount" (the total amount spent in that particular category).
    Try and put similar categories together and then provide the total amount spent in each category.
    The fourth line chart will have the savings for each month. Essentially this will just be the difference between the income and the expenditure for each month that you calculated in the first line chart.
    Each entry should have three keys: "name" (the month name), "amount" (income-expenditure for that month).
    Analyze all of the data and then find the common categories and accumulate them.
    ```json
    {
    "charts": {
        "lineChart": {
        "data": [
            { "name": "January", "Income": 4000, "Expenditure": 2400 },
            { "name": "February", "Income": 3000, "Expenditure": 1398 },
            { "name": "March", "Income": 2000, "Expenditure": 9800 },
            { "name": "April", "Income": 5000, "Expenditure": 3100 },
            { "name": "May", "Income": 7000, "Expenditure": 4500 },
            { "name": "June", "Income": 6500, "Expenditure": 4000 },
            { "name": "July", "Income": 8000, "Expenditure": 5000 },
            { "name": "August", "Income": 7200, "Expenditure": 4600 },
            { "name": "September", "Income": 6800, "Expenditure": 4400 },
            { "name": "October", "Income": 7500, "Expenditure": 4800 },
            { "name": "November", "Income": 7800, "Expenditure": 5100 },
            { "name": "December", "Income": 8200, "Expenditure": 5300 }
        ]
        },
        "barChart": {
        "data": [
            { "name": "Rent", "amount": 1500 },
            { "name": "Groceries", "amount": 800 },
            { "name": "Transport", "amount": 600 },
            { "name": "Entertainment", "amount": 400 },
            { "name": "Utilities", "amount": 300 }
        ]
        },
        "pieChart": {
        "data": [
            { "name": "Rent", "amount": 1500 },
            { "name": "Groceries", "amount": 800 },
            { "name": "Transport", "amount": 600 },
            { "name": "Entertainment", "amount": 400 },
            { "name": "Utilities", "amount": 300 }
        ]
        },
        "savingsChart": {
            "data": [
            { "name": "January", "amount": 2400 },
            { "name": "February", "amount": 1398 },
            { "name": "March", "amount": 9800 },
            { "name": "April", "amount": 3100 },
            { "name": "May", "amount": 4500 },
            { "name": "June", "amount": 4000 },
            { "name": "July", "amount": 5000 },
            { "name": "August", "amount": 4600 },
            { "name": "September", "amount": 4400 },
            { "name": "October", "amount": 4800 },
            { "name": "November", "amount": 5100 },
            { "name": "December", "amount": 5300 }
        ]
        }
    }
    }
    Your JSON must include the three charts with the specified data format.
    Do not include any additional text or explanations before or after the JSON.
    Return only valid JSON.
    """
    prompt = prompt_template + "\nThe overall bank statement text is provided below:\n" + full_text

    query_engine = vector_index.as_query_engine(response_mode="compact")
    response = query_engine.query(prompt)
    insights_json = response.response.strip()
    if insights_json.startswith("```json"):
        insights_json = insights_json[7:]
    if insights_json.endswith("```"):
        insights_json = insights_json[:-3]

    try:
        import json
        insights_data = json.loads(insights_json)
        print(insights_data)
    except json.JSONDecodeError as e:
        print("Error parsing JSON:", e)
        insights_data = {}

    return jsonify(insights_data), 200

# ============================================================================
# Authentication Endpoints
# ============================================================================

@app.route("/login", methods=["GET"])
def login():
    """Redirects user to Google's OAuth login page."""
    google_auth_url = (
        f"https://accounts.google.com/o/oauth2/auth?"
        f"client_id={GOOGLE_CLIENT_ID}"
        f"&redirect_uri={REDIRECT_URI}"
        f"&response_type=code"
        f"&scope=openid email profile"
    )
    return redirect(google_auth_url)

@app.route("/login/callback", methods=["GET"])
def login_callback():
    """Handles Google OAuth callback and logs in the user."""
    code = request.args.get("code")
    if not code:
        return jsonify({"error": "Authorization code missing"}), 400

    token_data = requests.post(
        "https://oauth2.googleapis.com/token",
        data={
            "code": code,
            "client_id": GOOGLE_CLIENT_ID,
            "client_secret": GOOGLE_CLIENT_SECRET,
            "redirect_uri": REDIRECT_URI,
            "grant_type": "authorization_code",
        }
    ).json()

    if "id_token" not in token_data:
        return jsonify({"error": "Failed to obtain ID token"}), 400

    try:
        id_info = id_token.verify_oauth2_token(token_data["id_token"], google_requests.Request(), GOOGLE_CLIENT_ID)
        user_id = id_info["sub"]
        email = id_info["email"]
        name = id_info.get("name", "Unknown User")
        if user_id not in users:
            users[user_id] = User(user_id, name, email)
        global global_current_user_id
        global_current_user_id = user_id
        login_user(users[user_id])
        # Create query string with the name
        params = {"name": name}
        redirect_url = f"http://localhost:3000/chatbot?{urlencode(params)}"
        return redirect(redirect_url)
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@app.route("/logout", methods=["GET"])
@login_required
def logout():
    """Logs out the user."""
    logout_user()
    return jsonify({"message": "Logout successful"}), 200

@app.route("/api/me", methods=["GET"])
@login_required
def get_me():
    return jsonify({
        "user_id": current_user.id,
        "name": current_user.name,
        "email": current_user.email
    }), 200

@app.route("/debug/session")
def debug_session():
    return jsonify(session)

# ============================================================================
# Main Entry Point
# ============================================================================

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=8080)