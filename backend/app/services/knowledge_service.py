import uuid
import logging
import requests
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any
from google.cloud import firestore, storage
from bs4 import BeautifulSoup
import re

from ..models import Knowledge, KnowledgeType, KnowledgeTextRequest, KnowledgeFileRequest, KnowledgeLinkRequest, KnowledgeQnARequest
from ..config import gcp_clients
from .vertex_ai_service import VertexAIService

logger = logging.getLogger(__name__)


class KnowledgeService:
    """Service layer for knowledge base operations"""
    
    def __init__(self):
        self.firestore_client = gcp_clients.get_firestore_client()
        self.bucket = gcp_clients.get_bucket()
        self.project_id = gcp_clients.get_project_id()
        
        # Initialize collections
        self.knowledge_collection = self.firestore_client.collection('knowledge')
        
        # Initialize Vertex AI service
        self.vertex_ai = VertexAIService(self.project_id)
        
        logger.info("✅ KnowledgeService initialized")
    
    def _normalize_text(self, text: str) -> str:
        """Normalize text by removing extra whitespace and normalizing newlines"""
        # Remove extra whitespace
        text = text.strip()
        # Normalize multiple newlines
        text = re.sub(r'\n\s*\n+', '\n\n', text)
        # Normalize multiple spaces
        text = re.sub(r' +', ' ', text)
        return text
    
    def _chunk_text(self, text: str, chunk_size: int = 1000, overlap: int = 200) -> List[str]:
        """Split text into chunks with overlap"""
        chunks = []
        words = text.split()
        
        for i in range(0, len(words), chunk_size - overlap):
            chunk = ' '.join(words[i:i + chunk_size])
            if chunk.strip():
                chunks.append(chunk)
        
        return chunks
    
    def add_text_knowledge(self, request: KnowledgeTextRequest) -> dict:
        """Add text knowledge to agent with chunking support"""
        try:
            logger.info(f"Adding text knowledge for agent: {request.agent_id}")
            
            # Normalize text
            content = request.content.strip()
            content = re.sub(r'\n\s*\n+', '\n\n', content)  # Normalize multiple newlines
            
            # Check content length
            if len(content) > 10000:
                raise ValueError("Content exceeds maximum length of 10000 characters")
            
            # Chunk the text if it's long enough
            word_count = len(content.split())
            if word_count > 500:
                chunks = self._chunk_text(content, chunk_size=500, overlap=100)
            else:
                chunks = [content]
            
            # Generate embeddings for each chunk
            knowledge_ids = []
            for i, chunk in enumerate(chunks):
                # Generate embedding for this chunk
                embedding = self.vertex_ai.generate_embedding(chunk)
                
                # Create knowledge document
                knowledge_id = f"KB_{uuid.uuid4().hex[:12].upper()}"
                knowledge_data = {
                    "knowledge_id": knowledge_id,
                    "agent_id": request.agent_id,
                    "session_id": request.session_id,
                    "type": KnowledgeType.TEXT.value,
                    "source_type": "MANUAL",
                    "content": chunk,
                    "embedding": embedding,
                    "metadata": {
                        "chunk_index": i,
                        "total_chunks": len(chunks)
                    },
                    "priority": 1,
                    "created_at": datetime.now(timezone.utc)
                }
                
                # Save to Firestore
                knowledge_ref = self.knowledge_collection.document(knowledge_id)
                knowledge_ref.set(knowledge_data)
                knowledge_ids.append(knowledge_id)
            
            logger.info(f"✅ Text knowledge added: {len(knowledge_ids)} chunks")
            return {"knowledge_ids": knowledge_ids, "chunks_added": len(knowledge_ids)}
            
        except Exception as e:
            logger.error(f"❌ Failed to add text knowledge: {e}")
            raise Exception(f"Failed to add text knowledge: {str(e)}")
    
    def add_file_knowledge(
        self,
        agent_id: str,
        session_id: Optional[str],
        file_name: str,
        file_type: str,
        file_url: str,
        file_size: int,
        extracted_text: str,
        file_metadata: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Add file knowledge to agent's KB.
        
        Args:
            agent_id: Agent ID
            session_id: Session ID for traceability
            file_name: Original file name
            file_type: File type (pdf, xlsx, csv, txt)
            file_url: GCS URL where file is stored
            file_size: File size in bytes
            extracted_text: Text extracted from the file
            file_metadata: Additional metadata from extraction (pages, sheets, etc.)
        
        Returns:
            Dict with knowledge_ids and chunks_added
        """
        try:
            logger.info(f"📁 Adding file knowledge for agent: {agent_id}, file: {file_name}")
            
            # Normalize the extracted text
            normalized_text = self._normalize_text(extracted_text)
            
            if not normalized_text.strip():
                raise ValueError("No text content to add")
            
            # Chunk the text
            chunks = self._chunk_text(normalized_text)
            logger.info(f"📄 Split into {len(chunks)} chunks")
            
            # Generate embeddings for each chunk
            embeddings = self.vertex_ai.generate_embeddings_batch(chunks)
            
            # Store each chunk as a separate knowledge entry
            knowledge_ids = []
            for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
                knowledge_id = f"KB_FILE_{uuid.uuid4().hex[:12].upper()}"
                knowledge_data = {
                    "knowledge_id": knowledge_id,
                    "agent_id": agent_id,
                    "session_id": session_id,
                    "type": KnowledgeType.FILE.value,
                    "source_type": "UPLOAD",
                    "content": chunk,
                    "embedding": embedding,
                    "metadata": {
                        "file_name": file_name,
                        "file_type": file_type,
                        "file_url": file_url,
                        "file_size": file_size,
                        "chunk_index": i,
                        "total_chunks": len(chunks),
                        **file_metadata  # Include pages, sheets, etc.
                    },
                    "priority": 1,
                    "created_at": datetime.now(timezone.utc)
                }
                
                knowledge_ref = self.knowledge_collection.document(knowledge_id)
                knowledge_ref.set(knowledge_data)
                knowledge_ids.append(knowledge_id)
                logger.info(f"✅ Stored chunk {i+1}/{len(chunks)}: {knowledge_id}")
            
            logger.info(f"✅ File knowledge added: {len(knowledge_ids)} chunks from {file_name}")
            return {
                "knowledge_ids": knowledge_ids,
                "chunks_added": len(knowledge_ids)
            }
            
        except Exception as e:
            logger.error(f"❌ Failed to add file knowledge: {e}")
            raise Exception(f"Failed to add file knowledge: {str(e)}")
    
    def _extract_text_from_file(self, file_url: str) -> str:
        """Extract text from file (simplified implementation)"""
        try:
            # For GCS URLs, download the file
            if file_url.startswith("gs://"):
                # Parse GCS URL
                parts = file_url.replace("gs://", "").split("/", 1)
                bucket_name = parts[0]
                blob_name = parts[1] if len(parts) > 1 else ""
                
                # Download from GCS
                from ..config import gcp_clients
                storage_client = gcp_clients.get_storage_client()
                bucket = storage_client.bucket(bucket_name)
                blob = bucket.blob(blob_name)
                content = blob.download_as_text()
                return content
            else:
                # For HTTP URLs, download
                response = requests.get(file_url, timeout=30)
                response.raise_for_status()
                return response.text
                
        except Exception as e:
            logger.error(f"❌ Failed to extract text from file: {e}")
            raise Exception(f"Failed to extract text from file: {str(e)}")
    
    def add_link_knowledge(self, request: KnowledgeLinkRequest) -> Dict[str, Any]:
        """Add link knowledge to agent"""
        try:
            logger.info(f"🔗 Adding link knowledge for agent: {request.agent_id}, URL: {request.url}")
            
            # Fetch URL content with better headers
            response = requests.get(request.url, timeout=30, headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
            })
            response.raise_for_status()
            
            # Parse HTML and extract text
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Get page title
            page_title = soup.title.string.strip() if soup.title and soup.title.string else request.url
            
            # Try to get meta description as fallback
            meta_description = ""
            meta_tag = soup.find('meta', attrs={'name': 'description'}) or soup.find('meta', attrs={'property': 'og:description'})
            if meta_tag and meta_tag.get('content'):
                meta_description = meta_tag.get('content', '')
            
            # Remove unwanted elements (but keep main content areas)
            for element in soup(["script", "style", "noscript", "iframe", "svg"]):
                element.decompose()
            
            # Try to find main content areas first
            main_content = soup.find('main') or soup.find('article') or soup.find(id='content') or soup.find(class_='content')
            
            if main_content:
                text = main_content.get_text(separator=' ', strip=True)
            else:
                # Remove nav, footer, etc. only if no main content found
                for element in soup(["nav", "footer", "header", "aside"]):
                    element.decompose()
                text = soup.get_text(separator=' ', strip=True)
            
            # Clean up text - normalize whitespace
            text = re.sub(r'\s+', ' ', text).strip()
            
            # If still no text, try getting from body
            if len(text) < 100:
                body = soup.find('body')
                if body:
                    text = body.get_text(separator=' ', strip=True)
                    text = re.sub(r'\s+', ' ', text).strip()
            
            # Add meta description if main text is too short
            if len(text) < 200 and meta_description:
                text = f"{page_title}. {meta_description}. {text}"
            
            logger.info(f"📝 Raw extracted length: {len(text)} chars")
            
            if len(text) < 50:
                raise ValueError(f"Could not extract enough text from URL. This site may require JavaScript to render content. Only got {len(text)} characters.")
            
            logger.info(f"📝 Extracted {len(text)} chars from URL")
            
            # Chunk the text
            chunks = self._chunk_text(text)
            logger.info(f"📄 Split into {len(chunks)} chunks")
            
            # Generate embeddings for each chunk
            embeddings = self.vertex_ai.generate_embeddings_batch(chunks)
            
            # Store each chunk as a separate knowledge entry
            knowledge_ids = []
            for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
                knowledge_id = f"KB_LINK_{uuid.uuid4().hex[:12].upper()}"
                knowledge_data = {
                    "knowledge_id": knowledge_id,
                    "agent_id": request.agent_id,
                    "session_id": request.session_id if hasattr(request, 'session_id') else None,
                    "type": KnowledgeType.LINK.value,
                    "source_type": "URL",
                    "content": chunk,
                    "embedding": embedding,
                    "metadata": {
                        "url": request.url,
                        "page_title": page_title,
                        "chunk_index": i,
                        "total_chunks": len(chunks),
                        "extracted_chars": len(text)
                    },
                    "priority": 1,
                    "created_at": datetime.now(timezone.utc)
                }
                
                knowledge_ref = self.knowledge_collection.document(knowledge_id)
                knowledge_ref.set(knowledge_data)
                knowledge_ids.append(knowledge_id)
            
            logger.info(f"✅ Link knowledge added: {len(knowledge_ids)} chunks from {request.url}")
            return {
                "knowledge_ids": knowledge_ids,
                "chunks_added": len(knowledge_ids),
                "url": request.url,
                "page_title": page_title,
                "extracted_chars": len(text)
            }
            
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Failed to fetch URL {request.url}: {e}")
            raise Exception(f"Failed to fetch URL: {str(e)}")
        except Exception as e:
            logger.error(f"❌ Failed to add link knowledge: {e}")
            raise Exception(f"Failed to add link knowledge: {str(e)}")
    
    def add_qna_knowledge(self, request: KnowledgeQnARequest) -> str:
        """Add Q&A knowledge to agent"""
        try:
            logger.info(f"Adding Q&A knowledge for agent: {request.agent_id}")
            
            # Combine Q + A
            qna_content = f"Q: {request.question}\nA: {request.answer}"
            
            # Generate embedding
            embedding = self.vertex_ai.generate_embedding(qna_content)
            
            # Create knowledge document with high priority
            knowledge_id = f"KB_{uuid.uuid4().hex[:12].upper()}"
            knowledge_data = {
                "knowledge_id": knowledge_id,
                "agent_id": request.agent_id,
                "type": KnowledgeType.QNA.value,
                "content": qna_content,
                "embedding": embedding,
                "metadata": {
                    "question": request.question,
                    "answer": request.answer
                },
                "priority": 10,  # High priority for Q&A
                "created_at": datetime.now(timezone.utc)
            }
            
            # Save to Firestore
            knowledge_ref = self.knowledge_collection.document(knowledge_id)
            knowledge_ref.set(knowledge_data)
            
            logger.info(f"✅ Q&A knowledge added: {knowledge_id}")
            return knowledge_id
            
        except Exception as e:
            logger.error(f"❌ Failed to add Q&A knowledge: {e}")
            raise Exception(f"Failed to add Q&A knowledge: {str(e)}")
    
    def list_knowledge(self, agent_id: str, kb_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """List all knowledge entries for an agent"""
        try:
            # First, get all knowledge for this agent
            query = self.knowledge_collection.where('agent_id', '==', agent_id)
            knowledge_refs = query.stream()
            
            knowledge_list = []
            for doc in knowledge_refs:
                data = doc.to_dict()
                
                # Filter by type if specified (case-insensitive)
                if kb_type:
                    doc_type = data.get('type', '').lower()
                    if doc_type != kb_type.lower():
                        continue
                
                # Remove embedding from response (too large)
                if 'embedding' in data:
                    del data['embedding']
                knowledge_list.append(data)
            
            # Sort by created_at descending
            knowledge_list.sort(key=lambda x: x.get('created_at', ''), reverse=True)
            
            logger.info(f"✅ Listed {len(knowledge_list)} knowledge entries for agent: {agent_id}")
            return knowledge_list
            
        except Exception as e:
            logger.error(f"❌ Failed to list knowledge: {e}")
            raise Exception(f"Failed to list knowledge: {str(e)}")
    
    def get_knowledge(self, knowledge_id: str) -> Optional[Dict[str, Any]]:
        """Get a single knowledge entry by ID"""
        try:
            knowledge_ref = self.knowledge_collection.document(knowledge_id)
            doc = knowledge_ref.get()
            
            if not doc.exists:
                return None
            
            data = doc.to_dict()
            # Remove embedding from response
            if 'embedding' in data:
                del data['embedding']
            
            return data
            
        except Exception as e:
            logger.error(f"❌ Failed to get knowledge: {e}")
            raise Exception(f"Failed to get knowledge: {str(e)}")
    
    def update_knowledge(self, knowledge_id: str, content: str) -> Dict[str, Any]:
        """Update a knowledge entry's content and regenerate embedding"""
        try:
            knowledge_ref = self.knowledge_collection.document(knowledge_id)
            doc = knowledge_ref.get()
            
            if not doc.exists:
                raise ValueError(f"Knowledge entry not found: {knowledge_id}")
            
            # Generate new embedding for updated content
            embedding = self.vertex_ai.generate_embedding(content)
            
            # Update document
            knowledge_ref.update({
                "content": content,
                "embedding": embedding,
                "updated_at": datetime.now(timezone.utc)
            })
            
            logger.info(f"✅ Knowledge updated: {knowledge_id}")
            return {"knowledge_id": knowledge_id, "updated": True}
            
        except Exception as e:
            logger.error(f"❌ Failed to update knowledge: {e}")
            raise Exception(f"Failed to update knowledge: {str(e)}")
    
    def delete_knowledge(self, knowledge_id: str) -> bool:
        """Delete a knowledge entry"""
        try:
            knowledge_ref = self.knowledge_collection.document(knowledge_id)
            doc = knowledge_ref.get()
            
            if not doc.exists:
                raise ValueError(f"Knowledge entry not found: {knowledge_id}")
            
            knowledge_ref.delete()
            
            logger.info(f"✅ Knowledge deleted: {knowledge_id}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to delete knowledge: {e}")
            raise Exception(f"Failed to delete knowledge: {str(e)}")

    def retrieve_knowledge(self, agent_id: str, query_embedding: List[float], top_k: int = 5, similarity_threshold: float = 0.7) -> List[Knowledge]:
        """
        Retrieve relevant knowledge using embedding similarity.
        
        Args:
            agent_id: The agent ID to search KB for
            query_embedding: The embedding vector of user's query
            top_k: Maximum number of results to return
            similarity_threshold: Minimum similarity score (0.0-1.0) to include KB
                                  - 0.3 = Only somewhat relevant content
                                  - 0.5 = Only moderately relevant content
                                  - 0.7 = Only highly relevant content
        """
        try:
            # Get all knowledge for this agent
            knowledge_refs = self.knowledge_collection.where('agent_id', '==', agent_id).stream()
            
            # Calculate similarities
            similarities = []
            all_scores = []  # For logging
            for knowledge_doc in knowledge_refs:
                knowledge_data = knowledge_doc.to_dict()
                if 'embedding' in knowledge_data and knowledge_data['embedding']:
                    embedding = knowledge_data['embedding']
                    similarity = self.vertex_ai.cosine_similarity(query_embedding, embedding)
                    
                    # Boost Q&A knowledge
                    priority_boost = knowledge_data.get('priority', 1) / 10.0
                    final_score = similarity + (priority_boost * 0.1)
                    
                    # Log ALL scores for debugging
                    kb_preview = knowledge_data.get('content', '')[:100]
                    all_scores.append((final_score, knowledge_data.get('knowledge_id'), kb_preview))
                    
                    # Only include if above threshold
                    if final_score >= similarity_threshold:
                        similarities.append((final_score, knowledge_data))
                        logger.info(f"✅ KB MATCH: {knowledge_data.get('knowledge_id')} score={final_score:.3f}")
                    else:
                        logger.info(f"⚠️ KB below threshold: {knowledge_data.get('knowledge_id')} score={final_score:.3f} (threshold={similarity_threshold})")
            
            # Log all scores for debugging
            if all_scores:
                logger.info(f"📊 All KB similarity scores: {[(s[0], s[1]) for s in all_scores]}")
            
            # Sort by similarity (descending)
            similarities.sort(key=lambda x: x[0], reverse=True)
            
            # Return top K (only those above threshold)
            top_knowledge = []
            for score, knowledge_data in similarities[:top_k]:
                knowledge_data['similarity_score'] = score
                top_knowledge.append(Knowledge(**knowledge_data))
            
            logger.info(f"✅ Retrieved {len(top_knowledge)} relevant KB entries (threshold={similarity_threshold})")
            return top_knowledge
            
        except Exception as e:
            logger.error(f"❌ Failed to retrieve knowledge: {e}")
            return []

