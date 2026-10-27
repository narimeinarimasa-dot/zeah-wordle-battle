import asyncio
import json
import os
from aiohttp import web

# 接続中のプレイヤー一覧
CONNECTED_PLAYERS = set()
TARGET_WORD = "CRANE"

# HTML画面を返す
async def index(request):
    html_path = os.path.join(os.path.dirname(__file__), "battle.html")
    if os.path.exists(html_path):
        with open(html_path, "r", encoding="utf-8") as f:
            return web.Response(text=f.read(), content_type="text/html")
    return web.Response(text="battle.html not found", status=404)

# WebSocket通信のハンドラ
async def websocket_handler(request):
    ws = web.WebSocketResponse()
    await ws.prepare(request)
    
    CONNECTED_PLAYERS.add(ws)
    print("🎮 プレイヤー接続")

    try:
        # 開始情報を送信
        await ws.send_str(json.dumps({
            "type": "init",
            "target": TARGET_WORD
        }))

        async for msg in ws:
            if msg.type == web.WSMsgType.TEXT:
                # 相手にブロードキャスト
                for p in CONNECTED_PLAYERS:
                    if p != ws and not p.closed:
                        await p.send_str(msg.data)
    finally:
        CONNECTED_PLAYERS.remove(ws)
        print("プレイヤー退出")

    return ws

app = web.Application()
app.router.add_get("/", index)
app.router.add_get("/ws", websocket_handler)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    print(f"🚀 サーバー起動 (ポート: {port})")
    web.run_app(app, host="0.0.0.0", port=port)