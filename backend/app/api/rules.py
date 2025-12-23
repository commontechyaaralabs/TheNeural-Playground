from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List

from ..models import (
    RuleSaveRequest, RuleResponse, RuleListResponse,
    ErrorResponse
)
from ..services.rules_service import RulesService

router = APIRouter(prefix="/rules", tags=["agent"])


def get_rules_service():
    return RulesService()


@router.post("/save", response_model=RuleResponse)
async def save_rule(
    request: RuleSaveRequest,
    rules_service: RulesService = Depends(get_rules_service)
):
    """
    Create or update a rule.
    
    This endpoint:
    1. Validates WHEN condition
    2. Validates DO action
    3. Stores rule as deterministic config
    """
    try:
        rule = rules_service.save_rule(request)
        return RuleResponse(data=rule)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("", response_model=RuleListResponse)
async def get_rules(
    agent_id: str = Query(..., description="Agent ID"),
    rules_service: RulesService = Depends(get_rules_service)
):
    """
    List all rules for an agent.
    
    Used to reload rule configuration in UI.
    """
    try:
        rules = rules_service.get_rules(agent_id)
        return RuleListResponse(data=rules)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

