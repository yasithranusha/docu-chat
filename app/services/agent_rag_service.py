from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from langchain.tools import tool
from langchain.agents import create_agent
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_pinecone import PineconeVectorStore
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_core.documents import Document
from langchain_core.messages import HumanMessage, AIMessage
from pinecone import Pinecone

from app.models import ChatHistory
from app.logger import get_logger

logger = get_logger(__name__)


class AgentRAGService:

    def __init__(
        self,
        db: Session,
        pinecone_client: Pinecone,
        index_name: str,
        embeddings: HuggingFaceEmbeddings,
        llm: ChatGoogleGenerativeAI
    ):
        logger.info("Initializing Agent RAG Service")

        self.db = db
        self.pinecone_client = pinecone_client
        self.index_name = index_name
        self.embeddings = embeddings
        self.llm = llm
        self.index = pinecone_client.Index(index_name)

        self.vectorstore = PineconeVectorStore(
            index=self.index,
            embedding=self.embeddings
        )

        # Store current document filter (will be set in query method)
        self._current_document_id = None

        # Create retrieval tool (the agent will decide when to use this)
        self._create_retrieval_tool()

        # Create agent with the tool
        self._create_agent()

        logger.info("Agent RAG Service initialized successfully")

    def _create_retrieval_tool(self):
        """
        Create retrieval tool that respects document_id filter.
        The filter is set in the query() method before agent invocation.
        """
        vectorstore = self.vectorstore
        service = self  # Capture self for closure

        @tool(response_format="content_and_artifact")
        def retrieve_documents(query: str) -> tuple[str, List[Document]]:
            """Retrieve relevant document chunks to answer questions"""

            logger.info(f"Agent invoking retrieval tool with query: {query[:50]}...")

            # Build search kwargs with optional document filter
            search_kwargs = {"k": 4}
            if service._current_document_id is not None:
                search_kwargs["filter"] = {"document_id": service._current_document_id}
                logger.info(f"Filtering by document_id: {service._current_document_id}")

            # Perform similarity search in Pinecone
            docs = vectorstore.similarity_search(query, **search_kwargs)

            # Format context for LLM
            context = "\n\n".join([
                f"Source (Page {doc.metadata.get('page', 'N/A')}):\n{doc.page_content}"
                for doc in docs
            ])

            logger.info(f"Retrieved {len(docs)} documents")
            return context, docs

        self.retrieve_tool = retrieve_documents

    def _create_agent(self):
        """
        Create agent with retrieval tool.

        The agent will:
        1. Receive a question
        2. Decide if it needs to retrieve documents
        3. Use the tool if needed
        4. Generate answer
        """
        system_prompt = """You are a helpful AI assistant that answers questions about documents.

When a user asks about document content:
- Use the retrieve_documents tool to find relevant information
- Cite the page numbers from the sources
- Be concise and accurate

When a user greets you or asks general questions:
- Respond naturally without using the tool
- Be friendly and helpful

Always be honest - if you don't have enough context, say so."""

        self.agent = create_agent(
            model=self.llm,
            tools=[self.retrieve_tool],
            system_prompt=system_prompt
        )

        logger.info("Agent created with retrieval tool")

    def _get_chat_history(self, session_id: str, limit: int = 10) -> List:
        """
        Retrieve chat history for a session from database.

        Args:
            session_id: Session ID to retrieve history for
            limit: Maximum number of messages to retrieve (default 10)

        Returns:
            List of LangChain messages (HumanMessage and AIMessage)
        """
        logger.info(f"Retrieving chat history for session: {session_id[:8]}...")

        # Query database for chat history
        history_records = (
            self.db.query(ChatHistory)
            .filter(ChatHistory.session_id == session_id)
            .order_by(ChatHistory.created_at.desc())
            .limit(limit)
            .all()
        )

        # Reverse to get chronological order (oldest first)
        history_records.reverse()

        # Convert to LangChain messages
        chat_history = []
        for record in history_records:
            chat_history.append(HumanMessage(content=record.question))
            chat_history.append(AIMessage(content=record.answer))

        logger.info(f"Retrieved {len(history_records)} conversation turns")
        return chat_history

    def query(
        self,
        question: str,
        session_id: Optional[str] = None,
        document_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Query using agent (decides when to retrieve).

        Args:
            question: User's question
            session_id: Session ID for conversational context (retrieves last 10 messages)
            document_id: Filter results by specific document ID

        Returns:
            Dict with answer, sources, session_id, and metadata
        """
        logger.info(
            f"Agent query - Session: {session_id[:8] if session_id else 'none'}... - "
            f"Document filter: {document_id if document_id else 'none'}"
        )

        try:
            # Set document filter (used by retrieval tool)
            self._current_document_id = document_id

            # Retrieve chat history if session exists
            chat_history = []
            if session_id:
                chat_history = self._get_chat_history(session_id)

            # Build messages list (history + current question)
            messages = chat_history + [HumanMessage(content=question)]

            logger.info(f"Invoking agent with {len(messages)} messages ({len(chat_history)} from history)")

            # Invoke agent with full conversation context
            # Agent will decide whether to use retrieval tool
            result = self.agent.invoke({  # type: ignore[arg-type]
                "messages": messages
            })

            # Extract answer from agent's response
            answer = result["messages"][-1].content

            # Extract sources if tool was used
            sources = []
            tool_calls = [msg for msg in result["messages"] if hasattr(msg, "tool_calls")]
            if tool_calls:
                # Tool was used - extract document metadata
                for msg in result["messages"]:
                    if hasattr(msg, "artifact") and msg.artifact:
                        # artifact contains the List[Document]
                        for doc in msg.artifact:
                            sources.append({
                                "content": doc.page_content[:200] + "...",
                                "metadata": doc.metadata
                            })
                        break

            logger.info(f"Agent responded with {len(sources)} sources")

            return {
                "question": question,
                "answer": answer,
                "sources": sources,
                "session_id": session_id,
                "agent_used_retrieval": len(sources) > 0
            }

        except Exception as e:
            logger.error(f"Agent query failed: {str(e)}")
            raise

        finally:
            # Reset document filter after query
            self._current_document_id = None
