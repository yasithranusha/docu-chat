from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_google_genai import GoogleGenerativeAI
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_classic.chains import create_retrieval_chain
from langchain_classic.chains.combine_documents import create_stuff_documents_chain
from langchain_core.prompts import ChatPromptTemplate
from pinecone import Pinecone, ServerlessSpec
from langchain_pinecone import PineconeVectorStore
from dotenv import load_dotenv

from app.config import settings

load_dotenv()

loader = PyPDFLoader("books/romeo_and_juliet.pdf")
document = loader.load()

text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=1000,      # Maximum number of characters per chunk (smaller chunks = more precise retrieval)
    chunk_overlap=200     # Number of characters that overlap between consecutive chunks (preserves context at boundaries)
)
chunks = text_splitter.split_documents(document)  # Split PDF into ~200-300 smaller chunks based on settings above

pc = Pinecone(api_key=settings.PINECONE_API_KEY)
index_name = settings.PINECONE_INDEX_NAME

# Create index if doesn't exist
if index_name not in [idx.name for idx in pc.list_indexes()]:
    pc.create_index(
        name=index_name,
        dimension=384,  # HuggingFace all-MiniLM-L6-v2 dimension
        metric='cosine',
        spec=ServerlessSpec(cloud='aws', region='us-east-1')
    )

for i, chunk in enumerate(chunks):
    chunk.metadata["document_id"] = 1
    chunk.metadata["chunk_index"] = i

embeddings = HuggingFaceEmbeddings(
    model_name="all-MiniLM-L6-v2"  # Fast, small, good quality
)

# Store in Pinecone
PineconeVectorStore.from_documents(
    documents=chunks,
    embedding=embeddings,
    index_name=index_name
)


vectorstore = PineconeVectorStore(
    index_name=index_name,
    embedding=embeddings
)

retriever = vectorstore.as_retriever(
    search_kwargs={
        "k": 4,
        "filter": {"document_id": {"$eq": 1}}  # Optional
    }
)

llm = GoogleGenerativeAI(model="gemini-2.5-flash", temperature=0.3)

prompt = ChatPromptTemplate.from_messages([
    ("system", "Use the context to answer questions. {context}"),
    ("human", "{input}")
])

document_chain = create_stuff_documents_chain(llm, prompt)

qa_chain = create_retrieval_chain(retriever, document_chain)
    # Step 1: retriever searches FAISS for top 4 most similar chunks to the question
    # Step 2: document_chain sends those 4 chunks + question to LLM (Gemini) to generate answer

result = qa_chain.invoke({"input": "What is this about?"})
print(result["answer"])