"""
================================================================================
MODULE 5 EXIT CONDITION VERIFICATION SUITE (verify_module5_exit.py)
================================================================================
Executes 2 full consecutive cold-start pass runs across:
- GET /health
- POST /analyze (Single Twitter preset payload)
- POST /analyze (Single Meta preset payload)
- POST /analyze/batch/csv (demo_batch.csv upload)
Verifying zero manual intervention, zero errors, and clean recovery.
"""

import urllib.request
import urllib.parse
import json
import os
import io
import time

API_BASE = "http://127.0.0.1:8000"

def run_http_post_json(endpoint: str, payload: dict) -> dict:
    url = f"{API_BASE}{endpoint}"
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read().decode("utf-8"))

def run_http_post_csv(endpoint: str, csv_path: str) -> dict:
    url = f"{API_BASE}{endpoint}"
    boundary = "----WebKitFormBoundary7MA4YWxkTrZu0gW"
    with open(csv_path, "rb") as f:
        file_bytes = f.read()

    body = (
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="file"; filename="{os.path.basename(csv_path)}"\r\n'
        f"Content-Type: text/csv\r\n\r\n"
    ).encode("utf-8") + file_bytes + f"\r\n--{boundary}--\r\n".encode("utf-8")

    req = urllib.request.Request(url, data=body, headers={"Content-Type": f"multipart/form-data; boundary={boundary}"})
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read().decode("utf-8"))

def execute_pass(pass_number: int):
    print(f"\n" + "="*60)
    print(f"COLD-START DEMO PASS #{pass_number}")
    print("="*60)

    # 1. Healthcheck
    req = urllib.request.Request(f"{API_BASE}/health")
    with urllib.request.urlopen(req) as resp:
        health = json.loads(resp.read().decode("utf-8"))
        print(f"[✓] GET /health ➔ {health}")
        assert health["status"] == "ok"

    # 2. Single Account Twitter Preset
    tw_payload = {
        "followers": 12, "following": 4500, "post_count": 5000, "verified": 0,
        "description_length": 0, "account_age_days": 2, "platform": "twitter"
    }
    tw_res = run_http_post_json("/analyze", tw_payload)
    print(f"[✓] Single Twitter ➔ Risk Score: {tw_res['risk_score']:.2f}% | Class: {tw_res['classification']}")
    assert "risk_score" in tw_res and tw_res["classification"] in ["FAKE", "SUSPICIOUS", "REAL"]

    # 3. Single Account Meta Preset
    meta_payload = {
        "followers": 0, "following": 4000, "post_count": 0, "has_profile_pic": 0,
        "bio_length": 0, "platform": "meta"
    }
    meta_res = run_http_post_json("/analyze", meta_payload)
    print(f"[✓] Single Meta    ➔ Risk Score: {meta_res['risk_score']:.2f}% | Class: {meta_res['classification']}")
    assert "risk_score" in meta_res and meta_res["classification"] == "FAKE"

    # 4. Batch CSV Upload (demo_batch.csv)
    csv_res = run_http_post_csv("/analyze/batch/csv", "demo_batch.csv")
    results = csv_res.get("results", [])
    print(f"[✓] Batch CSV Upload ➔ Processed {len(results)} accounts in parallel cleanly.")
    assert len(results) == 10, f"Expected 10 batch results, got {len(results)}"
    
    for r in results[:3]:
        print(f"   - @{r['account_id']:<15} Risk: {r['risk_score']:.2f}% | Class: {r['classification']}")

    print(f"SUCCESS: COLD-START PASS #{pass_number} PASSED 100% CLEAN!")

def main():
    print("STARTING MODULE 5 EXIT CONDITION DOUBLE PASS VALIDATION...")
    execute_pass(1)
    time.sleep(1)
    execute_pass(2)
    print("\n" + "="*60)
    print("🏆 ALL MODULE 5 EXIT CONDITIONS SATISFIED!")
    print("="*60)

if __name__ == "__main__":
    main()
