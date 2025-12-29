from typing import Optional, List, Dict, Any
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_google_genai import GoogleGenerativeAI
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_classic.chains import create_retrieval_chain
from langchain_classic.chains.combine_documents import create_stuff_documents_chain
from langchain_core.prompts import ChatPromptTemplate
from pinecone import Pinecone, ServerlessSpec
from langchain_pinecone import PineconeVectorStore

from app.config import settings


class RAGService:

    def __init__(self):

        # Initialize embeddings model (converts text to vectors)
        self.embeddings = HuggingFaceEmbeddings(
            model_name="all-MiniLM-L6-v2"  # 384 dimensions, fast, good quality
        )

        # Initialize LLM (generates answers)
        self.llm = GoogleGenerativeAI(
            model="gemini-2.5-flash",
            temperature=0.3,  # Lower = more focused, higher = more creative
            google_api_key=settings.GOOGLE_API_KEY
        )

        # Initialize Pinecone client
        self.pc = Pinecone(api_key=settings.PINECONE_API_KEY)
        self.index_name = settings.PINECONE_INDEX_NAME

        # Create Pinecone index if it doesn't exist
        self._initialize_pinecone()

        # Text splitter for chunking documents
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,      # Max characters per chunk
            chunk_overlap=200     # Overlap to preserve context
        )

    def _initialize_pinecone(self) -> None:
        existing_indexes = [idx.name for idx in self.pc.list_indexes()]

        if self.index_name not in existing_indexes:
            self.pc.create_index(
                name=self.index_name,
                dimension=384,  # HuggingFace all-MiniLM-L6-v2 dimension
                metric='cosine',  # Similarity metric
                spec=ServerlessSpec(
                    cloud='aws',
                    region='us-east-1'
                )
            )

    def process_pdf(
        self,
        file_path: str,
        document_id: int
    ) -> int:

        # Load PDF
        loader = PyPDFLoader(file_path)
        documents = loader.load()

        # Split into chunks
        chunks = self.text_splitter.split_documents(documents)

        # Add metadata to each chunk
        for i, chunk in enumerate(chunks):
            chunk.metadata["document_id"] = document_id
            chunk.metadata["chunk_index"] = i

        # Store in Pinecone (creates embeddings automatically)
        PineconeVectorStore.from_documents(
            documents=chunks,
            embedding=self.embeddings,
            index_name=self.index_name  # Now works because os.environ has PINECONE_API_KEY
        )

        return len(chunks)

    def query(
        self,
        question: str,
        document_id: Optional[int] = None
    ) -> Dict[str, Any]:

        # Connect to Pinecone vector store
        vectorstore = PineconeVectorStore(
            index_name=self.index_name,  # Now works because os.environ has PINECONE_API_KEY
            embedding=self.embeddings
        )

        # Create retriever with optional filtering
        search_kwargs = {"k": 4}  # Retrieve top 4 most similar chunks

        if document_id is not None:
            # Filter to specific document
            search_kwargs["filter"] = {"document_id": {"$eq": document_id}}

        retriever = vectorstore.as_retriever(search_kwargs=search_kwargs)

        # Create prompt template
        prompt = ChatPromptTemplate.from_messages([
            ("system", "Use the following context to answer the question. "
                      "If you don't know the answer, say so. Don't make up information.\n\n"
                      "Context: {context}"),
            ("human", "{input}")
        ])

        # Create document chain (combines retrieved docs with LLM)
        document_chain = create_stuff_documents_chain(self.llm, prompt)

        # Create retrieval chain (retrieves docs then generates answer)
        qa_chain = create_retrieval_chain(retriever, document_chain)

        # Execute the chain
        result = qa_chain.invoke({"input": question})

        # Format response
        return {
            "question": question,
            "answer": result["answer"],
            "sources": [
                {
                    "content": doc.page_content,
                    "metadata": doc.metadata
                }
                for doc in result.get("context", [])
            ]
        }


# Dependency injection function for FastAPI
def get_rag_service() -> RAGService:
    return RAGService()
