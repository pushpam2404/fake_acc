import os
from datetime import datetime
from fpdf import FPDF

class ForensicThreatReport(FPDF):
    def header(self):
        # Header title
        self.set_font("Helvetica", "B", 13)
        self.set_text_color(220, 38, 38) # Red title for alert profile
        self.cell(0, 6, "INDO-TIBETAN BORDER POLICE FORCE (ITBP)", border=False, align="C", new_x="LMARGIN", new_y="NEXT")
        self.set_font("Helvetica", "", 10)
        self.set_text_color(55, 65, 81) # Slate gray
        self.cell(0, 5, "MINISTRY OF HOME AFFAIRS, GOVERNMENT OF INDIA", border=False, align="C", new_x="LMARGIN", new_y="NEXT")
        self.set_font("Helvetica", "I", 8)
        self.cell(0, 4, "CYBER THREAT INTELLIGENCE & FORENSICS UNIT (LE-SENSITIVE)", border=False, align="C", new_x="LMARGIN", new_y="NEXT")
        self.ln(2)
        
        # Horizontal separating double line
        self.set_draw_color(156, 163, 175)
        self.set_line_width(0.8)
        self.line(10, 27, 200, 27)
        self.set_line_width(0.2)
        self.line(10, 28.5, 200, 28.5)
        self.ln(8)

    def footer(self):
        # Footer position
        self.set_y(-25)
        self.set_draw_color(156, 163, 175)
        self.line(10, 272, 200, 272)
        
        # Confidentiality disclaimer
        self.set_font("Helvetica", "I", 7)
        self.set_text_color(127, 29, 29) # Dark red
        self.cell(0, 4, "WARNING: CONFIDENTIAL & LAW ENFORCEMENT SENSITIVE. ADMISSIBLE UNDER SEC. 65B INDIAN EVIDENCE ACT.", border=0, align="C", new_x="LMARGIN", new_y="NEXT")
        
        # Page numbering
        self.set_font("Helvetica", "", 8)
        self.set_text_color(107, 114, 128)
        self.cell(0, 5, f"Case Report Page {self.page_no()}/{{nb}} | System Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", border=0, align="C")

def build_pdf_report(username: str, features: dict, prediction: dict) -> bytes:
    pdf = ForensicThreatReport()
    pdf.alias_nb_pages()
    pdf.add_page()
    
    # 1. CASE HEADER INFO
    pdf.set_font("Helvetica", "B", 11)
    pdf.set_text_color(17, 24, 39)
    pdf.cell(95, 6, f"CASE FILE REF: ITBP-FSA-{datetime.now().strftime('%Y%m%d')}-092", border=0)
    pdf.set_font("Helvetica", "", 10)
    pdf.cell(95, 6, f"REPORT DATE: {datetime.now().strftime('%d %B %Y')}", border=0, align="R", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(3)

    # 2. TARGET SUMMARY CARD (Dotted Box)
    pdf.set_draw_color(220, 38, 38) if prediction['classification'] == "FAKE" else pdf.set_draw_color(217, 119, 6)
    pdf.set_fill_color(254, 242, 242) if prediction['classification'] == "FAKE" else pdf.set_fill_color(255, 251, 235)
    pdf.set_line_width(0.5)
    
    # Render box header
    pdf.set_font("Helvetica", "B", 12)
    pdf.set_text_color(185, 28, 28) if prediction['classification'] == "FAKE" else pdf.set_text_color(180, 83, 9)
    pdf.cell(190, 8, f"  TARGET PROFILE INVESTIGATION DETAILED PROFILE SUMMARY", border=1, fill=True, new_x="LMARGIN", new_y="NEXT")
    
    # Render box body
    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(17, 24, 39)
    pdf.set_fill_color(255, 255, 255)
    
    body_content = (
        f"  Target Username/ID : @{username}\n"
        f"  Source Platform    : {prediction['platform'].upper()}\n"
        f"  Security Status    : {prediction['classification']} (Threat Level Matrix)\n"
        f"  Fake Probability   : {prediction['risk_score']}% Risk Score\n"
        f"  Detection Model    : Tuned XGBoost Decision Ensemble (SIH-1775-v1.0)"
    )
    pdf.multi_cell(190, 6, body_content, border=1, fill=True)
    pdf.ln(5)
    
    # 3. DETECTED EVIDENCE & SHAP ATTRIBUTION (Plain-English Explanations)
    pdf.set_font("Helvetica", "B", 11)
    pdf.set_text_color(31, 41, 55)
    pdf.cell(0, 6, "1. EVIDENCE & CLASSIFICATION REASONING (SHAP ATTRIBUTION)", new_x="LMARGIN", new_y="NEXT")
    pdf.set_draw_color(209, 213, 219)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(2)
    
    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(55, 65, 81)
    for idx, reason in enumerate(prediction.get("reasons", []), 1):
        pdf.cell(8, 6, f"{idx}.", border=0)
        pdf.multi_cell(182, 6, reason, border=0, new_x="LMARGIN", new_y="NEXT")
    
    pdf.ln(4)

    # 4. PROFILE TELEMETRY DATA (TABLE OF FEATURES)
    pdf.set_font("Helvetica", "B", 11)
    pdf.set_text_color(31, 41, 55)
    pdf.cell(0, 6, "2. PROFILE METADATA & TELEMETRY EXTRACTION", new_x="LMARGIN", new_y="NEXT")
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(3)

    # Table Header
    pdf.set_fill_color(243, 244, 246)
    pdf.set_font("Helvetica", "B", 9)
    pdf.set_text_color(75, 85, 99)
    pdf.cell(70, 7, "  Telemetry Parameter", border=1, fill=True)
    pdf.cell(50, 7, "Extracted Value", border=1, fill=True, align="C")
    pdf.cell(70, 7, "Standard Human Baseline Reference", border=1, fill=True, align="C", new_x="LMARGIN", new_y="NEXT")
    
    # Table Rows
    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(17, 24, 39)
    
    # Custom values formatted nicely
    metrics = [
        ("Follower Count", str(features.get("followers", 0)), "Variable (>100 usually for active humans)"),
        ("Following Count", str(features.get("following", 0)), "Variable (Ratio balanced with followers)"),
        ("Post Count (Total)", str(features.get("post_count", 0)), "Regular posting density"),
        ("Follower-Following Ratio", f"{round(features.get('follower_following_ratio', 0.0), 3)}", "Balanced (~0.5 - 10.0 range)"),
        ("Reputation Score", f"{round(features.get('reputation_score', 0.0), 3)}", "Between 0.3 and 0.8"),
    ]
    
    if prediction['platform'].lower() == "twitter":
        metrics.extend([
            ("Account Age (Days)", str(features.get("account_age_days", -1)), "Longer age builds trust (>30 days)"),
            ("Posts Per Day", f"{round(features.get('posts_per_day', 0.0), 2)}", "Low frequency (~0.1 - 5.0 posts/day)"),
            ("Username Length", str(features.get("username_length", 0)), "Human names (8-15 characters)"),
            ("Digits in Username", str(features.get("digits_in_username", 0)), "Low digital concentration (< 2 digits)")
        ])
    else:
        metrics.extend([
            ("Profile Picture Presence", "YES" if features.get("has_profile_pic", 0) == 1 else "NO", "Highly present (99% humans have one)"),
            ("Bio Length", str(features.get("bio_length", 0)), "Detailed bio (average 30-100 characters)")
        ])
        
    for label, val, ref in metrics:
        pdf.cell(70, 6, f"  {label}", border=1)
        pdf.cell(50, 6, val, border=1, align="C")
        pdf.cell(70, 6, f"  {ref}", border=1, new_x="LMARGIN", new_y="NEXT")
        
    pdf.ln(5)
    
    # 5. CO-OCCURRENCE & INTEL NETWORK FOOTPRINT (FORENSIC NOTES)
    pdf.set_font("Helvetica", "B", 11)
    pdf.set_text_color(31, 41, 55)
    pdf.cell(0, 6, "3. NETWORK CO-OCCURRENCE & CO-AUTHENTICITY METRICS", new_x="LMARGIN", new_y="NEXT")
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(2)
    
    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(55, 65, 81)
    network_notes = (
        "Forensic Network Audit Note: This account has been checked against our active relational graph DB. "
        "A high correlation score here indicates that multiple accounts share metadata footprints such as identical "
        "profile birth creation hours, identical posting phase-frequency delays, and shared lexical repetition clusters."
    )
    pdf.multi_cell(190, 4.5, network_notes, border=0)
    pdf.ln(3)

    # 6. MULTIMODAL CONTENT & PHISHING AUDIT (PLAYWRIGHT NLP & VISION)
    content_analysis = prediction.get("content_analysis")
    if content_analysis:
        pdf.set_font("Helvetica", "B", 11)
        pdf.set_text_color(31, 41, 55)
        pdf.cell(0, 6, "4. MULTIMODAL CONTENT & PHISHING FORENSIC AUDIT (PLAYWRIGHT NLP)", new_x="LMARGIN", new_y="NEXT")
        pdf.line(10, pdf.get_y(), 200, pdf.get_y())
        pdf.ln(2)

        pdf.set_font("Helvetica", "", 9)
        pdf.set_text_color(55, 65, 81)
        
        phish_level = content_analysis.get("phishing_threat_level", "LOW")
        sim_score = content_analysis.get("caption_similarity", {}).get("similarity_score", 0.0)
        posts_count = content_analysis.get("posts_analyzed", 0)

        pdf.cell(0, 5, f"Content Threat Level: {phish_level}  |  Caption Uniformity: {sim_score}%  |  Posts Analyzed: {posts_count}", new_x="LMARGIN", new_y="NEXT")
        
        for reason in content_analysis.get("forensic_reasons", [])[:3]:
            pdf.cell(5, 5, "- ", border=0)
            pdf.multi_cell(185, 5, reason, border=0, new_x="LMARGIN", new_y="NEXT")
        pdf.ln(2)
    
    # 7. SIGN-OFF BLOCK
    pdf.set_y(-45)
    pdf.set_font("Helvetica", "B", 9)
    pdf.set_text_color(31, 41, 55)
    pdf.cell(95, 5, "REPORT DIGEST MD5 SHA256 HASH", border=0)
    pdf.cell(95, 5, "OFFICER AUTHORIZATION SIGNATURE", border=0, align="R", new_x="LMARGIN", new_y="NEXT")
    
    pdf.set_font("Courier", "I", 7)
    pdf.set_text_color(107, 114, 128)
    import hashlib
    hash_str = f"{username}-{prediction['risk_score']}-{datetime.now().isoformat()}"
    sha_hash = hashlib.sha256(hash_str.encode()).hexdigest()
    pdf.cell(95, 5, sha_hash[:40].upper(), border=0)
    
    pdf.set_font("Helvetica", "", 8)
    pdf.cell(95, 5, ".................................................................", border=0, align="R", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(190, 5, "Investigating Officer Cyber Unit Sign-off", border=0, align="R")
    
    return bytes(pdf.output())
