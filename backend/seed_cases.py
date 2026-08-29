"""
backend/seed_cases.py
=====================
Seeds the cases.db with 8-10 realistic mock cases spanning all four statuses
and both platforms. Called once on startup if the table is empty.

Handle names and SHAP reasons text match the style in frontend/src/presets.ts
so the demo dashboard is never empty on first load.
"""

import json
import uuid
from datetime import datetime, timezone, timedelta

from backend.cases import SessionLocal, Case, create_tables


SEED_CASES = [
    # ── TWITTER / FAKE ──────────────────────────────────────────────────────
    {
        "platform": "twitter",
        "handle": "bot987654321",
        "risk_score": 94.7,
        "classification": "FAKE",
        "reasons": [
            "Following/Follower ratio is 375x (4,500 following vs 12 followers) — characteristic of coordinated follow-spam botnet",
            "Account age is 2 days with 5,000 posts — posts-per-day rate of 2,500 is mechanically impossible for a human actor",
            "Username contains 9 consecutive digits — high digit-density pattern associated with auto-generated bot handles",
            "Zero description length — profile bio completely absent, typical of mass-created throwaway accounts",
            "External URL present on a brand-new account with no followers — likely phishing redirect vector",
        ],
        "status": "TAKEDOWN_CONFIRMED",
        "reviewed_by": "Inspector R. Sharma",
        "report_generated": True,
        "created_at_offset_hours": -96,
        "updated_at_offset_hours": -12,
    },
    {
        "platform": "twitter",
        "handle": "crypto_guy_99",
        "risk_score": 67.3,
        "classification": "SUSPICIOUS",
        "reasons": [
            "Following/Follower ratio is 9x (1,900 following vs 210 followers) — inflated follow-back farming pattern",
            "60-day-old account with only 25 posts — low activity concealing possible dormant botnet node",
            "Minimal bio at 14 characters — insufficient identity verification, likely synthetic persona",
            "External URL on low-follower account — probable affiliate redirect or unregistered promotion",
            "Username suffix '99' combined with crypto-related display name — common social engineering pattern for investment fraud",
        ],
        "status": "REPORT_SENT",
        "reviewed_by": "Analyst P. Nair",
        "report_generated": True,
        "created_at_offset_hours": -72,
        "updated_at_offset_hours": -24,
    },
    {
        "platform": "twitter",
        "handle": "official_pmoindia_real",
        "risk_score": 88.4,
        "classification": "FAKE",
        "reasons": [
            "Threat Forensics: Handle uses spoofing prefix 'official_' with government entity name — identity impersonation pattern detected",
            "Threat Forensics: Display name token overlap with @PMOIndia is 0% — handle morphology contradicts claimed identity",
            "Account age is 14 days — recent creation of government-impersonation account matches known coordinated disinformation campaigns",
            "High digit-density in username combined with authority-claim keywords — synthetic persona disclosure signature",
            "No verified badge on account claiming to be official government communication channel",
        ],
        "status": "UNDER_REVIEW",
        "reviewed_by": "Inspector R. Sharma",
        "report_generated": False,
        "created_at_offset_hours": -48,
        "updated_at_offset_hours": -6,
    },
    {
        "platform": "twitter",
        "handle": "reel_virat_kohli_official",
        "risk_score": 91.2,
        "classification": "FAKE",
        "reasons": [
            "Threat Forensics: Identity token discrepancy — display name 'Virat Kohli' with handle 'reel_virat_kohli_official' shares 0% canonical token match",
            "Threat Forensics: Handle uses celebrity clone prefixes ('reel_', 'official') — confirmed impersonation signature",
            "1,988 followers vs 48,000 following — inverted ratio inconsistent with a celebrity account of this claimed identity",
            "Only 2 posts on an account impersonating a public figure with 260M+ real followers",
            "Bio contains Telegram funnel link — standard celebrity impersonation-to-investment-scam pipeline",
        ],
        "status": "FLAGGED",
        "reviewed_by": "Unassigned",
        "report_generated": False,
        "created_at_offset_hours": -2,
        "updated_at_offset_hours": -2,
    },

    # ── META (INSTAGRAM / FACEBOOK) / FAKE ──────────────────────────────────
    {
        "platform": "meta",
        "handle": "stockstrading0",
        "risk_score": 82.1,
        "classification": "FAKE",
        "reasons": [
            "Threat Forensics: Caption uniformity matrix = 81.3% — near-identical promotional flyer templates across all posts indicate coordinated content syndication",
            "Threat Forensics: Bio contains unregistered stock tip funnel (t.me/stocksignal_free) — SEBI-regulated activity without disclosure",
            "Threat Forensics: Outbound redirect to Telegram group with 50,000+ members — confirmed financial fraud funnel",
            "0 followers with 4,000 following — profile optimised for follow-back farming, not genuine engagement",
            "Post content is 100% duplicate marketing flyers — '120 DAYS FREE NIFTY CALLS' repetition is mechanically syndicated",
        ],
        "status": "TAKEDOWN_CONFIRMED",
        "reviewed_by": "Analyst P. Nair",
        "report_generated": True,
        "created_at_offset_hours": -120,
        "updated_at_offset_hours": -48,
    },
    {
        "platform": "meta",
        "handle": "up9o_official_rohit_singh",
        "risk_score": 96.5,
        "classification": "FAKE",
        "reasons": [
            "Threat Forensics: Display name 'virat•kohli' with handle 'up9o_official_rohit_singh' — lexical token overlap is 0%, confirmed celebrity identity clone",
            "Threat Forensics: Avatar matches Virat Kohli's verified Instagram profile photo — visual identity theft",
            "Threat Forensics: Handle contains spoofing prefix 'official_' combined with unrelated name — synthetic persona construction",
            "Only 2 posts and 1,988 followers — account bootstrapping phase typical of newly deployed impersonation campaign",
            "Account has no verification badge while explicitly claiming to be a verified public figure",
        ],
        "status": "REPORT_SENT",
        "reviewed_by": "Inspector R. Sharma",
        "report_generated": True,
        "created_at_offset_hours": -60,
        "updated_at_offset_hours": -18,
    },
    {
        "platform": "meta",
        "handle": "meta_ig_bot_farm_49",
        "risk_score": 78.9,
        "classification": "FAKE",
        "reasons": [
            "Default avatar (no profile picture set) on a 4,000-following account — machine-created account characteristic",
            "0 posts with 4,000 following and 0 followers — pure follow-farm node with no organic content activity",
            "Bio length is 0 — absent identity information consistent with auto-generated account batch",
            "Username contains sequential digits and 'bot_farm' semantic pattern",
            "Account shows no engagement signals — zero likes, zero comments, zero post history",
        ],
        "status": "UNDER_REVIEW",
        "reviewed_by": "Analyst P. Nair",
        "report_generated": False,
        "created_at_offset_hours": -36,
        "updated_at_offset_hours": -4,
    },
    {
        "platform": "meta",
        "handle": "free_iphone_giveaway_2024",
        "risk_score": 73.4,
        "classification": "SUSPICIOUS",
        "reasons": [
            "Threat Forensics: Bio contains phishing-grade prize claim language ('Win FREE iPhone 15 Pro — click link below')",
            "Threat Forensics: External URL resolves to shortened link (bit.ly redirect) — high-risk link obfuscation for credential harvesting",
            "Threat Forensics: Phishing threat level rated ELEVATED — 3 of 5 social engineering indicators positive",
            "Account age is 8 days with 47 posts — rapid-fire posting cadence inconsistent with authentic giveaway accounts",
            "0 followers with 2,100 following — engagement farming setup phase before mass phishing push",
        ],
        "status": "FLAGGED",
        "reviewed_by": "Unassigned",
        "report_generated": False,
        "created_at_offset_hours": -4,
        "updated_at_offset_hours": -4,
    },
    {
        "platform": "twitter",
        "handle": "infowar_cell_77",
        "risk_score": 85.6,
        "classification": "FAKE",
        "reasons": [
            "Threat Forensics: Zero-shot NLP classifier detects coordinated hate campaign signatures — entity defamation threat vector active",
            "Threat Forensics: Bio uses derogatory state-subversion hashtags aligned with known hostile information warfare playbook",
            "Account age is 7 days — newly provisioned node in an active coordinated inauthentic behaviour (CIB) cluster",
            "Following 3,200 accounts within the first week — automated follow-graph seeding consistent with botnet orchestration",
            "Content Threat weight elevated to w2=0.60 via Continuous Multimodal Fusion — tabular score overridden by NLP threat signal",
        ],
        "status": "REPORT_SENT",
        "reviewed_by": "Inspector R. Sharma",
        "report_generated": True,
        "created_at_offset_hours": -80,
        "updated_at_offset_hours": -32,
    },
    {
        "platform": "meta",
        "handle": "loan_offer_fast_approval",
        "risk_score": 69.8,
        "classification": "SUSPICIOUS",
        "reasons": [
            "Threat Forensics: Bio advertises instant personal loan approvals without RBI-registered NBFC disclosure",
            "Threat Forensics: External URL leads to a WhatsApp group invite — financial fraud funnel via unregulated channel",
            "Caption uniformity score of 67.4% — repetitive loan advertisement templates across 35 posts",
            "Profile picture matches stock photo used by 14 other flagged accounts in the CIB cluster database",
            "1 follower vs 890 following — account in follow-farming phase, not yet activated for mass fraud push",
        ],
        "status": "FLAGGED",
        "reviewed_by": "Unassigned",
        "report_generated": False,
        "created_at_offset_hours": -1,
        "updated_at_offset_hours": -1,
    },
]


def seed_cases() -> int:
    """
    Insert seed cases into the database.
    Returns the number of cases inserted.
    Called only if the cases table is empty (idempotent).
    """
    create_tables()
    db = SessionLocal()
    try:
        existing = db.query(Case).count()
        if existing > 0:
            return 0  # Already seeded

        now = datetime.now(timezone.utc)
        inserted = 0

        for data in SEED_CASES:
            offset_created = data.get("created_at_offset_hours", 0)
            offset_updated = data.get("updated_at_offset_hours", 0)
            created_at = now + timedelta(hours=offset_created)
            updated_at = now + timedelta(hours=offset_updated)

            case = Case(
                id=str(uuid.uuid4()),
                platform=data["platform"],
                handle=data["handle"],
                risk_score=float(data["risk_score"]),
                classification=data["classification"],
                reasons=json.dumps(data["reasons"]),
                status=data["status"],
                created_at=created_at,
                updated_at=updated_at,
                reviewed_by=data.get("reviewed_by", "Unassigned"),
                report_generated=bool(data.get("report_generated", False)),
            )
            db.add(case)
            inserted += 1

        db.commit()
        print(f"[seed_cases] Seeded {inserted} mock cases into cases.db.")
        return inserted
    finally:
        db.close()


if __name__ == "__main__":
    # Allow running directly: python -m backend.seed_cases
    n = seed_cases()
    print(f"Done. {n} cases inserted.")
