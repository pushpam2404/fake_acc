from pydantic import BaseModel
from typing import List, Optional

class AccountFeatures(BaseModel):
    followers: int
    following: int
    post_count: int
    verified: Optional[int] = 0
    description_length: Optional[int] = 0
    account_age_days: Optional[int] = -1
    follower_following_ratio: Optional[float] = None
    reputation_score: Optional[float] = None
    username_length: Optional[int] = 0
    digits_in_username: Optional[int] = 0
    digit_ratio_username: Optional[float] = 0.0
    has_url: Optional[int] = 0
    posts_per_day: Optional[float] = None
    has_profile_pic: Optional[int] = 0
    bio_length: Optional[int] = 0
    platform: Optional[str] = "auto"

class AnalyzeResponse(BaseModel):
    platform: str
    risk_score: float
    classification: str          # "REAL" | "SUSPICIOUS" | "FAKE"
    confidence: float
    reasons: List[str]
    network_graph: Optional[dict] = None


class BatchRequest(BaseModel):
    accounts: List[AccountFeatures]

class ReportRequest(BaseModel):
    username: str
    features: dict
    prediction: dict

class UrlRequest(BaseModel):
    url: str