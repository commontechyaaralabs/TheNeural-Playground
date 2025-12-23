import uuid
import logging
from datetime import datetime, timezone
from typing import List, Optional
from google.cloud import firestore

from ..models import Rule, RuleSaveRequest
from ..config import gcp_clients

logger = logging.getLogger(__name__)


class RulesService:
    """Service layer for rules management"""
    
    def __init__(self):
        self.firestore_client = gcp_clients.get_firestore_client()
        
        # Initialize collections
        self.rules_collection = self.firestore_client.collection('rules')
        
        logger.info("✅ RulesService initialized")
    
    def save_rule(self, request: RuleSaveRequest) -> Rule:
        """Create or update a rule"""
        try:
            logger.info(f"Saving rule for agent: {request.agent_id}")
            
            # Validate WHEN condition
            if not self._validate_condition(request.when):
                raise ValueError("Invalid WHEN condition")
            
            # Validate DO action
            if not self._validate_action(request.do):
                raise ValueError("Invalid DO action")
            
            # Generate rule ID (or use existing if updating)
            rule_id = f"RULE_{uuid.uuid4().hex[:12].upper()}"
            
            # Create rule document
            rule_data = {
                "rule_id": rule_id,
                "agent_id": request.agent_id,
                "name": request.name,
                "when": request.when.model_dump(),
                "do": request.do.model_dump(),
                "priority": request.priority,
                "active": True,
                "created_at": datetime.now(timezone.utc),
                "updated_at": datetime.now(timezone.utc)
            }
            
            # Save to Firestore
            rule_ref = self.rules_collection.document(rule_id)
            rule_ref.set(rule_data)
            
            logger.info(f"✅ Rule saved: {rule_id}")
            
            return Rule(**rule_data)
            
        except Exception as e:
            logger.error(f"❌ Failed to save rule: {e}")
            raise Exception(f"Failed to save rule: {str(e)}")
    
    def _validate_condition(self, condition) -> bool:
        """Validate WHEN condition"""
        try:
            if not hasattr(condition, 'type') or not hasattr(condition, 'value'):
                return False
            
            condition_type = condition.type
            if condition_type not in ['keyword', 'intent', 'sentiment']:
                return False
            
            if condition_type == 'keyword' and not isinstance(condition.value, str):
                return False
            
            if condition_type in ['intent', 'sentiment'] and not isinstance(condition.value, (str, dict)):
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Condition validation failed: {e}")
            return False
    
    def _validate_action(self, action) -> bool:
        """Validate DO action"""
        try:
            if not hasattr(action, 'type') or not hasattr(action, 'value'):
                return False
            
            action_type = action.type
            if action_type not in ['respond', 'redirect', 'skip_llm']:
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Action validation failed: {e}")
            return False
    
    def get_rules(self, agent_id: str) -> List[Rule]:
        """Get all rules for an agent, sorted by priority"""
        try:
            rules_refs = self.rules_collection.where('agent_id', '==', agent_id).where('active', '==', True).stream()
            
            rules = []
            for rule_doc in rules_refs:
                rule_data = rule_doc.to_dict()
                rules.append(Rule(**rule_data))
            
            # Sort by priority (descending)
            rules.sort(key=lambda x: x.priority, reverse=True)
            
            return rules
            
        except Exception as e:
            logger.error(f"❌ Failed to get rules: {e}")
            return []
    
    def delete_rule(self, rule_id: str) -> bool:
        """Delete a rule"""
        try:
            rule_ref = self.rules_collection.document(rule_id)
            rule_ref.delete()
            
            logger.info(f"✅ Rule deleted: {rule_id}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to delete rule: {e}")
            raise Exception(f"Failed to delete rule: {str(e)}")
    
    def evaluate_rules(self, agent_id: str, message: str, conditions: dict) -> Optional[Rule]:
        """
        Evaluate rules against message and conditions
        Returns the first matching rule (highest priority first)
        """
        try:
            rules = self.get_rules(agent_id)
            
            for rule in rules:
                if self._rule_matches(rule, message, conditions):
                    logger.info(f"✅ Rule matched: {rule.rule_id}")
                    return rule
            
            return None
            
        except Exception as e:
            logger.error(f"❌ Failed to evaluate rules: {e}")
            return None
    
    def _rule_matches(self, rule: Rule, message: str, conditions: dict) -> bool:
        """Check if a rule matches the message and conditions"""
        try:
            condition_type = rule.when.type
            condition_value = rule.when.value
            
            if condition_type == 'keyword':
                # Check if keyword is in message (case-insensitive)
                if isinstance(condition_value, str):
                    return condition_value.lower() in message.lower()
            
            elif condition_type == 'intent':
                # Check if intent matches
                detected_intent = conditions.get('intent', {}).get('intent', '')
                if isinstance(condition_value, str):
                    return detected_intent.lower() == condition_value.lower()
                elif isinstance(condition_value, dict):
                    return detected_intent.lower() == condition_value.get('intent', '').lower()
            
            elif condition_type == 'sentiment':
                # Check if sentiment matches
                detected_sentiment = conditions.get('sentiment', {}).get('sentiment', '')
                if isinstance(condition_value, str):
                    return detected_sentiment.lower() == condition_value.lower()
                elif isinstance(condition_value, dict):
                    return detected_sentiment.lower() == condition_value.get('sentiment', '').lower()
            
            return False
            
        except Exception as e:
            logger.error(f"❌ Rule matching failed: {e}")
            return False


