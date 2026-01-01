from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_classic.chains import create_retrieval_chain
from langchain_classic.chains.combine_documents import create_stuff_documents_chain
from langchain_classic.chains.history_aware_retriever import create_history_aware_retriever
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage, AIMessage
from pinecone import Pinecone
from langchain_pinecone import PineconeVectorStore

from app.models import ChatHistory


class RAGService:

    def __init__(
        self,
        db: Session,
        pinecone_client: Pinecone,
        index_name: str,
        embeddings: HuggingFaceEmbeddings,
        llm: ChatGoogleGenerativeAI
    ):

        self.db = db
        self.pinecone_client = pinecone_client
        self.index_name = index_name
        self.embeddings = embeddings
        self.llm = llm
        self.index = pinecone_client.Index(index_name)

        # Text splitter for chunking documents
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200
        )

    def process_pdf(self, file_path: str, document_id: int) -> int:
        # Load PDF
        loader = PyPDFLoader(file_path)
        documents = loader.load()

        # Split into chunks
        chunks = self.text_splitter.split_documents(documents)

        # Add metadata to each chunk
        for i, chunk in enumerate(chunks):
            chunk.metadata.update({
                "document_id": document_id,
                "chunk_index": i,
                "source": file_path
            })

        # Create vector store and add documents
        vector_store = PineconeVectorStore(
            index=self.index,
            embedding=self.embeddings,
            text_key="text"
        )

        vector_store.add_documents(chunks)

        return len(chunks)

    def query(
        self,
        question: str,
        session_id: str,
        document_id: Optional[int] = None
    ) -> Dict[str, Any]:
        # Get conversation history for context
        chat_history = self._get_chat_history(session_id, limit=10)

        # Create vector store retriever
        vector_store = PineconeVectorStore(
            index=self.index,
            embedding=self.embeddings,
            text_key="text"
        )

        # Add document filter if specified
        search_kwargs = {"k": 5}
        if document_id is not None:
            search_kwargs["filter"] = {"document_id": document_id}

        retriever = vector_store.as_retriever(search_kwargs=search_kwargs)

        # Create history-aware retriever (reformulates question based on context)
        contextualize_q_system_prompt = """Given a chat history and the latest user question \
which might reference context in the chat history, formulate a standalone question \
which can be understood without the chat history. Do NOT answer the question, \
just reformulate it if needed and otherwise return it as is."""

        contextualize_q_prompt = ChatPromptTemplate.from_messages([
            ("system", contextualize_q_system_prompt),
            MessagesPlaceholder("chat_history"),
            ("human", "{input}"),
        ])

        history_aware_retriever = create_history_aware_retriever(
            self.llm, retriever, contextualize_q_prompt
        )

        # Create Q&A chain
        qa_system_prompt = """You are an assistant for question-answering tasks. \
Use the following pieces of retrieved context to answer the question. \
If you don't know the answer, just say that you don't know. \
Use three sentences maximum and keep the answer concise.\n\n{context}"""

        qa_prompt = ChatPromptTemplate.from_messages([
            ("system", qa_system_prompt),
            MessagesPlaceholder("chat_history"),
            ("human", "{input}"),
        ])

        question_answer_chain = create_stuff_documents_chain(self.llm, qa_prompt)

        rag_chain = create_retrieval_chain(
            history_aware_retriever,
            question_answer_chain
        )

        # Execute chain with history
        result = rag_chain.invoke({
            "input": question,
            "chat_history": chat_history
        })

        # Extract sources from context
        sources = []
        if "context" in result:
            for doc in result["context"]:
                sources.append({
                    "content": doc.page_content,
                    "metadata": doc.metadata
                })

        return {
            "question": question,
            "answer": result["answer"],
            "sources": sources,
            "session_id": session_id
        }

    def _get_chat_history(self, session_id: str, limit: int = 10) -> List:
        history_records = (
            self.db.query(ChatHistory)
            .filter(ChatHistory.session_id == session_id)
            .order_by(ChatHistory.created_at.desc())
            .limit(limit)
            .all()
        )

        # Reverse to get chronological order
        history_records.reverse()

        # Convert to LangChain message format
        messages = []
        for record in history_records:
            messages.append(HumanMessage(content=record.question))
            messages.append(AIMessage(content=record.answer))

        return messages

    def delete_document_vectors(self, document_id: int) -> None:
        self.index.delete(filter={"document_id": document_id})


