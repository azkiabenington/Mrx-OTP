#!/usr/bin/env python3
"""
Test runner for verifying the 6 newly added OTP target handlers.
Records any failed tests to a text file.
"""
import sys
import os
import time

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from handlers import HANDLERS
from utils import fmt_08, normalize

TEST_KEYS = [
    ("singa_sms", "Singa SMS"),
    ("cititrans_wa", "CitiTrans WhatsApp"),
    ("kredione_voice", "KrediOne Voice Call"),
    ("kreditnavigator_voice", "KreditNavigator Voice Call"),
    ("kreditnavigator_wa", "KreditNavigator WhatsApp"),
    ("adiraku_voice", "Adiraku Voice Call"),
    ("indosaku_wa", "Indosaku WhatsApp"),
    ("beautyhaul_voice", "Beautyhaul Voice Call"),
    ("bonusbelanja_voice", "Bonus Belanja Voice Call"),
]

def run_tests(phone="081298765432", fail_log_path="gagal_test.txt"):
    n62 = normalize(phone)
    n08 = fmt_08(n62)
    results = []
    failures = []

    print(f"=== Testing {len(TEST_KEYS)} OTP Handlers on {n08} ===")
    for key, name in TEST_KEYS:
        fn = HANDLERS.get(key)
        if not fn:
            status_line = f"[MISSING] {name} ({key}): Handler not registered in HANDLERS"
            print(status_line)
            results.append((key, False, "handler not registered"))
            failures.append(status_line)
            continue

        try:
            ok, detail = fn(n08, n62, n08)
            status_tag = "[SUCCESS]" if ok else "[COOLDOWN]" if detail in ("cooldown", "rate limit") else "[FAIL]"
            status_line = f"{status_tag} {name} ({key}): ok={ok}, detail='{detail}'"
            print(status_line)
            results.append((key, ok, detail))
            if not ok and detail not in ("cooldown", "rate limit"):
                failures.append(f"{name} ({key}) - Detail: {detail}")
        except Exception as exc:
            status_line = f"[EXCEPTION] {name} ({key}): {exc}"
            print(status_line)
            results.append((key, False, str(exc)))
            failures.append(f"{name} ({key}) - Exception: {exc}")

    if failures:
        ts = time.strftime("%Y-%m-%d %H:%M:%S")
        with open(fail_log_path, "a", encoding="utf-8") as f:
            f.write(f"\n--- Test Run Failures ({ts}) ---\n")
            for line in failures:
                f.write(f"- {line}\n")
        print(f"\n[INFO] {len(failures)} failure(s) logged to {fail_log_path}")
    else:
        print("\n[INFO] All tested handlers responded with SUCCESS!")

    return results

if __name__ == "__main__":
    run_tests()
