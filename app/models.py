from datetime import datetime
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


class CampaignRequest(BaseModel):
    business_type: str = Field(..., title="Business Type")
    target_audience: str = Field(..., title="Target Audience")
    locations: list[str] = Field(..., title="Locations")
    daily_budget: PositiveInt = Field(..., title="Daily Budget", gt=0)
    landing_type: str = Field(..., title="Landing Type")
    status: str = Field(default="جدید", title="Status")
    created_at: datetime = Field(default_factory=datetime.utcnow, title="Created At")

    class Config:
        validate_assignment = True
        frozen = True
