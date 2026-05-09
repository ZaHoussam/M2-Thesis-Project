# ================================================================
#  test_connection.py — connectivity check before enrollment
#  Run with: python test_connection.py
#  Delete after use
# ================================================================
import httpx
import asyncio
import websockets
import json


SERVER_REST = "http://localhost:8000"
SERVER_WS   = "ws://localhost:8000/ws/verify"


async def test():

    print("\n" + "="*50)
    print("  CONNECTION TEST")
    print("="*50)

    # ── Test 1: Basic HTTP ping ───────────────────────────────
    print("\n  [1] Testing HTTP connection...")
    try:
        async with httpx.AsyncClient(timeout=5) as client:
            resp = await client.get(f"{SERVER_REST}/")
            print(f"      ✅ HTTP OK — status {resp.status_code}")
            print(f"      Response: {resp.text[:80]}")
    except httpx.ConnectError:
        print("      ❌ FAILED — server not reachable at", SERVER_REST)
        print("      → Is uvicorn running? Check Terminal 1.")
        return
    except Exception as e:
        print(f"      ❌ ERROR: {e}")
        return

    # ── Test 2: Health endpoint ───────────────────────────────
    print("\n  [2] Testing /health endpoint...")
    try:
        async with httpx.AsyncClient(timeout=5) as client:
            resp = await client.get(f"{SERVER_REST}/health")
            print(f"      ✅ Health OK — {resp.text[:80]}")
    except Exception as e:
        print(f"      ❌ ERROR: {e}")

    # ── Test 3: Enroll endpoint exists ────────────────────────
    print("\n  [3] Testing /enroll endpoint exists...")
    try:
        async with httpx.AsyncClient(timeout=5) as client:
            # Send empty body — expect 422 (validation error) not 404
            resp = await client.post(f"{SERVER_REST}/enroll", json={})
            if resp.status_code == 422:
                print(f"      ✅ /enroll exists — returned 422 (validation, expected)")
            elif resp.status_code == 404:
                print(f"      ❌ /enroll NOT FOUND — router not registered in main.py")
            else:
                print(f"      ⚠️  /enroll returned {resp.status_code}: {resp.text[:80]}")
    except Exception as e:
        print(f"      ❌ ERROR: {e}")

    # ── Test 4: WebSocket connection ──────────────────────────
    print("\n  [4] Testing WebSocket connection...")
    try:
        async with websockets.connect(SERVER_WS, open_timeout=5) as ws:
            print(f"      ✅ WebSocket connected")
            # Send a dummy payload
            await ws.send(json.dumps({"embedding": [0.0]*512, "lab_id": 1}))
            response = await asyncio.wait_for(ws.recv(), timeout=5)
            print(f"      ✅ WebSocket response: {response[:80]}")
    except ConnectionRefusedError:
        print("      ❌ WebSocket REFUSED — server not running or wrong port")
    except Exception as e:
        print(f"      ❌ WebSocket ERROR: {type(e).__name__}: {e}")

    # ── Test 5: Debug env ─────────────────────────────────────
    print("\n  [5] Testing server config via /debug...")
    try:
        async with httpx.AsyncClient(timeout=5) as client:
            resp = await client.get(f"{SERVER_REST}/debug")
            if resp.status_code == 200:
                print(f"      ✅ Config OK — {resp.text[:120]}")
            else:
                print(f"      ⚠️  /debug returned {resp.status_code}")
                print(f"         Add the debug route to server/main.py first")
    except Exception as e:
        print(f"      ❌ ERROR: {e}")

    print("\n" + "="*50)
    print("  TEST COMPLETE")
    print("="*50 + "\n")


if __name__ == "__main__":
    asyncio.run(test())