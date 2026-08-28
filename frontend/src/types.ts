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

export interface PostMediaItem {
  id: string;
  thumbnail_url: string;
  caption: string;
  likes?: number;
  comments?: number;
  timestamp?: string;
}

export interface ContentAnalysis {
  content_risk_score: number;
  phishing_threat_level: "LOW" | "MODERATE" | "ELEVATED" | "CRITICAL";
  phishing_indicators: string[];
  caption_similarity: {
    similarity_score: number;
    verdict: string;
    is_repetitive: boolean;
    method: string;
  };
  outbound_link_audit: {
    url?: string | null;
    risk_level: string;
    is_shortened: boolean;
    flag?: string | null;
  };
  has_avatar: boolean;
  forensic_reasons: string[];
  posts_analyzed: number;
}

export interface AnalyzeResponse {
  platform: "twitter" | "meta" | string;
  risk_score: number;
  classification: "REAL" | "SUSPICIOUS" | "FAKE";
  confidence: number;
  reasons: string[];
  username?: string;
  raw_features?: AccountFeatures;
  network_graph?: any;
  content_analysis?: ContentAnalysis;
  posts?: PostMediaItem[];
  avatar_url?: string;
  bio?: string;
  external_url?: string;
  multimodal_risk_score?: number;
}

export interface PresetAccount {
  id: string;
  name: string;
  platform: "twitter" | "meta";
  description: string;
  features: AccountFeatures;
}

