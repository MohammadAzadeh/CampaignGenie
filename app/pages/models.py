from datetime import datetime
from typing import Optional, Literal

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


# Create Literal types for type safety
CategoryType = Literal[
    "بیماری و درمان",
    "جراحی و خدمات زیبایی",
    "سبک زندگی سالم",
    "جشن‌ها و مراسمات",
    "مراقبت زیبایی و بهداشت فردی",
    "مد و پوشاک",
    "ورزش",
    "خودرو",
    "املاک",
    "مدرسه و کنکور سراسری",
    "کسب و کار",
    "اقتصاد",
    "صنعت و کشاورزی",
    "سرمایه شخصی",
    "تکنولوژی",
    "تجهیزات الکترونیک شخصی",
    "بازی ویدیویی",
    "کتاب و ادبیات",
    "خدمات",
    "سرگرمی و مهارت و هنر",
    "مذهب",
    "علم و دانش",
    "تفریح",
    "سفر و گردشگری",
    "سینما و تلویزیون و تئاتر",
    "موسیقی",
    "عامه پسند",
    "خانواده",
    "روابط عاطفی",
    "والدین",
    "لوازم و تجهیزات خانه",
    "ساخت و ساز و تغییر دکوراسیون",
    "غذا و نوشیدنی",
    "حیوانات خانگی",
    "زبان آموزی",
    "رمز ارز",
    "دانشگاه و تحصیلات عالی",
    "اشتغال",
    "مهاجرت",
    "حقوق",
    "سیاست",
    "اجتماعی",
]

UserSegmentType = CategoryType  # Same type since they use the same values


class Landing(BaseModel):
    address: str = Field(..., title="address of the landing")
    type: str = Field(..., title="type of landing")


class Business(BaseModel):
    name: str = Field(..., title="name of the business")
    type: str = Field(..., title="type of business")
    description: Optional[str] = Field(
        None, description="Brief description of the business"
    )


class MarketingExperience(BaseModel):
    is_traditional: bool = Field(..., description="Is traditional marketing experience")
    is_digital: bool = Field(..., description="Is digital marketing experience")
    description: str = Field(..., description="Description of marketing experience")
    spent_budget: str = Field(..., description="Amount of budget spent on marketing")
    feedback: str = Field(
        ..., description="Feedback or results from marketing experience"
    )


class CampaignRequest(BaseModel):
    business: Business = Field(..., title="Business")
    goal: str = Field(..., description="Advertising or marketing goal")
    target_audience: str = Field(..., title="Target Audience")
    locations: list[str] = Field(..., title="Locations")
    daily_budget: PositiveInt = Field(..., title="Daily Budget", gt=0)
    total_budget: PositiveInt = Field(..., title="Daily Budget", gt=0)
    landing: Landing = Field(..., title="Landing")
    experiences: Optional[list[MarketingExperience]] = Field(
        ...,
        description="List of previous marketing experiences",
        default_factory=list,
    )


class CampaignRequestDB(CampaignRequest):
    id: Optional[str] = None  # This is the MongoDB ID
    campaign_request_id: str
    advertiser_id: str
    status: Literal["new", "in_progress", "completed", "failed"]
    created_at: datetime
    session_id: str


class CampaignConfig(BaseModel):
    keywords: list[str] = Field(
        ...,
        description="Keywords to target, it should be keywords that are related to the business or intersting to the target audience",
    )
    user_segments: list[UserSegmentType] = Field(
        ..., description="User segments to target."
    )
    categories: list[CategoryType] = Field(..., description="Categories to target.")


class Image(BaseModel):
    source: Literal["generate", "user_asset"]
    image_url: Optional[str] = Field(
        None, description="Image URL, if source is user_asset"
    )
    prompt: Optional[str] = Field(
        None, description="Image generation prompt for ad, if source is generate"
    )


class AdDescription(BaseModel):
    title: str
    landing_url: str
    image: Image
    call_to_action: str = Field(
        ..., description="Engaging Call to Action, Less than 13 characters."
    )


class CampaignPlan(BaseModel):
    type: Literal["native", "banner"] = Field(...)
    name: str = Field(..., description="A short name consisting of goal and campaign type")
    business_description: str = Field(...)
    goal: str = Field(
        ..., description="Goal of the campaign | What satisfies the business owner?"
    )
    description: str = Field(...)
    budget: int = Field(..., ge=700_000, le=10_000_000)
    bidding_strategy: Literal["cpc"] = Field(...)
    bid_toman: int = Field(
        2000,
        ge=2000,
        le=1000000,
    )
    target_audience_description: str = Field(...)
    targeting_config: CampaignConfig
    ads_description: list[AdDescription]


class AdDescriptionDB(AdDescription):
    created_ad_id: Optional[str] = None


class CampaignPlanDB(CampaignPlan):
    id: Optional[str] = None  # This is the MongoDB ID
    campaign_plan_id: str
    task_session_id: str
    campaign_request_id: str
    created_at: datetime = Field(default_factory=datetime.utcnow, title="Created At")
    ads_description: list[AdDescriptionDB]


class Task(BaseModel):
    id: Optional[str] = None  # This is the MongoDB ID
    type: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    description: str
    session_id: str


class GenerateCampaignPlanTask(Task):
    type: Literal["generate_campaign_plan"]
    campaign_request_id: str
    campaign_plan_id: Optional[str] = None
    feedbacks: list[str] = Field(default_factory=list)
    status: Literal[
        "new",  # Task is created and waiting for execution
        "pending_confirm",  # Task is waiting for confirmation in panel
        "retry_with_feedback",  # Task should be retried with feedback
        "confirmed",  # Task is confirmed and waiting for completion
        "completed",  # Task is completed
        "failed",  # Task is failed
    ]


class CreateYektanetCampaignTask(Task):
    type: Literal["create_yektanet_campaign"]
    campaign_plan_id: str
    campaign_request_id: str
    created_campaign_id: Optional[str] = None
    created_ads: list[str] = []
    status: Literal[
        "new",  # Task is created and waiting for execution
        "create_ads",  # campaign created successfully, waiting for ads creation
        "completed",  # Task is completed
        "failed",  # Task is failed
    ]
    retry_count: int = 0
