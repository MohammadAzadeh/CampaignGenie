from pydantic import BaseModel, Field
from typing import Optional, List


class LandingDetail(BaseModel):
    webpage: Optional[str] = Field(
        None, description="Business webpage URL"
    )
    telegram: Optional[str] = Field(
        None, description="Telegram contact or channel"
    )
    instagram: Optional[str] = Field(
        None, description="Instagram profile link"
    )
    whatsapp: Optional[str] = Field(
        None, description="WhatsApp contact number or link"
    )
    phone_number: Optional[str] = Field(
        None, description="Business phone number"
    )


class BusinessDetail(BaseModel):
    name: str = Field(
        ..., description="Business name"
    )
    type: str = Field(
        ..., description="Type or category of the business"
    )
    location: Optional[str] = Field(
        None, description="Business location or address"
    )
    landing: LandingDetail = Field(
        ..., description="Landing detail information"
    )
    description: Optional[str] = Field(
        None, description="Brief description of the business"
    )


class BudgetDetail(BaseModel):
    daily_budget: int = Field(
        ..., description="Daily budget in toman"
    )
    total_budget: int = Field(
        ..., description="Total budget in toman"
    )


class MarketingExperience(BaseModel):
    is_traditional: bool = Field(
        ..., description="Is traditional marketing experience"
    )
    is_digital: bool = Field(
        ..., description="Is digital marketing experience"
    )
    description: str = Field(
        ..., description="Description of marketing experience"
    )
    spent_budget: str = Field(
        ..., description="Amount of budget spent on marketing"
    )
    feedback: str = Field(
        ..., description="Feedback or results from marketing experience"
    )


class UserRequest(BaseModel):
    id: int = Field(
        ..., description="Unique request ID"
    )
    advertiser_id: int = Field(
        ..., description="ID of the advertiser in Yektanet"
    )
    business_detail: BusinessDetail = Field(
        ..., description="Details about the business"
    )
    goal: str = Field(
        ..., description="Advertising or marketing goal"
    )
    budget: BudgetDetail = Field(
        ..., description="Budget details"
    )
    target_audience: Optional[str] = Field(
        None, description="Target audience"
    )
    experiences: List[MarketingExperience] = Field(
        ..., description="List of previous marketing experiences"
    )

