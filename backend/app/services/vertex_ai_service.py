import logging
from typing import List, Dict, Any, Optional
from google import genai
from google.genai import types
from vertexai.language_models import TextEmbeddingModel
import json
import re

logger = logging.getLogger(__name__)

# Google Search Grounding tool for web search capability
GOOGLE_SEARCH_TOOL = types.Tool(google_search=types.GoogleSearch())


class VertexAIService:
    """Service for Vertex AI text generation and embeddings"""
    
    def __init__(self, project_id: str, location: str = "us-central1"):
        self.project_id = project_id
        self.location = location
        
        # Initialize Gemini client using new google-genai SDK
        self.client = genai.Client(
            vertexai=True,
            project=project_id,
            location=location,
        )
        
        # Model name for Gemini 2.5 Pro
        self.model_name = "gemini-2.5-pro"
        
        # Initialize embedding model (still using vertexai for embeddings)
        from google.cloud import aiplatform
        aiplatform.init(project=project_id, location=location)
        # Using text-embedding-004 which is the latest stable embedding model
        self.embedding_model = TextEmbeddingModel.from_pretrained("text-embedding-004")
        
        logger.info(f"✅ Vertex AI service initialized for project: {project_id}, location: {location}")
    
    def generate_agent_specification(self, agent_description: str) -> Dict[str, str]:
        """
        Generate agent specification (name, role, tone, language) from description
        Uses Gemini 2.5 Pro to generate structured JSON response
        """
        try:
            prompt = f"""You are an AI assistant that creates agent specifications from user descriptions.

Given the following agent description, generate a JSON object with exactly these fields:
- name: A short, descriptive name for the agent (max 50 characters)
- role: The agent's role or purpose (max 100 characters)
- tone: The communication tone (e.g., "professional", "friendly", "casual", "formal", "helpful")
- language: The primary language (e.g., "English", "Spanish", "French")

Agent description: {agent_description}

Return ONLY a valid JSON object, no other text. Example format:
{{
  "name": "Customer Support Assistant",
  "role": "Help customers with product inquiries and support",
  "tone": "friendly",
  "language": "English"
}}"""

            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt
            )
            
            response_text = response.text.strip()
            
            # Extract JSON from response (handle markdown code blocks)
            json_match = re.search(r'\{[^{}]*\}', response_text, re.DOTALL)
            if json_match:
                response_text = json_match.group(0)
            
            # Parse JSON
            spec = json.loads(response_text)
            
            # Validate required fields
            required_fields = ["name", "role", "tone", "language"]
            for field in required_fields:
                if field not in spec:
                    raise ValueError(f"Missing required field: {field}")
            
            logger.info(f"✅ Generated agent specification: {spec['name']}")
            return spec
            
        except json.JSONDecodeError as e:
            logger.error(f"❌ Failed to parse JSON from Gemini response: {e}")
            logger.error(f"Response text: {response_text}")
            # Fallback to default values
            return {
                "name": "AI Assistant",
                "role": "Assist users with their queries",
                "tone": "friendly",
                "language": "English"
            }
        except Exception as e:
            logger.error(f"❌ Failed to generate agent specification: {e}")
            raise Exception(f"Failed to generate agent specification: {str(e)}")
    
    def generate_text(self, prompt: str, max_tokens: int = 1000) -> str:
        """Generate text using Gemini 2.5 Pro"""
        try:
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt
            )
            return response.text.strip()
        except Exception as e:
            logger.error(f"❌ Failed to generate text: {e}")
            raise Exception(f"Failed to generate text: {str(e)}")
    
    def generate_text_with_search(self, prompt: str, enable_search: bool = False) -> Dict[str, Any]:
        """
        Generate text using Gemini 2.5 Pro with optional Google Search Grounding.
        
        Args:
            prompt: The prompt to send to the model
            enable_search: If True, enables Google Search Grounding for web search
            
        Returns:
            Dict with:
            - response: The generated text
            - grounding_used: Whether web search was used
            - sources: List of web sources used (if grounding was used)
        """
        try:
            config = None
            if enable_search:
                logger.info("🔍 Google Search Grounding ENABLED - will search web if needed")
                config = types.GenerateContentConfig(
                    tools=[GOOGLE_SEARCH_TOOL]
                )
            
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt,
                config=config
            )
            
            result = {
                "response": response.text.strip(),
                "grounding_used": False,
                "sources": []
            }
            
            # Check if grounding metadata exists (web search was used)
            if enable_search and hasattr(response, 'candidates') and response.candidates:
                candidate = response.candidates[0]
                
                # Check for grounding metadata
                if hasattr(candidate, 'grounding_metadata') and candidate.grounding_metadata:
                    grounding_meta = candidate.grounding_metadata
                    result["grounding_used"] = True
                    
                    # Debug: Log the grounding metadata structure
                    logger.debug(f"🔍 Grounding metadata type: {type(grounding_meta)}")
                    logger.debug(f"🔍 Grounding metadata attrs: {dir(grounding_meta)}")
                    
                    # Extract search entry point if available
                    if hasattr(grounding_meta, 'search_entry_point') and grounding_meta.search_entry_point:
                        logger.info(f"🌐 Web search was performed")
                    
                    # Method 1: Try grounding_chunks (newer API)
                    if hasattr(grounding_meta, 'grounding_chunks') and grounding_meta.grounding_chunks:
                        logger.info(f"📦 Found {len(grounding_meta.grounding_chunks)} grounding chunks")
                        for chunk in grounding_meta.grounding_chunks:
                            if hasattr(chunk, 'web') and chunk.web:
                                source = {
                                    "title": getattr(chunk.web, 'title', 'Web Source'),
                                    "uri": getattr(chunk.web, 'uri', '')
                                }
                                if source["uri"]:  # Only add if URI exists
                                    result["sources"].append(source)
                                    logger.info(f"  📎 Source: {source['title']} - {source['uri']}")
                    
                    # Method 2: Try grounding_supports for citation URIs
                    if hasattr(grounding_meta, 'grounding_supports') and grounding_meta.grounding_supports:
                        logger.info(f"📚 Found {len(grounding_meta.grounding_supports)} grounding supports")
                        for support in grounding_meta.grounding_supports:
                            # Each support may have grounding_chunk_indices pointing to chunks
                            if hasattr(support, 'grounding_chunk_indices'):
                                logger.debug(f"  Support chunk indices: {support.grounding_chunk_indices}")
                            # Some APIs put URIs directly in supports
                            if hasattr(support, 'web_search_queries'):
                                logger.debug(f"  Web search queries: {support.web_search_queries}")
                    
                    # Method 3: Try retrieval_metadata (alternative structure)
                    if hasattr(grounding_meta, 'retrieval_metadata') and grounding_meta.retrieval_metadata:
                        logger.info(f"📖 Found retrieval metadata")
                        retrieval = grounding_meta.retrieval_metadata
                        if hasattr(retrieval, 'google_search_dynamic_retrieval_score'):
                            logger.info(f"  Search score: {retrieval.google_search_dynamic_retrieval_score}")
                    
                    # Method 4: Log web_search_queries for debugging (but don't generate fake sources)
                    if hasattr(grounding_meta, 'web_search_queries') and grounding_meta.web_search_queries:
                        logger.info(f"🔎 Web search queries: {grounding_meta.web_search_queries}")
                        # Note: We only show sources that Gemini actually returns in grounding_chunks
                        # We don't generate fake sources from search queries
                    
                    # Method 5: Try to get sources from grounding_supports with segment info
                    if not result["sources"] and hasattr(grounding_meta, 'grounding_supports'):
                        for i, support in enumerate(grounding_meta.grounding_supports or []):
                            # Try to extract segment and URI info
                            if hasattr(support, 'segment') and support.segment:
                                segment_text = getattr(support.segment, 'text', '')[:100] if hasattr(support.segment, 'text') else ''
                                logger.debug(f"  Segment {i}: {segment_text}...")
                            
                            # Check for grounding_chunk_indices to map back to chunks
                            if hasattr(support, 'grounding_chunk_indices') and support.grounding_chunk_indices:
                                for chunk_idx in support.grounding_chunk_indices:
                                    if hasattr(grounding_meta, 'grounding_chunks') and chunk_idx < len(grounding_meta.grounding_chunks):
                                        chunk = grounding_meta.grounding_chunks[chunk_idx]
                                        if hasattr(chunk, 'web') and chunk.web:
                                            uri = getattr(chunk.web, 'uri', '')
                                            title = getattr(chunk.web, 'title', 'Web Source')
                                            # Avoid duplicates
                                            if uri and not any(s['uri'] == uri for s in result["sources"]):
                                                result["sources"].append({"title": title, "uri": uri})
                                                logger.info(f"  📎 Source (from support): {title} - {uri}")
            
            if result["grounding_used"]:
                logger.info(f"✅ Response generated WITH web search ({len(result['sources'])} sources)")
            else:
                logger.info(f"✅ Response generated without web search")
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Failed to generate text with search: {e}")
            raise Exception(f"Failed to generate text with search: {str(e)}")
    
    def detect_intent(self, message: str) -> Dict[str, Any]:
        """Detect intent from user message"""
        try:
            prompt = f"""Analyze the following user message and determine the intent.

Message: {message}

Return a JSON object with:
- intent: The primary intent (e.g., "question", "greeting", "complaint", "request", "feedback")
- confidence: A confidence score between 0 and 1
- keywords: List of important keywords

Return ONLY a valid JSON object, no other text."""

            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt
            )
            response_text = response.text.strip()
            
            # Extract JSON
            json_match = re.search(r'\{[^{}]*\}', response_text, re.DOTALL)
            if json_match:
                response_text = json_match.group(0)
            
            intent_data = json.loads(response_text)
            
            # Ensure required fields
            if "intent" not in intent_data:
                intent_data["intent"] = "unknown"
            if "confidence" not in intent_data:
                intent_data["confidence"] = 0.5
            if "keywords" not in intent_data:
                intent_data["keywords"] = []
            
            return intent_data
            
        except Exception as e:
            logger.error(f"❌ Failed to detect intent: {e}")
            return {
                "intent": "unknown",
                "confidence": 0.0,
                "keywords": []
            }
    
    def detect_sentiment(self, message: str) -> Dict[str, Any]:
        """Detect sentiment from user message"""
        try:
            prompt = f"""Analyze the sentiment of the following message.

Message: {message}

Return a JSON object with:
- sentiment: The sentiment (e.g., "positive", "negative", "neutral")
- score: A score between -1 (very negative) and 1 (very positive)
- magnitude: The intensity of the sentiment (0 to 1)

Return ONLY a valid JSON object, no other text."""

            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt
            )
            response_text = response.text.strip()
            
            # Extract JSON
            json_match = re.search(r'\{[^{}]*\}', response_text, re.DOTALL)
            if json_match:
                response_text = json_match.group(0)
            
            sentiment_data = json.loads(response_text)
            
            # Ensure required fields
            if "sentiment" not in sentiment_data:
                sentiment_data["sentiment"] = "neutral"
            if "score" not in sentiment_data:
                sentiment_data["score"] = 0.0
            if "magnitude" not in sentiment_data:
                sentiment_data["magnitude"] = 0.0
            
            return sentiment_data
            
        except Exception as e:
            logger.error(f"❌ Failed to detect sentiment: {e}")
            return {
                "sentiment": "neutral",
                "score": 0.0,
                "magnitude": 0.0
            }
    
    def generate_embedding(self, text: str) -> List[float]:
        """Generate embedding for text using Vertex AI"""
        try:
            embeddings = self.embedding_model.get_embeddings([text])
            return embeddings[0].values
        except Exception as e:
            logger.error(f"❌ Failed to generate embedding: {e}")
            raise Exception(f"Failed to generate embedding: {str(e)}")
    
    def generate_embeddings_batch(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for multiple texts"""
        try:
            embeddings = self.embedding_model.get_embeddings(texts)
            return [emb.values for emb in embeddings]
        except Exception as e:
            logger.error(f"❌ Failed to generate embeddings batch: {e}")
            raise Exception(f"Failed to generate embeddings batch: {str(e)}")
    
    def cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """Calculate cosine similarity between two vectors"""
        try:
            import numpy as np
            
            vec1_np = np.array(vec1)
            vec2_np = np.array(vec2)
            
            dot_product = np.dot(vec1_np, vec2_np)
            norm1 = np.linalg.norm(vec1_np)
            norm2 = np.linalg.norm(vec2_np)
            
            if norm1 == 0 or norm2 == 0:
                return 0.0
            
            return float(dot_product / (norm1 * norm2))
        except Exception as e:
            logger.error(f"❌ Failed to calculate cosine similarity: {e}")
            return 0.0
