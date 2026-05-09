# ================================================================
#  core/ws_client.py — WebSocket client + MFA state machine
#  Now updates AppState so the display reflects auth results
# ================================================================
import json
import asyncio
import httpx
import websockets
from config import settings


class AuthClient:
    def __init__(self, state):
        self.state     = state        # shared AppState instance
        self.mfa_token = None

    async def run(self, embedding_queue: asyncio.Queue):
        async with websockets.connect(settings.server_ws_url) as ws:
            print(f"[CLIENT] Connected to {settings.server_ws_url}")

            while True:
                if self.state.state == "SCANNING":
                    embedding = await embedding_queue.get()

                    await ws.send(json.dumps({
                        "embedding": embedding,
                        "lab_id":    settings.lab_id,
                    }))
                    response = json.loads(await ws.recv())
                    decision = response.get("decision")

                    self.state.score = response.get("similarity_score")
                    print(f"[AUTH] {decision} — score: {self.state.score}")

                    if decision == "ALLOW":
                        self.state.state     = "ALLOW"
                        self.state.user_name = response.get("user_name")
                        await asyncio.sleep(2.5)
                        self.state.state = "SCANNING"

                    elif decision == "MFA_CHALLENGE":
                        self.mfa_token       = response.get("mfa_token")
                        self.state.state     = "MFA_PENDING"
                        self.state.pin_len   = 0
                        print("[AUTH] Face recognised — enter PIN")

                    elif decision == "DENY":
                        self.state.state = "DENY"
                        await asyncio.sleep(1.5)
                        self.state.state = "SCANNING"

                elif self.state.state == "MFA_PENDING":
                    pin = await asyncio.get_event_loop().run_in_executor(
                        None, self._get_pin
                    )
                    result   = await self._submit_pin(pin)
                    decision = result.get("decision")
                    print(f"[MFA] {decision} — {result.get('message')}")

                    if decision == "MFA_SUCCESS":
                        self.state.state     = "ALLOW"
                        self.state.user_name = result.get("user_name")
                    else:
                        self.state.state = "DENY"

                    await asyncio.sleep(2.5)
                    self.state.state   = "SCANNING"
                    self.state.pin_len = 0
                    self.mfa_token     = None

                else:
                    await asyncio.sleep(0.05)

    def _get_pin(self) -> str:
        """Blocking PIN input — runs in thread executor."""
        pin = ""
        print("Enter PIN (4 digits): ", end="", flush=True)
        while len(pin) < 4:
            import msvcrt
            ch = msvcrt.getwch()
            if ch.isdigit():
                pin += ch
                self.state.pin_len = len(pin)
                print("*", end="", flush=True)
        print()
        return pin

    async def _submit_pin(self, pin: str) -> dict:
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{settings.server_rest_url}/verify-mfa",
                json={"mfa_token": self.mfa_token, "pin": pin},
            )
            return resp.json()