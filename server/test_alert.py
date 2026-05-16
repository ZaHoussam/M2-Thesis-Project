# ================================================================
#  test_alert.py — manually trigger all three alert patterns
#  Run with: python test_alert.py
#  Delete after testing
# ================================================================
import asyncio
import sys
sys.path.insert(0, ".")

from core.alert_engine import record_attempt, get_lab_state_summary


async def test():
    print("\n" + "="*50)
    print("  ALERT ENGINE TEST")
    print("="*50)

    # ── Test Pattern 1 — 5 DENYs in 60 seconds ───────────────
    print("\n[1] Simulating 5 consecutive DENYs for Lab 1...")
    for i in range(6):
        alerts = record_attempt(lab_id=1, decision="DENY", det_score=0.95)
        state  = get_lab_state_summary(1)
        print(f"    Attempt {i+1}: deny_count={state['deny_count']}  alerts={len(alerts)}")
        if alerts:
            for a in alerts:
                print(f"    🚨 ALERT FIRED: {a['alert_type']} — {a['severity']}")
                print(f"       {a['description']}")

    # ── Test Pattern 2 — 10 attempts in 30 seconds ───────────
    print("\n[2] Simulating 10 rapid attempts for Lab 2...")
    for i in range(11):
        alerts = record_attempt(lab_id=2, decision="ALLOW", det_score=0.98)
        state  = get_lab_state_summary(2)
        print(f"    Attempt {i+1}: attempt_count={state['attempt_count']}  alerts={len(alerts)}")
        if alerts:
            for a in alerts:
                print(f"    🚨 ALERT FIRED: {a['alert_type']} — {a['severity']}")

    # ── Test Pattern 3 — suspicious movement ─────────────────
    print("\n[3] Simulating erratic detection scores for Lab 3...")
    import random
    for i in range(15):
        # Oscillating scores — person moving in and out
        score  = 0.99 if i % 2 == 0 else 0.60
        alerts = record_attempt(lab_id=3, decision="DENY", det_score=score)
        state  = get_lab_state_summary(3)
        print(f"    Frame {i+1}: det_score={score:.2f}  score_count={state['det_score_count']}  alerts={len(alerts)}")
        if alerts:
            for a in alerts:
                print(f"    🚨 ALERT FIRED: {a['alert_type']} — {a['severity']}")
                print(f"       {a['description']}")

    print("\n" + "="*50)
    print("  TEST COMPLETE")
    print("="*50 + "\n")


if __name__ == "__main__":
    asyncio.run(test())