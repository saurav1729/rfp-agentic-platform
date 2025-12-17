from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum

class RFPStatus(str, Enum):
    DISCOVERED = "discovered"
    QUALIFIED = "qualified"
    IN_PROGRESS = "in_progress"
    SUBMITTED = "submitted"
    WON = "won"
    LOST = "lost"

class WorkflowStage(str, Enum):
    DISCOVERY = "discovery"
    QUALIFICATION = "qualification"
    ANALYSIS = "analysis"
    PRICING = "pricing"
    PROPOSAL = "proposal"
    SUBMISSION = "submission"

class RFPModel(BaseModel):
    """MongoDB document model for RFPs"""
    id: Optional[str] = Field(default=None, alias="_id")
    external_id: str  # CPP reference number
    title: str
    description: Optional[str] = None
    agency: Optional[str] = None
    deadline: Optional[datetime] = None
    source_url: str
    budget_range: Optional[str] = None
    status: str = RFPStatus.DISCOVERED
    discovered_at: datetime = Field(default_factory=datetime.utcnow)
    confidence_score: float = 0.0
    posted_date: Optional[datetime] = None
    raw_data: Optional[Dict[str, Any]] = None  # Additional portal data
    
    class Config:
        allow_population_by_field_name = True

class WorkflowModel(BaseModel):
    """MongoDB document model for Workflows"""
    id: Optional[str] = Field(default=None, alias="_id")
    rfp_id: str
    current_stage: str = WorkflowStage.DISCOVERY
    data: Optional[Dict[str, Any]] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    agent_results: Optional[Dict[str, Any]] = None
    
    class Config:
        allow_population_by_field_name = True

class ProposalModel(BaseModel):
    """MongoDB document model for Proposals"""
    id: Optional[str] = Field(default=None, alias="_id")
    rfp_id: str
    workflow_id: str
    technical_summary: str = ""
    pricing_summary: str = ""
    proposal_content: str = ""
    status: str = "draft"
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        allow_population_by_field_name = True
