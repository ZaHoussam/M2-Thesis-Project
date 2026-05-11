# ================================================================
#  core/ws_client.py — WebSocket auth client
#  Sends embeddings to server, receives decisions,
#  pushes display state back to camera process.
# ================================================================
import json
import asyncio
import httpx
import websockets
from multiprocessing import Queue

from config import settings


class AuthClient:

    def __init__(self, state_queue: Queue):
        self.state_queue = state_queue   # sends display state to camera process
        self.mfa_token   = None
        self._state      = {
            "state":     "SCANNING",
            "score":     None,
            "user_name": None,
            "bbox":      None,
        }

    def _push_state(self):
        """Send current display state to camera process."""
        try:
            # Clear old state first — only latest matters
            while not self.state_queue.empty():
                self.state_queue.get_nowait()
            self.state_queue.put_nowait(dict(self._state))
        except Exception:
            pass

    def _set_state(self, state: str, score=None, user_name=None):
        self._state["state"]     = state
        self._state["score"]     = score
        self._state["user_name"] = user_name
        self._push_state()

    async def run(self, embedding_queue: asyncio.Queue):
        """Auto-retry connection loop."""
        while True:
            try:
                async with websockets.connect(settings.server_ws_url) as ws:
                    print(f"[CLIENT] Connected to {settings.server_ws_url}")
                    await self._handle(ws, embedding_queue)
            except (ConnectionRefusedError, OSError):
                print("[CLIENT] Server not reachable — retrying in 3s...")
                self._set_state("SCANNING")
                await asyncio.sleep(3)
            except Exception as e:
                print(f"[CLIENT] Connection lost: {e} — retrying in 3s...")
                self._set_state("SCANNING")
                await asyncio.sleep(3)

    async def _handle(self, ws, embedding_queue: asyncio.Queue):
        while True:
            if self._state["state"] == "SCANNING":
                embedding = await embedding_queue.get()

                await ws.send(json.dumps({
                    "embedding": embedding,
                    "lab_id":    settings.lab_id,
                }))

                response = json.loads(await ws.recv())
                decision = response.get("decision")
                score    = response.get("similarity_score")

                print(f"[AUTH] {decision} — score: {score}  margin: {response.get('margin')}")

                if decision == "ALLOW":
                    self._set_state("ALLOW", score, response.get("user_name"))
                    await asyncio.sleep(2.5)
                    self._set_state("SCANNING")

                elif decision == "DENY":
                    self._set_state("DENY", score)
                    await asyncio.sleep(1.5)
                    self._set_state("SCANNING")

            else:
                await asyncio.sleep(0.05)