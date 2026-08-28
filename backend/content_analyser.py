import re
import math
import logging
from typing import List, Dict, Any, Optional
import numpy as np

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ContentAnalyser")

# Lazy-load sentence transformer to ensure fast server startup
_embedding_model = None

def get_embedding_model():
    global _embedding_model
    if _embedding_model is None:
        try:
            logger.info("Initializing SentenceTransformer neural model (all-MiniLM-L6-v2)...")
            from sentence_transformers import SentenceTransformer
            _embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
            logger.info("SentenceTransformer model loaded successfully.")
        except Exception as e:
            logger.warning(f"SentenceTransformer fallback: {e}")
            _embedding_model = False
    return _embedding_model


# Phishing & Scam Intent Signatures (Categorized Threat Vectors)
PHISHING_PATTERNS = [
    {
        "category": "Crypto & Financial Fraud",
        "weight": 35,
        "regex": r"(?i)\b(guaranteed\s+profit|claim\s+airdrop|free\s+crypto|send\s+eth|double\s+your\s+(btc|sol|crypto)|presale\s+live|connect\s+wallet|meta\s*mask|seed\s*phrase|100x\s+returns|trading\s+signals)\b",
        "description": "Cryptocurrency doubling, fraudulent airdrop, or wallet drainer signature."
    },
    {
        "category": "Urgency & Account Impersonation",
        "weight": 30,
        "regex": r"(?i)\b(account\s+will\s+be\s+(deleted|suspended)|verify\s+now|urgent\s+action\s+required|official\s+support\s+desk|security\s+notice|click\s+here\s+immediately|confirm\s+identity)\b",
        "description": "Urgency-inducing impersonation of platform security or support."
    },
    {
        "category": "Off-Platform Redirects & Telegram Traps",
        "weight": 25,
        "regex": r"(?i)\b(dm\s+on\s+telegram|t\.me\/|wa\.me\/|message\s+me\s+on\s+whatsapp|inbox\s+for\s+link|link\s+in\s+bio\s+for\s+free)\b",
        "description": "Off-platform redirect to unmonitored messaging channels (Telegram/WhatsApp)."
    },
    {
        "category": "Giveaway & Phishing Bait",
        "weight": 25,
        "regex": r"(?i)\b(giveaway\s+winner|congratulations\s+you\s+won|claim\s+your\s+reward|free\s+gift\s*card|free\s+iphone|cash\s+app\s+flip|money\s+glitch)\b",
        "description": "High-risk lottery/giveaway lure commonly used to harvest credentials."
    },
    {
        "category": "Suspicious URL Shorteners",
        "weight": 20,
        "regex": r"(?i)\b(bit\.ly|tinyurl\.com|is\.gd|cutt\.ly|shorturl\.at|rb\.gy|linktr\.ee\/[a-zA-Z0-9_\-]+)\b",
        "description": "Obfuscated URL shortener disguising final web destination."
    }
]


def cosine_similarity(vec1: np.ndarray, vec2: np.ndarray) -> float:
    """Calculates cosine similarity between two 1D numpy vectors."""
    dot = np.dot(vec1, vec2)
    norm1 = np.linalg.norm(vec1)
    norm2 = np.linalg.norm(vec2)
    if norm1 == 0 or norm2 == 0:
        return 0.0
    return float(dot / (norm1 * norm2))


def analyze_caption_similarity(captions: List[str]) -> Dict[str, Any]:
    """
    Analyzes semantic and lexical similarity across multiple post captions.
    Uses SentenceTransformer neural embeddings when available, falling back to Jaccard token similarity.
    """
    valid_captions = [c.strip() for c in captions if len(c.strip()) > 5]
    if len(valid_captions) < 2:
        return {
            "similarity_score": 0.0,
            "verdict": "Insufficient post history for cross-caption analysis",
            "is_repetitive": False,
            "method": "insufficient_data"
        }

    model = get_embedding_model()

    if model:
        try:
            # 1. Real Neural Semantic Embeddings (all-MiniLM-L6-v2)
            embeddings = model.encode(valid_captions)
            similarities = []
            for i in range(len(embeddings)):
                for j in range(i + 1, len(embeddings)):
                    sim = cosine_similarity(embeddings[i], embeddings[j])
                    similarities.append(max(0.0, sim))

            avg_similarity = float(np.mean(similarities)) if similarities else 0.0
            similarity_pct = round(avg_similarity * 100, 1)

            if similarity_pct >= 80.0:
                verdict = f"Critical Template Repetition ({similarity_pct}%) — Captions are near-identical automated syndication."
                is_repetitive = True
            elif similarity_pct >= 60.0:
                verdict = f"Elevated Uniformity ({similarity_pct}%) — High structural overlap across published captions."
                is_repetitive = True
            else:
                verdict = f"Organic Diversity ({similarity_pct}%) — Distinct human phrasing across posts."
                is_repetitive = False

            return {
                "similarity_score": similarity_pct,
                "verdict": verdict,
                "is_repetitive": is_repetitive,
                "method": "SentenceTransformer (all-MiniLM-L6-v2)"
            }
        except Exception as e:
            logger.warning(f"Neural embedding failed, falling back to Jaccard: {e}")

    # Fallback: Jaccard Lexical Token Overlap
    jaccard_scores = []
    token_sets = [set(re.findall(r'\w+', c.lower())) for c in valid_captions]
    for i in range(len(token_sets)):
        for j in range(i + 1, len(token_sets)):
            s1, s2 = token_sets[i], token_sets[j]
            union = len(s1 | s2)
            if union > 0:
                jaccard_scores.append(len(s1 & s2) / union)

    avg_jaccard = float(np.mean(jaccard_scores)) if jaccard_scores else 0.0
    similarity_pct = round(avg_jaccard * 100, 1)

    return {
        "similarity_score": similarity_pct,
        "verdict": f"Lexical Similarity ({similarity_pct}%)" if similarity_pct < 60 else f"High Lexical Repetition ({similarity_pct}%)",
        "is_repetitive": similarity_pct >= 60,
        "method": "Jaccard Token Metric"
    }


def scan_text_for_phishing(text: str) -> List[Dict[str, Any]]:
    """Scans text against phishing and fraud threat vector patterns."""
    findings = []
    if not text:
        return findings

    for pattern in PHISHING_PATTERNS:
        matches = re.findall(pattern["regex"], text)
        if matches:
            matched_terms = list(set([m[0] if isinstance(m, tuple) else m for m in matches]))
            findings.append({
                "category": pattern["category"],
                "matched_terms": matched_terms,
                "risk_weight": pattern["weight"],
                "description": pattern["description"]
            })
    return findings


def analyze_multimodal_content(
    bio: str,
    external_url: Optional[str],
    posts: List[Dict[str, Any]],
    avatar_url: Optional[str] = None
) -> Dict[str, Any]:
    """
    Performs comprehensive Multimodal NLP, Content, and Phishing Analysis.
    Combines bio inspection, post caption neural similarity, phishing keyword detection,
    and external link safety audit.
    """
    total_threat_points = 0
    phishing_indicators = []
    forensic_reasons = []

    # 1. Analyze Bio Description
    bio_phishing = scan_text_for_phishing(bio)
    for find in bio_phishing:
        total_threat_points += find["risk_weight"]
        indicator = f"Bio contains {find['category']} triggers: '{', '.join(find['matched_terms'])}'"
        phishing_indicators.append(indicator)
        forensic_reasons.append(f"Profile biography flagged with {find['description']}")

    # 2. Analyze External Link URL
    outbound_link_audit = {
        "url": external_url,
        "risk_level": "SAFE",
        "is_shortened": False,
        "flag": None
    }
    if external_url:
        is_shortener = bool(re.search(r"(bit\.ly|tinyurl\.com|is\.gd|cutt\.ly|t\.me|wa\.me)", external_url, re.I))
        is_risky_tld = bool(re.search(r"\.(xyz|top|ru|click|link|cfd|gq|work)$", external_url, re.I))

        if is_shortener or is_risky_tld:
            total_threat_points += 30
            outbound_link_audit["risk_level"] = "HIGH"
            outbound_link_audit["is_shortened"] = is_shortener
            outbound_link_audit["flag"] = "Obfuscated / High-Risk TLD Destination"
            phishing_indicators.append(f"Outbound link uses suspicious redirect ({external_url})")
            forensic_reasons.append("Outbound bio URL points to an unverified or shortened destination.")
        else:
            outbound_link_audit["risk_level"] = "LOW"

    # 3. Analyze Post Captions & Content
    captions = [p.get("caption", "") for p in posts]
    similarity_analysis = analyze_caption_similarity(captions)

    if similarity_analysis["is_repetitive"]:
        total_threat_points += 35
        forensic_reasons.append(similarity_analysis["verdict"])
        phishing_indicators.append(f"Cross-post caption template uniformity measured at {similarity_analysis['similarity_score']}%")

    # Scan individual post captions for phishing
    post_phishing_hits = 0
    for idx, post in enumerate(posts):
        caption = post.get("caption", "")
        hits = scan_text_for_phishing(caption)
        if hits:
            post_phishing_hits += len(hits)
            for h in hits:
                total_threat_points += int(h["risk_weight"] * 0.5)
                phishing_indicators.append(f"Post #{idx+1} flagged for {h['category']}: '{', '.join(h['matched_terms'])}'")

    if post_phishing_hits > 0:
        forensic_reasons.append(f"{post_phishing_hits} post captions contain active phishing / urgency lures.")

    # 4. Avatar Assessment
    has_avatar = bool(avatar_url and "default" not in avatar_url.lower() and "placeholder" not in avatar_url.lower())
    if not has_avatar:
        total_threat_points += 15
        forensic_reasons.append("Profile lacks custom visual identity (uses system placeholder avatar).")

    # Compute Normalized Content Risk Score (0 - 100)
    content_risk_score = min(100.0, max(0.0, float(total_threat_points)))

    if content_risk_score >= 70:
        phishing_threat_level = "CRITICAL"
    elif content_risk_score >= 40:
        phishing_threat_level = "ELEVATED"
    elif content_risk_score >= 15:
        phishing_threat_level = "MODERATE"
    else:
        phishing_threat_level = "LOW"

    if not forensic_reasons:
        forensic_reasons = ["Multimodal content inspection shows authentic, human-generated captions and safe outbound links."]

    return {
        "content_risk_score": round(content_risk_score, 2),
        "phishing_threat_level": phishing_threat_level,
        "phishing_indicators": phishing_indicators,
        "caption_similarity": similarity_analysis,
        "outbound_link_audit": outbound_link_audit,
        "has_avatar": has_avatar,
        "forensic_reasons": forensic_reasons,
        "posts_analyzed": len(posts)
    }
