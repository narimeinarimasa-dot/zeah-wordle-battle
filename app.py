import asyncio
import json
import os
import random
from aiohttp import web

# ルームごとの管理: { "ルーム名": { "players": set(), "target": "CRANE" } }
ROOMS = {}

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
    "QUICK", "ABOUT", "ABOVE", "ADULT", "AGENT", "AHEAD", "ALIVE", "ALLOW", 
    "ALONE", "ALONG", "ALTER", "AMONG", "ANGER", "APRON", "ARGUE", "ARROW", 
    "ASSET", "AVOID", "AWAKE", "AWARD", "BACON", "BADGE", "BAKER", "BEARD",
    "BEGIN", "BELOW", "BENCH", "BERRY", "BINGO", "BIRTH", "BITER", "BLACK", 
    "BLAME", "BLEED", "BLEND", "BLESS", "BLOCK", "BLOOD", "BOARD", "BOAST",
    "BONUS", "BOUND", "BOWEL", "BRAID", "BRASS", "BREAD", "BRICK", "BRIDE",
    "BRIEF", "BRING", "BROTH", "BRUSH", "BUILD", "BUNCH", "BURST", "BUYER",
    "CABIN", "CABLE", "CAMEL", "CANAL", "CANDY", "CANOE", "CARDS", "CARGO",
    "CARRY", "CARVE", "CATCH", "CAUSE", "CELLO", "CHAIN", "CHAIR", "CHALK",
    "CHAMP", "CHANT", "CHAOS", "CHART", "CHASE", "CHEAT", "CHECK", "CHEEK",
    "CHESS", "CHEST", "CHICK", "CHIEF", "CHILD", "CHILI", "CHILL", "CHIME",
    "CHIPS", "CHOIR", "CHOKE", "CHORD", "CHORE", "CHUCK", "CHUNK", "CHURN",
    "CHUTE", "CIDER", "CIGAR", "HAPPY", "HONEY", "HOTEL", "IMAGE", "INDEX",
    "INNER", "INPUT", "IRONY", "IVORY", "JEANS", "JELLY", "JEWEL", "JOINT",
    "JOKER", "JUDGE", "JUICE", "KNIFE", "KNOCK", "LABEL", "LABOR", "LARGE",
    "LASER", "LAUGH", "LAYER", "LEMON", "LEVEL", "LEVER", "LIMIT", "LIVER",
    "LOCAL", "LOGIC", "LOOSE", "LOVER", "LOYAL", "LUCKY", "LUNCH", "LYRIC",
    "MANGO", "MAJOR", "MARCH", "MATCH", "MEDAL", "MELON", "MERCY", "MERIT",
    "METAL", "MICRO", "MIDST", "MINER", "MINOR", "MINUS", "MIXER", "MODEL",
    "MOIST", "MONEY", "MONTH", "MOTOR", "MOUTH", "MOVIE", "NAKED", "NERVE",
    "NEVER", "NOBLE", "NOISE", "NORTH", "NOTED", "NOVEL", "NURSE", "NYLON",
    "OCEAN", "OFFER", "ONION", "OPERA", "ORBIT", "ORDER", "ORGAN", "OTHER",
    "OUTER", "OWNER", "OZONE", "PADDY", "PAGER", "PAINT", "PANEL", "PAPER",
    "PARTY", "PATIO", "PAUSE", "PEARL", "PEDAL", "PENNY", "PHASE", "PHONE",
    "PHOTO", "PIANO", "PILOT", "PINCH", "PIZZA", "PLAIN", "RADIO", "RAISE",
    "RANGE", "RAPID", "RATIO", "RAYON", "RAZOR", "REACH", "READY", "REALM",
    "REBEL", "RELAX", "REPLY", "RESET", "RESIN", "RIDER", "RIDGE", "RIFLE",
    "RIGHT", "RIGID", "RINSE", "RISKY", "RIVAL", "RIVER", "ROAST", "ROBIN",
    "ROBOT", "RODEO", "ROUGH", "ROUND", "ROUTE", "ROYAL", "RUGBY", "RULER",
    "RUMOR", "RURAL", "SADLY", "SALAD", "SALON", "SALSA", "SALTY", "SATIN",
    "SAUCE", "SCALE", "SCARE", "SCENE", "SCENT", "SCOLD", "SCOOP", "SCOPE",
    "SHARK", "SHINE", "SHORE", "SKATE", "SLEEP", "SNAKE", "SOUND", "SPARK",
    "SPOON", "STAMP", "STAND", "STORY", "TABLE", "TIGER", "TOWER", "TRAIN",
    "TRUCK", "TRUTH", "VOICE", "WHALE", "WORLD", "YOUTH", "ZEBRA", "ZOOMS",
    "ZILCH", "ABYSS", "EPOCH", "GNOME", "KHANA", "QUIRK"
]

async def index(request):
    html_path = os.path.join(os.path.dirname(__file__), "battle.html")
    if os.path.exists(html_path):
        with open(html_path, "r", encoding="utf-8") as f:
            return web.Response(text=f.read(), content_type="text/html")
    return web.Response(text="battle.html not found", status=404)

async def websocket_handler(request):
    ws = web.WebSocketResponse()
    await ws.prepare(request)
    
    current_room = None

    try:
        async for msg in ws:
            if msg.type == web.WSMsgType.TEXT:
                data = json.loads(msg.data)
                mtype = data.get("type")

                # 🚪 入室処理
                if mtype == "join":
                    current_room = data.get("room", "default").strip()
                    if current_room not in ROOMS:
                        ROOMS[current_room] = {
                            "players": set(),
                            "target": random.choice(WORD_LIST)
                        }
                    
                    room_data = ROOMS[current_room]
                    room_data["players"].add(ws)
                    print(f"🚪 入室: ルーム [{current_room}] (人数: {len(room_data['players'])})")

                    # 入室したプレイヤーにお題を送信
                    await ws.send_str(json.dumps({
                        "type": "init",
                        "target": room_data["target"]
                    }))

                # 🎮 プレイ中のメッセージ中継（同じ部屋の人だけに送信！）
                elif mtype == "guess":
                    if current_room in ROOMS:
                        room_data = ROOMS[current_room]
                        if data.get("win"):
                            # 勝敗がついたら次回用にお題を新しく！
                            room_data["target"] = random.choice(WORD_LIST)

                        for p in room_data["players"]:
                            if p != ws and not p.closed:
                                await p.send_str(msg.data)

    finally:
        if current_room and current_room in ROOMS:
            room_data = ROOMS[current_room]
            room_data["players"].discard(ws)
            print(f"🚶 退出: ルーム [{current_room}]")
            if len(room_data["players"]) == 0:
                del ROOMS[current_room]

    return ws

app = web.Application()
app.router.add_get("/", index)
app.router.add_get("/ws", websocket_handler)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    print(f"🚀 サーバー起動 (ポート: {port})")
    web.run_app(app, host="0.0.0.0", port=port)
