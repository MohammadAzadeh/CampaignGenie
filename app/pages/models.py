from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, PositiveInt

IRAN_PROVINCES: list[str] = [
    "آذربایجان شرقی",
    "آذربایجان غربی",
    "اردبیل",
    "اصفهان",
    "البرز",
    "ایلام",
    "بوشهر",
    "تهران",
    "چهارمحال و بختیاری",
    "خراسان جنوبی",
    "خراسان رضوی",
    "خراسان شمالی",
    "خوزستان",
    "زنجان",
    "سمنان",
    "سیستان و بلوچستان",
    "فارس",
    "قزوین",
    "قم",
    "کردستان",
    "کرمان",
    "کرمانشاه",
    "کهگیلویه و بویراحمد",
    "گلستان",
    "گیلان",
    "لرستان",
    "مازندران",
    "مرکزی",
    "هرمزگان",
    "همدان",
    "یزد",
]


class Landing(BaseModel):
    address: str = Field(..., title="address of the landing")
    type: str = Field(..., title="type of landing")


class Business(BaseModel):
    name: str = Field(..., title="name of the business")
    type: str = Field(..., title="type of business")
    description: Optional[str] = Field(None, description="Brief description of the business")


class MarketingExperience(BaseModel):
    is_traditional: bool = Field(..., description="Is traditional marketing experience")
    is_digital: bool = Field(..., description="Is digital marketing experience")
    description: str = Field(..., description="Description of marketing experience")
    spent_budget: str = Field(..., description="Amount of budget spent on marketing")
    feedback: str = Field(..., description="Feedback or results from marketing experience")


class CampaignRequest(BaseModel):
    advertiser_id: int = Field(..., title="ID of the advertiser in Yektanet")
    business: Business = Field(..., title="Business")
    goal: str = Field(..., description="Advertising or marketing goal")
    target_audience: str = Field(..., title="Target Audience")
    locations: list[str] = Field(..., title="Locations")
    daily_budget: PositiveInt = Field(..., title="Daily Budget", gt=0)
    total_budget: PositiveInt = Field(..., title="Daily Budget", gt=0)
    landing: Landing = Field(..., title="Landing")
    experiences: list[MarketingExperience] = Field(..., description="List of previous marketing experiences")
    status: str = Field(default="جدید", title="Status")
    created_at: datetime = Field(default_factory=datetime.utcnow, title="Created At")

    class Config:
        validate_assignment = True
        frozen = True


class CampaignPlan(BaseModel):
    id: int
    needs_confirmation: bool
    campaign_plan: str
