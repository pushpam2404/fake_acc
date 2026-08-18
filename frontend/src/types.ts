export interface AccountFeatures {
  followers: number;
  following: number;
  post_count: number;
  verified?: number;
  description_length?: number;
  account_age_days?: number;
  follower_following_ratio?: number;
  reputation_score?: number;
  username_length?: number;
  digits_in_username?: number;
  digit_ratio_username?: number;
  has_url?: number;
  posts_per_day?: number;
  has_profile_pic?: number;
  bio_length?: number;
  username?: string;
  platform?: "auto" | "twitter" | "meta";
}

export interface AnalyzeResponse {
  platform: "twitter" | "meta" | string;
  risk_score: number;
  classification: "REAL" | "SUSPICIOUS" | "FAKE";
  confidence: number;
  reasons: string[];
}

export interface PresetAccount {
  id: string;
  name: string;
  platform: "twitter" | "meta";
  description: string;
  features: AccountFeatures;
}
