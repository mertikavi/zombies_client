"""
Run the multiplayer signaling server.
Usage: python run.py
"""

import uvicorn

if __name__ == "__main__":
    print("=" * 50)
    print("  Zombi Kaçışı — Multiplayer Sunucusu")
    print("  ws://localhost:8765/ws")
    print("=" * 50)
    uvicorn.run("server:app", host="0.0.0.0", port=8765, reload=True)
