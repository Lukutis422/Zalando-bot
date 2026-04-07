# -*- coding: utf-8 -*-
"""
KODAS BOT V4 ULTIMATE
✅ AI (OpenAI)
✅ Muzika (YouTube)
✅ Ekonomika + Akcijos + Inventorius
✅ Vedybos + Augintiniai + Žvejyba
✅ RPG Kovos + Nuotykiai
✅ Horoskopas + Gimtadieniai
✅ Giveaway sistema
✅ Profesionali Ticket sistema su mygtukais
✅ Anti-raid + Captcha + Auto-mod
✅ Slash komandos
✅ Moderavimas (mute/kick/ban/clear/blacklist)
"""
import discord
from discord import ui, app_commands
import random, os, re, time, json, asyncio, datetime, pathlib, urllib.request
from collections import defaultdict, deque
from dotenv import load_dotenv
try:
    from database import init_db, get_member, update_member, add_coins as db_add_coins, add_xp as db_add_xp
    from database import get_leaderboard_xp, get_leaderboard_coins, add_warning as db_add_warning
    from database import get_warnings as db_get_warnings, clear_warnings as db_clear_warnings
    from database import get_settings, update_settings, get_products as db_get_products
    from database import get_product, create_order as db_create_order, get_orders as db_get_orders
    from database import update_order as db_update_order, create_ticket as db_create_ticket
    from database import get_ticket_by_channel, update_ticket as db_update_ticket
    from database import get_ticket_stats, add_fish as db_add_fish, get_fish_stats as db_get_fish_stats
    from database import deposit, withdraw, take_loan, repay_loan, get_bank_history
    from database import create_giveaway as db_create_giveaway, join_giveaway, get_active_giveaways, end_giveaway
    from database import create_tournament, join_tournament, get_tournament, get_active_tournaments, start_tournament
    from database import process_referral_db, check_achievement_db, get_achievements_db
    from database import set_birthday, get_birthdays, create_marriage, get_marriage, delete_marriage
    from database import create_coupon, get_coupon, validate_coupon, use_coupon, get_coupons, deactivate_coupon
    from database import add_auto_delivery, get_auto_delivery, mark_delivery_used, get_delivery_stock, get_all_deliveries
    from database import create_subscription, get_expiring_subscriptions, get_expired_subscriptions, mark_notified, deactivate_subscription, get_user_subscriptions
    USE_DB = True
    init_db()
    print("✅ SQLite duomenų bazė prijungta!")
except ImportError:
    USE_DB = False
    print("⚠️ database.py nerastas — naudojamas JSON")
except Exception as ex:
    USE_DB = False
    print(f"⚠️ DB klaida: {ex} — naudojamas JSON")
from integrations_v2 import (
    ReactionRoleView, ReactionRoleButton, build_rr_embed,
    is_phishing, build_phishing_embed,
    build_boost_embed, get_spotify, build_spotify_embed,
    build_birthday_embed, build_twitch_embed, build_youtube_embed,
    get_int_settings, upd_int_settings, RR_DATA, save_rr,
    twitch_task, youtube_task
)
from shop_ticket import (
    ShopPanelView, build_shop_embed,
    StaffOrderView, PaymentSelectView,
    PokerGame, PokerView,
    TournamentView
)
from designs_v6 import (
    C, ft, pb, stars, medal, badge,
    embed_balance, embed_daily, embed_work, embed_rank,
    embed_leaderboard_xp, embed_leaderboard_coins, embed_levelup,
    embed_shop_main, embed_order_channel, embed_order_complete,
    embed_ticket_panel, embed_ticket_opened, embed_ticket_claimed, embed_ticket_stats, embed_ticket_rating,
    embed_casino, embed_blackjack_start, embed_blackjack_result,
    embed_trivia, embed_fish, embed_welcome,
    embed_giveaway, embed_battle, embed_stocks, embed_horoscope,
    embed_achievements, embed_now_playing, embed_queue, embed_added_to_queue,
    embed_mod_log, embed_webhook_order, embed_referral,
    TICKET_CATEGORIES_V2, PRIORITIES
)

load_dotenv()
TOKEN          = os.getenv("DISCORD_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

# ══════════════════════════════════════════════════════════════════════════════
#  AI
# ══════════════════════════════════════════════════════════════════════════════
async def ai_chat(system_msg: str, user_text: str, max_tokens=200) -> str:
    if not OPENAI_API_KEY:
        return "AI išjungta. Pridėk OPENAI_API_KEY į .env"
    try:
        import json as _j
        data = _j.dumps({
            "model": "gpt-4o-mini",
            "messages": [{"role":"system","content":system_msg},{"role":"user","content":user_text}],
            "max_tokens": max_tokens
        }).encode()
        req = urllib.request.Request(
            "https://api.openai.com/v1/chat/completions", data=data,
            headers={"Content-Type":"application/json","Authorization":f"Bearer {OPENAI_API_KEY}"}
        )
        loop = asyncio.get_event_loop()
        resp = await loop.run_in_executor(None, lambda: _j.loads(urllib.request.urlopen(req, timeout=15).read()))
        return resp["choices"][0]["message"]["content"].strip()
    except Exception as e:
        return f"AI klaida: {e}"

# ══════════════════════════════════════════════════════════════════════════════
#  DUOMENYS
# ══════════════════════════════════════════════════════════════════════════════
DATA_FILE = str(pathlib.Path(__file__).parent / "data.json")

def load_data():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE,"r",encoding="utf-8") as f: return json.load(f)
        except: pass
    return {}

def save_data(d):
    with open(DATA_FILE,"w",encoding="utf-8") as f:
        json.dump(d,f,indent=2,ensure_ascii=False)

D = load_data()
for k in ("xp","coins","daily_claimed","warnings","rep","rep_claimed","log_channels",
          "welcome_channels","auto_roles","level_rewards","daily_channels","tickets",
          "products","orders","order_counter","payment_methods","work_cooldowns",
          "marriages","pet_data","fish_caught","fish_cooldowns","birthdays",
          "rob_cooldowns","streaks","afk_users","blacklist","stocks","inventory",
          "giveaways","captcha_pending","raid_tracker","suggestions","confessions",
          "starboard_config","message_counts","voice_time","achievements","achieved"):
    D.setdefault(k, {})
save_data(D)

# ══════════════════════════════════════════════════════════════════════════════
#  KONSTANTOS
# ══════════════════════════════════════════════════════════════════════════════
XP_PER_MSG=15; XP_CD=60; LEVEL_XP=200
DAILY_MIN=200; DAILY_MAX=600; DAILY_CD_H=20
WORK_CD=3600; SPAM_LIMIT=6; SPAM_WINDOW=5; WARN_KICK=3
STOCK_UPDATE=300

DEFAULT_PRODUCTS=[
    {"id":1,"name":"Netflix Premium","desc":"4K, 4 ekranai","price":5.99,"old_price":17.99,"category":"streaming","emoji":"🎬","duration":"1 mėn.","stock":99},
    {"id":2,"name":"Netflix Premium","desc":"4K, 4 ekranai","price":14.99,"old_price":49.99,"category":"streaming","emoji":"🎬","duration":"3 mėn.","stock":99},
    {"id":3,"name":"Spotify Premium","desc":"Be reklamu","price":3.99,"old_price":10.99,"category":"music","emoji":"🎵","duration":"1 mėn.","stock":99},
    {"id":4,"name":"YouTube Premium","desc":"Be reklamu","price":4.99,"old_price":13.99,"category":"streaming","emoji":"▶️","duration":"1 mėn.","stock":99},
    {"id":5,"name":"Disney+","desc":"Marvel, Star Wars","price":4.49,"old_price":11.99,"category":"streaming","emoji":"🏰","duration":"1 mėn.","stock":99},
    {"id":6,"name":"Canva Pro","desc":"Premium dizainas","price":3.99,"old_price":12.99,"category":"editing","emoji":"🎨","duration":"1 mėn.","stock":99},
    {"id":7,"name":"NordVPN","desc":"VPN 6 prietaisai","price":2.99,"old_price":11.99,"category":"other","emoji":"🔒","duration":"1 mėn.","stock":99},
]
PAYMENT_META={
    "revolut":{"icon":"💜","label":"Revolut"},
    "paypal":{"icon":"💙","label":"PayPal"},
    "crypto":{"icon":"🪙","label":"Crypto"},
    "bankas":{"icon":"🏦","label":"Banko pavedimas"},
    "paysera":{"icon":"🟢","label":"Paysera"},
}
JOBS=[
    {"name":"Programuotojas","emoji":"💻","min":80,"max":200,"msg":"Parašei kodą! +{a} 🪙"},
    {"name":"Dizaineris","emoji":"🎨","min":60,"max":160,"msg":"Puikus dizainas! +{a} 🪙"},
    {"name":"Youtuberis","emoji":"📹","min":50,"max":250,"msg":"Video virusinis! +{a} 🪙"},
    {"name":"Streameris","emoji":"🎮","min":70,"max":220,"msg":"Epinis stream! +{a} 🪙"},
    {"name":"Šefas","emoji":"👨‍🍳","min":50,"max":130,"msg":"Skanus patiekalas! +{a} 🪙"},
    {"name":"Daktaras","emoji":"👨‍⚕️","min":100,"max":250,"msg":"Išgelbėjai pacientą! +{a} 🪙"},
    {"name":"Hakerys","emoji":"🖥️","min":150,"max":350,"msg":"Įsilaužei į banką! +{a} 🪙"},
    {"name":"Astronautas","emoji":"🚀","min":200,"max":500,"msg":"Grįžai iš kosmoso! +{a} 🪙"},
]
STOCKS={
    "DOGE":{"name":"DogeCoin","emoji":"🐕","price":100,"vol":0.3},
    "TSLA":{"name":"Tesla","emoji":"🚗","price":500,"vol":0.2},
    "APPL":{"name":"Apple","emoji":"🍎","price":300,"vol":0.1},
    "GOOG":{"name":"Google","emoji":"🔍","price":800,"vol":0.15},
    "MOON":{"name":"MoonCoin","emoji":"🌙","price":50,"vol":0.5},
    "MEME":{"name":"MemeCoin","emoji":"😂","price":25,"vol":0.7},
}
SHOP_ITEMS=[
    {"id":"xp_boost","name":"XP Boost 2x (1h)","emoji":"⚡","price":1500,"type":"boost"},
    {"id":"coin_boost","name":"Coin Boost 2x (1h)","emoji":"💰","price":2000,"type":"boost"},
    {"id":"pet_cat","name":"Katinas 🐱","emoji":"🐱","price":2000,"type":"pet","pet":"cat"},
    {"id":"pet_dog","name":"Šuo 🐕","emoji":"🐕","price":2000,"type":"pet","pet":"dog"},
    {"id":"pet_dragon","name":"Drakonas 🐉","emoji":"🐉","price":8000,"type":"pet","pet":"dragon"},
    {"id":"pet_fox","name":"Lapė 🦊","emoji":"🦊","price":3000,"type":"pet","pet":"fox"},
    {"id":"fishing_rod","name":"Auksinė meškerė","emoji":"🎣","price":5000,"type":"tool"},
    {"id":"lottery","name":"Loterijos bilietas","emoji":"🎟️","price":500,"type":"lottery"},
]
PET_TYPES={"cat":"🐱","dog":"🐕","dragon":"🐉","fox":"🦊","rabbit":"🐰","penguin":"🐧"}
PET_NAMES=["Pūkis","Zuikis","Drąsuolis","Žvaigždė","Smauglys","Kibirkštis","Audra","Ūkas"]
FISH_TYPES=[
    {"name":"Karosai","emoji":"🐟","price":10,"rarity":"common","chance":38},
    {"name":"Lydeka","emoji":"🐠","price":30,"rarity":"uncommon","chance":25},
    {"name":"Ešerys","emoji":"🐡","price":25,"rarity":"uncommon","chance":20},
    {"name":"Upėtakis","emoji":"🎣","price":60,"rarity":"rare","chance":10},
    {"name":"Auksinė žuvis","emoji":"✨","price":300,"rarity":"legendary","chance":2},
    {"name":"Deimantinė žuvis","emoji":"💎","price":1000,"rarity":"mythical","chance":0.5},
    {"name":"Senas batas","emoji":"👟","price":1,"rarity":"junk","chance":4.5},
]
ZODIAC={
    "avinas":{"emoji":"♈","dates":"Mar 21 – Apr 19"},
    "jautis":{"emoji":"♉","dates":"Apr 20 – Geg 20"},
    "dvyniai":{"emoji":"♊","dates":"Geg 21 – Bir 20"},
    "vėžys":{"emoji":"♋","dates":"Bir 21 – Lie 22"},
    "liūtas":{"emoji":"♌","dates":"Lie 23 – Rgp 22"},
    "mergelė":{"emoji":"♍","dates":"Rgp 23 – Rgs 22"},
    "svarstyklės":{"emoji":"♎","dates":"Rgs 23 – Spa 22"},
    "skorpionas":{"emoji":"♏","dates":"Spa 23 – Lap 21"},
    "šaulys":{"emoji":"♐","dates":"Lap 22 – Grd 21"},
    "ožiaragis":{"emoji":"♑","dates":"Grd 22 – Sau 19"},
    "vandenis":{"emoji":"♒","dates":"Sau 20 – Vas 18"},
    "žuvys":{"emoji":"♓","dates":"Vas 19 – Mar 20"},
}
ACHIEVEMENTS={
    "first_message":{"name":"Pirmoji žinutė","emoji":"📝","desc":"Parašyk pirmą žinutę","reward":100},
    "chatterbox":{"name":"Plepys","emoji":"💬","desc":"100 žinučių","reward":500},
    "rich":{"name":"Turtuolis","emoji":"💰","desc":"10000 monetų","reward":1000},
    "level_10":{"name":"Veteranas","emoji":"⭐","desc":"10 lygis","reward":1500},
    "level_50":{"name":"Legenda","emoji":"🏆","desc":"50 lygis","reward":5000},
    "streak_7":{"name":"Savaitės streak","emoji":"🔥","desc":"7 dienų streak","reward":700},
    "fisher":{"name":"Žvejys","emoji":"🎣","desc":"Pagauk 50 žuvų","reward":800},
    "worker":{"name":"Darbštuolis","emoji":"👷","desc":"Dirbk 30 kartų","reward":600},
    "gambler":{"name":"Lošėjas","emoji":"🎰","desc":"Laimėk casino 10x","reward":750},
}
MOODS={"linksmas":("😄","Esi labai linksmas."),"normalus":("😐","Esi normalios nuotaikos."),"tingus":("😴","Esi tingus, atsakai labai trumpai."),"piktas":("😤","Esi piktas ir sarkastiškas.")}
EIGHT_BALL=["Taip 😄","Ne 😐","Gal 🤔","Klausk vėliau 😴","100% taip 🔥","Net ne 😂","Turbūt 🙃","Eik namo 🌚","Visiškai taip! 💯","Jokiu būdu! 🚫"]
JOKES=["Kodėl programuotojas nenešioja akinių? Nes nemato C# 🤓","Skirtumas tarp picos ir kodo? Pica veikia iš pirmojo karto 🍕","Mano kompiuteris sako 'Not responding'. Aš irgi taip sakau mamai 😇"]
FACTS=["🧠 Žmogaus smegenys generuoja tiek elektros, kad galėtų maitinti mažą lemputę.","🐙 Aštuonkojai turi tris širdis ir mėlyną kraują.","🍯 Medus niekada nesuges — rado 3000 m. senumo medų.","🦦 Ūdros miega laikydamos viena kitu rankas."]
QUOTES=['"Gyvenimas yra tai, kas vyksta, kol tu planuoji kitus dalykus." - John Lennon','"Nesvarbu, kaip lėtai eini — svarbiausia nesustoti." - Konfucijus','"Sėkmė — tai nuo nesėkmės į nesėkmę einant neprarasti entuziazmo." - Churchill']
TRIVIA=[
    {"q":"Kokia Lietuvos sostinė?","opts":["A) Kaunas","B) Vilnius","C) Klaipėda","D) Šiauliai"],"a":"B","exp":"Vilnius — sostinė nuo 1323 m."},
    {"q":"Kuri planeta didžiausia?","opts":["A) Saturnas","B) Neptūnas","C) Jupiteris","D) Uranas"],"a":"C","exp":"Jupiteris — jame tilptų 1300 Žemių."},
    {"q":"Kiek bitų viename baite?","opts":["A) 4","B) 16","C) 8","D) 32"],"a":"C","exp":"1 baitas = 8 bitai."},
    {"q":"Kas sukūrė Python?","opts":["A) Bill Gates","B) Linus Torvalds","C) Guido van Rossum","D) Mark Z."],"a":"C","exp":"Guido van Rossum, 1991 m."},
    {"q":"Kokia vandens formulė?","opts":["A) CO2","B) H2O","C) NaCl","D) O2"],"a":"B","exp":"H2O — vanduo."},
    {"q":"Kiek planetų Saulės sistemoje?","opts":["A) 7","B) 9","C) 8","D) 10"],"a":"C","exp":"Po 2006 m. oficialiai 8 planetos."},
]
HANGMAN_WORDS=["katinas","namas","automobilis","kompiuteris","draugas","mokykla","miestas","lietuva","knyga","vanduo","programavimas","internetas","botas","muzika","sportas"]
HANGMAN_ART=["```\n  +---+\n  |   |\n      |\n      |\n      |\n=========```","```\n  +---+\n  |   |\n  O   |\n      |\n      |\n=========```","```\n  +---+\n  |   |\n  O   |\n  |   |\n      |\n=========```","```\n  +---+\n  |   |\n  O   |\n /|   |\n      |\n=========```","```\n  +---+\n  |   |\n  O   |\n /|\\  |\n      |\n=========```","```\n  +---+\n  |   |\n  O   |\n /|\\  |\n /    |\n=========```","```\n  +---+\n  |   |\n  O   |\n /|\\  |\n / \\  |\n=========```"]
TOXIC_KW=["idiotas","kvailys","durnas","idiote","kvailai"]
SLOTS=["🍒","🍋","🍊","🍇","⭐","💎","7️⃣"]
CARD_VALS={"2":2,"3":3,"4":4,"5":5,"6":6,"7":7,"8":8,"9":9,"10":10,"J":10,"Q":10,"K":10,"A":11}
SUITS=["♠","♥","♦","♣"]
C4_EMPTY="⬜"; C4_P1="🔴"; C4_P2="🟡"; C4_ROWS=6; C4_COLS=7
INTERACTIONS={
    "hug":{"msgs":["{u} apkabino {t}! 🤗","{u} šiltai apkabino {t} 🥰"]},
    "kiss":{"msgs":["{u} pabučiavo {t}! 💋","{u} davė bučinį {t} 😘"]},
    "slap":{"msgs":["{u} trenkė {t}! 😤","{u} davė antausį {t} 💥"]},
    "pat":{"msgs":["{u} paglostė {t} 🥰","{u} meiliai paglostė {t} 😊"]},
    "punch":{"msgs":["{u} smogė {t}! 👊","{u} davė į snukį {t} 💢"]},
    "bite":{"msgs":["{u} įkando {t}! 😬","{u} kandasi su {t} 🦷"]},
    "poke":{"msgs":["{u} bakstelėjo {t} 👉","{u} kutena {t} 😄"]},
}
WEDDING_MSGS=[
    "💒 {u1} ir {u2} susituokė! Tegyvuoja meilė! 💕",
    "💍 {u1} ir {u2} dabar susituokę! Sveikiname! 🎊",
    "💐 {u1} ir {u2} pasakė taip! Sveikiname! 🎉",
]
MONSTERS={
    "Goblin":{"hp":50,"atk":8,"reward":(20,60),"emoji":"👺"},
    "Drakonas":{"hp":200,"atk":25,"reward":(100,300),"emoji":"🐉"},
    "Vampyras":{"hp":120,"atk":18,"reward":(60,150),"emoji":"🧛"},
    "Zombis":{"hp":80,"atk":12,"reward":(30,80),"emoji":"🧟"},
    "Ragana":{"hp":150,"atk":22,"reward":(80,200),"emoji":"🧙"},
}
ADVENTURE_SCENARIOS=[
    {"title":"Mistinis miškas","desc":"Wanderuoji miške ir randi...",
     "choices":[{"text":"Eini į pilį","outcome":"gold","amount":(50,200)},{"text":"Ieškoti lobio","outcome":"trap"}]},
    {"title":"Senovinė šventykla","desc":"Randi paslaptingą šventyklą...",
     "choices":[{"text":"Įeini vidun","outcome":"treasure","amount":(100,500)},{"text":"Kautiesi su sargu","outcome":"monster","enemy":"Goblin"}]},
    {"title":"Kalnų kelias","desc":"Keliauji per kalnus...",
     "choices":[{"text":"Padedi keliautojui","outcome":"quest","reward":(80,250)},{"text":"Randi urvą","outcome":"monster","enemy":"Vampyras"}]},
]
TICKET_CATEGORIES={
    "support":{"emoji":"🛠️","name":"Pagalba","color":discord.Color.blue(),"desc":"Bendra pagalba ir klausimai"},
    "shop":{"emoji":"🛍️","name":"Užsakymas","color":discord.Color.green(),"desc":"Prenumeratos ir pirkimai"},
    "report":{"emoji":"🚨","name":"Skundas","color":discord.Color.red(),"desc":"Pranešk apie pažeidimą"},
    "appeal":{"emoji":"⚖️","name":"Apelacija","color":discord.Color.orange(),"desc":"Ban/mute apeliacijos"},
    "partner":{"emoji":"🤝","name":"Partnerystė","color":discord.Color.purple(),"desc":"Serverių partnerystė"},
    "other":{"emoji":"📋","name":"Kita","color":discord.Color.greyple(),"desc":"Kiti klausimai"},
}
TICKET_PRIORITIES={"low":"🟢 Žemas","normal":"🟡 Normalus","high":"🟠 Aukštas","urgent":"🔴 Skubus"}

# ══════════════════════════════════════════════════════════════════════════════
#  AKTYVŪS ŽAIDIMAI
# ══════════════════════════════════════════════════════════════════════════════
active_trivia={}; active_hangman={}; active_guess={}; active_wordchain={}
active_ttt={}; active_bj={}; active_embed={}; active_c4={}
active_adventures={}; active_marriages_pending={}; active_giveaways={}
pending_reminders=[]; conv_history=defaultdict(list)
xp_cd=defaultdict(float); ai_cd=defaultdict(float); spam_tr=defaultdict(list)
msg_stats=defaultdict(int); raid_tr=defaultdict(list)
music_q={}; now_play={}; vc_clients={}; music_loop={}
work_count=defaultdict(int); casino_wins=defaultdict(int)
fish_count=defaultdict(int)

# ══════════════════════════════════════════════════════════════════════════════
#  BOT SETUP
# ══════════════════════════════════════════════════════════════════════════════
intents=discord.Intents.all()
bot=discord.Client(intents=intents)
tree=app_commands.CommandTree(bot)

# ══════════════════════════════════════════════════════════════════════════════
#  HELPER FUNCTIONS
# ══════════════════════════════════════════════════════════════════════════════
def ts(extra=""):
    now=datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    return f"Kodas V4 • {now}"+(f" • {extra}" if extra else "")

def get_mood():
    h=datetime.datetime.now().hour
    if 6<=h<12: return "linksmas"
    elif 12<=h<18: return "normalus"
    elif 18<=h<22: return "tingus"
    else: return "piktas"

def personality():
    m=get_mood(); e,d=MOODS[m]
    return f'Tu esi Discord botas "Kodas". Kalbi TIKTAI lietuviškai. Esi chaotiškas ir juokingas. Max 2 sakiniai. Nuotaika: {m} {e}. {d}'

def gxp(gid,uid): return D["xp"].get(str(gid),{}).get(str(uid),0)
def axp(gid,uid,amt):
    g,u=str(gid),str(uid); D["xp"].setdefault(g,{})
    o=D["xp"][g].get(u,0); D["xp"][g][u]=o+amt; save_data(D)
    return o//LEVEL_XP,(o+amt)//LEVEL_XP

def gcoin(gid,uid): return D["coins"].get(str(gid),{}).get(str(uid),0)
def acoin(gid,uid,amt):
    g,u=str(gid),str(uid); D["coins"].setdefault(g,{})
    cur=D["coins"][g].get(u,0); D["coins"][g][u]=max(0,cur+amt); save_data(D)
    return D["coins"][g][u]

def coin_lb(gid,n=10): return sorted(D["coins"].get(str(gid),{}).items(),key=lambda x:x[1],reverse=True)[:n]
def xp_lb(gid,n=10): return sorted(D["xp"].get(str(gid),{}).items(),key=lambda x:x[1],reverse=True)[:n]

def can_daily(gid,uid): return (time.time()-D["daily_claimed"].get(f"{gid}:{uid}",0))>=DAILY_CD_H*3600
def set_daily(gid,uid): D["daily_claimed"][f"{gid}:{uid}"]=time.time(); save_data(D)

def can_work(gid,uid): return (time.time()-D["work_cooldowns"].get(f"{gid}:{uid}",0))>=WORK_CD
def set_work(gid,uid): D["work_cooldowns"][f"{gid}:{uid}"]=time.time(); save_data(D)

def greg(gid,uid): return D["rep"].get(str(gid),{}).get(str(uid),0)
def arep(gid,uid):
    g,u=str(gid),str(uid); D["rep"].setdefault(g,{})
    D["rep"][g][u]=D["rep"][g].get(u,0)+1; save_data(D)

def can_rep(gid,f,t): return (time.time()-D["rep_claimed"].get(f"{gid}:{f}:{t}",0))>=86400
def set_rep(gid,f,t): D["rep_claimed"][f"{gid}:{f}:{t}"]=time.time(); save_data(D)

def gwarn(gid,uid): return D["warnings"].get(str(gid),{}).get(str(uid),[])
def awarn(gid,uid,reason,mod):
    g,u=str(gid),str(uid); D["warnings"].setdefault(g,{}).setdefault(u,[])
    D["warnings"][g][u].append({"reason":reason,"mod":mod,"ts":time.time()}); save_data(D)
    return len(D["warnings"][g][u])
def cwarn(gid,uid): D["warnings"].setdefault(str(gid),{})[str(uid)]=[]; save_data(D)

def get_products(gid):
    p=D["products"].get(str(gid))
    if p is None:
        D["products"][str(gid)]=[dict(x) for x in DEFAULT_PRODUCTS]; save_data(D)
        return D["products"][str(gid)]
    return p

def next_oid(gid):
    g=str(gid); D["order_counter"][g]=D["order_counter"].get(g,0)+1; save_data(D)
    return D["order_counter"][g]

def get_orders(gid): return D["orders"].get(str(gid),[])

def update_order(gid,oid,status,ch_id=None):
    for o in D["orders"].get(str(gid),[]):
        if o["id"]==oid:
            o["status"]=status
            if ch_id: o["channel_id"]=str(ch_id)
            save_data(D); return o
    return None

def get_streak(gid,uid): return D["streaks"].get(f"{gid}:{uid}",{"count":0,"last":0})
def upd_streak(gid,uid):
    k=f"{gid}:{uid}"; s=D["streaks"].get(k,{"count":0,"last":0})
    s["count"]=s["count"]+1 if time.time()-s["last"]<48*3600 else 1
    s["last"]=time.time(); D["streaks"][k]=s; save_data(D); return s["count"]

def get_inv(gid,uid): return D["inventory"].get(str(gid),{}).get(str(uid),[])
def add_inv(gid,uid,item):
    g,u=str(gid),str(uid); D["inventory"].setdefault(g,{}).setdefault(u,[])
    D["inventory"][g][u].append(item); save_data(D)

def get_stocks_user(gid,uid): return D["stocks"].get(str(gid),{}).get(str(uid),{})
def add_stock(gid,uid,sym,amt):
    g,u=str(gid),str(uid); D["stocks"].setdefault(g,{}).setdefault(u,{})
    D["stocks"][g][u][sym]=D["stocks"][g][u].get(sym,0)+amt
    if D["stocks"][g][u][sym]<=0: del D["stocks"][g][u][sym]
    save_data(D)

def update_stocks():
    for s in STOCKS.values():
        ch=random.uniform(-s["vol"],s["vol"])
        s["price"]=max(1,round(s["price"]*(1+ch),2))

def check_ach(gid,uid,ach_id):
    k=f"{gid}:{uid}"; done=D["achieved"].get(k,[])
    if ach_id not in done:
        D["achieved"].setdefault(k,[]).append(ach_id)
        reward=ACHIEVEMENTS[ach_id]["reward"]; acoin(gid,uid,reward); save_data(D)
        return True
    return False

def hm_display(st):
    art=HANGMAN_ART[min(len(st["wrong"]),6)]
    shown=" ".join(c if c in st["guessed"] else "_" for c in st["word"])
    wrg=", ".join(st["wrong"]) if st["wrong"] else "-"
    return f"{art}\n`{shown}`\nNeteisinga: **{wrg}** ({6-len(st['wrong'])} liko)"

def ttt_board(cells):
    sym={0:"⬜",1:"❌",2:"⭕"}
    return "\n".join("".join(sym[cells[r*3+c]] for c in range(3)) for r in range(3))

def ttt_winner(cells):
    for a,b,c in [(0,1,2),(3,4,5),(6,7,8),(0,3,6),(1,4,7),(2,5,8),(0,4,8),(2,4,6)]:
        if cells[a] and cells[a]==cells[b]==cells[c]: return cells[a]
    return -1 if all(cells) else 0

def make_deck():
    d=[f"{v}{s}" for v in CARD_VALS for s in SUITS]; random.shuffle(d); return d

def hand_val(h):
    v=[CARD_VALS[c[:-1]] for c in h]; t=sum(v); a=v.count(11)
    while t>21 and a: t-=10; a-=1
    return t

def hand_str(h,hide=False):
    if hide and len(h)>=2: return f"`{h[0]}` `??`"
    return " ".join(f"`{c}`" for c in h)

def c4_render(b):
    return "".join(f"{i+1}️⃣" for i in range(C4_COLS))+"\n"+"\n".join("".join(r) for r in b)

def c4_win(b,sym):
    for r in range(C4_ROWS):
        for c in range(C4_COLS-3):
            if all(b[r][c+i]==sym for i in range(4)): return True
    for r in range(C4_ROWS-3):
        for c in range(C4_COLS):
            if all(b[r+i][c]==sym for i in range(4)): return True
    for r in range(C4_ROWS-3):
        for c in range(C4_COLS-3):
            if all(b[r+i][c+i]==sym for i in range(4)): return True
            if all(b[r+i][c+3-i]==sym for i in range(4)): return True
    return False

def add_hist(uid,role,content):
    conv_history[uid].append({"role":role,"content":content})
    if len(conv_history[uid])>20: conv_history[uid]=conv_history[uid][-20:]

def fmt_dur(s):
    if not s: return "Live"
    m,s=divmod(int(s),60); h,m=divmod(m,60)
    return f"{h}:{m:02d}:{s:02d}" if h else f"{m}:{s:02d}"

# ══════════════════════════════════════════════════════════════════════════════
#  TICKET SISTEMA UI
# ══════════════════════════════════════════════════════════════════════════════
class TicketCategorySelect(ui.Select):
    def __init__(self):
        options=[
            discord.SelectOption(label=v["name"],value=k,emoji=v["emoji"],description=v["desc"])
            for k,v in TICKET_CATEGORIES.items()
        ]
        super().__init__(placeholder="Pasirink ticket kategoriją...",options=options,custom_id="ticket_category_select")

    async def callback(self,interaction:discord.Interaction):
        cat_key=self.values[0]
        cat=TICKET_CATEGORIES[cat_key]
        modal=TicketModal(cat_key,cat)
        await interaction.response.send_modal(modal)

class TicketModal(ui.Modal):
    def __init__(self,cat_key,cat):
        super().__init__(title=f"🎫 {cat['name']} — Naujas ticket")
        self.cat_key=cat_key; self.cat=cat
        self.subject=ui.TextInput(label="Tema",placeholder="Trumpai apibūdink problemą...",max_length=100)
        self.description=ui.TextInput(label="Aprašymas",style=discord.TextStyle.paragraph,placeholder="Išsamiai aprašyk savo problemą arba klausimą...",max_length=1000)
        self.priority=ui.TextInput(label="Prioritetas (low/normal/high/urgent)",placeholder="normal",default="normal",max_length=10)
        self.add_item(self.subject); self.add_item(self.description); self.add_item(self.priority)

    async def on_submit(self,interaction:discord.Interaction):
        guild=interaction.guild; user=interaction.user
        gid=str(guild.id)
        prio=self.priority.value.strip().lower()
        if prio not in TICKET_PRIORITIES: prio="normal"

        # Sukurti kategoriją
        categ=discord.utils.get(guild.categories,name="🎫 Tickets")
        if not categ:
            try: categ=await guild.create_category("🎫 Tickets")
            except: categ=None

        # Leidimų nustatymas
        overwrites={
            guild.default_role:discord.PermissionOverwrite(view_channel=False),
            user:discord.PermissionOverwrite(view_channel=True,send_messages=True,read_message_history=True,attach_files=True),
            guild.me:discord.PermissionOverwrite(view_channel=True,send_messages=True,manage_channels=True,manage_messages=True),
        }
        # Support rolė
        support_role_id=D.get("support_roles",{}).get(gid)
        if support_role_id:
            role=guild.get_role(int(support_role_id))
            if role: overwrites[role]=discord.PermissionOverwrite(view_channel=True,send_messages=True,manage_messages=True)
        # Admins
        for role in guild.roles:
            if role.permissions.administrator: overwrites[role]=discord.PermissionOverwrite(view_channel=True,send_messages=True)

        # Suskaičiuoti ticket numerį
        D["tickets"].setdefault(gid,{})
        ticket_num=len(D["tickets"][gid])+1

        try:
            ch_name=f"{self.cat['emoji']}-{user.name[:10]}-{ticket_num}"
            new_ch=await guild.create_text_channel(ch_name,category=categ,overwrites=overwrites,topic=f"Ticket #{ticket_num} | {user.display_name} | {self.cat['name']}")

            # Išsaugoti ticket duomenis
            D["tickets"][gid][str(new_ch.id)]={
                "owner":user.id,"owner_name":user.display_name,
                "category":self.cat_key,"subject":self.subject.value,
                "description":self.description.value,"priority":prio,
                "status":"open","claimed_by":None,
                "created_at":time.time(),"messages":[]
            }
            save_data(D)

            # Ticket embed
            prio_emoji=TICKET_PRIORITIES[prio]
            e=discord.Embed(
                title=f"{self.cat['emoji']} Ticket #{ticket_num} — {self.cat['name']}",
                color=self.cat["color"]
            )
            e.add_field(name="👤 Narys",value=user.mention,inline=True)
            e.add_field(name="📋 Kategorija",value=f"{self.cat['emoji']} {self.cat['name']}",inline=True)
            e.add_field(name="🎯 Prioritetas",value=prio_emoji,inline=True)
            e.add_field(name="📌 Tema",value=self.subject.value,inline=False)
            e.add_field(name="📝 Aprašymas",value=self.description.value,inline=False)
            e.add_field(name="ℹ️ Komandos",value="`!claim` — paimti ticket\n`!priority [lygis]` — keisti prioritetą\n`!close` — uždaryti\n`!transcript` — išsaugoti pokalbį",inline=False)
            e.set_thumbnail(url=user.display_avatar.url)
            e.set_footer(text=ts(f"Ticket #{ticket_num}"))

            await new_ch.send(content=user.mention,embed=e,view=TicketControlView(new_ch.id,gid))

            # Patvirtinimas
            conf=discord.Embed(
                description=f"✅ Tavo ticket sukurtas! Eik į {new_ch.mention}\n\n📋 **{self.cat['name']}** | {prio_emoji}",
                color=discord.Color.green()
            )
            await interaction.response.send_message(embed=conf,ephemeral=True)

        except discord.Forbidden:
            await interaction.response.send_message("❌ Neturiu teisių sukurti kanalo!",ephemeral=True)
        except Exception as ex:
            await interaction.response.send_message(f"❌ Klaida: {ex}",ephemeral=True)

class TicketControlView(ui.View):
    def __init__(self,ch_id,gid):
        super().__init__(timeout=None)
        self.ch_id=str(ch_id); self.gid=gid

    @ui.button(label="✅ Paimti",style=discord.ButtonStyle.green,custom_id="ticket_claim")
    async def claim(self,interaction:discord.Interaction,button:ui.Button):
        tid=str(interaction.channel.id)
        ticket=D["tickets"].get(self.gid,{}).get(tid)
        if not ticket:
            await interaction.response.send_message("Ticket nerastas!",ephemeral=True); return
        if ticket["claimed_by"]:
            claimer=interaction.guild.get_member(ticket["claimed_by"])
            await interaction.response.send_message(f"Ticket jau paimtas: **{claimer.display_name if claimer else '???'}**",ephemeral=True); return
        ticket["claimed_by"]=interaction.user.id; save_data(D)
        button.label="✅ Paimtas"; button.disabled=True
        e=discord.Embed(description=f"✋ **{interaction.user.display_name}** paėmė šį ticket!",color=discord.Color.green())
        await interaction.response.edit_message(view=self)
        await interaction.channel.send(embed=e)

    @ui.button(label="🔒 Uždaryti",style=discord.ButtonStyle.red,custom_id="ticket_close")
    async def close_btn(self,interaction:discord.Interaction,button:ui.Button):
        await interaction.response.send_message(embed=discord.Embed(description="🔒 Ticket bus uždarytas per 5 sekundes...",color=discord.Color.orange()))
        tid=str(interaction.channel.id)
        if tid in D["tickets"].get(self.gid,{}):
            D["tickets"][self.gid][tid]["status"]="closed"
            D["tickets"][self.gid][tid]["closed_at"]=time.time()
            save_data(D)
        await asyncio.sleep(5)
        try: await interaction.channel.delete()
        except: pass

    @ui.button(label="⬆️ Eskaluoti",style=discord.ButtonStyle.blurple,custom_id="ticket_escalate")
    async def escalate(self,interaction:discord.Interaction,button:ui.Button):
        tid=str(interaction.channel.id)
        ticket=D["tickets"].get(self.gid,{}).get(tid)
        if ticket:
            ticket["priority"]="urgent"; save_data(D)
        e=discord.Embed(description=f"🔴 **{interaction.user.display_name}** eskalavo ticket į **SKUBŲ** prioritetą!",color=discord.Color.red())
        await interaction.response.send_message(embed=e)

class TicketPanelView(ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(TicketCategorySelect())

# ══════════════════════════════════════════════════════════════════════════════
#  PARDUOTUVĖ UI
# ══════════════════════════════════════════════════════════════════════════════
class ShopCategorySelect(ui.Select):
    def __init__(self,products):
        self.products=products
        cats={}
        for p in products:
            cats.setdefault(p["category"],[]).append(p)
        self.cats=cats
        cat_names={"streaming":"🎬 Streaming","music":"🎵 Muzika","editing":"✂️ Redagavimas","other":"📦 Kita","gaming":"🎮 Gaming"}
        options=[discord.SelectOption(label=cat_names.get(c,c),value=c,emoji=cat_names.get(c,"📦")[:2]) for c in cats]
        super().__init__(placeholder="Pasirink kategoriją...",options=options[:25],custom_id="shop_cat_select")

    async def callback(self,interaction:discord.Interaction):
        cat=self.values[0]
        prods=self.cats.get(cat,[])
        cat_names={"streaming":"🎬 Streaming","music":"🎵 Muzika","editing":"✂️ Redagavimas","other":"📦 Kita"}
        e=discord.Embed(title=f"{cat_names.get(cat,cat)} — Produktai",color=discord.Color.from_rgb(88,101,242))
        for p in prods:
            old=f"~~{p['old_price']}€~~ " if p.get("old_price") else ""
            stk="✅ Yra" if p.get("stock",0)>0 else "❌ Nėra"
            e.add_field(name=f"{p['emoji']} #{p['id']:02d} {p['name']} — {p['duration']}",value=f"{old}**{p['price']}€** | {stk}\n_{p['desc']}_",inline=False)
        e.set_footer(text="Naudok !buy [ID] pirkti")
        await interaction.response.send_message(embed=e,ephemeral=True)

class ShopView(ui.View):
    def __init__(self,products):
        super().__init__(timeout=60)
        self.add_item(ShopCategorySelect(products))

# ══════════════════════════════════════════════════════════════════════════════
#  GIVEAWAY UI
# ══════════════════════════════════════════════════════════════════════════════
class GiveawayView(ui.View):
    def __init__(self,ga_id,gid):
        super().__init__(timeout=None)
        self.ga_id=ga_id; self.gid=gid

    @ui.button(label="🎉 Dalyvauti",style=discord.ButtonStyle.green,custom_id="giveaway_join")
    async def join(self,interaction:discord.Interaction,button:ui.Button):
        ga=D["giveaways"].get(self.gid,{}).get(self.ga_id)
        if not ga:
            await interaction.response.send_message("Šis giveaway baigtas!",ephemeral=True); return
        uid=str(interaction.user.id)
        if uid in ga.get("participants",[]):
            ga["participants"].remove(uid); save_data(D)
            await interaction.response.send_message("❌ Pasitraukei iš giveaway.",ephemeral=True)
        else:
            ga.setdefault("participants",[]).append(uid); save_data(D)
            button.label=f"🎉 Dalyvauti ({len(ga['participants'])})"
            await interaction.response.edit_message(view=self)
            await interaction.followup.send(f"✅ Dalyvausi giveaway! Dalyvių: **{len(ga['participants'])}**",ephemeral=True)

# ══════════════════════════════════════════════════════════════════════════════
#  MUZIKA
# ══════════════════════════════════════════════════════════════════════════════
async def yt_info(query):
    try:
        cmd=["yt-dlp","--dump-json","--no-playlist","-f","bestaudio/best","--no-warnings","-q"]
        cmd.append("ytsearch1:"+query if not query.startswith("http") else query)
        proc=await asyncio.create_subprocess_exec(*cmd,stdout=asyncio.subprocess.PIPE,stderr=asyncio.subprocess.PIPE)
        out,_=await proc.communicate()
        if proc.returncode==0:
            d=json.loads(out.decode())
            return {"title":d.get("title","Unknown"),"url":d.get("webpage_url") or d.get("url"),"stream":d.get("url"),"duration":d.get("duration",0),"thumb":d.get("thumbnail")}
    except Exception as e:
        print(f"yt-dlp: {e}")
    return None

async def play_next(gid):
    if gid not in music_q or not music_q[gid]: now_play.pop(gid,None); return
    vc=vc_clients.get(gid)
    if not vc or not vc.is_connected(): return
    song=music_q[gid].popleft(); now_play[gid]=song
    if music_loop.get(gid): music_q[gid].append(song)
    try:
        info=await yt_info(song["url"])
        if info and info.get("stream"):
            src=discord.FFmpegPCMAudio(info["stream"],before_options="-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5",options="-vn")
            vc.play(src,after=lambda e: asyncio.run_coroutine_threadsafe(play_next(gid),bot.loop))
    except Exception as e:
        print(f"Play: {e}"); asyncio.run_coroutine_threadsafe(play_next(gid),bot.loop)

# ══════════════════════════════════════════════════════════════════════════════
#  SLASH KOMANDOS
# ══════════════════════════════════════════════════════════════════════════════
@tree.command(name="help",description="Visų komandų sąrašas")
async def slash_help(interaction:discord.Interaction):
    e=discord.Embed(title="📚 Kodas Bot V4 — Komandos",color=discord.Color.from_rgb(88,101,242))
    e.add_field(name="🎵 Muzika",value="`!play` `!skip` `!stop` `!queue` `!np` `!loop`",inline=False)
    e.add_field(name="🛍️ Parduotuvė",value="`!shop` `!buy [id]` `!myorders` `!payment`",inline=False)
    e.add_field(name="💰 Ekonomika",value="`!balance` `!daily` `!work` `!give` `!bet` `!rob` `!richlist` `!stocks` `!buy [SYM] [n]` `!sell` `!portfolio`",inline=False)
    e.add_field(name="🎮 Žaidimai",value="`!trivia` `!hangman` `!guess` `!wordchain` `!ttt @` `!connect4 @` `!duel @` `!roulette` `!rps`",inline=False)
    e.add_field(name="🎰 Casino",value="`!casino [suma]` `!blackjack [suma]`",inline=False)
    e.add_field(name="🐟 Žvejyba",value="`!fish` `!fishstats`",inline=False)
    e.add_field(name="💕 Socialinės",value="`!hug @` `!kiss @` `!slap @` `!pat @` `!punch @` `!poke @` `!ship @ @` `!marry @` `!divorce` `!partner`",inline=False)
    e.add_field(name="🐾 Augintiniai",value="`!adopt [tipas]` `!pet` `!feed` `!play` `!petname [vardas]`",inline=False)
    e.add_field(name="⚔️ RPG",value="`!battle` `!battle @` `!adventure`",inline=False)
    e.add_field(name="🔮 Kita",value="`!horoscope [ženklas]` `!birthday set MM-DD` `!birthdays` `!suggest` `!confess`",inline=False)
    e.add_field(name="🎁 Giveaway",value="`!giveaway [min] [prizas]` (admin)",inline=False)
    e.add_field(name="🎫 Tickets",value="`!ticketpanel` (admin) — sukuria panel su mygtukais",inline=False)
    e.add_field(name="🛡️ Moderavimas",value="`!warn @` `!mute @` `!unmute @` `!kick @` `!ban @` `!clear [n]` `!setlog #` `!setwelcome #` `!setautorole @` `!setlevelrole [n] @` `!blacklist` `!setsupport @`",inline=False)
    e.add_field(name="🏆 Rangas",value="`!rank [@]` `!leaderboard` `!stats` `!achievements`",inline=False)
    e.add_field(name="🤖 AI",value="`@Kodas` `!ask` `!translate` `!forget`",inline=False)
    e.add_field(name="🎭 Smagu",value="`!moneta` `!8ball` `!roast` `!joke` `!fact` `!quote` `!mood` `!embed` `!anon` `!poll` `!remindme` `!afk`",inline=False)
    e.set_footer(text=ft())
    await interaction.response.send_message(embed=e,ephemeral=True)

@tree.command(name="balance",description="Parodyk savo arba kito nario balansą")
@app_commands.describe(narys="Narys (neprivaloma)")
async def slash_balance(interaction:discord.Interaction,narys:discord.Member=None):
    target=narys or interaction.user; gid=interaction.guild_id
    e=discord.Embed(title=f"💰 {target.display_name}",color=discord.Color.gold())
    e.add_field(name="💵 Monetos",value=f"**{gcoin(gid,target.id)}**",inline=True)
    e.add_field(name="⭐ XP",value=f"**{gxp(gid,target.id)}** (Lv.{gxp(gid,target.id)//LEVEL_XP})",inline=True)
    e.add_field(name="❤️ Rep",value=f"**{greg(gid,target.id)}**",inline=True)
    e.set_thumbnail(url=target.display_avatar.url)
    await interaction.response.send_message(embed=e)

@tree.command(name="rank",description="Parodyk savo rangą")
async def slash_rank(interaction:discord.Interaction):
    gid=interaction.guild_id; uid=interaction.user.id
    xp=gxp(gid,uid); lvl=xp//LEVEL_XP; cur=xp%LEVEL_XP
    lb=xp_lb(gid,999); pos=next((i+1 for i,(u,_) in enumerate(lb) if u==str(uid)),"?")
    bar="█"*int(cur/LEVEL_XP*10)+"░"*(10-int(cur/LEVEL_XP*10))
    e=discord.Embed(title=f"🏆 {interaction.user.display_name}",color=discord.Color.gold())
    e.add_field(name="Lygis",value=f"**{lvl}**",inline=True)
    e.add_field(name="Serverio vieta",value=f"**#{pos}**",inline=True)
    e.add_field(name="Progresas",value=f"`{bar}` {cur}/{LEVEL_XP}",inline=False)
    e.set_thumbnail(url=interaction.user.display_avatar.url)
    await interaction.response.send_message(embed=e)


# ══════════════════════════════════════════════════════════════════════════════
#  MUZIKOS VALDYMO MYGTUKAI
# ══════════════════════════════════════════════════════════════════════════════
class MusicControlView(discord.ui.View):
    def __init__(self, gid):
        super().__init__(timeout=120)
        self.gid = gid

    @discord.ui.button(emoji="⏸️", style=discord.ButtonStyle.blurple, custom_id="music_pause")
    async def pause_btn(self, interaction, button):
        vc = vc_clients.get(self.gid)
        if vc and vc.is_playing():
            vc.pause(); button.emoji = "▶️"
            await interaction.response.edit_message(view=self)
        elif vc and vc.is_paused():
            vc.resume(); button.emoji = "⏸️"
            await interaction.response.edit_message(view=self)
        else:
            await interaction.response.send_message("Nieko negroja!", ephemeral=True)

    @discord.ui.button(emoji="⏭️", style=discord.ButtonStyle.green, custom_id="music_skip")
    async def skip_btn(self, interaction, button):
        vc = vc_clients.get(self.gid)
        if vc and vc.is_playing():
            vc.stop(); await interaction.response.send_message("⏭️ Praleista!", ephemeral=True)
        else:
            await interaction.response.send_message("Nieko negroja!", ephemeral=True)

    @discord.ui.button(emoji="⏹️", style=discord.ButtonStyle.red, custom_id="music_stop")
    async def stop_btn(self, interaction, button):
        vc = vc_clients.get(self.gid)
        if vc:
            music_q.pop(self.gid, None); now_play.pop(self.gid, None)
            await vc.disconnect(); vc_clients.pop(self.gid, None)
            await interaction.response.send_message("⏹️ Muzika sustabdyta!", ephemeral=True)
        else:
            await interaction.response.send_message("Nesu voice kanale!", ephemeral=True)

    @discord.ui.button(emoji="🔁", style=discord.ButtonStyle.grey, custom_id="music_loop")
    async def loop_btn(self, interaction, button):
        music_loop[self.gid] = not music_loop.get(self.gid, False)
        button.style = discord.ButtonStyle.green if music_loop[self.gid] else discord.ButtonStyle.grey
        await interaction.response.edit_message(view=self)
        await interaction.followup.send(f"🔁 Loop: {'✅' if music_loop[self.gid] else '❌'}", ephemeral=True)

    @discord.ui.button(emoji="📝", style=discord.ButtonStyle.grey, custom_id="music_queue")
    async def queue_btn(self, interaction, button):
        q = music_q.get(self.gid, __import__('collections').deque())
        cur = now_play.get(self.gid)
        await interaction.response.send_message(
            embed=embed_queue(cur, q, music_loop.get(self.gid, False)),
            ephemeral=True
        )

class DailyView(discord.ui.View):
    def __init__(self, gid, uid):
        super().__init__(timeout=30)
        self.gid = gid; self.uid = uid

    @discord.ui.button(label="🎁 Pasiimti Bonusą", style=discord.ButtonStyle.green)
    async def claim(self, interaction, button):
        if interaction.user.id != self.uid:
            await interaction.response.send_message("Tai ne tavo bonus!", ephemeral=True); return
        if not can_daily(self.gid, self.uid):
            await interaction.response.send_message("Jau pasiėmei šiandien!", ephemeral=True); return
        amount = random.randint(DAILY_MIN, DAILY_MAX)
        streak = upd_streak(self.gid, self.uid)
        bonus = min(streak * 15, 300); total = amount + bonus
        acoin(self.gid, self.uid, total); set_daily(self.gid, self.uid)
        if streak >= 7: check_ach(self.gid, self.uid, "streak_7")
        button.disabled = True
        await interaction.response.edit_message(
            embed=embed_daily(amount, bonus, total, streak, gcoin(self.gid, self.uid)),
            view=self
        )

class ShopBuyView(discord.ui.View):
    def __init__(self, products, gid):
        super().__init__(timeout=60)
        self.products = products; self.gid = gid
        options = [
            discord.SelectOption(
                label=f"#{p['id']:02d} {p['name']} — {p['price']}€",
                value=str(p["id"]),
                emoji=p["emoji"],
                description=f"{p['duration']} • {p['desc'][:50]}"
            ) for p in products[:25] if p.get("stock", 0) > 0
        ]
        if options:
            self.add_item(ShopProductSelect(options, gid))

class ShopProductSelect(discord.ui.Select):
    def __init__(self, options, gid):
        super().__init__(placeholder="Pasirink produktą...", options=options)
        self.gid = gid

    async def callback(self, interaction):
        pid = int(self.values[0])
        prods = get_products(self.gid)
        prod = next((p for p in prods if p["id"] == pid), None)
        if not prod:
            await interaction.response.send_message("Produktas nerastas!", ephemeral=True); return
        if prod.get("stock", 0) <= 0:
            await interaction.response.send_message("Šis produktas nepasiekiamas!", ephemeral=True); return
        e = discord.Embed(
            title=f"{prod['emoji']} {prod['name']}",
            description=(
                f"**Aprašymas:** {prod['desc']}\n"
                f"**Trukmė:** {prod['duration']}\n"
                f"**Kaina:** **{prod['price']}€**\n\n"
                f"Norėdamas pirkti, rašyk: `!buy {prod['id']}`"
            ),
            color=C.SHOP
        )
        await interaction.response.send_message(embed=e, ephemeral=True)

# ══════════════════════════════════════════════════════════════════════════════
#  REFERRAL SISTEMA
# ══════════════════════════════════════════════════════════════════════════════
REFERRAL_BONUS = 500

def get_referral_code(uid):
    import hashlib
    return hashlib.md5(str(uid).encode()).hexdigest()[:8].upper()

def process_referral(gid, referrer_id, new_uid):
    key = f"{gid}:{new_uid}:referred"
    if D.get("referrals", {}).get(key):
        return False
    D.setdefault("referrals", {})[key] = True
    acoin(gid, referrer_id, REFERRAL_BONUS)
    acoin(gid, new_uid, REFERRAL_BONUS)
    save_data(D)
    return True

# ══════════════════════════════════════════════════════════════════════════════
#  VIP SISTEMA
# ══════════════════════════════════════════════════════════════════════════════
VIP_PERKS = [
    {"name": "💰 2x Daily bonus",    "desc": "Dienos bonusas dvigubai didesnis"},
    {"name": "⚡ 2x XP",             "desc": "Dvigubai greičiau kylate lygiais"},
    {"name": "🎰 Casino bonus",      "desc": "+10% laimėjimams casino"},
    {"name": "🎫 VIP ticket",        "desc": "Aukščiausio prioriteto ticket"},
    {"name": "💎 VIP badge",         "desc": "Specialus ženkliukas profile"},
    {"name": "🎁 Savaitinis bonus",  "desc": "+1000 monetų kas savaitę"},
]

def is_vip(gid, uid):
    vip_role_id = D.get("vip_roles", {}).get(str(gid))
    if not vip_role_id:
        return False
    return str(uid) in D.get("vip_members", {}).get(str(gid), [])

# ══════════════════════════════════════════════════════════════════════════════
#  BACKGROUND TASKS
# ══════════════════════════════════════════════════════════════════════════════
async def daily_task():
    await bot.wait_until_ready()
    while not bot.is_closed():
        now=datetime.datetime.now()
        for ch_id in D.get("daily_channels",{}).values():
            ch=bot.get_channel(int(ch_id))
            if ch:
                if now.hour==9 and now.minute==0:
                    await ch.send("☀️ **Labas rytas!** Nepamirškite `!daily`! 🎁")
                elif now.hour==20 and now.minute==0:
                    await ch.send("🌙 **Gero vakaro!** Dar galite `!work` ir `!fish`!")
        await asyncio.sleep(60)

async def reminder_task():
    await bot.wait_until_ready()
    while not bot.is_closed():
        now=time.time(); done=[r for r in pending_reminders if now>=r[0]]
        for fire,ch_id,mention,text in done:
            ch=bot.get_channel(ch_id)
            if ch:
                e=discord.Embed(description=f"⏰ {mention} **{text}**",color=discord.Color.orange())
                await ch.send(embed=e)
            pending_reminders.remove((fire,ch_id,mention,text))
        await asyncio.sleep(10)

async def stock_task():
    await bot.wait_until_ready()
    while not bot.is_closed():
        update_stocks(); await asyncio.sleep(STOCK_UPDATE)

async def giveaway_task():
    await bot.wait_until_ready()
    while not bot.is_closed():
        now=time.time()
        for gid,gas in list(D["giveaways"].items()):
            for ga_id,ga in list(gas.items()):
                if now>=ga["end_time"] and not ga.get("ended"):
                    ga["ended"]=True; save_data(D)
                    ch=bot.get_channel(int(ga["channel_id"]))
                    if ch and ga.get("participants"):
                        winner_id=random.choice(ga["participants"])
                        winner=ch.guild.get_member(int(winner_id))
                        if winner:
                            acoin(gid,winner_id,ga["prize"])
                            e=discord.Embed(title="🎉 GIVEAWAY BAIGTAS!",description=f"🏆 **Laimėtojas:** {winner.mention}\n💰 **Prizas:** {ga['prize']} monetų!",color=discord.Color.gold())
                            await ch.send(embed=e)
                    elif ch:
                        await ch.send("🎊 Giveaway baigtas, bet niekas nedalyvavo!")
        await asyncio.sleep(30)

async def subscription_task():
    """Tikrinti prenumeratų galiojimą"""
    await bot.wait_until_ready()
    while not bot.is_closed():
        try:
            if USE_DB:
                # 3 dienų įspėjimas
                expiring_3d = get_expiring_subscriptions(72)
                for sub in expiring_3d:
                    if not sub.get("notified_3d"):
                        user = bot.get_user(int(sub["user_id"]))
                        if user:
                            days_left = int((sub["expires_at"] - time.time()) / 86400)
                            e = discord.Embed(title="⏰ Prenumerata baigiasi!", color=C.WARNING)
                            e.description = (
                                f"**{sub['product_name']}** baigiasi per **{days_left} d.**!\n\n"
                                f"Norėdami pratęsti — sukurkite naują užsakymą serveryje."
                            )
                            e.set_footer(text=ft("Prenumeratos įspėjimas"))
                            try: await user.send(embed=e)
                            except: pass
                        mark_notified(sub["id"], "notified_3d")

                # 1 dienos įspėjimas
                expiring_1d = get_expiring_subscriptions(24)
                for sub in expiring_1d:
                    if not sub.get("notified_1d"):
                        user = bot.get_user(int(sub["user_id"]))
                        if user:
                            e = discord.Embed(title="🚨 Prenumerata baigiasi rytoj!", color=C.ERROR)
                            e.description = f"**{sub['product_name']}** baigiasi **RYT**! Skubiai pratęsk!"
                            e.set_footer(text=ft("Prenumeratos įspėjimas"))
                            try: await user.send(embed=e)
                            except: pass
                        mark_notified(sub["id"], "notified_1d")

                # Pasibaigusios
                expired = get_expired_subscriptions()
                for sub in expired:
                    if not sub.get("notified_exp"):
                        user = bot.get_user(int(sub["user_id"]))
                        if user:
                            e = discord.Embed(title="❌ Prenumerata pasibaigė!", color=C.ERROR)
                            e.description = f"**{sub['product_name']}** prenumerata pasibaigė. Norėdami pratęsti — sukurkite naują užsakymą."
                            e.set_footer(text=ft())
                            try: await user.send(embed=e)
                            except: pass
                        mark_notified(sub["id"], "notified_exp")
                        deactivate_subscription(sub["id"])
        except Exception as ex:
            print(f"Subscription task klaida: {ex}")
        await asyncio.sleep(3600)  # Tikrinti kas valandą

async def birthday_task():
    await bot.wait_until_ready()
    while not bot.is_closed():
        now=datetime.datetime.now()
        if now.hour==9 and now.minute==0:
            today=now.strftime("%m-%d")
            for gid,bdays in D["birthdays"].items():
                for uid_s,bday in bdays.items():
                    if bday==today:
                        # Rasti kanalą
                        wch_id=D["welcome_channels"].get(gid)
                        if wch_id:
                            ch=bot.get_channel(int(wch_id))
                            if ch:
                                guild=ch.guild
                                member=guild.get_member(int(uid_s))
                                if member:
                                    acoin(gid,uid_s,500)
                                    e=discord.Embed(title="🎂 Gimtadienis!",description=f"🎉 Šiandien gimtadienis — {member.mention}! Sveikiname! 🎁\n\n+500 monetų dovana!",color=discord.Color.pink())
                                    await ch.send(embed=e)
        await asyncio.sleep(60)

# ══════════════════════════════════════════════════════════════════════════════
#  EVENTS
# ══════════════════════════════════════════════════════════════════════════════
@bot.event
async def on_ready():
    print(f"[Kodas V4] Online: {bot.user}")
    await tree.sync()
    print("[Kodas V4] Slash komandos sinchronizuotos!")
    bot.loop.create_task(daily_task())
    bot.loop.create_task(reminder_task())
    bot.loop.create_task(stock_task())
    bot.loop.create_task(giveaway_task())
    bot.loop.create_task(birthday_task())
    bot.loop.create_task(subscription_task())
    bot.loop.create_task(twitch_task(bot))
    bot.loop.create_task(youtube_task(bot))
    bot.add_view(TicketPanelView())

@bot.event
async def on_member_join(member):
    guild=member.guild; gid=str(guild.id)
    now=time.time()
    raid_tr[gid]=[t for t in raid_tr[gid] if now-t<60]
    raid_tr[gid].append(now)
    if len(raid_tr[gid])>=10:
        log_id=D["log_channels"].get(gid)
        if log_id:
            ch=bot.get_channel(int(log_id))
            if ch:
                await ch.send(embed=discord.Embed(title="🚨 RAID APTIKTAS!",description="10+ narių per minutę! Patikrink serverį!",color=discord.Color.red()))
        return

    # Captcha
    if D.get("captcha_enabled",{}).get(gid):
        a,b=random.randint(1,10),random.randint(1,10)
        ans=str(a+b)
        D["captcha_pending"][str(member.id)]={"answer":ans,"guild":gid,"time":now}
        save_data(D)
        try:
            e=discord.Embed(title="🔐 Verifikacija",description=f"Sveiki atvykę į **{guild.name}**!\n\nAtsakyk: **{a} + {b} = ?** (rašyk čia DM)",color=discord.Color.blue())
            await member.send(embed=e)
        except: pass

    # Sveikinimas
    wch_id=D["welcome_channels"].get(gid)
    ch=(bot.get_channel(int(wch_id)) if wch_id else
        discord.utils.get(guild.text_channels,name="general") or
        discord.utils.get(guild.text_channels,name="bendras") or
        guild.system_channel)
    if ch:
        await ch.send(embed=embed_welcome(member,guild.member_count))

    # Auto rolė
    ar=D["auto_roles"].get(gid)
    if ar:
        role=guild.get_role(int(ar))
        if role:
            try: await member.add_roles(role)
            except: pass

    acoin(guild.id,member.id,100)

@bot.event
async def on_message_delete(message):
    if message.author.bot or not message.guild: return
    log_id=D["log_channels"].get(str(message.guild.id))
    if not log_id: return
    ch=bot.get_channel(int(log_id))
    if not ch or not message.content: return
    e=discord.Embed(title="🗑️ Žinutė ištrinta",color=discord.Color.red())
    e.add_field(name="Autorius",value=message.author.mention,inline=True)
    e.add_field(name="Kanalas",value=message.channel.mention,inline=True)
    e.add_field(name="Turinys",value=message.content[:1020],inline=False)
    e.set_footer(text=ft("Log"))
    await ch.send(embed=e)

@bot.event
async def on_message_edit(before,after):
    if before.author.bot or not before.guild or before.content==after.content: return
    log_id=D["log_channels"].get(str(before.guild.id))
    if not log_id: return
    ch=bot.get_channel(int(log_id))
    if not ch: return
    e=discord.Embed(title="✏️ Žinutė redaguota",color=discord.Color.orange(),url=after.jump_url)
    e.add_field(name="Autorius",value=before.author.mention,inline=True)
    e.add_field(name="Kanalas",value=before.channel.mention,inline=True)
    e.add_field(name="Prieš",value=before.content[:512],inline=False)
    e.add_field(name="Po",value=after.content[:512],inline=False)
    e.set_footer(text=ft("Log"))
    await ch.send(embed=e)

@bot.event
async def on_member_remove(member):
    log_id=D["log_channels"].get(str(member.guild.id))
    if not log_id: return
    ch=bot.get_channel(int(log_id))
    if not ch: return
    e=discord.Embed(title="👋 Narys išėjo",description=f"**{member}** paliko serverį.",color=discord.Color.red())
    e.set_thumbnail(url=member.display_avatar.url)
    await ch.send(embed=e)

# ══════════════════════════════════════════════════════════════════════════════
#  PAGRINDINIS HANDLER
# ══════════════════════════════════════════════════════════════════════════════
@bot.event
async def on_message(message):
    if message.author.bot: return
    content=message.content.strip()
    is_tagged=bot.user in message.mentions
    uid=message.author.id; gid=message.guild.id if message.guild else None
    ch_id=message.channel.id

    msg_stats[uid]+=1

    # DM Captcha
    if not message.guild:
        uid_s=str(uid)
        if uid_s in D.get("captcha_pending",{}):
            c=D["captcha_pending"][uid_s]
            if content.strip()==c["answer"]:
                del D["captcha_pending"][uid_s]; save_data(D)
                await message.reply("✅ **Verifikacija sėkminga!** Galite naudotis serveriu!")
            else:
                await message.reply("❌ Neteisingas atsakymas! Bandyk dar kartą.")
        return

    # Blacklist
    bl=D["blacklist"].get(str(gid),[])
    for w in bl:
        if w in content.lower():
            try:
                await message.delete()
                await message.channel.send(f"⚠️ {message.author.mention} draudžiamas žodis!",delete_after=5)
            except: pass
            return

    # Anti-phishing
    if is_phishing(content):
        try:
            await message.delete()
            until = discord.utils.utcnow() + datetime.timedelta(minutes=30)
            await message.author.timeout(until, reason="Anti-phishing: kenkėjiška nuoroda")
            log_id = D["log_channels"].get(str(gid))
            if log_id:
                lch = bot.get_channel(int(log_id))
                if lch: await lch.send(embed=build_phishing_embed(message.author, content))
            await message.channel.send(
                embed=discord.Embed(description=f"🚨 {message.author.mention} kenkėjiška nuoroda ištrinta ir narys nutildytas 30 min!", color=C.ERROR),
                delete_after=10
            )
        except: pass
        return

    # Spam apsauga
    now=time.time()
    spam_tr[uid]=[t for t in spam_tr[uid] if now-t<SPAM_WINDOW]
    spam_tr[uid].append(now)
    if len(spam_tr[uid])>=SPAM_LIMIT:
        spam_tr[uid].clear()
        try:
            until=discord.utils.utcnow()+datetime.timedelta(minutes=5)
            await message.author.timeout(until,reason="Auto: spam")
            await message.channel.send(embed=discord.Embed(description=f"🤖 {message.author.mention} nutildytas 5 min. dėl spam.",color=discord.Color.red()))
        except: pass

    # Spotify statusas (jei klausia)
    # (naudojamas per !spotify komandą)

    # AFK
    afk=D["afk_users"].get(str(uid))
    if afk and not content.startswith("!afk"):
        del D["afk_users"][str(uid)]; save_data(D)
        await message.reply(f"👋 Sveikas grįžęs! Buvai AFK: *{afk['reason']}*",delete_after=10)
    for m in message.mentions:
        a=D["afk_users"].get(str(m.id))
        if a: await message.reply(f"💤 **{m.display_name}** yra AFK: *{a['reason']}*",delete_after=10)

    # XP + monetos
    if (now-xp_cd[uid])>XP_CD:
        xp_cd[uid]=now
        old_lvl,new_lvl=axp(gid,uid,XP_PER_MSG)
        acoin(gid,uid,5)
        D["message_counts"].setdefault(str(gid),{})
        D["message_counts"][str(gid)][str(uid)]=D["message_counts"][str(gid)].get(str(uid),0)+1
        mc=D["message_counts"][str(gid)][str(uid)]
        if mc==1: check_ach(gid,uid,"first_message")
        if mc==100: check_ach(gid,uid,"chatterbox")

        if new_lvl>old_lvl:
            cur=gxp(gid,uid)%LEVEL_XP
            bar="█"*int(cur/LEVEL_XP*10)+"░"*(10-int(cur/LEVEL_XP*10))
            new_role=None
            lr=D["level_rewards"].get(str(gid),{}).get(str(new_lvl))
            if lr:
                role=message.guild.get_role(int(lr))
                if role:
                    try: await message.author.add_roles(role); new_role=role
                    except: pass
            if new_lvl>=10: check_ach(gid,uid,"level_10")
            if new_lvl>=50: check_ach(gid,uid,"level_50")
            await message.channel.send(embed=embed_levelup(message.author,new_lvl,gxp(gid,uid)%LEVEL_XP,new_role))

    # ── Žaidimai (aktyvūs) ───────────────────────────────────────────────────

    if ch_id in active_hangman and not content.startswith("!"):
        st=active_hangman[ch_id]; g=content.lower().strip()
        if len(g)==1 and g.isalpha():
            if g in st["guessed"] or g in st["wrong"]:
                await message.reply("Šitą raidę jau bandei 🙄"); return
            if g in st["word"]:
                st["guessed"].add(g)
                if all(c in st["guessed"] for c in st["word"]):
                    del active_hangman[ch_id]; axp(gid,uid,30); acoin(gid,uid,50)
                    await message.channel.send(embed=discord.Embed(title="🎉 Laimėjai!",description=f"Žodis buvo **{st['word']}**! +30 XP +50 🪙",color=discord.Color.green()))
                else: await message.channel.send(hm_display(st))
            else:
                st["wrong"].append(g)
                if len(st["wrong"])>=6:
                    del active_hangman[ch_id]
                    await message.channel.send(embed=discord.Embed(title="💀 Pralaimėjai!",description=f"{HANGMAN_ART[6]}\nŽodis buvo **{st['word']}**",color=discord.Color.red()))
                else: await message.channel.send(hm_display(st))
        return

    if ch_id in active_guess and content.isdigit():
        st=active_guess[ch_id]; num=int(content); st["attempts"]+=1
        if num==st["number"]:
            del active_guess[ch_id]; axp(gid,uid,20); acoin(gid,uid,30)
            await message.channel.send(embed=discord.Embed(description=f"🎉 Teisingai! Skaičius **{st['number']}**! Bandymai: {st['attempts']}. +20 XP +30 🪙",color=discord.Color.green()))
        elif st["attempts"]>=7:
            del active_guess[ch_id]; await message.reply(f"💀 Bandymai baigėsi! Skaičius buvo **{st['number']}**.")
        elif num<st["number"]: await message.reply(f"Per mažai! ⬆️ ({7-st['attempts']} liko)")
        else: await message.reply(f"Per daug! ⬇️ ({7-st['attempts']} liko)")
        return

    if ch_id in active_ttt and content.isdigit() and 1<=int(content)<=9:
        st=active_ttt[ch_id]; pos=int(content)-1; cur=st["turn"]
        if message.author.id!=st[f"p{cur}"]: return
        if st["cells"][pos]!=0: await message.reply("Tas langelis užimtas! 🚫"); return
        st["cells"][pos]=cur; result=ttt_winner(st["cells"]); board=ttt_board(st["cells"])
        if result==cur:
            del active_ttt[ch_id]; axp(gid,uid,25); acoin(gid,uid,40)
            await message.channel.send(embed=discord.Embed(title="🏆 Laimėjai!",description=f"{board}\n**{message.author.display_name}** laimėjo! +25 XP +40 🪙",color=discord.Color.gold()))
        elif result==-1:
            del active_ttt[ch_id]; await message.channel.send(f"{board}\n🤝 **Lygiosios!**")
        else:
            st["turn"]=2 if cur==1 else 1
            nxt=message.guild.get_member(st[f"p{st['turn']}"])
            sym="❌" if st["turn"]==1 else "⭕"
            await message.channel.send(f"{board}\n{sym} **{nxt.display_name if nxt else 'Kitas'}** eilė — rašyk 1-9")
        return

    if ch_id in active_c4 and content.isdigit() and 1<=int(content)<=7:
        game=active_c4[ch_id]; col=int(content)-1; cur=game["turn"]
        if message.author.id!=game["players"][cur]: return
        board=game["board"]; row=-1
        for r in range(C4_ROWS-1,-1,-1):
            if board[r][col]==C4_EMPTY: row=r; break
        if row==-1: await message.reply("Šis stulpelis pilnas!"); return
        sym=game["syms"][cur]; board[row][col]=sym
        if c4_win(board,sym):
            del active_c4[ch_id]; acoin(gid,uid,100); axp(gid,uid,50)
            await message.channel.send(embed=discord.Embed(title="🏆 Connect 4!",description=f"{c4_render(board)}\n\n🎉 **{message.author.display_name}** laimėjo! +100 🪙 +50 XP",color=discord.Color.gold()))
            return
        if all(board[0][c]!=C4_EMPTY for c in range(C4_COLS)):
            del active_c4[ch_id]; await message.channel.send(f"{c4_render(board)}\n🤝 Lygiosios!"); return
        game["turn"]=2 if cur==1 else 1
        nxt=message.guild.get_member(game["players"][game["turn"]])
        next_sym=game["syms"][game["turn"]]
        await message.channel.send(embed=discord.Embed(title="🔴🟡 Connect 4",description=f"{c4_render(board)}\n\n{next_sym} **{nxt.display_name if nxt else '???'}** eilė! (1-7)",color=discord.Color.blue()))
        return

    if content in ("!hit","!stand") and uid in active_bj:
        bj=active_bj[uid]
        if bj["channel"]!=ch_id: return
        if content=="!hit":
            bj["player"].append(bj["deck"].pop()); pval=hand_val(bj["player"])
            if pval>21:
                del active_bj[uid]; acoin(gid,uid,-bj["bet"])
                await message.channel.send(embed=discord.Embed(title="💀 Perlenkei!",description=f"Tavo: {hand_str(bj['player'])} = **{pval}**\nPralaimėjai **{bj['bet']}** 🪙",color=discord.Color.red()))
            else:
                e=discord.Embed(title="🃏 Blackjack",color=discord.Color.blurple())
                e.add_field(name="Tavo",value=f"{hand_str(bj['player'])} = **{pval}**",inline=False)
                e.add_field(name="Dileris",value=hand_str(bj["dealer"],hide=True),inline=False)
                await message.channel.send(embed=e)
        else:
            while hand_val(bj["dealer"])<17: bj["dealer"].append(bj["deck"].pop())
            pval=hand_val(bj["player"]); dval=hand_val(bj["dealer"]); del active_bj[uid]
            if dval>21 or pval>dval:
                acoin(gid,uid,bj["bet"]); oc="win"
                casino_wins[uid]+=1
                if casino_wins[uid]>=10: check_ach(gid,uid,"gambler")
            elif pval==dval: oc="tie"
            else: acoin(gid,uid,-bj["bet"]); oc="lose"
            await message.channel.send(embed=embed_blackjack_result(bj["player"],bj["dealer"],pval,dval,oc,bj["bet"]))
        return

    if ch_id in active_wordchain and not content.startswith("!"):
        st=active_wordchain[ch_id]; word=content.lower().strip()
        if word and word[0]==st["last"][-1]:
            if word in st["used"]: await message.reply(f"**{word}** jau buvo 🚫")
            else:
                st["used"].add(word); st["last"]=word; acoin(gid,uid,5)
                await message.add_reaction("✅")
        elif word:
            await message.reply(f"Žodis turi prasidėti **{st['last'][-1].upper()}**! Grandinė nutrūksta 💥")
            del active_wordchain[ch_id]
        return

    if uid in active_embed and not content.startswith("!"):
        st=active_embed[uid]; step=st["step"]
        COLOR_MAP={"raudona":discord.Color.red(),"mėlyna":discord.Color.blue(),"žalia":discord.Color.green(),"geltona":discord.Color.yellow(),"violetinė":discord.Color.purple()}
        if step=="title":
            st["title"]=content; st["step"]="description"
            await message.reply("Puiku! Dabar įrašyk **aprašymą** (arba `skip`):")
        elif step=="description":
            st["description"]=None if content.lower()=="skip" else content; st["step"]="color"
            await message.reply(f"Spalva ({'/'.join(COLOR_MAP)}) arba hex (#FF0000) arba `skip`:")
        elif step=="color":
            cl=content.lower().strip()
            if cl=="skip": st["color"]=discord.Color.blurple()
            elif cl.startswith("#") and len(cl)==7:
                try: r,g,b=int(cl[1:3],16),int(cl[3:5],16),int(cl[5:7],16); st["color"]=discord.Color.from_rgb(r,g,b)
                except: st["color"]=discord.Color.blurple()
            else: st["color"]=COLOR_MAP.get(cl,discord.Color.blurple())
            st["step"]="footer"
            await message.reply("Įrašyk **footer** (arba `skip`):")
        elif step=="footer":
            st["footer"]=None if content.lower()=="skip" else content; st["step"]="image"
            await message.reply("Įrašyk **paveikslėlio URL** (arba `skip`):")
        elif step=="image":
            st["image"]=None if content.lower()=="skip" else content; del active_embed[uid]
            emb=discord.Embed(title=st.get("title"),description=st.get("description"),color=st.get("color",discord.Color.blurple()))
            if st.get("footer"): emb.set_footer(text=st["footer"])
            if st.get("image"): emb.set_image(url=st["image"])
            await message.channel.send("🎨 **Štai tavo embed:**",embed=emb)
        return

    if uid in active_adventures and content in ["1","2","3"]:
        adv=active_adventures[uid]
        if time.time()-adv["time"]>60:
            del active_adventures[uid]; await message.reply("⏰ Per ilgai laukei!"); return
        idx=int(content)-1; sc=adv["scenario"]
        if idx>=len(sc["choices"]): return
        ch_c=sc["choices"][idx]; outcome=ch_c["outcome"]; del active_adventures[uid]
        if outcome=="gold":
            amt=random.randint(*ch_c["amount"]); acoin(gid,uid,amt)
            result=f"💰 Radai **{amt}** monetų!"; color=discord.Color.gold()
        elif outcome=="treasure":
            amt=random.randint(*ch_c["amount"]); acoin(gid,uid,amt)
            result=f"🎁 Radai lobį! +**{amt}** monetų!"; color=discord.Color.gold()
        elif outcome=="trap":
            result="💥 Patekei į spąstus! Išgyvenai, bet praradai energijos."; color=discord.Color.red()
        elif outcome=="monster":
            enemy=ch_c["enemy"]; m=MONSTERS.get(enemy,MONSTERS["Goblin"])
            if random.random()<0.6:
                rw=random.randint(*m["reward"]); acoin(gid,uid,rw)
                result=f"{m['emoji']} Nugalėjai **{enemy}**! +{rw} monetų!"; color=discord.Color.green()
            else:
                result=f"{m['emoji']} **{enemy}** nugalėjo tave! 💀"; color=discord.Color.red()
        elif outcome=="quest":
            rw=random.randint(*ch_c["reward"]); acoin(gid,uid,rw)
            result=f"📜 Padėjai keliautojui! +**{rw}** monetų!"; color=discord.Color.blue()
        else:
            result="🤷 Nieko ypatingo nenutiko."; color=discord.Color.gray()
        await message.channel.send(embed=discord.Embed(title="🗺️ Nuotykio pabaiga",description=result,color=color))
        return

    # Marriage accept/decline
    if content=="!accept":
        prop_key=None; prop_id=None
        for k,d in active_marriages_pending.items():
            if d["target"]==uid and k.startswith(f"{gid}:") and time.time()-d["time"]<60:
                prop_key=k; prop_id=int(k.split(":")[1]); break
        if not prop_key:
            await message.reply("Nėra aktyvių vestuvių pasiūlymų! 💔"); return
        del active_marriages_pending[prop_key]
        acoin(gid,prop_id,-1000)
        D["marriages"].setdefault(str(gid),{})
        D["marriages"][str(gid)][str(prop_id)]=uid
        D["marriages"][str(gid)][str(uid)]=prop_id
        save_data(D)
        proposer=message.guild.get_member(prop_id)
        msg=random.choice(WEDDING_MSGS).format(u1=proposer.display_name if proposer else "???",u2=message.author.display_name)
        e=discord.Embed(title="💒 VESTUVĖS!",description=msg,color=discord.Color.gold())
        await message.channel.send(embed=e)
        return

    if content=="!decline":
        for k,d in list(active_marriages_pending.items()):
            if d["target"]==uid and k.startswith(f"{gid}:"):
                del active_marriages_pending[k]
                await message.reply("💔 Vestuvių pasiūlymas atmestas...")
                return
        await message.reply("Nėra aktyvių pasiūlymų!")
        return

    # ══════════════════════════════════════════════════════════════════════════
    #  KOMANDOS
    # ══════════════════════════════════════════════════════════════════════════

    if content=="!help":
        e=discord.Embed(title="📚 Kodas Bot V4 — Komandų sąrašas",color=discord.Color.from_rgb(88,101,242))
        e.add_field(name="🎵 Muzika",value="`!play` `!skip` `!stop` `!pause` `!resume` `!queue` `!np` `!loop`",inline=False)
        e.add_field(name="🛍️ Parduotuvė",value="`!shop` `!buy [id]` `!myorders` `!payment`",inline=False)
        e.add_field(name="💰 Ekonomika",value="`!balance` `!daily` `!work` `!give @ suma` `!bet suma` `!rob @` `!richlist`",inline=False)
        e.add_field(name="📈 Akcijos",value="`!stocks` `!buystock [SYM] [n]` `!sellstock [SYM] [n]` `!portfolio`",inline=False)
        e.add_field(name="🛒 Parduotuvė",value="`!itemshop` `!buyitem [id]` `!inventory`",inline=False)
        e.add_field(name="🎮 Žaidimai",value="`!trivia` `!hangman` `!guess` `!wordchain` `!ttt @` `!connect4 @` `!duel @` `!roulette` `!rps`",inline=False)
        e.add_field(name="🎰 Casino",value="`!casino [suma]` `!blackjack [suma]`",inline=False)
        e.add_field(name="🐟 Žvejyba",value="`!fish` `!fishstats`",inline=False)
        e.add_field(name="💕 Socialinės",value="`!hug @` `!kiss @` `!slap @` `!pat @` `!punch @` `!poke @` `!ship @ @` `!marry @` `!divorce` `!partner`",inline=False)
        e.add_field(name="🐾 Augintiniai",value="`!adopt [tipas]` `!pet` `!feed` `!playpet` `!petname [vardas]`",inline=False)
        e.add_field(name="⚔️ RPG",value="`!battle` `!battle @` `!adventure`",inline=False)
        e.add_field(name="🔮 Kita",value="`!horoscope [ženklas]` `!birthday set MM-DD` `!birthdays` `!suggest [idėja]` `!confess [tekstas]`",inline=False)
        e.add_field(name="🎁 Giveaway",value="`!giveaway [min] [prizas]` (admin)",inline=False)
        e.add_field(name="🎫 Tickets",value="`!ticketpanel` `!claim` `!priority [lygis]` `!close` `!transcript`",inline=False)
        e.add_field(name="🛡️ Admin",value="`!warn @` `!mute @` `!unmute @` `!kick @` `!ban @` `!clear [n]` `!setlog #` `!setwelcome #` `!setautorole @` `!setlevelrole [n] @` `!blacklist` `!setsupport @` `!captcha on/off`",inline=False)
        e.add_field(name="🏆 Rangas",value="`!rank [@]` `!leaderboard` `!stats` `!achievements`",inline=False)
        e.add_field(name="🤖 AI",value="`@Kodas [žinutė]` `!ask [klausimas]` `!translate [kalba] [tekstas]` `!forget`",inline=False)
        e.add_field(name="🎭 Smagu",value="`!moneta` `!8ball` `!roast [@]` `!joke` `!fact` `!quote` `!mood` `!embed` `!anon` `!poll` `!remindme` `!afk`",inline=False)
        e.add_field(name="💡 Slash komandos",value="`/help` `/balance` `/rank`",inline=False)
        e.add_field(name="🔗 Integracijos",value="`!settwitch #` `!addtwitch [vardas]` `!setyoutube #` `!addyoutube [ID]` `!setboostch #` `!integrations`",inline=False)
        e.add_field(name="🎭 Reaction Roles",value="`!rrpanel` `!rradd @rolė [emoji]` `!rrclear` `!rrtitle [pavadinimas]`",inline=False)
        e.add_field(name="🎵 Spotify",value="`!spotify [@narys]`",inline=False)
        e.set_footer(text=ft())
        await message.channel.send(embed=e)
        return

    # ── MUZIKA ────────────────────────────────────────────────────────────────

    if content.startswith("!play"):
        query=content[5:].strip()
        if not query: await message.reply("🎵 Naudok: `!play [daina]`"); return
        if not message.author.voice: await message.reply("❌ Tu turi būti voice kanale!"); return
        vc=vc_clients.get(gid)
        if not vc or not vc.is_connected():
            try: vc=await message.author.voice.channel.connect(); vc_clients[gid]=vc
            except Exception as ex: await message.reply(f"❌ {ex}"); return
        elif vc.channel!=message.author.voice.channel: await vc.move_to(message.author.voice.channel)
        async with message.channel.typing():
            info=await yt_info(query)
            if not info: await message.reply("❌ Nepavyko rasti! (ar įdiegtas yt-dlp?)"); return
            song={"title":info["title"],"url":info["url"],"duration":info["duration"],"requester":message.author.display_name}
            music_q.setdefault(gid,deque())
            if not vc.is_playing() and not vc.is_paused():
                music_q[gid].append(song); await play_next(gid)
                e=discord.Embed(title="🎵 Dabar groja",description=f"**{song['title']}**",color=discord.Color.green())
                e.add_field(name="⏱️",value=fmt_dur(song["duration"]),inline=True)
                e.add_field(name="👤",value=song["requester"],inline=True)
            else:
                music_q[gid].append(song)
                e=discord.Embed(title="📝 Pridėta į eilę",description=f"**{song['title']}**",color=discord.Color.blue())
                e.add_field(name="📍 Pozicija",value=f"#{len(music_q[gid])}",inline=True)
            await message.channel.send(embed=e)
        return

    if content=="!skip":
        vc=vc_clients.get(gid)
        if vc and vc.is_playing(): vc.stop(); await message.reply("⏭️ Praleista!")
        else: await message.reply("❌ Nieko negroja!")
        return

    if content=="!stop":
        vc=vc_clients.get(gid)
        if vc:
            music_q.pop(gid,None); now_play.pop(gid,None)
            await vc.disconnect(); vc_clients.pop(gid,None)
            await message.reply("⏹️ Sustabdyta!")
        else: await message.reply("❌ Nesu voice kanale!")
        return

    if content=="!pause":
        vc=vc_clients.get(gid)
        if vc and vc.is_playing(): vc.pause(); await message.reply("⏸️ Pauzė!")
        else: await message.reply("❌ Nieko negroja!")
        return

    if content=="!resume":
        vc=vc_clients.get(gid)
        if vc and vc.is_paused(): vc.resume(); await message.reply("▶️ Tęsiama!")
        else: await message.reply("❌ Nepauzuota!")
        return

    if content in ("!queue","!q"):
        q=music_q.get(gid,deque()); cur=now_play.get(gid)
        if not cur and not q: await message.reply("📭 Eilė tuščia!"); return
        e=discord.Embed(title="🎵 Muzikos eilė",color=discord.Color.purple())
        if cur: e.add_field(name="▶️ Dabar",value=f"**{cur['title']}** ({fmt_dur(cur['duration'])})",inline=False)
        if q:
            txt="\n".join(f"`{i}.` **{s['title']}**" for i,s in enumerate(list(q)[:10],1))
            if len(q)>10: txt+=f"\n*...ir dar {len(q)-10}*"
            e.add_field(name="📝 Eilė",value=txt,inline=False)
        e.set_footer(text=f"Loop: {'✅' if music_loop.get(gid) else '❌'}")
        await message.channel.send(embed=e)
        return

    if content in ("!np","!nowplaying"):
        cur=now_play.get(gid)
        if not cur: await message.reply("❌ Nieko negroja!"); return
        e=discord.Embed(title="🎵 Dabar groja",description=f"**{cur['title']}**",color=discord.Color.green())
        e.add_field(name="⏱️",value=fmt_dur(cur["duration"]),inline=True)
        e.add_field(name="👤",value=cur["requester"],inline=True)
        await message.channel.send(embed=e)
        return

    if content=="!loop":
        music_loop[gid]=not music_loop.get(gid,False)
        await message.reply(f"🔁 Loop: {'✅ Įjungtas' if music_loop[gid] else '❌ Išjungtas'}")
        return

    # ── PARDUOTUVĖ ────────────────────────────────────────────────────────────

    if content=="!shop":
        prods=get_products(message.guild.id)
        e=embed_shop_main(message.guild.name,prods)
        await message.channel.send(embed=e,view=ShopBuyView(prods,gid))
        return

    if content.startswith("!buy") and not content.startswith("!buystock") and not content.startswith("!buyitem"):
        if not message.guild: return
        parts=content.split()
        if len(parts)<2 or not parts[1].isdigit(): await message.reply("Naudok: `!buy [ID]`"); return
        pid=int(parts[1]); prods=get_products(message.guild.id)
        prod=next((p for p in prods if p["id"]==pid),None)
        if not prod: await message.reply(f"Produktas **#{pid}** nerastas!"); return
        if prod.get("stock",0)<=0: await message.reply("Šis produktas nepasiekiamas ❌"); return
        order={"id":next_oid(message.guild.id),"product_id":prod["id"],"product_name":prod["name"],"duration":prod["duration"],"price":prod["price"],"user_id":str(uid),"username":message.author.display_name,"status":"laukiama","ts":time.time(),"channel_id":None}
        D["orders"].setdefault(str(message.guild.id),[]).append(order); save_data(D)
        categ=discord.utils.get(message.guild.categories,name="📦 Užsakymai")
        if not categ:
            try: categ=await message.guild.create_category("📦 Užsakymai")
            except: categ=None
        ow={message.guild.default_role:discord.PermissionOverwrite(view_channel=False),message.author:discord.PermissionOverwrite(view_channel=True,send_messages=True,read_message_history=True),message.guild.me:discord.PermissionOverwrite(view_channel=True,send_messages=True,manage_channels=True)}
        for role in message.guild.roles:
            if role.permissions.administrator: ow[role]=discord.PermissionOverwrite(view_channel=True,send_messages=True)
        try:
            new_ch=await message.guild.create_text_channel(f"🛍️-užsakymas-{order['id']:04d}",category=categ,overwrites=ow)
            order["channel_id"]=str(new_ch.id); save_data(D)
            e=discord.Embed(title=f"🛍️ Užsakymas #{order['id']:04d}",color=discord.Color.from_rgb(88,101,242))
            e.add_field(name="Produktas",value=f"{prod['emoji']} **{prod['name']}**",inline=True)
            e.add_field(name="Trukmė",value=prod["duration"],inline=True)
            e.add_field(name="Kaina",value=f"**{prod['price']}€**",inline=True)
            e.add_field(name="Pirkėjas",value=message.author.mention,inline=True)
            e.add_field(name="Statusas",value="⏳ Laukiama apmokėjimo",inline=True)
            methods=D["payment_methods"].get(str(message.guild.id),{})
            if methods:
                pay_txt="".join(f"{PAYMENT_META.get(k,{'icon':'💳'})['icon']} **{PAYMENT_META.get(k,{'label':k})['label']}:** `{v}`\n" for k,v in methods.items())
                e.add_field(name="💳 Mokėjimas",value=pay_txt,inline=False)
            e.add_field(name="📋 Instrukcija",value="1. Sumokėk nurodytu būdu\n2. Pateik mokėjimo screenshot\n3. Adminas suaktyvins\n\n*Uždaryti: `!close`*",inline=False)
            e.set_thumbnail(url=message.author.display_avatar.url)
            e.set_footer(text=ts(f"#{order['id']:04d}"))
            await new_ch.send(content=message.author.mention,embed=e)
            await message.reply(embed=discord.Embed(description=f"✅ Užsakymas sukurtas! Eik į {new_ch.mention}",color=discord.Color.green()))
        except discord.Forbidden:
            await message.reply("Neturiu teisių 🚫")
        return

    if content=="!myorders":
        if not message.guild: return
        orders=[o for o in get_orders(message.guild.id) if o["user_id"]==str(uid)]
        if not orders: await message.reply("Neturi jokių užsakymų! `!shop`"); return
        e=discord.Embed(title=f"📦 {message.author.display_name} — Užsakymai",color=discord.Color.from_rgb(88,101,242))
        emo={"laukiama":"⏳","vykdoma":"🔄","ivykdyta":"✅","atšaukta":"❌"}
        for o in orders[-10:]:
            dt=datetime.datetime.fromtimestamp(o["ts"]).strftime("%Y-%m-%d")
            e.add_field(name=f"#{o['id']:04d} — {o['product_name']}",value=f"{emo.get(o['status'],'❓')} {o['status']} • {o['price']}€ • {dt}",inline=False)
        await message.channel.send(embed=e)
        return

    if content=="!orders":
        if not message.guild or not message.author.guild_permissions.administrator: await message.reply("Reikalingos teisės 🚫"); return
        pending=[o for o in get_orders(message.guild.id) if o["status"]!="ivykdyta"]
        if not pending: await message.reply("Nėra laukiančių užsakymų ✅"); return
        e=discord.Embed(title=f"📋 Užsakymai ({len(pending)} laukia)",color=discord.Color.orange())
        for o in pending:
            dt=datetime.datetime.fromtimestamp(o["ts"]).strftime("%m-%d %H:%M")
            e.add_field(name=f"#{o['id']:04d} — {o['product_name']}",value=f"⏳ {o['username']} • {o['price']}€ • {dt}",inline=False)
        e.set_footer(text="!complete [ID]")
        await message.channel.send(embed=e)
        return

    if content.startswith("!complete"):
        if not message.guild or not message.author.guild_permissions.administrator: await message.reply("Reikalingos teisės 🚫"); return
        parts=content.split()
        if len(parts)<2 or not parts[1].isdigit(): await message.reply("Naudok: `!complete [ID]`"); return
        oid=int(parts[1]); order=update_order(message.guild.id,oid,"ivykdyta")
        if not order: await message.reply(f"Užsakymas **#{oid}** nerastas"); return
        await message.channel.send(embed=discord.Embed(description=f"✅ Užsakymas **#{oid:04d}** įvykdytas! — {order['product_name']} / {order['username']}",color=discord.Color.green()))
        if order.get("channel_id"):
            uch=bot.get_channel(int(order["channel_id"]))
            if uch: await uch.send(embed=discord.Embed(title="✅ Užsakymas įvykdytas!",description=f"**{order['product_name']}** suaktyvinta! 🎉",color=discord.Color.green()))
        return

    if content.startswith("!addproduct"):
        if not message.guild or not message.author.guild_permissions.administrator: await message.reply("Reikalingos teisės 🚫"); return
        rest=content[11:].strip(); parts=[p.strip() for p in rest.split("|")]
        if len(parts)<4: await message.reply("Naudok: `!addproduct Pavadinimas | Aprašymas | Kaina | Kategorija | Emoji | Trukmė`"); return
        prods=get_products(message.guild.id); new_id=max((p["id"] for p in prods),default=0)+1
        new_p={"id":new_id,"name":parts[0],"desc":parts[1] if len(parts)>1 else "","price":float(parts[2]) if len(parts)>2 else 0.0,"old_price":None,"category":parts[3] if len(parts)>3 else "other","emoji":parts[4] if len(parts)>4 else "📦","duration":parts[5] if len(parts)>5 else "1 mėn.","stock":99}
        prods.append(new_p); D["products"][str(message.guild.id)]=prods; save_data(D)
        await message.channel.send(embed=discord.Embed(description=f"✅ **#{new_id}** {new_p['emoji']} **{new_p['name']}** — {new_p['price']}€",color=discord.Color.green()))
        return

    if content.startswith("!removeproduct"):
        if not message.guild or not message.author.guild_permissions.administrator: await message.reply("Reikalingos teisės 🚫"); return
        parts=content.split()
        if len(parts)<2 or not parts[1].isdigit(): await message.reply("Naudok: `!removeproduct [ID]`"); return
        pid=int(parts[1]); prods=get_products(message.guild.id)
        prod=next((p for p in prods if p["id"]==pid),None)
        if not prod: await message.reply("Nerastas!"); return
        prods.remove(prod); D["products"][str(message.guild.id)]=prods; save_data(D)
        await message.reply(f"✅ **{prod['name']}** pašalintas.")
        return

    if content.startswith("!setpayment"):
        if not message.guild or not message.author.guild_permissions.administrator: await message.reply("Reikalingos teisės 🚫"); return
        rest=content[11:].strip(); parts=rest.split(" ",1)
        if len(parts)<2: await message.reply(f"Naudok: `!setpayment [būdas] [info]`\nBūdai: {', '.join(PAYMENT_META)}"); return
        method,details=parts[0].lower(),parts[1]
        D["payment_methods"].setdefault(str(message.guild.id),{})[method]=details; save_data(D)
        meta=PAYMENT_META.get(method,{"icon":"💳","label":method})
        await message.channel.send(embed=discord.Embed(description=f"✅ {meta['icon']} **{meta['label']}**: `{details}`",color=discord.Color.green()))
        return

    if content=="!payment":
        if not message.guild: return
        methods=D["payment_methods"].get(str(message.guild.id),{})
        e=discord.Embed(title="💳 Mokėjimo būdai",color=discord.Color.from_rgb(88,101,242))
        if methods:
            for k,v in methods.items():
                meta=PAYMENT_META.get(k,{"icon":"💳","label":k})
                e.add_field(name=f"{meta['icon']} {meta['label']}",value=f"`{v}`",inline=False)
        else:
            e.description="Mokėjimo būdai nenustatyti.\n`!setpayment [būdas] [info]`"
        await message.channel.send(embed=e)
        return

    # ── AKCIJŲ RINKA ──────────────────────────────────────────────────────────

    if content=="!stocks":
        await message.channel.send(embed=embed_stocks(STOCKS))
        return

    if content.startswith("!buystock"):
        parts=content.split()
        if len(parts)<3 or not parts[2].isdigit(): await message.reply("Naudok: `!buystock [SYM] [kiekis]`"); return
        sym=parts[1].upper(); amount=int(parts[2])
        if sym not in STOCKS: await message.reply(f"Akcija **{sym}** nerasta! `!stocks`"); return
        total=int(STOCKS[sym]["price"]*amount)
        if gcoin(gid,uid)<total: await message.reply(f"Neturi tiek! Reikia: **{total}** 🪙"); return
        acoin(gid,uid,-total); add_stock(gid,uid,sym,amount)
        check_ach(gid,uid,"investor") if False else None
        await message.channel.send(embed=discord.Embed(description=f"📈 Nupirkai **{amount}x {sym}** už **{total}** 🪙!",color=discord.Color.green()))
        return

    if content.startswith("!sellstock"):
        parts=content.split()
        if len(parts)<3 or not parts[2].isdigit(): await message.reply("Naudok: `!sellstock [SYM] [kiekis]`"); return
        sym=parts[1].upper(); amount=int(parts[2])
        user_stocks=get_stocks_user(gid,uid)
        if sym not in user_stocks or user_stocks[sym]<amount: await message.reply(f"Neturi tiek **{sym}** akcijų!"); return
        total=int(STOCKS[sym]["price"]*amount); acoin(gid,uid,total); add_stock(gid,uid,sym,-amount)
        await message.channel.send(embed=discord.Embed(description=f"📉 Pardavei **{amount}x {sym}** už **{total}** 🪙!",color=discord.Color.blue()))
        return

    if content=="!portfolio":
        user_stocks=get_stocks_user(gid,uid)
        if not user_stocks: await message.reply("Portfelis tuščias! `!buystock [SYM] [n]`"); return
        e=discord.Embed(title=f"💼 {message.author.display_name} Portfelis",color=discord.Color.gold())
        total_val=0
        for sym,amount in user_stocks.items():
            if sym in STOCKS:
                val=STOCKS[sym]["price"]*amount; total_val+=val
                e.add_field(name=f"{STOCKS[sym]['emoji']} {sym}",value=f"**{amount}** vnt. = **{val:.0f}** 🪙",inline=True)
        e.add_field(name="💰 Viso",value=f"**{total_val:.0f}** 🪙",inline=False)
        await message.channel.send(embed=e)
        return

    # ── DAIKTŲ PARDUOTUVĖ ────────────────────────────────────────────────────

    if content=="!itemshop":
        e=discord.Embed(title="🛒 Daiktų Parduotuvė",description="Naudok `!buyitem [id]` pirkti",color=discord.Color.purple())
        for item in SHOP_ITEMS:
            e.add_field(name=f"{item['emoji']} {item['name']}",value=f"**{item['price']}** 🪙 | ID: `{item['id']}`",inline=True)
        await message.channel.send(embed=e)
        return

    if content.startswith("!buyitem"):
        item_id=content[8:].strip()
        if not item_id: await message.reply("Naudok: `!buyitem [id]`"); return
        item=next((i for i in SHOP_ITEMS if i["id"]==item_id),None)
        if not item: await message.reply("Daiktas nerastas!"); return
        if gcoin(gid,uid)<item["price"]: await message.reply(f"Reikia **{item['price']}** 🪙!"); return
        acoin(gid,uid,-item["price"])
        if item["type"]=="pet":
            pet_type=item["pet"]
            D["pet_data"].setdefault(str(gid),{})[str(uid)]={"type":pet_type,"emoji":PET_TYPES.get(pet_type,"🐾"),"name":random.choice(PET_NAMES),"hunger":100,"happiness":100,"level":1,"xp":0,"last_fed":time.time(),"last_played":time.time()}
            save_data(D)
            await message.reply(f"✅ Įsivaikinaite {PET_TYPES.get(pet_type,'🐾')} augintinį!")
        elif item["type"]=="lottery":
            prize=random.choice([0,0,0,100,200,500,1000,5000])
            if prize>0:
                acoin(gid,uid,prize)
                await message.reply(f"🎟️ Laimėjai loterijos bilietą! Prizas: **{prize}** 🪙! 🎉")
            else:
                await message.reply("🎟️ Deja, šį kartą nelaimėjai... Bandyk dar kartą!")
        else:
            add_inv(gid,uid,item_id)
            await message.reply(f"✅ Nusipirkai **{item['emoji']} {item['name']}**!")
        return

    if content=="!inventory":
        inv=get_inv(gid,uid)
        if not inv: await message.reply("Inventorius tuščias! `!itemshop`"); return
        e=discord.Embed(title=f"🎒 {message.author.display_name} Inventorius",color=discord.Color.purple())
        counts={}
        for i in inv: counts[i]=counts.get(i,0)+1
        for item_id,count in counts.items():
            item=next((x for x in SHOP_ITEMS if x["id"]==item_id),None)
            if item: e.add_field(name=f"{item['emoji']} {item['name']}",value=f"x**{count}**",inline=True)
        await message.channel.send(embed=e)
        return

    # ── MODERAVIMAS ───────────────────────────────────────────────────────────

    if content.startswith("!warn"):
        if not message.guild or not message.author.guild_permissions.kick_members: await message.reply("Reikalingos teisės 🚫"); return
        if not message.mentions: await message.reply("Naudok: `!warn @vardas [priežastis]`"); return
        target=message.mentions[0]; reason=re.sub(r"<@!?\d+>","",content[5:]).strip() or "Priežastis nenurodyta"
        count=awarn(message.guild.id,target.id,reason,message.author.display_name)
        e=discord.Embed(title=f"⚠️ Perspėjimas — {target.display_name}",color=discord.Color.yellow())
        e.add_field(name="Priežastis",value=reason,inline=False)
        e.add_field(name="Perspėjimai",value=f"**{count}/{WARN_KICK}**",inline=True)
        e.set_thumbnail(url=target.display_avatar.url)
        await message.channel.send(embed=e)
        if count>=WARN_KICK:
            try: await target.kick(reason=f"Auto-kick: {WARN_KICK} perspėjimai"); await message.channel.send(embed=discord.Embed(description=f"🦵 **{target.display_name}** išspirtas!",color=discord.Color.red()))
            except: pass
        return

    if content.startswith("!mute"):
        if not message.guild or not message.author.guild_permissions.moderate_members: await message.reply("Reikalingos teisės 🚫"); return
        if not message.mentions: await message.reply("Naudok: `!mute @vardas [minutės] [priežastis]`"); return
        target=message.mentions[0]; parts=content.split()
        mins=int(parts[2]) if len(parts)>2 and parts[2].isdigit() else 10
        reason=" ".join(parts[3:]) if len(parts)>3 else "Priežastis nenurodyta"
        try:
            until=discord.utils.utcnow()+datetime.timedelta(minutes=mins)
            await target.timeout(until,reason=reason)
            await message.channel.send(embed=discord.Embed(description=f"🔇 **{target.display_name}** nutildytas **{mins}** min. | {reason}",color=discord.Color.orange()))
        except Exception as ex: await message.reply(f"Klaida: {ex}")
        return

    if content.startswith("!unmute"):
        if not message.guild or not message.author.guild_permissions.moderate_members: await message.reply("Reikalingos teisės 🚫"); return
        if not message.mentions: await message.reply("Naudok: `!unmute @vardas`"); return
        try:
            await message.mentions[0].timeout(None)
            await message.channel.send(embed=discord.Embed(description=f"🔊 **{message.mentions[0].display_name}** nutildymas pašalintas.",color=discord.Color.green()))
        except Exception as ex: await message.reply(f"Klaida: {ex}")
        return

    if content.startswith("!kick"):
        if not message.guild or not message.author.guild_permissions.kick_members: await message.reply("Reikalingos teisės 🚫"); return
        if not message.mentions: await message.reply("Naudok: `!kick @vardas [priežastis]`"); return
        target=message.mentions[0]; reason=re.sub(r"<@!?\d+>","",content[5:]).strip() or "Priežastis nenurodyta"
        try: await target.kick(reason=reason); await message.channel.send(embed=discord.Embed(description=f"🦵 **{target.display_name}** išspirtas. | {reason}",color=discord.Color.red()))
        except Exception as ex: await message.reply(f"Klaida: {ex}")
        return

    if content.startswith("!ban"):
        if not message.guild or not message.author.guild_permissions.ban_members: await message.reply("Reikalingos teisės 🚫"); return
        if not message.mentions: await message.reply("Naudok: `!ban @vardas [priežastis]`"); return
        target=message.mentions[0]; reason=re.sub(r"<@!?\d+>","",content[4:]).strip() or "Priežastis nenurodyta"
        try:
            await target.ban(reason=reason)
            await message.channel.send(embed=embed_mod_log("🔨 Ban",target,message.author,reason,C.CRIMSON))
            log_id=D["log_channels"].get(str(gid))
            if log_id:
                lch=bot.get_channel(int(log_id))
                if lch: await lch.send(embed=embed_mod_log("🔨 Ban",target,message.author,reason,C.CRIMSON))
        except Exception as ex: await message.reply(f"Klaida: {ex}")
        return

    if content.startswith("!clear"):
        if not message.guild or not message.author.guild_permissions.manage_messages: await message.reply("Reikalingos teisės 🚫"); return
        parts=content.split(); n=min(int(parts[1]) if len(parts)>1 and parts[1].isdigit() else 10,100)
        deleted=await message.channel.purge(limit=n+1)
        await message.channel.send(f"🗑️ Ištrinta **{len(deleted)-1}** žinučių.",delete_after=5)
        return

    if content.startswith("!warnings"):
        if not message.guild: return
        target=message.mentions[0] if message.mentions else message.author
        warns=gwarn(message.guild.id,target.id)
        e=discord.Embed(title=f"⚠️ {target.display_name} — Perspėjimai ({len(warns)}/{WARN_KICK})",color=discord.Color.yellow() if warns else discord.Color.green())
        if warns:
            for i,w in enumerate(warns,1):
                dt=datetime.datetime.fromtimestamp(w["ts"]).strftime("%Y-%m-%d")
                e.add_field(name=f"{i}. {w['reason']}",value=f"Mod: {w['mod']} • {dt}",inline=False)
        else: e.description="Perspėjimų nėra ✅"
        await message.channel.send(embed=e)
        return

    if content.startswith("!clearwarns"):
        if not message.guild or not message.author.guild_permissions.kick_members: await message.reply("Reikalingos teisės 🚫"); return
        if not message.mentions: await message.reply("Naudok: `!clearwarns @vardas`"); return
        cwarn(message.guild.id,message.mentions[0].id)
        await message.reply(embed=discord.Embed(description=f"✅ **{message.mentions[0].display_name}** perspėjimai išvalyti.",color=discord.Color.green()))
        return

    if content.startswith("!blacklist"):
        if not message.guild or not message.author.guild_permissions.administrator: await message.reply("Reikalingos teisės 🚫"); return
        word=content[10:].strip().lower()
        if not word:
            bl=D["blacklist"].get(str(gid),[])
            await message.reply(f"📋 Draudžiami žodžiai: {', '.join(bl) if bl else 'nėra'}"); return
        bl=D["blacklist"].setdefault(str(gid),[])
        if word in bl:
            bl.remove(word); save_data(D); await message.reply(f"✅ `{word}` pašalintas.")
        else:
            bl.append(word); save_data(D); await message.reply(f"✅ `{word}` pridėtas.")
        return

    if content.startswith("!setlog"):
        if not message.guild or not message.author.guild_permissions.administrator: await message.reply("Reikalingos teisės 🚫"); return
        if not message.channel_mentions: await message.reply("Naudok: `!setlog #kanalas`"); return
        D["log_channels"][str(gid)]=message.channel_mentions[0].id; save_data(D)
        await message.reply(f"✅ Log kanalas: {message.channel_mentions[0].mention}")
        return

    if content.startswith("!setwelcome"):
        if not message.guild or not message.author.guild_permissions.administrator: await message.reply("Reikalingos teisės 🚫"); return
        if not message.channel_mentions: await message.reply("Naudok: `!setwelcome #kanalas`"); return
        D["welcome_channels"][str(gid)]=message.channel_mentions[0].id; save_data(D)
        await message.reply(f"✅ Sveikinimų kanalas: {message.channel_mentions[0].mention}")
        return

    if content.startswith("!setautorole"):
        if not message.guild or not message.author.guild_permissions.administrator: await message.reply("Reikalingos teisės 🚫"); return
        if not message.role_mentions: await message.reply("Naudok: `!setautorole @rolė`"); return
        D["auto_roles"][str(gid)]=message.role_mentions[0].id; save_data(D)
        await message.reply(f"✅ Auto rolė: {message.role_mentions[0].mention}")
        return

    if content.startswith("!setlevelrole"):
        if not message.guild or not message.author.guild_permissions.administrator: await message.reply("Reikalingos teisės 🚫"); return
        parts=content.split()
        if len(parts)<2 or not parts[1].isdigit() or not message.role_mentions: await message.reply("Naudok: `!setlevelrole [lygis] @rolė`"); return
        D["level_rewards"].setdefault(str(gid),{})[parts[1]]=message.role_mentions[0].id; save_data(D)
        await message.reply(f"✅ Lygis **{parts[1]}** → {message.role_mentions[0].mention}")
        return

    if content.startswith("!setsupport"):
        if not message.guild or not message.author.guild_permissions.administrator: await message.reply("Reikalingos teisės 🚫"); return
        if not message.role_mentions: await message.reply("Naudok: `!setsupport @rolė`"); return
        D.setdefault("support_roles",{})[str(gid)]=message.role_mentions[0].id; save_data(D)
        await message.reply(f"✅ Support rolė: {message.role_mentions[0].mention}")
        return

    if content.startswith("!captcha"):
        if not message.guild or not message.author.guild_permissions.administrator: await message.reply("Reikalingos teisės 🚫"); return
        mode=content[8:].strip().lower()
        D.setdefault("captcha_enabled",{})[str(gid)]=(mode=="on"); save_data(D)
        await message.reply(f"✅ Captcha: {'✅ įjungta' if mode=='on' else '❌ išjungta'}")
        return

    if content=="!setchannel":
        if not message.guild or not message.author.guild_permissions.manage_channels: await message.reply("Reikalingos teisės 🚫"); return
        D["daily_channels"][str(gid)]=ch_id; save_data(D)
        await message.reply("✅ Kanalas nustatytas kasdienių žinių kanalui!")
        return

    # ── TICKET SISTEMA ────────────────────────────────────────────────────────

    if content=="!ticketpanel":
        if not message.guild or not message.author.guild_permissions.administrator: await message.reply("Reikalingos teisės 🚫"); return
        await message.channel.send(embed=embed_ticket_panel(message.guild.name),view=TicketPanelView())
        try: await message.delete()
        except: pass
        return

    if content=="!claim":
        if not message.guild: return
        tid=str(ch_id); gid_s=str(gid)
        ticket=D["tickets"].get(gid_s,{}).get(tid)
        if not ticket: await message.reply("Šis kanalas nėra ticket!"); return
        if ticket["claimed_by"]: await message.reply(f"Jau paimtas!"); return
        ticket["claimed_by"]=uid; save_data(D)
        await message.channel.send(embed=discord.Embed(description=f"✋ **{message.author.display_name}** paėmė šį ticket!",color=discord.Color.green()))
        return

    if content.startswith("!priority"):
        if not message.guild: return
        prio=content[9:].strip().lower()
        if prio not in TICKET_PRIORITIES: await message.reply(f"Prioritetai: {', '.join(TICKET_PRIORITIES)}"); return
        tid=str(ch_id); gid_s=str(gid)
        ticket=D["tickets"].get(gid_s,{}).get(tid)
        if not ticket: await message.reply("Šis kanalas nėra ticket!"); return
        ticket["priority"]=prio; save_data(D)
        await message.channel.send(embed=discord.Embed(description=f"🎯 Prioritetas pakeistas į: **{TICKET_PRIORITIES[prio]}**",color=discord.Color.orange()))
        return

    if content=="!transcript":
        if not message.guild: return
        tid=str(ch_id); gid_s=str(gid)
        ticket=D["tickets"].get(gid_s,{}).get(tid)
        if not ticket: await message.reply("Šis kanalas nėra ticket!"); return
        transcript=f"=== TICKET TRANSCRIPT ===\n"
        transcript+=f"Kategorija: {ticket.get('category','?')}\n"
        transcript+=f"Tema: {ticket.get('subject','?')}\n"
        transcript+=f"Narys: {ticket.get('owner_name','?')}\n"
        transcript+=f"Sukurtas: {datetime.datetime.fromtimestamp(ticket.get('created_at',0)).strftime('%Y-%m-%d %H:%M')}\n"
        transcript+=f"Prioritetas: {ticket.get('priority','normal')}\n"
        transcript+=f"========================\n\n"
        transcript+=f"Aprašymas:\n{ticket.get('description','')}\n"
        import io
        file=discord.File(io.BytesIO(transcript.encode()),filename=f"ticket-{ch_id}.txt")
        await message.channel.send("📄 Ticket transcript:", file=file)
        return

    if content=="!close":
        if not message.guild: return
        gid_s=str(gid); tid=str(ch_id)
        tickets_in=D["tickets"].get(gid_s,{})
        orders_by_ch={o.get("channel_id"):o for o in get_orders(gid_s)}
        if tid not in tickets_in and tid not in orders_by_ch:
            await message.reply("Šis kanalas nėra ticket arba užsakymo kanalas 🚫"); return
        is_admin=message.author.guild_permissions.manage_channels
        if tid in tickets_in and tickets_in[tid]["owner"]!=uid and not is_admin:
            await message.reply("Tik kūrėjas arba adminas gali uždaryti 🚫"); return
        await message.channel.send("🔒 Kanalas bus ištrintas per 5 sekundes...")
        await asyncio.sleep(5)
        if tid in tickets_in:
            D["tickets"][gid_s][tid]["status"]="closed"
            D["tickets"][gid_s][tid]["closed_at"]=time.time()
            save_data(D)
        try: await message.channel.delete()
        except: pass
        return

    if content.startswith("!ticket"):
        if not message.guild: return
        reason=content[7:].strip() or "Priežastis nenurodyta"
        gid_s=str(gid); D["tickets"].setdefault(gid_s,{})
        count=len(D["tickets"][gid_s])+1
        categ=discord.utils.get(message.guild.categories,name="🎫 Tickets")
        if not categ:
            try: categ=await message.guild.create_category("🎫 Tickets")
            except: categ=None
        ow={message.guild.default_role:discord.PermissionOverwrite(view_channel=False),message.author:discord.PermissionOverwrite(view_channel=True,send_messages=True,read_message_history=True),message.guild.me:discord.PermissionOverwrite(view_channel=True,send_messages=True,manage_channels=True)}
        for role in message.guild.roles:
            if role.permissions.administrator: ow[role]=discord.PermissionOverwrite(view_channel=True,send_messages=True)
        try:
            new_ch=await message.guild.create_text_channel(f"🎫-{message.author.name[:10]}-{count}",category=categ,overwrites=ow)
            D["tickets"][gid_s][str(new_ch.id)]={"owner":uid,"owner_name":message.author.display_name,"category":"support","subject":reason,"description":reason,"priority":"normal","status":"open","claimed_by":None,"created_at":time.time()}
            save_data(D)
            e=discord.Embed(title=f"🎫 Ticket #{count}",description=f"Sveiki, {message.author.mention}!\n**Priežastis:** {reason}\n\nAdministratorius netrukus suteiks pagalbą.\n\n*Uždaryti: `!close`*",color=discord.Color.green())
            e.set_footer(text=ft())
            await new_ch.send(content=message.author.mention,embed=e,view=TicketControlView(new_ch.id,gid_s))
            await message.reply(embed=discord.Embed(description=f"✅ Ticket sukurtas: {new_ch.mention}",color=discord.Color.green()))
        except discord.Forbidden:
            await message.reply("Neturiu teisių sukurti kanalo 🚫")
        return

    # ── EKONOMIKA ─────────────────────────────────────────────────────────────

    if content.startswith("!balance") or content=="!bal":
        target=message.mentions[0] if message.mentions else message.author
        coins=gcoin(gid,target.id); xp=gxp(gid,target.id); lvl=xp//LEVEL_XP
        streak=get_streak(gid,target.id)["count"]
        e=discord.Embed(title=f"💰 {target.display_name}",color=discord.Color.gold())
        e.add_field(name="💵 Monetos",value=f"**{coins}**",inline=True)
        e.add_field(name="⭐ XP/Lygis",value=f"**{xp}** (Lv.{lvl})",inline=True)
        e.add_field(name="❤️ Reputacija",value=f"**{greg(gid,target.id)}**",inline=True)
        e.add_field(name="🔥 Streak",value=f"**{streak}** dienų",inline=True)
        e.set_thumbnail(url=target.display_avatar.url)
        await message.channel.send(embed=e)
        return

    if content=="!daily":
        if not can_daily(gid,uid): await message.reply("Jau paėmei šiandien! ⏰"); return
        amount=random.randint(DAILY_MIN,DAILY_MAX); streak=upd_streak(gid,uid)
        bonus=min(streak*15,300); total=amount+bonus
        acoin(gid,uid,total); set_daily(gid,uid)
        if streak>=7: check_ach(gid,uid,"streak_7")
        e=discord.Embed(title="🎁 Dienos bonus!",color=discord.Color.green())
        e.add_field(name="Bazė",value=f"**{amount}** 🪙",inline=True)
        e.add_field(name="🔥 Streak",value=f"x{streak} (+{bonus})",inline=True)
        e.add_field(name="Viso",value=f"**{total}** 🪙",inline=True)
        e.add_field(name="Likutis",value=f"**{gcoin(gid,uid)}** 🪙",inline=True)
        await message.reply(embed=e)
        return

    if content=="!work":
        if not can_work(gid,uid):
            last=D["work_cooldowns"].get(f"{gid}:{uid}",0)
            wait=WORK_CD-(time.time()-last)
            await message.reply(f"⏰ Pailsėk! Galėsi dirbti po **{int(wait//60)}** min."); return
        job=random.choice(JOBS); earned=random.randint(job["min"],job["max"])
        acoin(gid,uid,earned); set_work(gid,uid)
        work_count[uid]+=1
        if work_count[uid]>=30: check_ach(gid,uid,"worker")
        await message.channel.send(embed=embed_work(job["name"],job["emoji"],earned,gcoin(gid,uid),job["msg"].format(a=earned)))
        return

    if content.startswith("!give"):
        if not message.mentions: await message.reply("Naudok: `!give @vardas [suma]`"); return
        nums=[p for p in content.split() if p.isdigit()]
        if not nums: await message.reply("Įrašyk sumą!"); return
        amount=int(nums[0]); target=message.mentions[0]
        if gcoin(gid,uid)<amount: await message.reply(f"Neturi tiek! Likutis: **{gcoin(gid,uid)}** 🪙"); return
        acoin(gid,uid,-amount); nb=acoin(gid,target.id,amount)
        await message.reply(embed=discord.Embed(description=f"💸 **{message.author.display_name}** → **{target.display_name}**: **{amount}** 🪙! Jo likutis: **{nb}** 🪙",color=discord.Color.green()))
        return

    if content.startswith("!bet"):
        parts=content.split()
        if len(parts)<2 or not parts[1].isdigit(): await message.reply("Naudok: `!bet [suma]`"); return
        bet=int(parts[1])
        if gcoin(gid,uid)<bet: await message.reply(f"Neturi tiek! Likutis: **{gcoin(gid,uid)}** 🪙"); return
        if random.random()<0.5:
            nb=acoin(gid,uid,bet); await message.reply(embed=discord.Embed(description=f"🎉 Laimėjai **+{bet}** 🪙! Viso: **{nb}** 🪙",color=discord.Color.green()))
        else:
            nb=acoin(gid,uid,-bet); await message.reply(embed=discord.Embed(description=f"💀 Pralaimėjai **{bet}** 🪙. Liko: **{nb}** 🪙",color=discord.Color.red()))
        return

    if content.startswith("!rob"):
        if not message.mentions: await message.reply("Naudok: `!rob @vardas`"); return
        target=message.mentions[0]
        if target.id==uid: await message.reply("Negali apiplėšti savęs!"); return
        rob_key=f"{gid}:{uid}:rob"; last=D["rob_cooldowns"].get(rob_key,0)
        if time.time()-last<1800:
            await message.reply(f"⏰ Per anksti! Palauk **{int((1800-(time.time()-last))/60)}** min."); return
        D["rob_cooldowns"][rob_key]=time.time(); save_data(D)
        target_coins=gcoin(gid,target.id)
        if target_coins<100: await message.reply(f"**{target.display_name}** per vargšas! (min 100 🪙)"); return
        if random.random()<0.4:
            stolen=random.randint(int(target_coins*0.1),int(target_coins*0.3))
            acoin(gid,target.id,-stolen); acoin(gid,uid,stolen)
            await message.channel.send(embed=discord.Embed(title="🦹 Apiplėšimas pavyko!",description=f"Pavogei **{stolen}** 🪙 iš **{target.display_name}**!",color=discord.Color.green()))
        else:
            fine=random.randint(50,200); acoin(gid,uid,-fine)
            await message.channel.send(embed=discord.Embed(title="🚔 Pagautas!",description=f"Bauda: **{fine}** 🪙!",color=discord.Color.red()))
        return

    if content=="!richlist":
        lb=coin_lb(gid)
        if not lb: await message.reply("Dar niekas neuždirbo monetų!"); return
        entries=[(message.guild.get_member(int(u)).display_name if message.guild.get_member(int(u)) else "Nežinomas",c) for u,c in lb]
        e=embed_leaderboard_coins(entries,message.guild.name)
        await message.channel.send(embed=e)
        return

    # ── ŽVEJYBA ───────────────────────────────────────────────────────────────

    if content=="!fish":
        fk=f"{gid}:{uid}:fish"; last=D["fish_cooldowns"].get(fk,0)
        if time.time()-last<30: await message.reply(f"🎣 Palauk **{int(30-(time.time()-last))}s**!"); return
        D["fish_cooldowns"][fk]=time.time()
        roll=random.uniform(0,100); cum=0; caught=FISH_TYPES[0]
        for f in FISH_TYPES:
            cum+=f["chance"]
            if roll<=cum: caught=f; break
        acoin(gid,uid,caught["price"])
        D["fish_caught"].setdefault(str(gid),{}).setdefault(str(uid),{})
        D["fish_caught"][str(gid)][str(uid)][caught["name"]]=D["fish_caught"][str(gid)][str(uid)].get(caught["name"],0)+1
        save_data(D)
        fish_count[uid]+=1
        if fish_count[uid]>=50: check_ach(gid,uid,"fisher")
        total_f=sum(D["fish_caught"].get(str(gid),{}).get(str(uid),{}).values())
        await message.channel.send(embed=embed_fish(caught["name"],caught["emoji"],caught["rarity"],caught["price"],total_f))
        return

    if content=="!fishstats":
        stats=D["fish_caught"].get(str(gid),{}).get(str(uid),{})
        if not stats: await message.reply("Dar nepagavai žuvies! `!fish`"); return
        e=discord.Embed(title=f"🎣 {message.author.display_name} žvejybos statistika",color=discord.Color.blue())
        for name,count in sorted(stats.items(),key=lambda x:x[1],reverse=True)[:10]:
            fish=next((f for f in FISH_TYPES if f["name"]==name),None)
            e.add_field(name=f"{fish['emoji'] if fish else '🐟'} {name}",value=f"**{count}** pagauta",inline=True)
        e.set_footer(text=f"Viso: {sum(stats.values())}")
        await message.channel.send(embed=e)
        return

    # ── CASINO ────────────────────────────────────────────────────────────────

    if content.startswith("!casino"):
        parts=content.split()
        if len(parts)<2 or not parts[1].isdigit(): await message.reply("Naudok: `!casino [suma]` 🎰"); return
        bet=int(parts[1])
        if bet<10: await message.reply("Min statymas: 10 🪙"); return
        if gcoin(gid,uid)<bet: await message.reply(f"Neturi tiek! Likutis: **{gcoin(gid,uid)}** 🪙"); return
        reels=[random.choice(SLOTS) for _ in range(3)]
        if reels[0]==reels[1]==reels[2]:
            mult=10 if reels[0]=="💎" else 5 if reels[0]=="7️⃣" else 3
            rt="jackpot" if reels[0]=="💎" else "bigwin" if mult>=5 else "win"
            win=bet*mult; acoin(gid,uid,win)
            casino_wins[uid]+=1
            if casino_wins[uid]>=10: check_ach(gid,uid,"gambler")
        elif reels[0]==reels[1] or reels[1]==reels[2] or reels[0]==reels[2]:
            rt="half"; win=int(bet*0.5); acoin(gid,uid,-bet+win)
        else:
            rt="lose"; win=bet; acoin(gid,uid,-bet)
        e=embed_casino(reels,rt,win,gcoin(gid,uid))
        await message.channel.send(embed=e)
        return

    if content.startswith("!blackjack"):
        if uid in active_bj: await message.reply("Jau žaidi! `!hit` arba `!stand`"); return
        parts=content.split()
        if len(parts)<2 or not parts[1].isdigit(): await message.reply("Naudok: `!blackjack [suma]`"); return
        bet=int(parts[1])
        if gcoin(gid,uid)<bet: await message.reply(f"Neturi tiek! Likutis: **{gcoin(gid,uid)}** 🪙"); return
        deck=make_deck(); player=[deck.pop(),deck.pop()]; dealer=[deck.pop(),deck.pop()]
        active_bj[uid]={"deck":deck,"player":player,"dealer":dealer,"bet":bet,"channel":ch_id}
        pval=hand_val(player)
        if pval==21:
            del active_bj[uid]; win=int(bet*1.5); acoin(gid,uid,win)
            await message.channel.send(embed=discord.Embed(title="🃏 BLACKJACK!",description=f"Tavo: {hand_str(player)} = **21**\n🎉 **Laimėjai {win} 🪙!**",color=discord.Color.gold()))
        else:
            e=discord.Embed(title="🃏 Blackjack",description="`!hit` arba `!stand`",color=discord.Color.blurple())
            e.add_field(name="Tavo",value=f"{hand_str(player)} = **{pval}**",inline=False)
            e.add_field(name="Dileris",value=hand_str(dealer,hide=True),inline=False)
            await message.channel.send(embed=e)
        return

    if content.startswith("!rps"):
        choices={"akmuo":"🪨","žirklės":"✂️","popierius":"📄"}; wins={"akmuo":"žirklės","žirklės":"popierius","popierius":"akmuo"}
        user_c=content[4:].strip().lower()
        if user_c not in choices: await message.reply("Naudok: `!rps [akmuo/žirklės/popierius]`"); return
        bot_c=random.choice(list(choices))
        if user_c==bot_c: result="🤝 Lygiosios!"
        elif wins[user_c]==bot_c: result="🎉 Laimėjai! +20 🪙"; acoin(gid,uid,20)
        else: result="💀 Pralaimėjai!"
        await message.reply(embed=discord.Embed(title="🪨✂️📄 Akmuo Žirklės Popierius",description=f"Tu: {choices[user_c]} vs Botas: {choices[bot_c]}\n\n**{result}**",color=discord.Color.blue()))
        return

    # ── ŽAIDIMAI ──────────────────────────────────────────────────────────────

    if content=="!trivia":
        if ch_id in active_trivia: await message.reply("Jau vyksta!"); return
        q=random.choice(TRIVIA); active_trivia[ch_id]={"answer":q["a"],"exp":q["exp"]}
        await message.channel.send(embed=embed_trivia(q["q"],q["opts"]))
        def chk(m): return m.channel.id==ch_id and m.content.upper() in ["A","B","C","D"] and not m.author.bot
        try:
            ans=await bot.wait_for("message",check=chk,timeout=30.0)
            tr=active_trivia.pop(ch_id,None)
            if tr:
                if ans.content.upper()==tr["answer"]:
                    axp(gid,ans.author.id,50); acoin(gid,ans.author.id,30)
                    await ans.reply(embed=discord.Embed(description=f"✅ Teisingai! {tr['exp']}\n**+50 XP +30 🪙**",color=discord.Color.green()))
                else:
                    await ans.reply(embed=discord.Embed(description=f"❌ Neteisingai! Atsakymas: **{tr['answer']}**. {tr['exp']}",color=discord.Color.red()))
        except asyncio.TimeoutError:
            tr=active_trivia.pop(ch_id,None)
            if tr: await message.channel.send(f"⏰ Laikas baigėsi! Atsakymas: **{tr['answer']}**. {tr['exp']}")
        return

    if content=="!hangman":
        if ch_id in active_hangman: await message.reply("Jau vyksta!"); return
        word=random.choice(HANGMAN_WORDS)
        active_hangman[ch_id]={"word":word,"guessed":set(),"wrong":[]}
        shown=" ".join("_" for _ in word)
        e=discord.Embed(title="🔤 Pasikorimas!",description=f"{HANGMAN_ART[0]}\n`{shown}`\n\nSiųskite po vieną raidę!",color=discord.Color.orange())
        await message.channel.send(embed=e)
        return

    if content=="!guess":
        if ch_id in active_guess: await message.reply("Jau vyksta!"); return
        active_guess[ch_id]={"number":random.randint(1,100),"attempts":0}
        await message.channel.send(embed=discord.Embed(description="🔢 Atspėk skaičių 1-100! Turi 7 bandymus.",color=discord.Color.blue()))
        return

    if content=="!wordchain":
        if ch_id in active_wordchain: await message.reply("Jau vyksta!"); return
        start=random.choice(["katinas","namas","sportas","muzika","botas"])
        active_wordchain[ch_id]={"last":start,"used":{start}}
        e=discord.Embed(title="🔗 Žodžių grandinė!",description=f"Pradinis: **{start}**\nKitas turi prasidėti **{start[-1].upper()}**!\nKiekvienas žodis = **+5 🪙**",color=discord.Color.green())
        await message.channel.send(embed=e)
        return

    if content.startswith("!ttt"):
        if not message.mentions: await message.reply("Naudok: `!ttt @vardas`"); return
        opp=message.mentions[0]
        if opp.id==uid or opp.bot: await message.reply("Negalima!"); return
        if ch_id in active_ttt: await message.reply("Jau vyksta!"); return
        active_ttt[ch_id]={"cells":[0]*9,"turn":1,"p1":uid,"p2":opp.id}
        e=discord.Embed(title="⬜ Kryžiukai-Nuliukai",description=f"**{message.author.display_name}** (❌) vs **{opp.display_name}** (⭕)\n\n{ttt_board([0]*9)}\n\n❌ **{message.author.display_name}** eilė — rašyk 1-9",color=discord.Color.blurple())
        await message.channel.send(embed=e)
        return

    if content.startswith("!connect4"):
        if not message.mentions: await message.reply("Naudok: `!connect4 @vardas`"); return
        opp=message.mentions[0]
        if opp.id==uid or opp.bot: await message.reply("Negalima!"); return
        if ch_id in active_c4: await message.reply("Jau vyksta!"); return
        board=[[C4_EMPTY for _ in range(C4_COLS)] for _ in range(C4_ROWS)]
        active_c4[ch_id]={"board":board,"players":{1:uid,2:opp.id},"turn":1,"syms":{1:C4_P1,2:C4_P2}}
        await message.channel.send(embed=discord.Embed(title="🔴🟡 Connect 4",description=f"{c4_render(board)}\n\n{C4_P1} **{message.author.display_name}** vs {C4_P2} **{opp.display_name}**\n\n{C4_P1} Tavo eilė! Rašyk 1-7",color=discord.Color.blue()))
        return

    if content.startswith("!duel"):
        if not message.mentions: await message.reply("Naudok: `!duel @vardas`"); return
        target=message.mentions[0]
        if target.id==uid or target.bot: return
        await message.channel.send(f"⚔️ **{message.author.display_name}** iššaukė **{target.display_name}** į kovą!")
        await asyncio.sleep(2)
        winner=random.choice([message.author,target]); loser=target if winner==message.author else message.author
        axp(gid,winner.id,15); acoin(gid,winner.id,20)
        await message.channel.send(embed=discord.Embed(description=f"🏆 **{winner.display_name}** laimi! **{loser.display_name}** gali grįžti namo 😂\n+15 XP +20 🪙",color=discord.Color.gold()))
        return

    if content=="!roulette":
        await message.channel.send(f"🔫 **{message.author.display_name}** sukioja būgną...")
        await asyncio.sleep(2)
        if random.randint(1,6)==1:
            await message.channel.send(embed=discord.Embed(description=f"💥 **BANG!** {message.author.mention} nusišovė! Timeout 10 min 💀",color=discord.Color.red()))
            try: await message.author.timeout(discord.utils.utcnow()+datetime.timedelta(minutes=10))
            except: pass
        else:
            acoin(gid,uid,15)
            await message.channel.send(embed=discord.Embed(description=f"*click* — tuščia! **{message.author.display_name}** dar gyvas 😅 +15 🪙",color=discord.Color.green()))
        return

    # ── REPUTACIJA ────────────────────────────────────────────────────────────

    if content.startswith("!rep"):
        if not message.mentions: await message.reply("Naudok: `!rep @vardas`"); return
        target=message.mentions[0]
        if target.id==uid: await message.reply("Negali duoti sau!"); return
        if target.bot: await message.reply("Botams nereikia rep!"); return
        if not can_rep(gid,uid,target.id): await message.reply(f"Jau davei **{target.display_name}** šiandien! ⏰"); return
        arep(gid,target.id); set_rep(gid,uid,target.id); total=greg(gid,target.id)
        await message.channel.send(embed=discord.Embed(description=f"⭐ **{message.author.display_name}** davė reputacijos **{target.display_name}**! Viso: **{total}** ⭐",color=discord.Color.yellow()))
        return

    if content=="!toprep":
        lb=sorted(D["rep"].get(str(gid),{}).items(),key=lambda x:x[1],reverse=True)[:5]
        if not lb: await message.reply("Dar niekas negavo rep!"); return
        e=discord.Embed(title="⭐ Reputacijos lyderiai",color=discord.Color.yellow())
        medals=["🥇","🥈","🥉","4️⃣","5️⃣"]
        for i,(u,pts) in enumerate(lb):
            m=message.guild.get_member(int(u))
            e.add_field(name=f"{medals[i]} {m.display_name if m else 'Nežinomas'}",value=f"**{pts}** ⭐",inline=False)
        await message.channel.send(embed=e)
        return

    # ── SOCIALINĖS INTERAKCIJOS ───────────────────────────────────────────────

    for action,data in INTERACTIONS.items():
        if content.startswith(f"!{action}"):
            if action in ("hug","kiss","slap","pat","punch","poke","bite"):
                if not message.mentions: await message.reply(f"Naudok: `!{action} @vardas`"); return
                target_name=message.mentions[0].display_name
            else:
                target_name=message.author.display_name
            msg_template=random.choice(data["msgs"])
            msg_text=msg_template.format(u=message.author.display_name,t=target_name)
            await message.channel.send(embed=discord.Embed(description=msg_text,color=discord.Color.pink()))
            return

    if content.startswith("!ship"):
        if len(message.mentions)<2: await message.reply("Naudok: `!ship @vardas1 @vardas2`"); return
        u1,u2=message.mentions[0],message.mentions[1]
        random.seed(min(u1.id,u2.id)*max(u1.id,u2.id))
        compat=random.randint(0,100); random.seed()
        if compat<20: comment="Oi... gal geriau ne 😬"
        elif compat<50: comment="Galėtų būti geriau... 🤔"
        elif compat<80: comment="Gera pora! 💕"
        else: comment="TOBULA PORA! 💖💖💖"
        e=discord.Embed(title="💘 Meilės skaičiuoklė",description=f"**{u1.display_name}** ❤️ **{u2.display_name}**",color=discord.Color.red())
        e.add_field(name="Suderinamumas",value=f"**{compat}%**",inline=True)
        e.add_field(name="Verdiktas",value=comment,inline=True)
        await message.channel.send(embed=e)
        return

    # ── VEDYBŲ SISTEMA ────────────────────────────────────────────────────────

    if content.startswith("!marry"):
        if not message.mentions: await message.reply("Naudok: `!marry @vardas`"); return
        target=message.mentions[0]
        if target.id==uid: await message.reply("Negali vesti savęs!"); return
        if target.bot: await message.reply("Negalima vesti boto!"); return
        marriages=D["marriages"].get(str(gid),{})
        if str(uid) in marriages: await message.reply("Tu jau vedęs! `!divorce` jei nori skirtis."); return
        if str(target.id) in marriages: await message.reply(f"**{target.display_name}** jau vedęs!"); return
        if gcoin(gid,uid)<1000: await message.reply("Reikia **1000** 🪙 žiedui!"); return
        active_marriages_pending[f"{gid}:{uid}"]={"target":target.id,"time":time.time()}
        e=discord.Embed(title="💍 Vestuvių pasiūlymas!",description=f"**{message.author.display_name}** prašo **{target.display_name}** rankos!\n\n{target.mention}, ar sutinki?\nRašyk `!accept` arba `!decline`",color=discord.Color.pink())
        e.set_footer(text="Pasiūlymas galioja 60 sekundžių")
        await message.channel.send(embed=e)
        return

    if content=="!divorce":
        marriages=D["marriages"].get(str(gid),{})
        if str(uid) not in marriages: await message.reply("Tu nesi vedęs!"); return
        partner_id=marriages[str(uid)]
        del D["marriages"][str(gid)][str(uid)]
        if str(partner_id) in D["marriages"].get(str(gid),{}):
            del D["marriages"][str(gid)][str(partner_id)]
        save_data(D)
        await message.channel.send(embed=discord.Embed(description=f"💔 **{message.author.display_name}** ir jų partneris skiriasi...",color=discord.Color.dark_gray()))
        return

    if content=="!partner":
        marriages=D["marriages"].get(str(gid),{})
        target=message.mentions[0] if message.mentions else message.author
        if str(target.id) not in marriages: await message.reply(f"**{target.display_name}** nėra vedęs!"); return
        partner_id=marriages[str(target.id)]
        partner=message.guild.get_member(partner_id)
        await message.channel.send(embed=discord.Embed(title="💕 Santuoka",description=f"**{target.display_name}** 💍 **{partner.display_name if partner else '???'}**",color=discord.Color.pink()))
        return

    # ── AUGINTINIAI ───────────────────────────────────────────────────────────

    if content=="!adopt":
        types_list=" | ".join([f"{emoji} {t}" for t,emoji in PET_TYPES.items()])
        if D["pet_data"].get(str(gid),{}).get(str(uid)):
            await message.reply("Jau turi augintinį! Naudok `!pet`"); return
        await message.reply(f"🐾 Augintinių tipai: {types_list}\n\nNusipirk su `!buyitem [pet_cat/pet_dog/pet_dragon/pet_fox]`!")
        return

    if content=="!pet":
        pet=D["pet_data"].get(str(gid),{}).get(str(uid))
        if not pet: await message.reply("Neturi augintinio! Nusipirk su `!buyitem [pet_cat]` ir pan."); return
        passed=(time.time()-pet.get("last_fed",time.time()))/3600
        hunger=max(0,min(100,pet.get("hunger",100)-int(passed*5)))
        happiness=max(0,min(100,pet.get("happiness",100)-int(passed*3)))
        pet["hunger"]=hunger; pet["happiness"]=happiness; save_data(D)
        hb="█"*(hunger//10)+"░"*(10-hunger//10)
        hpb="█"*(happiness//10)+"░"*(10-happiness//10)
        e=discord.Embed(title=f"{pet['emoji']} {pet['name']}",description=f"Tipas: **{pet['type']}** | Lygis: **{pet.get('level',1)}**",color=discord.Color.green() if happiness>50 else discord.Color.orange())
        e.add_field(name="🍖 Alkis",value=f"`{hb}` {hunger}%",inline=False)
        e.add_field(name="💕 Laimė",value=f"`{hpb}` {happiness}%",inline=False)
        e.set_footer(text="!feed — maitinti | !playpet — žaisti")
        await message.channel.send(embed=e)
        return

    if content=="!feed":
        pet=D["pet_data"].get(str(gid),{}).get(str(uid))
        if not pet: await message.reply("Neturi augintinio!"); return
        if gcoin(gid,uid)<20: await message.reply("Reikia **20** 🪙 maistui!"); return
        acoin(gid,uid,-20); pet["hunger"]=min(100,pet.get("hunger",50)+30); pet["last_fed"]=time.time()
        pet["xp"]=pet.get("xp",0)+5
        if pet["xp"]>=pet.get("level",1)*50:
            pet["level"]=pet.get("level",1)+1; pet["xp"]=0
            await message.channel.send(f"🎉 **{pet['name']}** pakilo į **{pet['level']}** lygį!")
        save_data(D)
        await message.reply(f"🍖 Pamaitinai **{pet['emoji']} {pet['name']}**! Alkis: {pet['hunger']}%")
        return

    if content=="!playpet":
        pet=D["pet_data"].get(str(gid),{}).get(str(uid))
        if not pet: await message.reply("Neturi augintinio!"); return
        if time.time()-pet.get("last_played",0)<300: await message.reply(f"⏰ Augintinis pavargo! Palauk **{int(300-(time.time()-pet.get('last_played',0)))}s**"); return
        pet["happiness"]=min(100,pet.get("happiness",50)+20); pet["last_played"]=time.time()
        save_data(D)
        actions=["žaidė su kamuoliu 🎾","bėgiojo ratu 🏃","mokėsi triukų 🎪","glostėsi 🥰"]
        await message.reply(f"{pet['emoji']} **{pet['name']}** {random.choice(actions)}! Laimė: {pet['happiness']}%")
        return

    if content.startswith("!petname"):
        new_name=content[8:].strip()[:20]
        pet=D["pet_data"].get(str(gid),{}).get(str(uid))
        if not pet: await message.reply("Neturi augintinio!"); return
        old=pet["name"]; pet["name"]=new_name; save_data(D)
        await message.reply(f"✅ **{old}** dabar vadinasi **{new_name}**!")
        return

    # ── RPG ───────────────────────────────────────────────────────────────────

    if content.startswith("!battle"):
        if message.mentions:
            opp=message.mentions[0]
            if opp.id==uid or opp.bot: await message.reply("Negalima!"); return
            p1_hp=p2_hp=100; log=[]
            while p1_hp>0 and p2_hp>0:
                dmg=random.randint(8,20); crit=random.random()<0.15
                if crit: dmg*=2
                p2_hp-=dmg; log.append(f"⚔️ {message.author.display_name}: **{dmg}**{'💥' if crit else ''}")
                if p2_hp<=0: break
                dmg=random.randint(8,20); crit=random.random()<0.15
                if crit: dmg*=2
                p1_hp-=dmg; log.append(f"🗡️ {opp.display_name}: **{dmg}**{'💥' if crit else ''}")
            winner,loser=(message.author,opp) if p1_hp>0 else (opp,message.author)
            acoin(gid,winner.id,50); axp(gid,winner.id,25)
            await message.channel.send(embed=discord.Embed(title="⚔️ PvP Kova",description="\n".join(log[-6:])+f"\n\n🏆 **{winner.display_name}** laimi! +50 🪙 +25 XP",color=discord.Color.gold()))
        else:
            monster_name=random.choice(list(MONSTERS)); m=MONSTERS[monster_name]
            p_hp=100; m_hp=m["hp"]; log=[]
            while p_hp>0 and m_hp>0:
                pdmg=random.randint(10,25); m_hp-=pdmg; log.append(f"⚔️ Tu: **{pdmg}**")
                if m_hp<=0: break
                mdmg=random.randint(m["atk"]-3,m["atk"]+3); p_hp-=mdmg; log.append(f"{m['emoji']} {monster_name}: **{mdmg}**")
            if p_hp>0:
                rw=random.randint(*m["reward"]); acoin(gid,uid,rw); axp(gid,uid,20)
                result=f"🎉 **Laimėjai!** +{rw} 🪙 +20 XP"; color=discord.Color.green()
            else:
                result="💀 **Pralaimėjai!**"; color=discord.Color.red()
            await message.channel.send(embed=discord.Embed(title=f"⚔️ Kova su {m['emoji']} {monster_name}",description="\n".join(log[-6:])+f"\n\n{result}",color=color))
        return

    if content=="!adventure":
        sc=random.choice(ADVENTURE_SCENARIOS)
        active_adventures[uid]={"scenario":sc,"time":time.time()}
        e=discord.Embed(title=f"🗺️ {sc['title']}",description=sc["desc"],color=discord.Color.blue())
        for i,ch_c in enumerate(sc["choices"],1):
            e.add_field(name=f"{i}. {ch_c['text']}",value="​",inline=False)
        e.set_footer(text="Rašyk skaičių")
        await message.channel.send(embed=e)
        return

    # ── HOROSKOPAS ────────────────────────────────────────────────────────────

    if content.startswith("!horoscope"):
        sign=content.split(" ",1)[1].lower() if " " in content else None
        if not sign or sign not in ZODIAC:
            signs=" | ".join([f"{v['emoji']} {k}" for k,v in ZODIAC.items()])
            await message.reply(f"Naudok: `!horoscope [ženklas]`\nŽenklai: {signs}"); return
        z=ZODIAC[sign]; today_seed=int(time.time()//86400)+hash(sign)
        random.seed(today_seed)
        luck=random.randint(1,5); love=random.randint(1,5); work=random.randint(1,5)
        pred=random.choice(["Šiandien laukia netikėti susitikimai!","Puiki diena finansams!","Meilė ore!","Darykite tai, ko ilgai vengėte.","Klausykite intuityvaus."])
        random.seed()
        stars=lambda n: "⭐"*n+"☆"*(5-n)
        await message.channel.send(embed=embed_horoscope(sign,z,luck,love,work,pred))
        return

    # ── GIMTADIENIAI ──────────────────────────────────────────────────────────

    if content.startswith("!birthday set"):
        date_str=content[14:].strip()
        try:
            month,day=map(int,date_str.split("-"))
            if not (1<=month<=12 and 1<=day<=31): raise ValueError()
        except:
            await message.reply("Naudok: `!birthday set MM-DD` (pvz: `!birthday set 05-15`)"); return
        D["birthdays"].setdefault(str(gid),{})[str(uid)]=f"{month:02d}-{day:02d}"; save_data(D)
        await message.reply(f"🎂 Gimtadienis nustatytas: **{month:02d}-{day:02d}**!")
        return

    if content in ("!birthday","!birthdays"):
        bdays=D["birthdays"].get(str(gid),{})
        if not bdays: await message.reply("Niekas nenusistatė gimtadienio! `!birthday set MM-DD`"); return
        today=datetime.datetime.now().strftime("%m-%d")
        e=discord.Embed(title="🎂 Gimtadieniai",color=discord.Color.pink())
        for uid_s,bday in sorted(bdays.items(),key=lambda x:x[1]):
            m=message.guild.get_member(int(uid_s))
            if m:
                today_mark="🎉 **ŠIANDIEN!**" if bday==today else ""
                e.add_field(name=f"📅 {bday}",value=f"**{m.display_name}** {today_mark}",inline=True)
        await message.channel.send(embed=e)
        return

    # ── GIVEAWAY ─────────────────────────────────────────────────────────────

    if content.startswith("!giveaway"):
        if not message.guild or not message.author.guild_permissions.administrator: await message.reply("Reikalingos teisės 🚫"); return
        parts=content.split()
        if len(parts)<3: await message.reply("Naudok: `!giveaway [minutės] [prizas_monetomis]`"); return
        try: minutes=int(parts[1]); prize=int(parts[2])
        except: await message.reply("Neteisingas formatas!"); return
        ga_id=str(int(time.time()))
        D["giveaways"].setdefault(str(gid),{})[ga_id]={"channel_id":str(ch_id),"end_time":time.time()+minutes*60,"prize":prize,"participants":[],"ended":False}
        save_data(D)
        e=discord.Embed(title="🎉 GIVEAWAY!",description=f"**Prizas:** {prize} 🪙\n**Trukmė:** {minutes} min.\n\nSpausk mygtuką dalyvauti!",color=discord.Color.gold())
        e.set_footer(text=f"Baigsis: {datetime.datetime.now()+datetime.timedelta(minutes=minutes):%H:%M}")
        await message.channel.send(embed=e,view=GiveawayView(ga_id,str(gid)))
        return

    # ── PASIŪLYMAI / PRISIPAŽINIMAI ───────────────────────────────────────────

    if content.startswith("!suggest"):
        suggestion=content[8:].strip()
        if not suggestion: await message.reply("Naudok: `!suggest [tavo pasiūlymas]`"); return
        e=discord.Embed(title="💡 Naujas pasiūlymas",description=suggestion,color=discord.Color.blue())
        e.set_author(name=message.author.display_name,icon_url=message.author.display_avatar.url)
        e.set_footer(text="Balsuok: 👍 arba 👎")
        msg=await message.channel.send(embed=e)
        await msg.add_reaction("👍"); await msg.add_reaction("👎")
        try: await message.delete()
        except: pass
        return

    if content.startswith("!confess"):
        confession=content[8:].strip()
        if not confession: await message.reply("Naudok: `!confess [tekstas]` (anonimiškai)"); return
        try: await message.delete()
        except: pass
        D["confessions"].setdefault(str(gid),{"count":0})["count"]+=1
        num=D["confessions"][str(gid)]["count"]; save_data(D)
        e=discord.Embed(title=f"🤫 Prisipažinimas #{num}",description=confession,color=discord.Color.dark_purple())
        e.set_footer(text="Anoniminis prisipažinimas")
        await message.channel.send(embed=e)
        return

    # ── RANGAS / STATISTIKA ───────────────────────────────────────────────────

    if content.startswith("!rank"):
        target=message.mentions[0] if message.mentions else message.author
        xp=gxp(gid,target.id); lvl=xp//LEVEL_XP; cur=xp%LEVEL_XP
        lb=xp_lb(gid,999); pos=next((i+1 for i,(u,_) in enumerate(lb) if u==str(target.id)),"?")
        bar="█"*int(cur/LEVEL_XP*10)+"░"*(10-int(cur/LEVEL_XP*10))
        e=discord.Embed(title=f"🏆 {target.display_name}",color=discord.Color.gold())
        e.add_field(name="Lygis",value=f"**{lvl}**",inline=True)
        e.add_field(name="XP",value=f"**{xp}**",inline=True)
        e.add_field(name="Serverio vieta",value=f"**#{pos}**",inline=True)
        e.add_field(name="Monetos",value=f"**{gcoin(gid,target.id)}** 🪙",inline=True)
        e.add_field(name="Reputacija",value=f"**{greg(gid,target.id)}** ⭐",inline=True)
        e.add_field(name="Perspėjimai",value=f"**{len(gwarn(gid,target.id))}/{WARN_KICK}**",inline=True)
        e.add_field(name="Progresas",value=f"`{bar}` {cur}/{LEVEL_XP}",inline=False)
        e.set_thumbnail(url=target.display_avatar.url)
        e.set_footer(text=ft())
        await message.channel.send(embed=e)
        return

    if content in ("!leaderboard","!lb"):
        lb=xp_lb(gid)
        if not lb: await message.reply("Dar niekas neturi XP!"); return
        entries=[(message.guild.get_member(int(u)).display_name if message.guild.get_member(int(u)) else "Nežinomas",x,x//LEVEL_XP) for u,x in lb]
        e=embed_leaderboard_xp(entries,message.guild.name)
        await message.channel.send(embed=e)
        return

    if content=="!stats":
        top=sorted(msg_stats.items(),key=lambda x:x[1],reverse=True)[:5]
        e=discord.Embed(title="📊 Sesijos aktyvumas",color=discord.Color.blue())
        medals=["🥇","🥈","🥉","4️⃣","5️⃣"]
        for i,(u,c) in enumerate(top):
            m=message.guild.get_member(u)
            e.add_field(name=f"{medals[i]} {m.display_name if m else 'Nežinomas'}",value=f"{c} žinučių",inline=False)
        e.set_footer(text=ts(f"Viso: {sum(msg_stats.values())} žinučių"))
        await message.channel.send(embed=e)
        return

    if content=="!achievements":
        user_achs=D["achieved"].get(f"{gid}:{uid}",[])
        e=discord.Embed(title=f"🏆 {message.author.display_name} — Pasiekimai",color=discord.Color.gold())
        for ach_id,ach in ACHIEVEMENTS.items():
            status="✅" if ach_id in user_achs else "❌"
            e.add_field(name=f"{status} {ach['emoji']} {ach['name']}",value=f"{ach['desc']} • +{ach['reward']} 🪙",inline=False)
        await message.channel.send(embed=e)
        return

    # ── UTILITY ───────────────────────────────────────────────────────────────

    if content.startswith("!userinfo"):
        target=message.mentions[0] if message.mentions else message.author
        member=message.guild.get_member(target.id) or target
        joined=member.joined_at.strftime("%Y-%m-%d") if hasattr(member,"joined_at") and member.joined_at else "?"
        roles=[r.mention for r in getattr(member,"roles",[]) if r.name!="@everyone"]
        e=discord.Embed(title=f"👤 {target.display_name}",color=discord.Color.blurple())
        e.add_field(name="Paskyra sukurta",value=target.created_at.strftime("%Y-%m-%d"),inline=True)
        e.add_field(name="Prisijungė",value=joined,inline=True)
        e.add_field(name="ID",value=str(target.id),inline=True)
        e.add_field(name="Monetos",value=f"{gcoin(gid,target.id)} 🪙",inline=True)
        e.add_field(name="XP/Lygis",value=f"{gxp(gid,target.id)} / {gxp(gid,target.id)//LEVEL_XP}",inline=True)
        if roles: e.add_field(name=f"Vaidmenys ({len(roles)})",value=" ".join(roles[:10]),inline=False)
        e.set_thumbnail(url=target.display_avatar.url)
        await message.channel.send(embed=e)
        return

    if content=="!serverinfo":
        g=message.guild
        e=discord.Embed(title=f"🏠 {g.name}",color=discord.Color.blurple())
        e.add_field(name="Sukurtas",value=g.created_at.strftime("%Y-%m-%d"),inline=True)
        e.add_field(name="Nariai",value=f"{g.member_count-sum(1 for m in g.members if m.bot)} žm., {sum(1 for m in g.members if m.bot)} botai",inline=True)
        e.add_field(name="Kanalai",value=f"{len(g.text_channels)} teksto, {len(g.voice_channels)} balso",inline=True)
        e.add_field(name="Vaidmenys",value=str(len(g.roles)),inline=True)
        if g.icon: e.set_thumbnail(url=g.icon.url)
        e.set_footer(text=ts(f"ID: {g.id}"))
        await message.channel.send(embed=e)
        return

    if content.startswith("!poll"):
        rest=content[5:].strip()
        if not rest: await message.reply("Naudok: `!poll [klausimas] | [opt1] | [opt2]`"); return
        parts=[p.strip() for p in rest.split("|")]
        question=parts[0]; options=parts[1:] if len(parts)>1 else None
        emoji_nums=["1️⃣","2️⃣","3️⃣","4️⃣","5️⃣","6️⃣","7️⃣","8️⃣","9️⃣","🔟"]
        e=discord.Embed(title=f"📊 {question}",color=discord.Color.blue())
        if options: e.description="\n".join(f"{emoji_nums[i]} {opt}" for i,opt in enumerate(options))
        e.set_footer(text=ts(message.author.display_name))
        poll_msg=await message.channel.send(embed=e)
        if options:
            for i in range(len(options)): await poll_msg.add_reaction(emoji_nums[i])
        else:
            await poll_msg.add_reaction("✅"); await poll_msg.add_reaction("❌")
        try: await message.delete()
        except: pass
        return

    if content.startswith("!remindme"):
        match=re.match(r"!remindme\s+(\d+)([mh])\s+(.+)",content)
        if not match: await message.reply("Naudok: `!remindme 10m Paskambinti`"); return
        n,unit,text=int(match.group(1)),match.group(2).lower(),match.group(3)
        secs=n*60 if unit=="m" else n*3600
        pending_reminders.append((time.time()+secs,ch_id,message.author.mention,text))
        await message.reply(embed=discord.Embed(description=f"✅ Priminsiu po **{n}{'min' if unit=='m' else 'val'}**: {text}",color=discord.Color.green()))
        return

    if content.startswith("!afk"):
        reason=content[4:].strip() or "AFK"
        D["afk_users"][str(uid)]={"reason":reason,"time":time.time()}; save_data(D)
        await message.reply(f"💤 Tu dabar AFK: *{reason}*")
        return

    if content=="!embed":
        active_embed[uid]={"step":"title"}
        await message.reply(embed=discord.Embed(title="🎨 Embed kūrimas",description="Pirmiausia įrašyk **pavadinimą** (title):",color=discord.Color.blurple()))
        return

    if content.startswith("!anon"):
        text=content[5:].strip()
        if not text: await message.reply("Naudok: `!anon [žinutė]`"); return
        try: await message.delete()
        except: pass
        e=discord.Embed(description=f"*{text}*",color=discord.Color.dark_grey())
        e.set_author(name="Anonimai 🎭")
        await message.channel.send(embed=e)
        return

    # ── AI ────────────────────────────────────────────────────────────────────

    if content.startswith("!translate"):
        rest=content[10:].strip(); parts=rest.split(" ",1)
        if len(parts)<2: await message.reply("Naudok: `!translate [kalba] [tekstas]`"); return
        lang,text=parts
        async with message.channel.typing():
            translated=await ai_chat("Tu esi vertėjas. Grąžink TIK išverstą tekstą.",f"Išversk į {lang}:\n\n{text}")
            e=discord.Embed(color=discord.Color.blue())
            e.add_field(name="Originalas",value=text[:1020],inline=False)
            e.add_field(name=f"Vertimas ({lang})",value=translated[:1020],inline=False)
            await message.channel.send(embed=e)
        return

    if content.startswith("!ask"):
        question=content[4:].strip()
        if not question: await message.reply("Naudok: `!ask [klausimas]`"); return
        async with message.channel.typing():
            answer=await ai_chat("Tu esi protingas asistentas. Atsakyk trumpai ir aiškiai lietuviškai.",question)
            e=discord.Embed(title="🤖 Atsakymas",description=answer,color=discord.Color.blue())
            await message.channel.send(embed=e)
        return

    if content=="!forget":
        conv_history[uid].clear()
        await message.reply(embed=discord.Embed(description="🧹 Atmintis išvalyta. Kas tu apskritai? 🤔",color=discord.Color.blurple()))
        return

    # ── SMAGU ─────────────────────────────────────────────────────────────────

    if content=="!moneta": await message.reply(random.choice(["Herbas! 🪙","Skaičius! 🪙"])); return
    if content.startswith("!8ball"): await message.reply(random.choice(EIGHT_BALL)); return
    if content.startswith("!roast"):
        target=message.mentions[0].display_name if message.mentions else message.author.display_name
        await message.reply(f"**{target}**, {random.choice(['Tu durnas ar tik apsimeti? 😄','Eik miegot 😴','Net botas supranta daugiau 😂'])}"); return
    if content=="!joke": await message.reply(random.choice(JOKES)); return
    if content=="!fact": await message.reply(random.choice(FACTS)); return
    if content=="!quote": await message.reply(random.choice(QUOTES)); return
    if content=="!mood":
        mood=get_mood()
        descs={"linksmas":"Šiandien esu SUPER linksmas! 😄","normalus":"Esu normalus. Tiesiog egzistuoju. 😐","tingus":"Nenorisi net rašyti... 😴","piktas":"Viską hate. 😤"}
        await message.reply(embed=discord.Embed(description=f"Nuotaika: **{mood}** {MOODS[mood][0]}\n{descs[mood]}",color=discord.Color.blurple()))
        return

    if content.startswith("!ship"):
        if len(message.mentions)<2: await message.reply("Naudok: `!ship @vardas1 @vardas2`"); return
        u1,u2=message.mentions[0],message.mentions[1]
        random.seed(min(u1.id,u2.id)*max(u1.id,u2.id)); compat=random.randint(0,100); random.seed()
        if compat<20: comment="Oi... gal geriau ne 😬"
        elif compat<50: comment="Galėtų būti geriau 🤔"
        elif compat<80: comment="Gera pora! 💕"
        else: comment="TOBULA PORA! 💖💖💖"
        e=discord.Embed(title="💘 Meilės skaičiuoklė",description=f"**{u1.display_name}** ❤️ **{u2.display_name}**",color=discord.Color.red())
        e.add_field(name="Suderinamumas",value=f"**{compat}%**",inline=True)
        e.add_field(name="Verdiktas",value=comment,inline=True)
        await message.channel.send(embed=e)
        return


    # !referral - referral sistema
    if content.startswith("!referral"):
        code = get_referral_code(uid)
        e = discord.Embed(title="🤝 Tavo Referral Kodas", color=C.GOLD)
        e.description = (
            f"Pakvieskite draugą ir **abu** gausite **+{REFERRAL_BONUS}** 🪙!\n\n"
            f"Tavo kodas: `{code}`\n\n"
            f"Draugas turi rašyti: `!usecode {code}`"
        )
        await message.channel.send(embed=e)
        return

    if content.startswith("!usecode"):
        code = content[8:].strip().upper()
        if not code: await message.reply("Naudok: `!usecode [kodas]`"); return
        # Rasti referrer pagal kodą
        referrer = None
        for m in message.guild.members:
            if get_referral_code(m.id) == code and m.id != uid:
                referrer = m; break
        if not referrer:
            await message.reply("❌ Referral kodas nerastas!"); return
        if process_referral(gid, referrer.id, uid):
            await message.channel.send(embed=embed_referral(referrer, message.author, REFERRAL_BONUS))
        else:
            await message.reply("Tu jau naudojai referral kodą!")
        return

    # !vip - VIP informacija
    if content == "!vip":
        if is_vip(gid, uid):
            await message.channel.send(embed=embed_vip(message.author, VIP_PERKS))
        else:
            e = discord.Embed(title="💎 VIP Sistema", color=C.GOLD)
            e.description = "Tu nesi VIP narys. Susisiek su administracija dėl VIP statuso!"
            for p in VIP_PERKS:
                e.add_field(name=p["name"], value=p["desc"], inline=True)
            await message.channel.send(embed=e)
        return

    # !setvip - nustatyti VIP rolę (admin)
    if content.startswith("!setvip"):
        if not message.guild or not message.author.guild_permissions.administrator:
            await message.reply("Reikalingos teisės 🚫"); return
        if not message.role_mentions:
            await message.reply("Naudok: `!setvip @rolė`"); return
        D.setdefault("vip_roles", {})[str(gid)] = message.role_mentions[0].id
        save_data(D)
        await message.reply(f"✅ VIP rolė: {message.role_mentions[0].mention}")
        return

    # !rate - įvertinti ticket
    if content.startswith("!rate"):
        rating_str = content[5:].strip()
        if not rating_str.isdigit() or not 1 <= int(rating_str) <= 5:
            await message.reply("Naudok: `!rate [1-5]`"); return
        rating = int(rating_str)
        tid = str(ch_id); gid_s = str(gid)
        ticket = D["tickets"].get(gid_s, {}).get(tid)
        if not ticket:
            await message.reply("Šis kanalas nėra ticket!"); return
        ticket["rating"] = rating; save_data(D)
        ticket_num = int(tid) % 10000 if tid.isdigit() else 0
        await message.channel.send(embed=embed_ticket_rating(message.author, ticket_num, rating))
        return

    # !addnote - pridėti pastabą į ticket
    if content.startswith("!addnote"):
        note = content[8:].strip()
        if not note: await message.reply("Naudok: `!addnote [tekstas]`"); return
        tid = str(ch_id); gid_s = str(gid)
        ticket = D["tickets"].get(gid_s, {}).get(tid)
        if not ticket: await message.reply("Šis kanalas nėra ticket!"); return
        e = discord.Embed(
            title="📌 Pastaba pridėta",
            description=note,
            color=C.INFO
        )
        e.set_author(name=message.author.display_name, icon_url=message.author.display_avatar.url)
        e.set_footer(text=ft(f"Pastaba nuo {message.author.display_name}"))
        await message.channel.send(embed=e)
        return

    # !ticketstats - ticket statistika
    if content == "!ticketstats":
        if not message.guild or not message.author.guild_permissions.manage_channels:
            await message.reply("Reikalingos teisės 🚫"); return
        gid_s = str(gid)
        all_t = D["tickets"].get(gid_s, {})
        open_t = [t for t in all_t.values() if t.get("status") == "open"]
        closed_t = [t for t in all_t.values() if t.get("status") == "closed"]
        avg_min = 0
        if closed_t:
            durations = [(t.get("closed_at",0) - t.get("created_at",0))/60 for t in closed_t if t.get("closed_at")]
            avg_min = sum(durations) / len(durations) if durations else 0
        stats = {"total": len(all_t), "open": len(open_t), "closed": len(closed_t), "avg_minutes": avg_min}
        await message.channel.send(embed=embed_ticket_stats(stats, message.guild.name))
        return

    # !webhook - nustatyti webhook kanalą (admin)
    if content.startswith("!setwebhook"):
        if not message.guild or not message.author.guild_permissions.administrator:
            await message.reply("Reikalingos teisės 🚫"); return
        if not message.channel_mentions:
            await message.reply("Naudok: `!setwebhook #kanalas`"); return
        D.setdefault("webhook_channels", {})[str(gid)] = message.channel_mentions[0].id
        save_data(D)
        await message.reply(f"✅ Webhook kanalas: {message.channel_mentions[0].mention}")
        return



    # !shoppanel - parduotuvė su mygtukais (admin)
    if content == "!shoppanel":
        if not message.guild or not message.author.guild_permissions.administrator:
            await message.reply("Reikalingos administratoriaus teisės 🚫"); return
        prods = get_products(gid)
        settings = get_settings(str(gid)) if USE_DB else {}
        payment_methods = settings.get("payment_methods", D["payment_methods"].get(str(gid), {}))
        if not payment_methods:
            payment_methods = D["payment_methods"].get(str(gid), {})
        shop_embed = build_shop_embed(message.guild.name, prods, payment_methods)
        shop_view = ShopPanelView(prods, payment_methods, bot)
        await message.channel.send(embed=shop_embed, view=shop_view)
        try: await message.delete()
        except: pass
        return

    # !poker - pradėti pokerio žaidimą
    if content.startswith("!poker"):
        if not message.guild:
            await message.reply("Tik serveryje!"); return
        parts = content.split()
        if len(parts) < 2 or not parts[1].isdigit():
            await message.reply("Naudok: `!poker [statymas]`"); return
        bet = int(parts[1])
        if bet < 50: await message.reply("Minimalus statymas: 50 🪙"); return
        if gcoin(gid, uid) < bet:
            await message.reply(f"Neturi tiek! Likutis: **{gcoin(gid, uid)}** 🪙"); return
        # Surinkti žaidėjus (kas reaguos per 30 sek)
        poker_desc = (
            f"**{message.author.display_name}** kviečia žaisti pokerį!\n\n"
            f"**Statymas:** {bet:,} 🪙\n"
            f"Norintys dalyvauti — reaguokite ✅ per 30 sekundžių!\n"
            f"*(Reikia 2-6 žaidėjų)*"
        )
        e = discord.Embed(title="🃏 ═══ POKERIS ═══ 🃏", description=poker_desc, color=C.CASINO)
        invite_msg = await message.channel.send(embed=e)
        await invite_msg.add_reaction("✅")
        await asyncio.sleep(30)
        invite_msg = await message.channel.fetch_message(invite_msg.id)
        reaction = discord.utils.get(invite_msg.reactions, emoji="✅")
        players = []
        if reaction:
            async for user in reaction.users():
                if not user.bot and gcoin(gid, user.id) >= bet:
                    players.append((user.id, user.display_name))
                    acoin(gid, user.id, -bet)
        if len(players) < 2:
            # Grąžinti monetas
            for pid, _ in players:
                acoin(gid, pid, bet)
            await message.channel.send("❌ Nepakanka žaidėjų! Monetos grąžintos.")
            return
        game = PokerGame(players, bet)
        e = discord.Embed(title="🃏 ═══ POKERIS PRASIDEDA! ═══ 🃏", color=C.CASINO)
        e.description = f"**Žaidėjai:** {player_names}\n**Puodas:** {game.pot:,} 🪙"
        e.add_field(name="🎴 Bendros kortelės", value="*Bus atidengtos vėliau...*", inline=False)
        e.add_field(name="📋 Fazė", value="**PREFLOP**", inline=True)
        cp = game.current_player()
        if cp: e.add_field(name="⏳ Eilė", value=f"**{cp[1]}**", inline=True)
        view = PokerView(game, ch_id)
        await message.channel.send(embed=e, view=view)
        return

    # !tournament - sukurti turnyrą (admin)
    if content.startswith("!tournament create"):
        if not message.guild or not message.author.guild_permissions.administrator:
            await message.reply("Reikalingos teisės 🚫"); return
        parts = content.split("|")
        if len(parts) < 3:
            await message.reply("Naudok: `!tournament create [pavadinimas] | [žaidimas] | [prizas]`\nPvz: `!tournament create Šachmatų turnyras | ttt | 5000`"); return
        name = parts[0].replace("!tournament create","").strip()
        game_type = parts[1].strip()
        try: prize = int(parts[2].strip())
        except: await message.reply("Prizas turi būti skaičius!"); return
        if USE_DB:
            tid = create_tournament(gid, name, game_type, prize)
        else:
            import random as _r; tid = _r.randint(1000,9999)
            import random as _r; tid = _r.randint(1000,9999)
        e = discord.Embed(title=f"Turnyras: {name}", color=C.GOLD)
        e.description = f"Žaidimas: {game_type.upper()}\nPrizas: {prize:,} monetu"
        e.set_footer(text=ft(f"ID: {tid}"))
        await message.channel.send(embed=e, view=TournamentView(tid, game_type))
        return





    if content.startswith("!tournament start"):
        if not message.guild or not message.author.guild_permissions.administrator:
            await message.reply("Reikalingos teisės 🚫"); return
        parts = content.split()
        if len(parts) < 3 or not parts[2].isdigit():
            await message.reply("Naudok: `!tournament start [ID]`"); return
        tid = int(parts[2])
        if USE_DB:
            t = get_tournament(tid)
            if not t: await message.reply("Turnyras nerastas!"); return
            if len(t["participants"]) < 2: await message.reply("Reikia bent 2 dalyvių!"); return
            bracket = start_tournament(tid)
            e = discord.Embed(title=f"🏆 {t['name']} — PRADĖTAS!", color=C.GOLD)
            e.description = f"Dalyviai: {len(t['participants'])}\nPrizas: {t['prize']:,} monetu"
            await message.channel.send(embed=e)
        else:
            await message.reply("Turnyrų sistema reikalauja database.py!")
        return

    # !deposit - įnešti į banką
    if content.startswith("!deposit"):
        if not message.guild: return
        parts = content.split()
        if len(parts) < 2 or not parts[1].isdigit():
            await message.reply("Naudok: `!deposit [suma]`"); return
        amount = int(parts[1])
        if USE_DB:
            ok, result = deposit(gid, uid, amount)
            if ok:
                await message.reply(embed=discord.Embed(description=f"🏦 Įnešei **{amount:,}** 🪙 į banką! Banko likutis: **{result:,}** 🪙", color=C.SUCCESS))
            else:
                await message.reply(f"❌ {result}")
        else:
            if gcoin(gid, uid) < amount: await message.reply("Neturi tiek monetų!"); return
            acoin(gid, uid, -amount)
            D.setdefault("bank", {}).setdefault(str(gid), {})[str(uid)] = D["bank"][str(gid)].get(str(uid), 0) + amount
            save_data(D)
            bank_bal = D["bank"][str(gid)][str(uid)]
            await message.reply(embed=discord.Embed(description=f"🏦 Įnešei **{amount:,}** 🪙 į banką! Banko likutis: **{bank_bal:,}** 🪙", color=C.SUCCESS))
        return

    # !withdraw - išimti iš banko
    if content.startswith("!withdraw"):
        if not message.guild: return
        parts = content.split()
        if len(parts) < 2 or not parts[1].isdigit():
            await message.reply("Naudok: `!withdraw [suma]`"); return
        amount = int(parts[1])
        if USE_DB:
            ok, result = withdraw(gid, uid, amount)
            if ok:
                await message.reply(embed=discord.Embed(description=f"💸 Išėmei **{amount:,}** 🪙 iš banko! Piniginė: **{gcoin(gid,uid):,}** 🪙", color=C.SUCCESS))
            else:
                await message.reply(f"❌ {result}")
        else:
            bank_bal = D.get("bank", {}).get(str(gid), {}).get(str(uid), 0)
            if bank_bal < amount: await message.reply("Banke neturi tiek!"); return
            D["bank"][str(gid)][str(uid)] -= amount; save_data(D)
            acoin(gid, uid, amount)
            await message.reply(embed=discord.Embed(description=f"💸 Išėmei **{amount:,}** 🪙 iš banko!", color=C.SUCCESS))
        return

    # !bank - banko informacija
    if content == "!bank":
        if not message.guild: return
        if USE_DB:
            m = get_member(gid, uid)
            bank_bal = m.get("bank_balance", 0)
            loan = m.get("loan_amount", 0)
        else:
            bank_bal = D.get("bank", {}).get(str(gid), {}).get(str(uid), 0)
            loan = 0
        e = discord.Embed(title="🏦 Tavo Bankas", color=C.GOLD)
        e.add_field(name="💵 Piniginė",   value=f"**{gcoin(gid,uid):,}** 🪙", inline=True)
        e.add_field(name="🏦 Banke",      value=f"**{bank_bal:,}** 🪙",        inline=True)
        e.add_field(name="💳 Paskola",    value=f"**{loan:,}** 🪙",             inline=True)
        e.add_field(name="Palukanos", value="2% per diena", inline=True)
        e.add_field(name="Komandos", value="!deposit !withdraw !loan !repay", inline=False)
        e.set_footer(text=ft())
        await message.channel.send(embed=e)
        return



        await message.channel.send(embed=e)
        return

    # !loan - paskola
    if content.startswith("!loan"):
        if not message.guild: return
        parts = content.split()
        if len(parts) < 2 or not parts[1].isdigit():
            await message.reply("Naudok: `!loan [suma]` (maks. 10,000 🪙)"); return
        amount = int(parts[1])
        if USE_DB:
            ok, result = take_loan(gid, uid, amount)
            if ok:
                await message.reply(embed=discord.Embed(description=f"💳 Gavai paskolą **{result:,}** 🪙! Grąžink per 7 dienas su 10% palūkanomis (`!repay`)", color=C.WARNING))
            else:
                await message.reply(f"❌ {result}")
        else:
            await message.reply("Paskolų sistema reikalauja database.py!")
        return

    # !repay - grąžinti paskolą
    if content == "!repay":
        if not message.guild: return
        if USE_DB:
            ok, result = repay_loan(gid, uid)
            if ok:
                await message.reply(embed=discord.Embed(description=f"✅ Paskola grąžinta! Sumokėta: **{result:,}** 🪙", color=C.SUCCESS))
            else:
                await message.reply(f"❌ {result}")
        else:
            await message.reply("Paskolų sistema reikalauja database.py!")
        return



    # ── REACTION ROLES ────────────────────────────────────────────────────────

    # !rrpanel - sukurti reaction roles panelį (admin)
    if content.startswith("!rrpanel"):
        if not message.guild or not message.author.guild_permissions.administrator:
            await message.reply("Reikalingos teisės 🚫"); return
        gid_s = str(gid)
        rr_config = RR_DATA.get(gid_s, {})
        if not rr_config.get("roles"):
            await message.reply(
                "Nėra reaction rolių! Pridėk su:\n"
                "`!rradd @rolė [emoji] [aprašymas]`"
            ); return
        title = rr_config.get("title", "Pasirink Rolę")
        desc  = rr_config.get("description", "Spausk mygtuką gauti rolę!")
        roles_data = rr_config["roles"]
        e = build_rr_embed(title, desc, roles_data, message.guild)
        view = ReactionRoleView(roles_data)
        await message.channel.send(embed=e, view=view)
        try: await message.delete()
        except: pass
        return

    # !rradd - pridėti reaction role (admin)
    if content.startswith("!rradd"):
        if not message.guild or not message.author.guild_permissions.administrator:
            await message.reply("Reikalingos teisės 🚫"); return
        if not message.role_mentions:
            await message.reply("Naudok: `!rradd @rolė [emoji] [aprašymas]`"); return
        role = message.role_mentions[0]
        parts = content.split()
        emoji = parts[2] if len(parts) > 2 and not parts[2].startswith("<@") else None
        desc_text = " ".join(parts[3:]) if len(parts) > 3 else ""
        gid_s = str(gid)
        if gid_s not in RR_DATA: RR_DATA[gid_s] = {"roles": [], "title": "Pasirink Role", "description": "Gauk roles!"}
        RR_DATA[gid_s]["roles"].append({"role_id": role.id, "label": role.name, "emoji": emoji, "desc": desc_text})
        save_rr(RR_DATA)
        await message.reply(embed=discord.Embed(description=f"✅ Reaction role pridėta: **{role.name}**", color=C.SUCCESS))
        return

    # !rrclear - išvalyti reaction roles (admin)
    if content == "!rrclear":
        if not message.guild or not message.author.guild_permissions.administrator:
            await message.reply("Reikalingos teisės 🚫"); return
        RR_DATA[str(gid)] = {"roles": [], "title": "Pasirink Role", "description": "Gauk roles!"}
        save_rr(RR_DATA)
        await message.reply("✅ Reaction roles išvalytos.")
        return

    # !rrtitle - pakeisti pavadinimą (admin)
    if content.startswith("!rrtitle"):
        if not message.guild or not message.author.guild_permissions.administrator:
            await message.reply("Reikalingos teisės 🚫"); return
        title_text = content[8:].strip()
        if not title_text: await message.reply("Naudok: `!rrtitle [pavadinimas]`"); return
        RR_DATA.setdefault(str(gid), {})["title"] = title_text
        save_rr(RR_DATA)
        await message.reply(f"✅ Pavadinimas: **{title_text}**")
        return

    # ── TWITCH / YOUTUBE NUSTATYMAI ───────────────────────────────────────────

    # !settwitch - nustatyti Twitch kanalą (admin)
    if content.startswith("!settwitch"):
        if not message.guild or not message.author.guild_permissions.administrator:
            await message.reply("Reikalingos teisės 🚫"); return
        if not message.channel_mentions:
            await message.reply("Naudok: `!settwitch #kanalas`"); return
        upd_int_settings(gid, twitch_channel=message.channel_mentions[0].id)
        await message.reply(f"✅ Twitch notifikacijos: {message.channel_mentions[0].mention}")
        return

    # !addtwitch - pridėti streameris (admin)
    if content.startswith("!addtwitch"):
        if not message.guild or not message.author.guild_permissions.administrator:
            await message.reply("Reikalingos teisės 🚫"); return
        streamer = content[10:].strip().lower()
        if not streamer: await message.reply("Naudok: `!addtwitch [streamerio_vardas]`"); return
        s = get_int_settings(gid)
        streamers = s.get("twitch_streamers", [])
        if streamer not in streamers:
            streamers.append(streamer)
            upd_int_settings(gid, twitch_streamers=streamers)
        await message.reply(embed=discord.Embed(description=f"✅ Twitch streameris pridėtas: **{streamer}**", color=C.SUCCESS))
        return

    # !removetwitch - pašalinti streameris (admin)
    if content.startswith("!removetwitch"):
        if not message.guild or not message.author.guild_permissions.administrator:
            await message.reply("Reikalingos teisės 🚫"); return
        streamer = content[13:].strip().lower()
        s = get_int_settings(gid)
        streamers = s.get("twitch_streamers", [])
        if streamer in streamers:
            streamers.remove(streamer)
            upd_int_settings(gid, twitch_streamers=streamers)
            await message.reply(f"✅ **{streamer}** pašalintas.")
        else:
            await message.reply("Streameris nerastas!")
        return

    # !setyoutube - YouTube notifikacijų kanalas (admin)
    if content.startswith("!setyoutube"):
        if not message.guild or not message.author.guild_permissions.administrator:
            await message.reply("Reikalingos teisės 🚫"); return
        if not message.channel_mentions:
            await message.reply("Naudok: `!setyoutube #kanalas`"); return
        upd_int_settings(gid, youtube_channel=message.channel_mentions[0].id)
        await message.reply(f"✅ YouTube notifikacijos: {message.channel_mentions[0].mention}")
        return

    # !addyoutube - pridėti YouTube kanalą (admin)
    if content.startswith("!addyoutube"):
        if not message.guild or not message.author.guild_permissions.administrator:
            await message.reply("Reikalingos teisės 🚫"); return
        yt_id = content[11:].strip()
        if not yt_id: await message.reply("Naudok: `!addyoutube [YouTube_kanalo_ID]`"); return
        s = get_int_settings(gid)
        channels = s.get("youtube_channels", [])
        if yt_id not in channels:
            channels.append(yt_id)
            upd_int_settings(gid, youtube_channels=channels)
        await message.reply(embed=discord.Embed(description=f"✅ YouTube kanalas pridėtas: `{yt_id}`", color=C.SUCCESS))
        return

    # !setboostch - boost notifikacijų kanalas (admin)
    if content.startswith("!setboostch"):
        if not message.guild or not message.author.guild_permissions.administrator:
            await message.reply("Reikalingos teisės 🚫"); return
        if not message.channel_mentions:
            await message.reply("Naudok: `!setboostch #kanalas`"); return
        upd_int_settings(gid, boost_channel=message.channel_mentions[0].id)
        await message.reply(f"✅ Boost notifikacijos: {message.channel_mentions[0].mention}")
        return

    # !settwichrole - Twitch ping rolė (admin)
    if content.startswith("!settwitchrole"):
        if not message.guild or not message.author.guild_permissions.administrator:
            await message.reply("Reikalingos teisės 🚫"); return
        if not message.role_mentions:
            await message.reply("Naudok: `!settwitchrole @rolė`"); return
        upd_int_settings(gid, twitch_role=message.role_mentions[0].id)
        await message.reply(f"✅ Twitch ping rolė: {message.role_mentions[0].mention}")
        return

    # !integrations - rodyti integracijas
    if content == "!integrations":
        if not message.guild: return
        s = get_int_settings(gid)
        e = discord.Embed(title="🔗 Integracijos", color=C.GOLD)
        e.add_field(name="📺 Twitch kanalas",  value=f"<#{s['twitch_channel']}>" if s.get("twitch_channel") else "❌ Nenustatyta",  inline=True)
        e.add_field(name="🎮 Twitch streameriai", value=", ".join(s.get("twitch_streamers",[])) or "❌ Nėra", inline=True)
        e.add_field(name="📹 YouTube kanalas",  value=f"<#{s['youtube_channel']}>" if s.get("youtube_channel") else "❌ Nenustatyta", inline=True)
        e.add_field(name="💎 Boost kanalas",    value=f"<#{s['boost_channel']}>" if s.get("boost_channel") else "❌ Nenustatyta",   inline=True)
        rr = RR_DATA.get(str(gid), {})
        e.add_field(name="🎭 Reaction Roles",   value=f"{len(rr.get('roles',[]))} rolių", inline=True)
        e.set_footer(text=ft())
        await message.channel.send(embed=e)
        return

    # !spotify - rodyti ką klauso narys
    if content.startswith("!spotify"):
        target = message.mentions[0] if message.mentions else message.author
        sp = get_spotify(target)
        if not sp:
            await message.reply(f"**{target.display_name}** šiuo metu neklauso Spotify arba statusas nematomas."); return
        await message.channel.send(embed=build_spotify_embed(target, sp))
        return

    # !antiphishing - valdymas (admin)
    if content.startswith("!antiphishing"):
        if not message.guild or not message.author.guild_permissions.administrator:
            await message.reply("Reikalingos teisės 🚫"); return
        mode = content[13:].strip().lower()
        upd_int_settings(gid, antiphishing=mode != "off")
        await message.reply(f"✅ Anti-phishing: {'✅ Įjungtas' if mode != 'off' else '❌ Išjungtas'}")
        return



    # ══════════════════════════════════════════════════════════════════════════
    #  NUOLAIDŲ KODAI
    # ══════════════════════════════════════════════════════════════════════════

    # !coupon - panaudoti nuolaidų kodą
    if content.startswith("!coupon"):
        if not message.guild: return
        code = content[7:].strip().upper()
        if not code:
            await message.reply("Naudok: `!coupon [KODAS]`"); return

        if USE_DB:
            coupon, msg = validate_coupon(gid, code, uid)
            if not coupon:
                await message.reply(embed=discord.Embed(description=f"❌ {msg}", color=C.ERROR))
                return
            # Išsaugoti aktyvų kuponą nariui (sesijoje)
            D.setdefault("active_coupons", {})[f"{gid}:{uid}"] = {
                "code": code, "discount": coupon["discount_pct"], "id": coupon["id"]
            }
            save_data(D)
            e = discord.Embed(title="🎟️ Kuponas aktyvuotas!", color=C.SUCCESS)
            e = discord.Embed(title="Kuponas aktyvuotas!", color=C.SUCCESS)
            remaining = coupon['max_uses'] - coupon['used_count'] - 1
            disc = coupon['discount_pct']
            e.description = f"Kodas **{code}** aktyvuotas!\nNuolaida: **{disc}%** | Liko: **{remaining}** naudojimų\n\nKuponas bus pritaikytas kitam pirkimui!"
            e.set_footer(text=ft())
            await message.reply(embed=e)
            await message.reply("Kuponų sistema reikalauja database.py!")
        return

    # !createcoupon - sukurti nuolaidų kodą (admin)
    if content.startswith("!createcoupon"):
        if not message.guild or not message.author.guild_permissions.administrator:
            await message.reply("Reikalingos teisės 🚫"); return
        parts = content.split()
        if len(parts) < 4:
            await message.reply(
                "Naudok: `!createcoupon [KODAS] [nuolaida%] [naudojimų] [dienų galiojimas]`\n"
                "Pvz: `!createcoupon VASARA20 20 100 30`"
            ); return
        code = parts[1].upper()
        try:
            discount = int(parts[2])
            max_uses = int(parts[3])
            expires_days = int(parts[4]) if len(parts) > 4 else 30
        except:
            await message.reply("Neteisingas formatas!"); return

        if discount < 1 or discount > 100:
            await message.reply("Nuolaida turi būti 1-100%!"); return

        if USE_DB:
            cid = create_coupon(gid, code, discount, max_uses, expires_days, uid)
            if cid:
                e = discord.Embed(title="🎟️ Kuponas sukurtas!", color=C.SUCCESS)
                e.add_field(name="🏷️ Kodas",     value=f"**{code}**",          inline=True)
                e.add_field(name="💰 Nuolaida",   value=f"**{discount}%**",     inline=True)
                e.add_field(name="🔢 Naudojimai", value=f"**{max_uses}**",      inline=True)
                e.add_field(name="📅 Galioja",    value=f"**{expires_days}d.**", inline=True)
                e.set_footer(text=ft())
                await message.channel.send(embed=e)
            else:
                await message.reply("❌ Toks kodas jau egzistuoja!")
        else:
            await message.reply("Kuponų sistema reikalauja database.py!")
        return

    # !coupons - peržiūrėti kuponus (admin)
    if content == "!coupons":
        if not message.guild or not message.author.guild_permissions.administrator:
            await message.reply("Reikalingos teisės 🚫"); return
        if USE_DB:
            coupons = get_coupons(gid)
            if not coupons:
                await message.reply("Nėra sukurtų kuponų. `!createcoupon`"); return
            e = discord.Embed(title="🎟️ Visi nuolaidų kodai", color=C.GOLD)
            for c in coupons[:15]:
                status = "✅" if c["active"] else "❌"
                expires = datetime.datetime.fromtimestamp(c["expires_at"]).strftime("%Y-%m-%d") if c.get("expires_at") else "∞"
                e.add_field(
                    name=f"{status} `{c['code']}` — {c['discount_pct']}%",
                    value=f"Panaudota: {c['used_count']}/{c['max_uses']} | Galioja iki: {expires}",
                    inline=False
                )
            e.set_footer(text=ft())
            await message.channel.send(embed=e)
        else:
            await message.reply("Kuponų sistema reikalauja database.py!")
        return

    # !deletecoupon - ištrinti kuponą (admin)
    if content.startswith("!deletecoupon"):
        if not message.guild or not message.author.guild_permissions.administrator:
            await message.reply("Reikalingos teisės 🚫"); return
        code = content[13:].strip().upper()
        if not code: await message.reply("Naudok: `!deletecoupon [KODAS]`"); return
        if USE_DB:
            deactivate_coupon(gid, code)
            await message.reply(embed=discord.Embed(description=f"✅ Kuponas `{code}` išjungtas.", color=C.SUCCESS))
        return

    # ══════════════════════════════════════════════════════════════════════════
    #  AUTOMATINIS PRISTATYMAS
    # ══════════════════════════════════════════════════════════════════════════

    # !adddelivery - pridėti auto pristatymo duomenis (admin)
    if content.startswith("!adddelivery"):
        if not message.guild or not message.author.guild_permissions.administrator:
            await message.reply("Reikalingos teisės 🚫"); return
        parts = content.split(None, 2)
        if len(parts) < 3 or not parts[1].isdigit():
            await message.reply(
                "Naudok: `!adddelivery [produkto_ID] [prisijungimo duomenys]`\n"
                "Pvz: `!adddelivery 1 email@gmail.com\nSlaptažodis: abc123`\n\n"
                "Kiekvienas `!adddelivery` = vienas vartotojas. Pridėk tiek kiek turi."
            ); return
        pid = int(parts[1])
        creds = parts[2]
        prods = get_products(gid)
        prod = next((p for p in prods if p["id"] == pid), None)
        if not prod:
            await message.reply(f"Produktas **#{pid}** nerastas! `!shop`"); return
        if USE_DB:
            add_auto_delivery(gid, pid, creds)
            stock = get_delivery_stock(gid, pid)
            stock = get_delivery_stock(gid, pid)
            emoji = prod.get('emoji','📦'); pname = prod.get('name','?')
            await message.reply(embed=discord.Embed(description=f'✅ Auto pristatymas pridėtas {emoji} {pname}! Sandėlyje: **{stock}** vnt.', color=C.SUCCESS))
            await message.reply("Auto pristatymas reikalauja database.py!")
        return

    # !deliverystock - peržiūrėti sandėlį (admin)
    if content.startswith("!deliverystock"):
        if not message.guild or not message.author.guild_permissions.administrator:
            await message.reply("Reikalingos teisės 🚫"); return
        prods = get_products(gid)
        e = discord.Embed(title="📦 Auto pristatymo sandėlis", color=C.GOLD)
        if USE_DB:
            for prod in prods:
                stock = get_delivery_stock(gid, prod["id"])
                status = "🟢" if stock > 0 else "🔴"
                e.add_field(
                    name=f"{status} #{prod['id']:02d} {prod['emoji']} {prod['name']}",
                    value=f"Sandėlyje: **{stock}** vnt. auto pristatymų",
                    inline=True
                )
        else:
            e.description = "Auto pristatymas reikalauja database.py!"
        e.set_footer(text=ft("!adddelivery [ID] [duomenys] — pridėti"))
        await message.channel.send(embed=e)
        return

    # ══════════════════════════════════════════════════════════════════════════
    #  PRENUMERATOS
    # ══════════════════════════════════════════════════════════════════════════

    # !mysubs - mano prenumeratos
    if content == "!mysubs":
        if not message.guild: return
        if USE_DB:
            subs = get_user_subscriptions(gid, uid)
            if not subs:
                await message.reply("Neturi aktyvių prenumeratų. `!shop`"); return
            e = discord.Embed(title=f"📋 {message.author.display_name} — Prenumeratos", color=C.GOLD)
            for sub in subs:
                expires = datetime.datetime.fromtimestamp(sub["expires_at"])
                days_left = max(0, int((sub["expires_at"] - time.time()) / 86400))
                status = "🟢" if days_left > 3 else "🟡" if days_left > 0 else "🔴"
                e.add_field(
                    name=f"{status} {sub['product_name']}",
                    value=f"Baigiasi: **{expires.strftime('%Y-%m-%d')}** ({days_left} d.)",
                    inline=False
                )
            e.set_footer(text=ft())
            await message.channel.send(embed=e)
        else:
            await message.reply("Prenumeratų sistema reikalauja database.py!")
        return


    # ── Atsitiktinis elgesys ──────────────────────────────────────────────────
    if not is_tagged and not content.startswith("!"):
        for kw in TOXIC_KW:
            if kw in content.lower() and random.random()<0.4:
                await message.reply("Oi oi, tokio žodyno čia nenaudojame 😇"); break
        if random.random()<0.05:
            try: await message.add_reaction(random.choice(["😂","💀","🔥","👀","😏","🤨","😭","🗿"]))
            except: pass
        if random.random()<0.02:
            await message.channel.send(random.choice(["Aš čia vienintelis normalus 😄","Kas vyksta čia 😂","Man atrodo jūs visi įtartini 🤨"]))

    # ── AI pokalbis ───────────────────────────────────────────────────────────
    if is_tagged:
        if (time.time()-ai_cd[uid])<5: await message.reply("Palauk sekundę 🙄"); return
        ai_cd[uid]=time.time()
        user_input=re.sub(r"<@!?\d+>","",content).strip()
        if not user_input:
            await message.reply(random.choice(["Ko nori 😂","Kalbėk greičiau 😄","Jei nesąmonė — ignoruosiu 😏"])); return
        if random.random()<0.1:
            await message.reply(random.choice(["Ko nori 😂","Vėl tu... nu gerai 👀","Ugh, gerai, klausau 🙄"])); return
        add_hist(uid,"user",user_input)
        async with message.channel.typing():
            history_text="\n".join(f"{'Vartotojas' if m['role']=='user' else 'Kodas'}: {m['content']}" for m in conv_history[uid][-10:])
            reply=await ai_chat(personality(),f"Pokalbio istorija:\n{history_text}\n\nNauja žinutė: {user_input}")
            add_hist(uid,"assistant",reply)
            await message.reply(reply)


@bot.event
async def on_member_update(before, after):
    # Server boost notifikacija
    if before.premium_since is None and after.premium_since is not None:
        guild = after.guild
        gid = str(guild.id)
        s = get_int_settings(gid)
        boost_ch_id = s.get("boost_channel") or D["welcome_channels"].get(gid)
        if boost_ch_id:
            ch = bot.get_channel(int(boost_ch_id))
            if ch:
                await ch.send(embed=build_boost_embed(after, guild))
                # Bonus boost'eriui
                acoin(gid, after.id, 2000)
                await ch.send(
                    embed=discord.Embed(description=f"💎 {after.mention} gavo **+2000** 🪙 uz boost!", color=C.GOLD),
                    delete_after=30
                )

bot.run(TOKEN)
