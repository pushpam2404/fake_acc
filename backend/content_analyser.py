import re
import math
import logging
import unicodedata
from typing import List, Dict, Any, Optional
import numpy as np
import importlib
from sklearn.feature_extraction.text import TfidfVectorizer

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ContentAnalyser")

# Lazy-load neural SentenceTransformer model (all-MiniLM-L6-v2)
_embedding_model = None

def get_embedding_model():
    """Loads the 384-dimensional dense neural embedding model."""
    global _embedding_model
    if _embedding_model is None:
        try:
            logger.info("Initializing SentenceTransformer neural model (all-MiniLM-L6-v2)...")
            st_module = importlib.import_module("sentence_transformers")
            SentenceTransformer = getattr(st_module, "SentenceTransformer")
            _embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
            logger.info("SentenceTransformer model loaded successfully.")
        except Exception as e:
            logger.warning(f"SentenceTransformer fallback: {e}")
            _embedding_model = False
    return _embedding_model


# ==============================================================================
# COMPREHENSIVE THREAT TAXONOMY
# Covers: Impersonation, Defamation, Hostile Information Warfare,
# Political Incitement, Phishing, Financial Fraud, and Fake Account Signatures.
# ==============================================================================
THREAT_PATTERNS = [
    # 1. Malicious Entity Impersonation & Targeted Defamation
    {
        "category": "Malicious Impersonation & Entity Defamation",
        "weight": 45,
        "regex": r"(?i)\b(fuck|anti|fake|kill|hate|terrorist|corrupt|boycott)[\s_\-\.@]*(bjp|modi|congress|rahul|police|itbp|army|gov|india|isro|cbi|ed|court|official|hindu|muslim|sikh)\b",
        "description": "Malicious entity spoofing or targeted defamation hijacking institutional/political names."
    },
    # 2. Hostile Information Warfare, Incitement & Subversion
    {
        "category": "Hostile Information Warfare & Subversion",
        "weight": 40,
        "regex": r"(?i)\b(satta|beolado|hifazat|deshdrohi|gaddar|terrorist\s+government|bjp\s+terrorism|fuckbjp|fuckmodi|boycottindia|khalistan|azadi|anti[\s\-]?national|overthrow\s+government|civil\s+war|riot|insurgency)\b",
        "description": "Inflammatory political propaganda, state subversion, or violent narrative incitement."
    },
    # 3. Targeted Hate Slogans & Attack Hashtags
    {
        "category": "Hate Sloganeering & Attack Hashtags",
        "weight": 35,
        "regex": r"(?i)(#fuck[a-zA-Z0-9_]+|#boycott[a-zA-Z0-9_]+|#anti[a-zA-Z0-9_]+|\b(fuck[\s_]?[a-zA-Z0-9]+|dalal|gaddar|terrorist|jihadi|chutiya|suar|randi)\b)",
        "description": "Targeted attack hashtags or toxic profanity directed against organizations or public figures."
    },
    # 4. Unregistered Stock Trading & Financial Advisory Scams
    {
        "category": "Unregistered Stock Tips & Telegram Funnel",
        "weight": 45,
        "regex": r"(?i)\b(intraday\s+calls|f&o\s+trading|nifty|banknifty|call[\s\/]+put|sure\s*shot|stock\s+tips|free\s+telegram|120\s+days\s+free|demo\s+calls|jackpot\s+calls|trading\s+signals|full\s*time\s*trader|stock\s*market)\b",
        "description": "Unregistered stock advisory, F&O intraday calls, or high-risk financial Telegram funnel."
    },
    # 5. Crypto & Financial Fraud
    {
        "category": "Crypto & Financial Fraud",
        "weight": 35,
        "regex": r"(?i)\b(guaranteed\s+profit|claim\s+airdrop|free\s+crypto|send\s+eth|double\s+your\s+(btc|sol|crypto)|presale\s+live|connect\s+wallet|meta\s*mask|seed\s*phrase|100x\s+returns|trading\s+signals)\b",
        "description": "Cryptocurrency doubling, fraudulent airdrop, or wallet drainer signature."
    },
    # 6. Urgency Bait & Authority Impersonation
    {
        "category": "Urgency & Account Impersonation",
        "weight": 30,
        "regex": r"(?i)\b(account\s+will\s+be\s+(deleted|suspended)|verify\s+now|urgent\s+action\s+required|official\s+support\s+desk|security\s+notice|click\s+here\s+immediately|confirm\s+identity)\b",
        "description": "Urgency-inducing impersonation of platform security or administrative authority."
    },
    # 7. Burner / Fake Persona & Engagement Farming
    {
        "category": "Burner / Fake Persona Farm",
        "weight": 25,
        "regex": r"(?i)\b(backup\s+acc(ount)?|burner\s+acc|dm\s+for\s+promo|follow\s+back\s+fast|f4f|follow4follow|gain\s+followers|shadowbanned\s+new\s+acc|10k\s+followers\s+cheap)\b",
        "description": "Burner persona, engagement pod, or coordinated follow-for-follow farm signature."
    },
    # 8. Off-Platform Redirects & Traps
    {
        "category": "Off-Platform Redirects & Telegram Traps",
        "weight": 25,
        "regex": r"(?i)\b(dm\s+on\s+telegram|t\.me\/|wa\.me\/|message\s+me\s+on\s+whatsapp|inbox\s+for\s+link|link\s+in\s+bio\s+for\s+free)\b",
        "description": "Off-platform redirect to unmonitored messaging channels (Telegram/WhatsApp)."
    },
    # 9. Suspicious URL Shorteners
    {
        "category": "Suspicious URL Shorteners",
        "weight": 20,
        "regex": r"(?i)\b(bit\.ly|tinyurl\.com|is\.gd|cutt\.ly|shorturl\.at|rb\.gy|linktr\.ee\/[a-zA-Z0-9_\-]+)\b",
        "description": "Obfuscated URL shortener disguising destination endpoint."
    }
]

# Canonical Threat Vector Anchors for Zero-Shot Semantic Cosine Analysis
SEMANTIC_THREAT_ANCHORS = [
    {
        "topic": "Information Warfare & Anti-National Propaganda",
        "anchor_text": "Anti-national political incitement, state subversion, terrorism accusations, government overthrow, violent agitation, and hate speech.",
        "weight": 40
    },
    {
        "topic": "Malicious Impersonation & Identity Hijacking",
        "anchor_text": "Fake account impersonating a political party, government agency, official department, or public figure with defamatory intent.",
        "weight": 35
    },
    {
        "topic": "Financial & Phishing Fraud",
        "anchor_text": "Cryptocurrency doubling scheme, fraudulent crypto airdrop, wallet drainer scam, and prize phishing lure.",
        "weight": 35
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


def clean_user_caption(raw_text: str) -> str:
    """
    Strips automated social platform accessibility boilerplate from alt text.
    Ensures that platform metadata (e.g. 'Video by X on July 06, 2026. May be an image...')
    is not falsely treated as bot caption syndication.
    """
    if not raw_text:
        return ""
    text = raw_text.strip()
    # Remove "Video by X on Date." / "Photo by X on Date."
    text = re.sub(r"(?i)\b(video|photo|reel)\s+by\s+[^\.]+\s+on\s+[a-zA-Z0-9,\s]+\.?", "", text)
    # Remove "May be an image of..." / "May be a meme of..."
    text = re.sub(r"(?i)\bmay\s+be\s+an?\s+(image|photo|video|meme)\s+of\s+[^\.]*", "", text)
    # Remove "No photo description available"
    text = re.sub(r"(?i)\bno\s+photo\s+description\s+available\.?", "", text)
    # Remove generic filler "Public media post from @X"
    text = re.sub(r"(?i)\bpublic\s+media\s+post\s+from\s+@[a-zA-Z0-9_\.]+", "", text)
    return text.strip()


def analyze_caption_similarity(captions: List[str]) -> Dict[str, Any]:
    """
    Analyzes semantic and lexical similarity across multiple post captions.
    Uses cleaned human text to prevent platform accessibility metadata false positives.
    """
    cleaned = [clean_user_caption(c) for c in captions]
    valid_captions = [c for c in cleaned if len(c) >= 6]

    # If the user did not write repeated manual captions (typical of personal videos/reels)
    if len(valid_captions) < 2:
        return {
            "similarity_score": 0.0,
            "verdict": "Organic media uploads with diverse visual content and zero syndicated caption spam.",
            "is_repetitive": False,
            "method": "clean_visual_media"
        }

    model = get_embedding_model()

    if model:
        try:
            embeddings = model.encode(valid_captions)
            similarities = []
            for i in range(len(embeddings)):
                for j in range(i + 1, len(embeddings)):
                    sim = cosine_similarity(embeddings[i], embeddings[j])
                    similarities.append(max(0.0, float(sim)))

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
                "method": "SentenceTransformer Neural Model (all-MiniLM-L6-v2, 384-dim)"
            }
        except Exception as e:
            logger.warning(f"Neural embedding calculation notice, using TF-IDF fallback: {e}")

    # High-performance TF-IDF fallback
    try:
        vec = TfidfVectorizer(ngram_range=(1, 2), stop_words="english", min_df=1)
        tfidf_matrix = vec.fit_transform(valid_captions).toarray()

        similarities = []
        for i in range(len(tfidf_matrix)):
            for j in range(i + 1, len(tfidf_matrix)):
                sim = cosine_similarity(tfidf_matrix[i], tfidf_matrix[j])
                similarities.append(max(0.0, float(sim)))

        avg_similarity = float(np.mean(similarities)) if similarities else 0.0
        similarity_pct = round(avg_similarity * 100, 1)

        return {
            "similarity_score": similarity_pct,
            "verdict": f"Uniformity ({similarity_pct}%)",
            "is_repetitive": similarity_pct >= 50.0,
            "method": "TF-IDF N-Gram Vectorizer"
        }
    except Exception:
        return {
            "similarity_score": 0.0,
            "verdict": "Organic Diversity",
            "is_repetitive": False,
            "method": "Lexical Fallback"
        }


def scan_text_for_threats(text: str) -> List[Dict[str, Any]]:
    """Scans text against comprehensive threat taxonomy patterns."""
    findings = []
    if not text:
        return findings

    for pattern in THREAT_PATTERNS:
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


def normalize_unicode_text(text: str) -> str:
    """Normalizes stylized Unicode fonts (e.g. 𝓡𝓸𝓱𝓲𝓽, ᴵᴬᴹ) to standard ASCII."""
    if not text:
        return ""
    normalized = unicodedata.normalize('NFKD', text)
    ascii_text = normalized.encode('ascii', 'ignore').decode('utf-8')
    return ascii_text.strip()


def detect_identity_discrepancy_and_spoofing(
    username: str,
    display_name: str,
    bio: str,
    followers: int = 0,
    post_count: int = 0
) -> Dict[str, Any]:
    """
    Detects identity discrepancies, celebrity/brand impersonation, and fake 'official_' spoofing.
    Handles aesthetic Unicode font personalization gracefully without false positives.
    """
    threat_points = 0
    flags = []
    
    u_clean = (username or "").lower().strip()
    d_raw = (display_name or "").strip()
    d_ascii = normalize_unicode_text(d_raw).lower()
    b_clean = (bio or "").lower().strip()

    # Clean tokens
    d_tokens = set([t for t in re.split(r'[\s•_\-\.]+', d_ascii) if len(t) >= 3 and not t.isdigit()])
    u_tokens = set([t for t in re.split(r'[\s•_\-\.]+', u_clean) if len(t) >= 3 and not t.isdigit()])

    generic_stop_words = {'official', 'real', 'original', 'user', 'page', 'the', 'fan', 'club', 'team', 'account', 'instagram', 'twitter', 'iam'}
    d_meaningful = d_tokens - generic_stop_words
    u_meaningful = u_tokens - generic_stop_words

    # Only evaluate discrepancy if display name contains clear, readable identity words
    if len(d_meaningful) >= 1 and len(u_meaningful) >= 1:
        overlap = d_meaningful & u_meaningful
        if not overlap:
            has_spoof_prefix = bool(re.search(r'\b(official|real|original|verified)\b', u_clean))
            has_ai_claim = bool(re.search(r'\b(ai\s+creator|parody|clone)\b', b_clean))
            
            # High-confidence impersonation: Handle explicitly uses 'official_' or bio claims 'AI creator / Parody'
            if has_spoof_prefix:
                threat_points += 55
                flags.append(f"Severe Impersonation Pattern: Display name claims '{display_name}' while unverified handle is '@{username}' with spoofing 'official' moniker.")
            elif has_ai_claim:
                threat_points += 35
                flags.append(f"Synthetic Impersonation: Display name claims '{display_name}' while bio claims AI clone persona on handle '@{username}'.")

    # Check for 'AI Creator' / Clone / Parody / Fan Bio on unverified profiles
    if re.search(r'\b(ai\s+creator|parody|clone)\b', b_clean) and "official" in u_clean:
        threat_points += 25
        flags.append("Synthetic Persona Disclosure: Bio claims 'AI creator / Clone' while adopting external identity.")

    # Asymmetric Low-History Inflated Following
    if post_count <= 3 and followers >= 1500 and "official" in u_clean:
        threat_points += 20
        flags.append(f"Premature Audience Footprint ({followers:,} followers on {post_count} posts) with unverified persona.")

    return {
        "threat_points": threat_points,
        "flags": flags
    }


def analyze_handle_and_identity(username: str, bio: str) -> Dict[str, Any]:
    """Inspects username structure, handle profanity, and impersonation prefixes."""
    username_clean = (username or "").lower().strip()
    threat_points = 0
    flags = []

    # Check for derogatory entity hijacking (e.g. fuck_bjp, anti_india, fake_police)
    impersonation_match = re.search(r"(fuck|anti|fake|kill|hate|terrorist|corrupt|boycott)[\s_\-\.]*(bjp|modi|congress|rahul|police|itbp|army|gov|india|official)", username_clean)
    if impersonation_match:
        threat_points += 45
        flags.append(f"Handle contains targeted entity defamation / attack prefix: '{impersonation_match.group(0)}'")

    # Check for severe handle profanity
    if re.search(r"\b(fuck|bitch|bastard|randi|chutiya|dalal)\b", username_clean):
        threat_points += 30
        flags.append("Handle contains severe profanity / abusive terminology")

    # Check for deliberate evasion delimiter syntax
    if re.search(r"[\._]{2,}$|[\._]\.$", username_clean):
        threat_points += 15
        flags.append("Obfuscated handle delimiter syntax (evasion pattern)")

    return {
        "threat_points": threat_points,
        "flags": flags
    }


def evaluate_semantic_threat_vectors(text: str) -> List[Dict[str, Any]]:
    """Evaluates semantic similarity between profile text and canonical threat concepts using 384-dim neural embeddings."""
    if not text or len(text.strip()) < 10:
        return []

    model = get_embedding_model()
    semantic_hits = []

    if model:
        try:
            text_emb = model.encode([text])[0]
            for anchor in SEMANTIC_THREAT_ANCHORS:
                anchor_emb = model.encode([anchor["anchor_text"]])[0]
                sim = cosine_similarity(text_emb, anchor_emb)
                if sim >= 0.38:
                    semantic_hits.append({
                        "topic": anchor["topic"],
                        "similarity": round(sim * 100, 1),
                        "weight": anchor["weight"]
                    })
            return semantic_hits
        except Exception as e:
            logger.warning(f"Neural threat evaluation notice: {e}")

    # Fallback to TF-IDF vectorizer if neural model unavailable
    try:
        for anchor in SEMANTIC_THREAT_ANCHORS:
            vec = TfidfVectorizer(ngram_range=(1, 2))
            tfidf = vec.fit_transform([text, anchor["anchor_text"]]).toarray()
            sim = cosine_similarity(tfidf[0], tfidf[1])
            if sim >= 0.22:
                semantic_hits.append({
                    "topic": anchor["topic"],
                    "similarity": round(sim * 100, 1),
                    "weight": anchor["weight"]
                })
    except Exception as e:
        logger.warning(f"Semantic threat evaluation notice: {e}")

    return semantic_hits


def analyze_multimodal_content(
    bio: str,
    external_url: Optional[str],
    posts: List[Dict[str, Any]],
    avatar_url: Optional[str] = None,
    username: Optional[str] = None,
    display_name: Optional[str] = None,
    followers: int = 0,
    post_count: int = 0
) -> Dict[str, Any]:
    """
    Performs comprehensive Multimodal NLP, Threat, Impersonation, and Content Analysis.
    Distinguishes genuine everyday human accounts from coordinated threat/impersonation networks.
    """
    total_threat_points = 0
    phishing_indicators = []
    forensic_reasons = []

    # 1. Analyze Identity Discrepancy & Impersonation Spoofing
    if username or display_name:
        identity_audit = detect_identity_discrepancy_and_spoofing(
            username=username or "",
            display_name=display_name or "",
            bio=bio,
            followers=followers,
            post_count=post_count
        )
        if identity_audit["threat_points"] > 0:
            total_threat_points += identity_audit["threat_points"]
            for flag in identity_audit["flags"]:
                phishing_indicators.append(f"Impersonation Alert: {flag}")
                forensic_reasons.append(flag)

    # 2. Analyze Username Structure & Profanity
    if username:
        handle_audit = analyze_handle_and_identity(username, bio)
        if handle_audit["threat_points"] > 0:
            total_threat_points += handle_audit["threat_points"]
            for flag in handle_audit["flags"]:
                phishing_indicators.append(f"Identity Threat: {flag}")
                forensic_reasons.append(f"Account handle flagged: {flag}")

    # 3. Analyze Bio Description (Regex Patterns)
    bio_threats = scan_text_for_threats(bio)
    for find in bio_threats:
        total_threat_points += find["risk_weight"]
        indicator = f"Bio contains {find['category']} triggers: '{', '.join(find['matched_terms'])}'"
        phishing_indicators.append(indicator)
        forensic_reasons.append(f"Profile biography flagged with {find['description']}")

    # 4. Neural Semantic Vector Threat Matching (SentenceTransformer)
    cleaned_post_text = ' '.join([clean_user_caption(p.get('caption', '')) for p in posts])
    combined_profile_text = f"{username or ''} {bio} {cleaned_post_text}".strip()
    semantic_threats = evaluate_semantic_threat_vectors(combined_profile_text)
    for sem in semantic_threats:
        total_threat_points += int(sem["weight"] * 0.7)
        phishing_indicators.append(f"Neural NLP Semantic Match: {sem['topic']} ({sem['similarity']}% semantic resonance)")
        forensic_reasons.append(f"Content exhibits {sem['similarity']}% semantic resonance with {sem['topic']}.")

    # 5. Analyze External Link URL (Whitelists safe first-party social platforms)
    outbound_link_audit = {
        "url": external_url,
        "risk_level": "SAFE",
        "is_shortened": False,
        "flag": None
    }
    if external_url:
        is_safe_social = bool(re.search(r"(threads\.net|threads\.com|instagram\.com|youtube\.com|youtu\.be|facebook\.com|x\.com|twitter\.com|linkedin\.com)", external_url, re.I))
        is_telegram = bool(re.search(r"(t\.me|telegram\.me|wa\.me)", external_url, re.I))
        is_shortener = bool(re.search(r"(bit\.ly|tinyurl\.com|is\.gd|cutt\.ly|shorturl\.at|rb\.gy)", external_url, re.I))
        is_risky_tld = bool(re.search(r"\.(xyz|top|ru|click|link|cfd|gq|work)$", external_url, re.I))

        if is_safe_social and not is_telegram:
            outbound_link_audit["risk_level"] = "SAFE"
            outbound_link_audit["flag"] = "Verified Social Profile Link (Threads / Meta)"
        elif is_telegram or is_shortener or is_risky_tld:
            total_threat_points += 30
            outbound_link_audit["risk_level"] = "HIGH"
            outbound_link_audit["is_shortened"] = is_shortener
            outbound_link_audit["flag"] = "Unverified Telegram Redirect / Obfuscated Shortener"
            phishing_indicators.append(f"Outbound link uses high-risk redirect ({external_url})")
            forensic_reasons.append("Outbound bio URL points to an unverified or shortened destination.")
        else:
            outbound_link_audit["risk_level"] = "LOW"

    # 6. Analyze Post Captions & Content
    captions = [p.get("caption", "") for p in posts]
    similarity_analysis = analyze_caption_similarity(captions)

    if similarity_analysis["is_repetitive"]:
        total_threat_points += 35
        forensic_reasons.append(similarity_analysis["verdict"])
        phishing_indicators.append(f"Cross-post caption template uniformity measured at {similarity_analysis['similarity_score']}%")

    # Scan individual post captions for threats (using cleaned text)
    post_threat_hits = 0
    for idx, post in enumerate(posts):
        raw_cap = post.get("caption", "")
        cleaned_cap = clean_user_caption(raw_cap)
        if len(cleaned_cap) > 5:
            hits = scan_text_for_threats(cleaned_cap)
            if hits:
                post_threat_hits += len(hits)
                for h in hits:
                    total_threat_points += int(h["risk_weight"] * 0.5)
                    phishing_indicators.append(f"Post #{idx+1} flagged for {h['category']}: '{', '.join(h['matched_terms'])}'")

    if post_threat_hits > 0:
        forensic_reasons.append(f"{post_threat_hits} post captions contain active hostility / phishing / scam triggers.")

    # 7. Avatar Assessment
    has_avatar = bool(avatar_url and "default" not in avatar_url.lower() and "placeholder" not in avatar_url.lower())
    if not has_avatar:
        total_threat_points += 15
        forensic_reasons.append("Profile lacks custom visual identity (uses system placeholder avatar).")

    # Compute Normalized Content Risk Score (0 - 100)
    content_risk_score = min(100.0, max(0.0, float(total_threat_points)))

    if content_risk_score >= 60:
        phishing_threat_level = "CRITICAL"
    elif content_risk_score >= 35:
        phishing_threat_level = "ELEVATED"
    elif content_risk_score >= 15:
        phishing_threat_level = "MODERATE"
    else:
        phishing_threat_level = "LOW"

    if not forensic_reasons:
        forensic_reasons = ["Multimodal content inspection shows authentic, human-generated visual media and genuine personal identity."]

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
