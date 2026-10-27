import asyncio
import json
import os
import random
from aiohttp import web

# 接続中のプレイヤー一覧
CONNECTED_PLAYERS = set()

# 🎯 対戦で使える英単語リスト（定番＆よく使われる5文字単語）
WORD_LIST = [
    "CRANE", "SLATE", "DRESS", "TRILL", "HOLEY", "PILOT", "SHIRT", "ROBOT",
    "WATER", "LIGHT", "MUSIC", "PLANT", "SPACE", "SWEET", "HEART", "DREAM",
    "CLOUD", "GHOST", "TRAIN", "APPLE", "HOUSE", "MOUSE", "SMILE", "PEACE",
    "STORM", "FLAME", "MAGIC", "POWER", "NIGHT", "BEACH", "CHIPS", "LUNCH",
    "STORY", "WORLD", "FRONT", "STAND", "GREEN", "BLIND", "TRUCK", "SHINE", 
    "JUICE", "BLOCK", "SLEEP", "DANCE", "FROST", "BRUSH", "FLUTE", "SKATE", 
    "STAMP", "SHORE", "PRIDE", "CRISP", "GRAIN", "CROWN", "SPARK", "CHASE", 
    "BRAIN", "BREAD", "BROWN", "KNOCK", "RADIO", "GRAND", "SNAKE", "GRASS", 
    "MATCH", "VOICE", "SOUND", "PAPER", "ANIME", "CREAM", "CHEEK", "ROUND", 
    "COUNT", "BLOCK", "HEAVY", "LEMON", "SHARP", "BLAST", "FLOOR", "FLUID",
    "ANGEL", "ALERT", "AUDIO", "BASIC", "BEAST", "BLADE", "BLENT", "BLINK", 
    "BOOST", "BRING", "CABLE", "CANDY", "CARGO", "CHEST", "CHIEF", "CHILD", 
    "CIVIL", "CLERK", "COACH", "CRAFT", "DRINK", "DRIVE", "EARTH", "EMPTY", 
    "ENTRY", "EQUAL", "EVENT", "EVERY", "EXTRA", "FIGHT", "FIRST", "FOCUS", 
    "FORGE", "FRAME", "GRAPE", "GUARD", "GUIDE", "HOTEL", "INDEX", "INPUT", 
    "LUCKY", "MARCH", "MODEL", "MOTOR", "MOUTH", "NOBLE", "OCEAN", "PIANO", 
    "QUICK"
]

# 現在の試合のお題（最初の1人が来たら選ばれる）
CURRENT_TARGET = None

def get_new_target():
    global CURRENT_TARGET
    CURRENT_TARGET = random.choice(WORD_LIST)
    print(f"🎯 新しいお題決定: {CURRENT_TARGET}")
    return CURRENT_TARGET

async def index(request):
    html_path = os.path.join(os.path.dirname(__file__), "battle.html")
    if os.path.exists(html_path):
        with open(html_path, "r", encoding="utf-8") as f:
            return web.Response(text=f.read(), content_type="text/html")
    return web.Response(text="battle.html not found", status=404)

async def websocket_handler(request):
    global CURRENT_TARGET
    ws = web.WebSocketResponse()
    await ws.prepare(request)

    # 最初のプレイヤーが来たときにお題を新しく決める
    if len(CONNECTED_PLAYERS) == 0 or CURRENT_TARGET is None:
        get_new_target()

    CONNECTED_PLAYERS.add(ws)
    print(f"🎮 プレイヤー接続 (現在 {len(CONNECTED_PLAYERS)} 人)")

    try:
        # 接続したプレイヤーに現在のお題を送信（2人とも同じ単語になる！）
        await ws.send_str(json.dumps({
            "type": "init",
            "target": CURRENT_TARGET
        }))

        async for msg in ws:
            if msg.type == web.WSMsgType.TEXT:
                data = json.loads(msg.data)

                # どちらかが勝ったら、次回の試合のために新しいお題をセット！
                if data.get("win"):
                    get_new_target()

                # 相手にブロードキャスト
                for p in CONNECTED_PLAYERS:
                    if p != ws and not p.closed:
                        await p.send_str(msg.data)
    finally:
        CONNECTED_PLAYERS.remove(ws)
        print("プレイヤー退出")
        # 全員抜けたらお題をリセット
        if len(CONNECTED_PLAYERS) == 0:
            CURRENT_TARGET = None

    return ws

app = web.Application()
app.router.add_get("/", index)
app.router.add_get("/ws", websocket_handler)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    print(f"🚀 サーバー起動 (ポート: {port})")
    web.run_app(app, host="0.0.0.0", port=port)
