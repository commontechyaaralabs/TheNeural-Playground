import uuid
import logging
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List
from google.cloud import firestore

from ..models import Agent, Persona, AgentCreateRequest, PersonaUpdateRequest
from ..config import gcp_clients
from .vertex_ai_service import VertexAIService

logger = logging.getLogger(__name__)


class AgentService:
    """Service layer for agent management operations"""
    
    def __init__(self):
        self.firestore_client = gcp_clients.get_firestore_client()
        self.project_id = gcp_clients.get_project_id()
        
        # Initialize collections
        self.agents_collection = self.firestore_client.collection('agents')
        self.personas_collection = self.firestore_client.collection('personas')
        
        # Initialize Vertex AI service
        self.vertex_ai = VertexAIService(self.project_id)
        
        logger.info("✅ AgentService initialized")
    
    def create_agent(self, request: AgentCreateRequest) -> Agent:
        """Create a new agent from description"""
        try:
            # Use session_id as user_id if user_id is not provided
            user_id = request.user_id if request.user_id else request.session_id
            
            logger.info(f"Creating agent for session: {request.session_id}")
            
            # Generate agent specification using Vertex AI
            spec = self.vertex_ai.generate_agent_specification(request.agent_description)
            
            # Generate agent ID
            agent_id = f"AGENT_{uuid.uuid4().hex[:12].upper()}"
            
            # Create agent document
            agent_data = {
                "agent_id": agent_id,
                "user_id": user_id,
                "session_id": request.session_id,
                "name": spec["name"],
                "role": spec["role"],
                "tone": spec["tone"],
                "language": spec["language"],
                "description": request.agent_description,
                "created_at": datetime.now(timezone.utc),
                "updated_at": datetime.now(timezone.utc),
                "active": True
            }
            
            # Save agent to Firestore
            agent_ref = self.agents_collection.document(agent_id)
            agent_ref.set(agent_data)
            
            # Create persona document
            persona_data = {
                "agent_id": agent_id,
                "name": spec["name"],
                "role": spec["role"],
                "tone": spec["tone"],
                "language": spec["language"],
                "response_length": "short",  # Default response length
                "guidelines": "",  # Default empty guidelines
                "created_at": datetime.now(timezone.utc),
                "updated_at": datetime.now(timezone.utc)
            }
            
            persona_ref = self.personas_collection.document(agent_id)
            persona_ref.set(persona_data)
            
            logger.info(f"✅ Agent created: {agent_id}")
            
            return Agent(**agent_data)
            
        except Exception as e:
            logger.error(f"❌ Failed to create agent: {e}")
            raise Exception(f"Failed to create agent: {str(e)}")
    
    def get_agent(self, agent_id: str) -> Optional[Agent]:
        """Get agent by ID"""
        try:
            agent_ref = self.agents_collection.document(agent_id)
            agent_doc = agent_ref.get()
            
            if not agent_doc.exists:
                return None
            
            agent_data = agent_doc.to_dict()
            return Agent(**agent_data)
            
        except Exception as e:
            logger.error(f"❌ Failed to get agent: {e}")
            raise Exception(f"Failed to get agent: {str(e)}")
    
    def get_persona(self, agent_id: str) -> Optional[Persona]:
        """Get persona by agent ID"""
        try:
            persona_ref = self.personas_collection.document(agent_id)
            persona_doc = persona_ref.get()
            
            if not persona_doc.exists:
                return None
            
            persona_data = persona_doc.to_dict()
            
            # Add default values for new fields if they don't exist in the database
            if 'response_length' not in persona_data:
                persona_data['response_length'] = 'short'
            if 'guidelines' not in persona_data:
                persona_data['guidelines'] = ''
            
            return Persona(**persona_data)
            
        except Exception as e:
            logger.error(f"❌ Failed to get persona: {e}")
            raise Exception(f"Failed to get persona: {str(e)}")
    
    def update_persona(self, agent_id: str, request: PersonaUpdateRequest) -> Persona:
        """Update persona for an agent"""
        try:
            # Get existing persona
            persona_ref = self.personas_collection.document(agent_id)
            persona_doc = persona_ref.get()
            
            if not persona_doc.exists:
                raise Exception(f"Persona not found for agent: {agent_id}")
            
            # Build update data (only include non-None fields)
            update_data = {}
            if request.name is not None:
                update_data["name"] = request.name
            if request.role is not None:
                update_data["role"] = request.role
            if request.tone is not None:
                update_data["tone"] = request.tone
            if request.language is not None:
                update_data["language"] = request.language
            if request.response_length is not None:
                update_data["response_length"] = request.response_length
            if request.guidelines is not None:
                update_data["guidelines"] = request.guidelines
            
            # Always update the timestamp
            update_data["updated_at"] = datetime.now(timezone.utc)
            
            # Update persona in Firestore
            persona_ref.update(update_data)
            
            # Also update agent name if it changed
            if request.name is not None:
                agent_ref = self.agents_collection.document(agent_id)
                agent_ref.update({
                    "name": request.name,
                    "updated_at": datetime.now(timezone.utc)
                })
            
            # Also update agent role and tone if changed
            agent_update = {}
            if request.role is not None:
                agent_update["role"] = request.role
            if request.tone is not None:
                agent_update["tone"] = request.tone
            if agent_update:
                agent_update["updated_at"] = datetime.now(timezone.utc)
                agent_ref = self.agents_collection.document(agent_id)
                agent_ref.update(agent_update)
            
            # Return updated persona
            updated_doc = persona_ref.get()
            updated_data = updated_doc.to_dict()
            
            logger.info(f"✅ Persona updated for agent: {agent_id}")
            return Persona(**updated_data)
            
        except Exception as e:
            logger.error(f"❌ Failed to update persona: {e}")
            raise Exception(f"Failed to update persona: {str(e)}")
    
    def get_agents_by_session(self, session_id: str) -> List[Agent]:
        """Get all agents for a session"""
        try:
            agents_refs = self.agents_collection.where('session_id', '==', session_id).where('active', '==', True).stream()
            
            agents = []
            for agent_doc in agents_refs:
                agent_data = agent_doc.to_dict()
                agents.append(Agent(**agent_data))
            
            return agents
            
        except Exception as e:
            logger.error(f"❌ Failed to get agents by session: {e}")
            return []
    
    def get_all_agents(self) -> List[Agent]:
        """Get all active agents"""
        try:
            agents_refs = self.agents_collection.where('active', '==', True).stream()
            
            agents = []
            for agent_doc in agents_refs:
                agent_data = agent_doc.to_dict()
                agents.append(Agent(**agent_data))
            
            return agents
            
        except Exception as e:
            logger.error(f"❌ Failed to get all agents: {e}")
            return []
    
    def delete_agent(self, agent_id: str) -> bool:
        """Delete agent and cascade delete related data"""
        try:
            # Delete agent
            agent_ref = self.agents_collection.document(agent_id)
            agent_ref.delete()
            
            # Delete persona
            persona_ref = self.personas_collection.document(agent_id)
            persona_ref.delete()
            
            # Delete knowledge (cascade)
            knowledge_refs = self.firestore_client.collection('knowledge').where('agent_id', '==', agent_id).stream()
            for knowledge_ref in knowledge_refs:
                knowledge_ref.reference.delete()
            
            # Delete rules (cascade)
            rule_refs = self.firestore_client.collection('rules').where('agent_id', '==', agent_id).stream()
            for rule_ref in rule_refs:
                rule_ref.reference.delete()
            
            # Delete chat logs (cascade)
            chat_refs = self.firestore_client.collection('chat_logs').where('agent_id', '==', agent_id).stream()
            for chat_ref in chat_refs:
                chat_ref.reference.delete()
            
            logger.info(f"✅ Agent deleted: {agent_id}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to delete agent: {e}")
            raise Exception(f"Failed to delete agent: {str(e)}")
    
    def cleanup_old_agents(self, days_old: int = 7) -> int:
        """Delete agents older than N days"""
        try:
            from datetime import timedelta
            
            cutoff_date = datetime.now(timezone.utc) - timedelta(days=days_old)
            
            # Find old agents
            old_agents = self.agents_collection.where('created_at', '<', cutoff_date).stream()
            
            deleted_count = 0
            for agent_doc in old_agents:
                agent_id = agent_doc.id
                self.delete_agent(agent_id)
                deleted_count += 1
            
            logger.info(f"✅ Cleaned up {deleted_count} old agents")
            return deleted_count
            
        except Exception as e:
            logger.error(f"❌ Failed to cleanup old agents: {e}")
            raise Exception(f"Failed to cleanup old agents: {str(e)}")

