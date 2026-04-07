# -*- coding: utf-8 -*-
"""
KODAS BOT V7 — Integracijos ir Discord Funkcijos
"""
import discord
from discord import ui
import asyncio, json, os, re, time, datetime, pathlib
from designs_v6 import C, ft

# ══════════════════════════════════════════════════════════════════════════════
#  REACTION ROLES
# ══════════════════════════════════════════════════════════════════════════════
class ReactionRoleButton(ui.Button):
    def __init__(self, role_id, label, emoji=None, style=discord.ButtonStyle.blurple):
        super().__init__(label=label, emoji=emoji, style=style, custom_id=f"rrole_{role_id}")
        self.role_id = role_id

    async def callback(self, interaction):
        role = interaction.guild.get_role(self.role_id)
        if not role:
            await interaction.response.send_message("❌ Rolė nerasta!", ephemeral=True); return
        # Patikrinti hierarchiją
        if role >= interaction.guild.me.top_role:
            await interaction.response.send_message(
                f"❌ Negaliu duoti rolės **{role.name}** — ji aukščiau mano rolės!\n"
                f"Adminai turi pakelti boto rolę aukščiau **{role.name}** servero nustatymuose.",
                ephemeral=True
            ); return
        try:
            if role in interaction.user.roles:
                await interaction.user.remove_roles(role)
                await interaction.response.send_message(f"❌ Rolė **{role.name}** pašalinta!", ephemeral=True)
            else:
                await interaction.user.add_roles(role)
                await interaction.response.send_message(f"✅ Gavai rolę **{role.name}**!", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"❌ Klaida: {e}", ephemeral=True)

class ReactionRoleView(ui.View):
    def __init__(self, roles_data):
        super().__init__(timeout=None)
        styles = [discord.ButtonStyle.blurple, discord.ButtonStyle.green, discord.ButtonStyle.red, discord.ButtonStyle.grey]
        for i, item in enumerate(roles_data[:20]):
            btn = ReactionRoleButton(item["role_id"], item["label"], item.get("emoji"), styles[i%4])
            btn.row = i // 5
            self.add_item(btn)

def build_rr_embed(title, description, roles_data, guild):
    e = discord.Embed(title=f"🎭 {title}", color=C.GOLD)
    e.description = (
        f"```\n╔══════════════════════════════════╗\n"
        f"║      PASIRINK SAVO ROLES!        ║\n"
        f"╚══════════════════════════════════╝\n```\n"
        f"{description}\n\nSpausk mygtuka gauti arba pasalinti role!"
    )
    for item in roles_data:
        role = guild.get_role(item["role_id"])
        members = len(role.members) if role else 0
        e.add_field(name=f"{item.get('emoji','')} {item['label']}", value=f"{item.get('desc','')}\n{members} nariai", inline=True)
    e.set_footer(text=ft("Reaction Roles"))
    return e

# RR duomenys
RR_FILE = str(pathlib.Path(__file__).parent / "reaction_roles.json")
def load_rr():
    if os.path.exists(RR_FILE):
        try:
            with open(RR_FILE,"r",encoding="utf-8") as f: return json.load(f)
        except: pass
    return {}
def save_rr(d):
    with open(RR_FILE,"w",encoding="utf-8") as f: json.dump(d,f,indent=2,ensure_ascii=False)
RR_DATA = load_rr()

# ══════════════════════════════════════════════════════════════════════════════
#  ANTI-PHISHING
# ══════════════════════════════════════════════════════════════════════════════
PHISHING = [
    r"discord\.gift/[a-zA-Z0-9]+",
    r"discordnitro[a-zA-Z0-9\-]*\.(com|net|org|xyz)",
    r"dlscord\.(com|gift|gg)",
    r"discrod\.(com|gg)",
    r"discord-gift\.(com|net|org)",
    r"free.*nitro",
    r"nitro.*free",
]
SUSPICIOUS = ["discordnitro","discord-gift","discord-free","free-nitro","dlscord","discrod","steamgift"]

def is_phishing(content):
    c = content.lower()
    for p in PHISHING:
        if re.search(p, c): return True
    for s in SUSPICIOUS:
        if s in c: return True
    return False

def build_phishing_embed(member, content):
    e = discord.Embed(title="Phishing Aptiktas!", color=C.ERROR)
    e.add_field(name="Narys",    value=member.mention,                     inline=True)
    e.add_field(name="Veiksmas", value="Zinuté istrintas, narys nutildytas", inline=True)
    e.add_field(name="Turinys",  value=f"||{content[:200]}||",             inline=False)
    e.set_thumbnail(url=member.display_avatar.url)
    e.set_footer(text=ft("Anti-Phishing"))
    return e

# ══════════════════════════════════════════════════════════════════════════════
#  SERVER BOOST
# ══════════════════════════════════════════════════════════════════════════════
def build_boost_embed(member, guild):
    tier_names = {0:"Nera",1:"1 lygis",2:"2 lygis",3:"3 lygis"}
    e = discord.Embed(title="Serveris Sustiprintas!", color=discord.Color.from_rgb(255,115,250))
    e.description = f"🎉 {member.mention} sustipino serveri!\n\nAciu uz palaikymа!"
    e.add_field(name="Viso Boostu",    value=f"**{guild.premium_subscription_count or 0}**", inline=True)
    e.add_field(name="Serverio lygis", value=tier_names.get(guild.premium_tier,"?"),          inline=True)
    e.set_thumbnail(url=member.display_avatar.url)
    e.set_footer(text=ft("Server Boost"))
    return e

# ══════════════════════════════════════════════════════════════════════════════
#  SPOTIFY
# ══════════════════════════════════════════════════════════════════════════════
def get_spotify(member):
    for a in member.activities:
        if isinstance(a, discord.Spotify): return a
    return None

def build_spotify_embed(member, sp):
    e = discord.Embed(title="Dabar Klauso", color=discord.Color.from_rgb(30,215,96))
    e.set_author(name=member.display_name, icon_url=member.display_avatar.url)
    e.add_field(name="Daina",     value=f"**{sp.title}**",           inline=False)
    e.add_field(name="Atlikejas", value=", ".join(sp.artists),        inline=True)
    e.add_field(name="Albumas",   value=sp.album,                     inline=True)
    if sp.album_cover_url: e.set_thumbnail(url=sp.album_cover_url)
    e.set_footer(text=ft("Spotify"))
    return e

# ══════════════════════════════════════════════════════════════════════════════
#  GIMTADIENIAI
# ══════════════════════════════════════════════════════════════════════════════
def build_birthday_embed(member):
    e = discord.Embed(title="Gimtadienis!", color=discord.Color.from_rgb(255,105,180))
    e.description = (
        f"🎂 Siandien gimtadienis — {member.mention}!\n\n"
        f"Viso serverio sveikinimai! 🎊🎈🎁"
    )
    e.add_field(name="Dovana", value="**+500** 🪙 automatiskai!", inline=True)
    e.add_field(name="Linkime", value="Sveikatos ir laimes! 🌟",  inline=True)
    e.set_thumbnail(url=member.display_avatar.url)
    e.set_footer(text=ft("Gimtadieniai"))
    return e

# ══════════════════════════════════════════════════════════════════════════════
#  TWITCH
# ══════════════════════════════════════════════════════════════════════════════
TWITCH_CLIENT_ID     = os.getenv("TWITCH_CLIENT_ID","")
TWITCH_CLIENT_SECRET = os.getenv("TWITCH_CLIENT_SECRET","")
_twitch_token = {"t":None,"exp":0}
_twitch_live  = {}

async def _get_twitch_token():
    if not TWITCH_CLIENT_ID or not TWITCH_CLIENT_SECRET: return None
    if _twitch_token["t"] and time.time() < _twitch_token["exp"]: return _twitch_token["t"]
    try:
        import aiohttp
        async with aiohttp.ClientSession() as s:
            async with s.post("https://id.twitch.tv/oauth2/token", params={
                "client_id":TWITCH_CLIENT_ID,"client_secret":TWITCH_CLIENT_SECRET,"grant_type":"client_credentials"
            }) as r:
                if r.status==200:
                    d=await r.json()
                    _twitch_token["t"]=d["access_token"]
                    _twitch_token["exp"]=time.time()+d["expires_in"]-60
                    return d["access_token"]
    except: pass
    return None

async def check_twitch(streamer):
    t=await _get_twitch_token()
    if not t: return None
    try:
        import aiohttp
        async with aiohttp.ClientSession() as s:
            async with s.get(f"https://api.twitch.tv/helix/streams?user_login={streamer}",
                headers={"Client-ID":TWITCH_CLIENT_ID,"Authorization":f"Bearer {t}"}) as r:
                if r.status==200:
                    d=await r.json()
                    streams=d.get("data",[])
                    return streams[0] if streams else None
    except: pass
    return None

async def get_twitch_user(streamer):
    t=await _get_twitch_token()
    if not t: return None
    try:
        import aiohttp
        async with aiohttp.ClientSession() as s:
            async with s.get(f"https://api.twitch.tv/helix/users?login={streamer}",
                headers={"Client-ID":TWITCH_CLIENT_ID,"Authorization":f"Bearer {t}"}) as r:
                if r.status==200:
                    d=await r.json()
                    users=d.get("data",[])
                    return users[0] if users else None
    except: pass
    return None

def build_twitch_embed(stream, user=None):
    e = discord.Embed(
        title=f"{stream.get('user_name','?')} yra LIVE!",
        url=f"https://twitch.tv/{stream.get('user_login','?')}",
        color=discord.Color.from_rgb(145,70,255)
    )
    e.add_field(name="Pavadinimas", value=stream.get("title","?")[:100],         inline=False)
    e.add_field(name="Zaidimas",    value=stream.get("game_name","?"),            inline=True)
    e.add_field(name="Ziurovai",    value=f"**{stream.get('viewer_count',0):,}**", inline=True)
    if user and user.get("profile_image_url"): e.set_thumbnail(url=user["profile_image_url"])
    if stream.get("thumbnail_url"):
        thumb = stream["thumbnail_url"].replace("{width}","1280").replace("{height}","720")
        e.set_image(url=thumb+f"?t={int(time.time())}")
    e.set_footer(text=ft("Twitch"))
    return e

# ══════════════════════════════════════════════════════════════════════════════
#  YOUTUBE
# ══════════════════════════════════════════════════════════════════════════════
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY","")
_yt_cache = {}

async def check_youtube(channel_id):
    if not YOUTUBE_API_KEY: return None
    try:
        import aiohttp
        async with aiohttp.ClientSession() as s:
            async with s.get("https://www.googleapis.com/youtube/v3/search", params={
                "key":YOUTUBE_API_KEY,"channelId":channel_id,
                "part":"snippet","order":"date","maxResults":1,"type":"video"
            }) as r:
                if r.status==200:
                    d=await r.json()
                    items=d.get("items",[])
                    if items:
                        item=items[0]
                        vid_id=item["id"]["videoId"]
                        last=_yt_cache.get(channel_id)
                        if last and last!=vid_id:
                            _yt_cache[channel_id]=vid_id
                            return item
                        elif not last:
                            _yt_cache[channel_id]=vid_id
    except: pass
    return None

def build_youtube_embed(video):
    sn=video.get("snippet",{})
    vid_id=video["id"]["videoId"]
    e=discord.Embed(title=f"Naujas video: {sn.get('channelTitle','?')}",url=f"https://youtube.com/watch?v={vid_id}",color=discord.Color.red())
    e.add_field(name="Pavadinimas",value=sn.get("title","?")[:100],inline=False)
    if sn.get("thumbnails",{}).get("high",{}).get("url"): e.set_image(url=sn["thumbnails"]["high"]["url"])
    e.set_footer(text=ft("YouTube"))
    return e

# ══════════════════════════════════════════════════════════════════════════════
#  INTEGRACIJOS NUSTATYMAI
# ══════════════════════════════════════════════════════════════════════════════
INT_FILE = str(pathlib.Path(__file__).parent / "integrations.json")
def load_int():
    if os.path.exists(INT_FILE):
        try:
            with open(INT_FILE,"r",encoding="utf-8") as f: return json.load(f)
        except: pass
    return {}
def save_int(d):
    with open(INT_FILE,"w",encoding="utf-8") as f: json.dump(d,f,indent=2,ensure_ascii=False)
INTEGRATIONS = load_int()

def get_int_settings(gid): return INTEGRATIONS.get(str(gid),{})
def upd_int_settings(gid,**kw):
    g=str(gid)
    if g not in INTEGRATIONS: INTEGRATIONS[g]={}
    INTEGRATIONS[g].update(kw)
    save_int(INTEGRATIONS)

# ══════════════════════════════════════════════════════════════════════════════
#  BACKGROUND TASKS
# ══════════════════════════════════════════════════════════════════════════════
async def twitch_task(bot):
    await bot.wait_until_ready()
    while not bot.is_closed():
        for guild in bot.guilds:
            gid=str(guild.id)
            s=get_int_settings(gid)
            streamers=s.get("twitch_streamers",[])
            ch_id=s.get("twitch_channel")
            if not ch_id or not streamers: continue
            ch=bot.get_channel(int(ch_id))
            if not ch: continue
            for streamer in streamers:
                try:
                    stream=await check_twitch(streamer)
                    was_live=_twitch_live.get(f"{gid}:{streamer}",False)
                    if stream and not was_live:
                        _twitch_live[f"{gid}:{streamer}"]=True
                        user=await get_twitch_user(streamer)
                        embed=build_twitch_embed(stream,user)
                        role_id=s.get("twitch_role")
                        mention=f"<@&{role_id}>" if role_id else "@here"
                        await ch.send(content=mention,embed=embed)
                    elif not stream and was_live:
                        _twitch_live[f"{gid}:{streamer}"]=False
                except Exception as e:
                    print(f"Twitch err: {e}")
        await asyncio.sleep(120)

async def youtube_task(bot):
    await bot.wait_until_ready()
    while not bot.is_closed():
        for guild in bot.guilds:
            gid=str(guild.id)
            s=get_int_settings(gid)
            channels=s.get("youtube_channels",[])
            ch_id=s.get("youtube_channel")
            if not ch_id or not channels: continue
            ch=bot.get_channel(int(ch_id))
            if not ch: continue
            for yt_ch in channels:
                try:
                    video=await check_youtube(yt_ch)
                    if video:
                        embed=build_youtube_embed(video)
                        role_id=s.get("youtube_role")
                        mention=f"<@&{role_id}>" if role_id else ""
                        await ch.send(content=mention,embed=embed)
                except Exception as e:
                    print(f"YouTube err: {e}")
        await asyncio.sleep(300)
