"""Target recommendation data model for AI-identified targets"""
from typing import Optional, List
from pydantic import BaseModel, Field


class TargetRecommendation(BaseModel):
    """AI-generated target recommendation"""
    contact_id: str
    contact_name: str
    company_name: str
    role: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    linkedin_url: Optional[str] = None
    seniority_score: float = Field(ge=0.0, le=1.0, description="Seniority level score 0-1")
    solution_fit: str = Field(description="onlyne_reputation | the_ai_company | both")
    confidence_score: float = Field(ge=0.0, le=1.0, description="Confidence in recommendation 0-1")
    overall_score: Optional[float] = Field(default=None, ge=0.0, le=1.0, description="Overall recommendation score (weighted combination of seniority and confidence)")
    identified_gaps: List[str] = Field(default_factory=list, description="Industry-specific gaps")
    recommended_pitch_angle: Optional[str] = None
    pain_points: List[str] = Field(default_factory=list, description="Industry-specific pain points")
    reasoning: str = Field(description="AI explanation with industry context")
    industry: Optional[str] = None
    knowledge_base_context: Optional[dict] = Field(default=None, description="RAG query results with case studies, services, insights")
    related_case_studies: Optional[List[str]] = Field(default_factory=list, description="IDs or titles of relevant case studies")
    relevant_services: Optional[List[str]] = Field(default_factory=list, description="Relevant service names or IDs")
    relevant_platforms: Optional[List[str]] = Field(default_factory=list, description="Relevant platform names (VANI, Revenue Growth Platform, etc.)")
    relevant_insights: Optional[List[str]] = Field(default_factory=list, description="Relevant industry insights")
    
    def to_dict(self) -> dict:
        """Convert to dictionary for API response"""
        data = self.dict(exclude_none=True)
        # overall_score is now a proper field, so it will be included automatically
        return data
    
    @classmethod
    def from_dict(cls, data: dict) -> 'TargetRecommendation':
        """Create from dictionary"""
        return cls(**data)






