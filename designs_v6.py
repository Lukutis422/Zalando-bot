# -*- coding: utf-8 -*-
"""
KODAS BOT V6 FINAL — Premium Design System
Aukso / Sidabro / Premium stilius
"""
import discord
import datetime
import random
import time

# ══════════════════════════════════════════════════════════════════════════════
#  SPALVŲ SISTEMA
# ══════════════════════════════════════════════════════════════════════════════
class C:
    GOLD       = discord.Color.from_rgb(255, 215, 0)
    DARK_GOLD  = discord.Color.from_rgb(184, 134, 11)
    SILVER     = discord.Color.from_rgb(192, 192, 192)
    PLATINUM   = discord.Color.from_rgb(229, 228, 226)
    BRONZE     = discord.Color.from_rgb(205, 127, 50)
    ROYAL      = discord.Color.from_rgb(65, 105, 225)
    PURPLE     = discord.Color.from_rgb(75, 0, 130)
    CRIMSON    = discord.Color.from_rgb(220, 20, 60)
    EMERALD    = discord.Color.from_rgb(0, 201, 87)
    SAPPHIRE   = discord.Color.from_rgb(15, 82, 186)
    SUCCESS    = discord.Color.from_rgb(0, 201, 87)
    ERROR      = discord.Color.from_rgb(220, 20, 60)
    WARNING    = discord.Color.from_rgb(255, 165, 0)
    INFO       = discord.Color.from_rgb(65, 105, 225)
    SHOP       = discord.Color.from_rgb(184, 134, 11)
    TICKET     = discord.Color.from_rgb(75, 0, 130)
    CASINO     = discord.Color.from_rgb(220, 20, 60)
    MUSIC      = discord.Color.from_rgb(30, 215, 96)
    NEUTRAL    = discord.Color.from_rgb(80, 80, 100)
    PINK       = discord.Color.from_rgb(255, 105, 180)
    DARK       = discord.Color.from_rgb(30, 30, 40)

def ft(extra=""):
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    return f"💎 Kodas V6 • {now}" + (f" • {extra}" if extra else "")

def pb(val, mx, ln=10, f="█", e="░"):
    filled = int((val / max(mx, 1)) * ln)
    return f * filled + e * (ln - filled)

def stars(n, mx=5):
    return "⭐" * n + "☆" * (mx - n)

def medal(pos):
    return {1:"🥇",2:"🥈",3:"🥉"}.get(pos, f"**{pos}.**")

def badge(level):
    if level >= 100: return "👑 Dievas"
    if level >= 75:  return "💎 Nemirtingas"
    if level >= 50:  return "🔥 Legenda"
    if level >= 30:  return "⚡ Elitas"
    if level >= 20:  return "🎖️ Veteranas"
    if level >= 10:  return "🌟 Aktyvus"
    return "🌱 Naujokas"

# ══════════════════════════════════════════════════════════════════════════════
#  BALANCE / PROFILIS
# ══════════════════════════════════════════════════════════════════════════════
def embed_balance(member, coins, xp, rep, streak, level, xp_cur):
    b = badge(level)
    bar = pb(xp_cur, 200)
    pct = int(xp_cur / 200 * 100)
    e = discord.Embed(color=C.GOLD)
    e.set_author(name=f"💰 {member.display_name} — Profilis", icon_url=member.display_avatar.url)
    e.description = (
        f"```\n"
        f"╔══════════════════════════╗\n"
        f"║  {b:^26}║\n"
        f"╚══════════════════════════╝\n"
        f"```"
    )
    e.add_field(name="💵 Monetos",    value=f"```\n{coins:,} 🪙\n```", inline=True)
    e.add_field(name="🎯 Lygis",      value=f"```\nLv. {level}\n```",  inline=True)
    e.add_field(name="⭐ Reputacija", value=f"```\n{rep} ⭐\n```",     inline=True)
    e.add_field(name="⚡ XP",         value=f"```\n{xp:,} XP\n```",   inline=True)
    e.add_field(name="🔥 Streak",     value=f"```\n{streak} dienų\n```", inline=True)
    e.add_field(name="📊 Progresas",
                value=f"`{bar}` **{pct}%** ({xp_cur}/200)", inline=False)
    e.set_thumbnail(url=member.display_avatar.url)
    e.set_footer(text=ft())
    return e

def embed_daily(amount, bonus, total, streak, balance):
    e = discord.Embed(title="🎁 Dienos Bonus!", color=C.GOLD)
    e.description = (
        f"```\n"
        f"╔══════════════════════╗\n"
        f"║   DIENOS APDOVANOJIMAS  ║\n"
        f"╚══════════════════════╝\n"
        f"```"
    )
    e.add_field(name="💵 Bazinis",       value=f"**+{amount:,}** 🪙", inline=True)
    e.add_field(name=f"🔥 Streak x{streak}", value=f"**+{bonus:,}** 🪙", inline=True)
    e.add_field(name="💎 Viso gauta",    value=f"**+{total:,}** 🪙", inline=True)
    e.add_field(name="🏦 Likutis",       value=f"**{balance:,}** 🪙", inline=False)
    if streak >= 30: e.add_field(name="🏆", value="Mėnesio streak pasiekimas! Legendinis!", inline=False)
    elif streak >= 7: e.add_field(name="🔥", value="Savaitės streak! Puiku!", inline=False)
    e.set_footer(text=ft("Grįžk rytoj didesniam bonusui!"))
    return e

def embed_work(name, emoji, earned, balance, msg):
    e = discord.Embed(title=f"{emoji} {name} — Darbas Atliktas!", color=C.SUCCESS)
    e.description = f"*{msg}*"
    e.add_field(name="💵 Uždirbta", value=f"**+{earned:,}** 🪙", inline=True)
    e.add_field(name="🏦 Likutis",  value=f"**{balance:,}** 🪙", inline=True)
    e.set_footer(text=ft("Grįžk po valandos!"))
    return e

# ══════════════════════════════════════════════════════════════════════════════
#  RANGAS
# ══════════════════════════════════════════════════════════════════════════════
def embed_rank(member, xp, level, xp_cur, pos, coins, rep, warns, warn_max):
    bar = pb(xp_cur, 200)
    pct = int(xp_cur / 200 * 100)
    b = badge(level)
    e = discord.Embed(color=C.GOLD)
    e.set_author(name=f"🏆 {member.display_name} — Rangas", icon_url=member.display_avatar.url)
    e.description = (
        f"```\n"
        f"┌──────────────────────────┐\n"
        f"│  {b:^26}│\n"
        f"└──────────────────────────┘\n"
        f"```"
    )
    e.add_field(name="🎯 Lygis",         value=f"**{level}**",           inline=True)
    e.add_field(name="⚡ Viso XP",       value=f"**{xp:,}**",            inline=True)
    e.add_field(name="🏅 Serverio vieta", value=f"**#{pos}**",            inline=True)
    e.add_field(name="💰 Monetos",        value=f"**{coins:,}** 🪙",      inline=True)
    e.add_field(name="⭐ Reputacija",     value=f"**{rep}** ⭐",          inline=True)
    e.add_field(name="⚠️ Perspėjimai",   value=f"**{warns}/{warn_max}**", inline=True)
    e.add_field(name=f"📊 Progresas ({pct}%)",
                value=f"`{bar}` {xp_cur}/200 XP iki kito lygio", inline=False)
    e.set_thumbnail(url=member.display_avatar.url)
    e.set_footer(text=ft())
    return e

def embed_leaderboard_xp(entries, guild_name):
    e = discord.Embed(title=f"🏆 XP Lyderiai — {guild_name}", color=C.GOLD)
    e.description = (
        f"```\n"
        f"╔══════════════════════════════╗\n"
        f"║      SERVERIO LYDERIAI       ║\n"
        f"╚══════════════════════════════╝\n"
        f"```"
    )
    for i, (name, xp, level) in enumerate(entries, 1):
        bar = pb(xp % 200, 200, 8)
        e.add_field(
            name=f"{medal(i)} {name}",
            value=f"{badge(level)} • Lv.**{level}** • **{xp:,}** XP\n`{bar}`",
            inline=False
        )
    e.set_footer(text=ft())
    return e

def embed_leaderboard_coins(entries, guild_name):
    e = discord.Embed(title=f"💰 Turtingiausi — {guild_name}", color=C.GOLD)
    e.description = (
        f"```\n"
        f"╔══════════════════════════════╗\n"
        f"║      TURTINGIAUSI NARIAI     ║\n"
        f"╚══════════════════════════════╝\n"
        f"```"
    )
    for i, (name, coins) in enumerate(entries, 1):
        bar = "█" * min(int(coins / 500), 10)
        e.add_field(
            name=f"{medal(i)} {name}",
            value=f"**{coins:,}** 🪙 {bar}",
            inline=False
        )
    e.set_footer(text=ft())
    return e

def embed_levelup(member, new_level, xp_cur, new_role=None):
    b = badge(new_level)
    bar = pb(xp_cur, 200)
    e = discord.Embed(color=C.GOLD)
    e.set_author(name="🎉 LEVEL UP!", icon_url=member.display_avatar.url)
    e.description = (
        f"```\n"
        f"╔══════════════════════════════╗\n"
        f"║  {member.display_name[:28]:^28}  ║\n"
        f"║   pasiekė {new_level} lygį! 🏆   ║\n"
        f"╚══════════════════════════════╝\n"
        f"```"
    )
    e.add_field(name="🏅 Titulas", value=f"**{b}**", inline=True)
    e.add_field(name="🎯 Lygis",   value=f"**{new_level}**", inline=True)
    if new_role:
        e.add_field(name="🎁 Nauja rolė!", value=f"**{new_role.name}**", inline=True)
    e.add_field(name="📊 Progresas iki kito",
                value=f"`{bar}` {xp_cur}/200", inline=False)
    e.set_thumbnail(url=member.display_avatar.url)
    e.set_footer(text=ft())
    return e

# ══════════════════════════════════════════════════════════════════════════════
#  PARDUOTUVĖ
# ══════════════════════════════════════════════════════════════════════════════
def embed_shop_main(guild_name, products):
    e = discord.Embed(color=C.SHOP)
    e.set_author(name=f"🛍️ {guild_name} — Prenumeratų Parduotuvė")
    e.description = (
        f"```\n"
        f"╔══════════════════════════════════╗\n"
        f"║    💎 PREMIUM PRENUMERATOS 💎    ║\n"
        f"╚══════════════════════════════════╝\n"
        f"```\n"
        f"✅ Greitas pristatymas  •  🔒 Saugus pirkimas\n"
        f"💬 24/7 Pagalba  •  🔄 Pinigų grąžinimo garantija\n\n"
        f"**`!buy [ID]`** — pirkti  |  **`!myorders`** — mano užsakymai"
    )
    cats = {}
    for p in products:
        cats.setdefault(p["category"], []).append(p)
    cat_display = {
        "streaming": ("🎬", "Streaming"),
        "music":     ("🎵", "Muzika"),
        "editing":   ("✂️", "Redagavimas"),
        "gaming":    ("🎮", "Gaming"),
        "other":     ("📦", "Kita"),
    }
    for cat, cat_prods in cats.items():
        emoji, cat_name = cat_display.get(cat, ("📦", cat))
        lines = []
        for p in cat_prods:
            stk = "🟢" if p.get("stock", 0) > 0 else "🔴"
            old = f"~~{p['old_price']}€~~ " if p.get("old_price") else ""
            disc = f"🏷️ `-{int((1-p['price']/p['old_price'])*100)}%`" if p.get("old_price") else ""
            lines.append(
                f"{stk} `#{p['id']:02d}` **{p['emoji']} {p['name']}** — {p['duration']}\n"
                f"　{old}**{p['price']}€** {disc}\n"
                f"　*{p['desc']}*"
            )
        e.add_field(name=f"{emoji} {cat_name}", value="\n".join(lines), inline=False)
    e.set_footer(text=ft("!buy [ID] pirkti"))
    return e

def embed_order_channel(member, order, product, payment_methods):
    e = discord.Embed(title=f"🛍️ Užsakymas #{order['id']:04d}", color=C.SHOP)
    e.description = (
        f"```\n"
        f"┌──────────────────────────────┐\n"
        f"│  {product['emoji']} {product['name'][:24]:<24}│\n"
        f"│  {product['duration']:<14} │ {product['price']}€{'':>8}│\n"
        f"└──────────────────────────────┘\n"
        f"```"
    )
    e.add_field(name="👤 Pirkėjas",  value=member.mention,           inline=True)
    e.add_field(name="📋 Statusas",  value="⏳ Laukiama apmokėjimo", inline=True)
    e.add_field(name="\u200b",       value="\u200b",                  inline=True)
    if payment_methods:
        pay_meta = {"revolut":("💜","Revolut"),"paypal":("💙","PayPal"),"crypto":("🪙","Crypto"),"bankas":("🏦","Bankas"),"paysera":("🟢","Paysera")}
        pay_txt = "\n".join(f"{pay_meta.get(k,('💳',k))[0]} **{pay_meta.get(k,('💳',k))[1]}:** `{v}`" for k,v in payment_methods.items())
        e.add_field(name="💳 Mokėjimo Būdai", value=pay_txt, inline=False)
    e.add_field(
        name="📋 Instrukcija",
        value=(
            "**1.** Sumokėk nurodytu būdu\n"
            "**2.** Pateik mokėjimo screenshot šiame kanale\n"
            "**3.** Adminas patikrins ir suaktyvins per 5–30 min\n\n"
            "*`!close` — uždaryti kanalą*"
        ),
        inline=False
    )
    e.set_thumbnail(url=member.display_avatar.url)
    e.set_footer(text=ft(f"#{order['id']:04d} • {product['price']}€"))
    return e

def embed_order_complete(order):
    e = discord.Embed(title="✅ Užsakymas Įvykdytas!", color=C.SUCCESS)
    e.description = (
        f"```\n"
        f"╔══════════════════════════════╗\n"
        f"║  🎉 PRENUMERATA SUAKTYVINTA! ║\n"
        f"╚══════════════════════════════╝\n"
        f"```"
    )
    e.add_field(name="📦 Produktas", value=f"**{order['product_name']}**", inline=True)
    e.add_field(name="⏱️ Trukmė",    value=f"**{order['duration']}**",     inline=True)
    e.add_field(name="💰 Sumokėta",  value=f"**{order['price']}€**",        inline=True)
    e.add_field(name="🙏 Ačiū!",     value="Mėgaukis prenumerata! Iškilus problemoms — sukurk ticket.", inline=False)
    e.set_footer(text=ft("Ačiū už pirkimą!"))
    return e

# ══════════════════════════════════════════════════════════════════════════════
#  TICKET SISTEMA
# ══════════════════════════════════════════════════════════════════════════════
TICKET_CATEGORIES_V2 = {
    "support":   {"emoji":"🛠️","name":"Pagalba",     "color":discord.Color.from_rgb(65,105,225),  "desc":"Bendra pagalba"},
    "shop":      {"emoji":"🛍️","name":"Užsakymas",   "color":discord.Color.from_rgb(0,201,87),    "desc":"Prenumeratos ir pirkimai"},
    "report":    {"emoji":"🚨","name":"Skundas",     "color":discord.Color.from_rgb(220,20,60),   "desc":"Pranešk apie pažeidimą"},
    "appeal":    {"emoji":"⚖️","name":"Apeliacijos", "color":discord.Color.from_rgb(255,165,0),   "desc":"Ban/mute apeliacija"},
    "vip":       {"emoji":"💎","name":"VIP",         "color":discord.Color.from_rgb(255,215,0),   "desc":"VIP narių pagalba"},
    "technical": {"emoji":"🔧","name":"Techninis",   "color":discord.Color.from_rgb(30,144,255),  "desc":"Techninės problemos"},
    "partner":   {"emoji":"🤝","name":"Partnerystė", "color":discord.Color.from_rgb(75,0,130),    "desc":"Serverių partnerystė"},
    "other":     {"emoji":"📋","name":"Kita",        "color":discord.Color.from_rgb(100,100,120), "desc":"Kiti klausimai"},
}
PRIORITIES = {"low":("🟢","Žemas"),"normal":("🟡","Normalus"),"high":("🟠","Aukštas"),"urgent":("🔴","SKUBUS")}

def embed_ticket_panel(guild_name):
    e = discord.Embed(color=C.TICKET)
    e.set_author(name=f"🎫 {guild_name} — Pagalbos Centras")
    e.description = (
        f"```\n"
        f"╔══════════════════════════════════╗\n"
        f"║       💎 SUPPORT SISTEMA 💎       ║\n"
        f"╚══════════════════════════════════╝\n"
        f"```\n"
        f"Reikia pagalbos? Pasirink kategoriją!\n"
        f"Mūsų komanda atsilieps kuo greičiau. 🙏\n"
    )
    for k, v in TICKET_CATEGORIES_V2.items():
        e.add_field(name=f"{v['emoji']} {v['name']}", value=f"*{v['desc']}*", inline=True)
    e.set_footer(text=ft("Pasirink kategoriją ↓"))
    return e

def embed_ticket_opened(member, num, cat_name, cat_emoji, subject, description, priority, cat_color):
    pe, pn = PRIORITIES.get(priority, ("🟡","Normalus"))
    e = discord.Embed(color=cat_color)
    e.set_author(name=f"🎫 Ticket #{num:04d} — {cat_name}", icon_url=member.display_avatar.url)
    e.description = (
        f"```\n"
        f"┌──────────────────────────────┐\n"
        f"│  Sveiki atvykę į support!    │\n"
        f"│  Atsakysime kuo greičiau.    │\n"
        f"└──────────────────────────────┘\n"
        f"```"
    )
    e.add_field(name="👤 Narys",        value=member.mention,           inline=True)
    e.add_field(name="🎯 Prioritetas",  value=f"{pe} **{pn}**",         inline=True)
    e.add_field(name="📅 Sukurtas",     value=f"<t:{int(time.time())}:R>", inline=True)
    e.add_field(name="📌 Tema",         value=f"**{subject}**",          inline=False)
    e.add_field(name="📝 Aprašymas",    value=description[:1000],        inline=False)
    e.add_field(
        name="ℹ️ Komandos",
        value=(
            "`!claim` — paimti ticket\n"
            "`!priority [low/normal/high/urgent]` — prioritetas\n"
            "`!addnote [tekstas]` — pastaba\n"
            "`!rate [1-5]` — įvertinti pagalbą\n"
            "`!transcript` — išsaugoti pokalbį\n"
            "`!close` — uždaryti"
        ),
        inline=False
    )
    e.set_thumbnail(url=member.display_avatar.url)
    e.set_footer(text=ft(f"Ticket #{num:04d}"))
    return e

def embed_ticket_claimed(claimer):
    e = discord.Embed(color=C.SUCCESS)
    e.set_author(name=f"✋ Ticket paimtas!", icon_url=claimer.display_avatar.url)
    e.description = (
        f"**{claimer.display_name}** perimamas šis ticket!\n"
        f"Tikėtis atsakymo netrukus. 🙏"
    )
    e.set_footer(text=ft())
    return e

def embed_ticket_stats(stats, guild_name):
    e = discord.Embed(title=f"📊 Ticket Statistika — {guild_name}", color=C.TICKET)
    e.description = (
        f"```\n"
        f"╔══════════════════════════════╗\n"
        f"║      SUPPORT STATISTIKA      ║\n"
        f"╚══════════════════════════════╝\n"
        f"```"
    )
    total = stats.get("total", 0)
    open_ = stats.get("open", 0)
    closed = stats.get("closed", 0)
    avg = stats.get("avg_minutes", 0)
    e.add_field(name="📊 Viso",    value=f"**{total}**",  inline=True)
    e.add_field(name="🟢 Atviri",  value=f"**{open_}**",  inline=True)
    e.add_field(name="🔒 Uždaryti",value=f"**{closed}**", inline=True)
    if avg:
        h, m = divmod(int(avg), 60)
        e.add_field(name="⏱️ Vid. laikas", value=f"**{h}h {m}min**" if h else f"**{m}min**", inline=True)
    if total > 0:
        rate = int(closed / total * 100)
        e.add_field(name=f"📈 Išsprendimo rodiklis", value=f"`{pb(rate,100)}` **{rate}%**", inline=False)
    e.set_footer(text=ft())
    return e

def embed_ticket_rating(member, ticket_num, rating):
    stars_str = "⭐" * rating + "☆" * (5 - rating)
    labels = {1:"Labai blogai 😞",2:"Blogai 😕",3:"Gerai 😊",4:"Puikiai 😄",5:"Tobulai! 🤩"}
    e = discord.Embed(title="⭐ Ticket Įvertinimas", color=C.GOLD)
    e.description = (
        f"**{member.display_name}** įvertino pagalbą:\n\n"
        f"**{stars_str}**\n"
        f"*{labels.get(rating, '')}*"
    )
    e.set_footer(text=ft(f"Ticket #{ticket_num:04d}"))
    return e

# ══════════════════════════════════════════════════════════════════════════════
#  CASINO / ŽAIDIMAI
# ══════════════════════════════════════════════════════════════════════════════
def embed_casino(reels, result_type, amount, balance):
    line = "  ┃  ".join(reels)
    colors = {"jackpot":C.GOLD,"bigwin":C.GOLD,"win":C.SUCCESS,"half":C.WARNING,"lose":C.ERROR}
    titles = {"jackpot":"💎 ══ JACKPOT! ══ 💎","bigwin":"🎰 ═ DIDELIS LAIMĖJIMAS ═ 🎰","win":"🎉 ════ LAIMĖJAI! ════ 🎉","half":"🎰 ══ BEVEIK... ══ 🎰","lose":"💀 ═══ PRALAIMĖJAI ═══ 💀"}
    e = discord.Embed(color=colors.get(result_type, C.NEUTRAL))
    e.title = titles.get(result_type, "🎰 Casino")
    e.description = (
        f"```\n"
        f"┌─────────────────────────┐\n"
        f"│   {line:^21}   │\n"
        f"└─────────────────────────┘\n"
        f"```"
    )
    if result_type in ("jackpot","bigwin","win"):
        e.add_field(name="💵 Laimėta",  value=f"**+{amount:,}** 🪙", inline=True)
    elif result_type == "half":
        e.add_field(name="💵 Grąžinta", value=f"**+{amount:,}** 🪙", inline=True)
    else:
        e.add_field(name="💸 Praradai", value=f"**-{amount:,}** 🪙", inline=True)
    e.add_field(name="🏦 Likutis", value=f"**{balance:,}** 🪙", inline=True)
    e.set_footer(text=ft("!casino [suma]"))
    return e

def embed_blackjack_start(player, dealer, pval, bet):
    e = discord.Embed(title="🃏 ═══ BLACKJACK ═══ 🃏", color=C.CASINO)
    e.description = f"```\nStatymas: {bet:,} 🪙\n```"
    e.add_field(name="🎴 Tavo kortelės",
                value=f"{'  '.join(f'`{c}`' for c in player)}\n**Suma: {pval}**", inline=True)
    e.add_field(name="🎭 Dileris",
                value=f"`{dealer[0]}` `🂠`\n**Suma: ?**", inline=True)
    e.add_field(name="🎮 Veiksmas",
                value="`!hit` — imti kortelę\n`!stand` — sustoti", inline=False)
    e.set_footer(text=ft())
    return e

def embed_blackjack_result(player, dealer, pval, dval, outcome, amount):
    colors = {"win":C.SUCCESS,"lose":C.ERROR,"tie":C.INFO,"blackjack":C.GOLD}
    titles = {"win":"🎉 LAIMĖJAI!","lose":"💀 PRALAIMĖJAI!","tie":"🤝 LYGIOSIOS!","blackjack":"💎 BLACKJACK!"}
    e = discord.Embed(title=titles.get(outcome,"🃏"), color=colors.get(outcome,C.NEUTRAL))
    e.add_field(name="🎴 Tavo",
                value=f"{'  '.join(f'`{c}`' for c in player)}\n**{pval}**", inline=True)
    e.add_field(name="🎭 Dileris",
                value=f"{'  '.join(f'`{c}`' for c in dealer)}\n**{dval}**", inline=True)
    if outcome in ("win","blackjack"):
        e.add_field(name="💵 Laimėta", value=f"**+{amount:,}** 🪙", inline=False)
    elif outcome == "lose":
        e.add_field(name="💸 Praradai", value=f"**-{amount:,}** 🪙", inline=False)
    else:
        e.add_field(name="🔄 Grąžinta", value=f"**{amount:,}** 🪙", inline=False)
    e.set_footer(text=ft())
    return e

def embed_trivia(question, options):
    e = discord.Embed(title="❓ ═══ TRIVIA ═══ ❓", color=C.GOLD)
    e.description = f"```\n{question}\n```"
    for opt in options:
        e.add_field(name=f"**{opt[0]}**", value=opt[3:], inline=True)
    e.set_footer(text=ft("30 sekundžių • A/B/C/D"))
    return e

# ══════════════════════════════════════════════════════════════════════════════
#  ŽVEJYBA
# ══════════════════════════════════════════════════════════════════════════════
def embed_fish(name, emoji, rarity, price, total):
    rarity_colors = {"common":C.NEUTRAL,"uncommon":C.SUCCESS,"rare":C.SAPPHIRE,"legendary":C.GOLD,"mythical":C.PURPLE,"junk":discord.Color.from_rgb(50,50,50)}
    rarity_labels = {"common":"⚪ Paprastas","uncommon":"🟢 Neįprastas","rare":"🔵 Retas","legendary":"🟡 Legendinis","mythical":"💜 Mitinis","junk":"⬛ Šiukšlė"}
    e = discord.Embed(title="🎣 ═══ Žvejyba ═══ 🎣", color=rarity_colors.get(rarity, C.NEUTRAL))
    e.description = f"```\nPagevai:\n{emoji} {name}\n```"
    e.add_field(name="⭐ Retumas",       value=f"**{rarity_labels.get(rarity,rarity)}**", inline=True)
    e.add_field(name="💰 Vertė",          value=f"**+{price}** 🪙",                        inline=True)
    e.add_field(name="🎣 Viso pagauta",   value=f"**{total}** žuvų",                        inline=True)
    e.set_footer(text=ft("!fish vėl po 30 sek."))
    return e

# ══════════════════════════════════════════════════════════════════════════════
#  MUZIKA
# ══════════════════════════════════════════════════════════════════════════════
def embed_now_playing(song, queue_len=0):
    e = discord.Embed(title="🎵 ═══ Dabar Groja ═══ 🎵", color=C.MUSIC)
    e.description = f"**[{song['title']}]({song.get('url','#')})**"
    e.add_field(name="⏱️ Trukmė",    value=song.get("duration_fmt","?"),    inline=True)
    e.add_field(name="👤 Užsakė",    value=song.get("requester","?"),        inline=True)
    e.add_field(name="📝 Eilėje",    value=f"**{queue_len}** dainų",         inline=True)
    if song.get("thumb"):
        e.set_thumbnail(url=song["thumb"])
    e.set_footer(text=ft("!skip !stop !queue !loop"))
    return e

def embed_queue(current, queue, loop):
    e = discord.Embed(title="🎵 ═══ Muzikos Eilė ═══ 🎵", color=C.MUSIC)
    if current:
        e.add_field(name="▶️ Dabar Groja",
                    value=f"**{current['title']}** ({current.get('duration_fmt','?')})", inline=False)
    if queue:
        lines = []
        for i, s in enumerate(list(queue)[:10], 1):
            lines.append(f"`{i}.` **{s['title']}** ({s.get('duration_fmt','?')})")
        if len(queue) > 10:
            lines.append(f"*...ir dar {len(queue)-10} dainų*")
        e.add_field(name="📝 Eilė", value="\n".join(lines), inline=False)
    e.set_footer(text=f"{'🔁 Loop įjungtas' if loop else '🔁 Loop išjungtas'} • {ft()}")
    return e

def embed_added_to_queue(song, pos):
    e = discord.Embed(title="📝 Pridėta į Eilę", color=C.INFO)
    e.description = f"**{song['title']}**"
    e.add_field(name="📍 Pozicija", value=f"**#{pos}**",                    inline=True)
    e.add_field(name="⏱️ Trukmė",   value=song.get("duration_fmt","?"),     inline=True)
    e.add_field(name="👤 Užsakė",   value=song.get("requester","?"),         inline=True)
    e.set_footer(text=ft())
    return e

# ══════════════════════════════════════════════════════════════════════════════
#  SVEIKINIMAS / GIVEAWAY / MISC
# ══════════════════════════════════════════════════════════════════════════════
def embed_welcome(member, member_count):
    e = discord.Embed(color=C.GOLD)
    e.set_author(name=f"👋 Naujas narys!", icon_url=member.display_avatar.url)
    e.description = (
        f"```\n"
        f"╔══════════════════════════════╗\n"
        f"║       SVEIKI ATVYKĘ! 🎉      ║\n"
        f"╚══════════════════════════════╝\n"
        f"```\n"
        f"🎉 {member.mention} prisijungė prie serverio!\n\n"
        f"Tu esi narys **#{member_count}**! 🏅\n"
        f"Naudok **`!help`** pamatyti visas komandas."
    )
    e.add_field(name="💰 Pradinis bonus", value="**+100** 🪙 automatiškai!", inline=True)
    e.set_thumbnail(url=member.display_avatar.url)
    e.set_footer(text=ft("Sveikiname!"))
    return e

def embed_giveaway(prize, minutes, end_unix, participants=0):
    e = discord.Embed(title="🎉 ═══ GIVEAWAY! ═══ 🎉", color=C.GOLD)
    e.description = (
        f"```\n"
        f"╔══════════════════════════════╗\n"
        f"║    💎 LAIMĖK MONETAS! 💎     ║\n"
        f"╚══════════════════════════════╝\n"
        f"```"
    )
    e.add_field(name="🏆 Prizas",      value=f"**{prize:,}** 🪙",         inline=True)
    e.add_field(name="⏱️ Trukmė",     value=f"**{minutes}** min.",         inline=True)
    e.add_field(name="👥 Dalyviai",    value=f"**{participants}**",         inline=True)
    e.add_field(name="⏰ Baigiasi",    value=f"<t:{end_unix}:R>",           inline=True)
    e.add_field(name="📋 Dalyvauti",   value="Spausk **🎉 Dalyvauti** žemiau!", inline=False)
    e.set_footer(text=ft("Sėkmės!"))
    return e

def embed_battle(attacker, defender, log, winner, loser, reward):
    e = discord.Embed(title="⚔️ ═══ KOVA ═══ ⚔️", color=C.GOLD if reward > 0 else C.ERROR)
    e.description = (
        f"```\n"
        f"  {attacker[:14]:^14} ⚔️ {defender[:14]:^14}\n"
        f"```\n" + "\n".join(log[-6:])
    )
    e.add_field(name="🏆 Laimėtojas",  value=f"**{winner}**",      inline=True)
    e.add_field(name="💀 Pralaimėjo",  value=f"**{loser}**",       inline=True)
    e.add_field(name="💰 Prizas",       value=f"**+{reward}** 🪙", inline=True)
    e.set_footer(text=ft())
    return e

def embed_stocks(stocks_dict):
    e = discord.Embed(title="📈 ═══ Akcijų Rinka ═══ 📈", color=C.GOLD)
    e.description = (
        f"```\n"
        f"╔══════════════════════════════╗\n"
        f"║     LIVE RINKOS DUOMENYS     ║\n"
        f"╚══════════════════════════════╝\n"
        f"```\n"
        f"**`!buystock [SYM] [n]`** pirkti  |  **`!sellstock [SYM] [n]`** parduoti"
    )
    for sym, d in stocks_dict.items():
        chg = random.uniform(-5, 5)
        trend = "📈" if chg > 0 else "📉"
        e.add_field(
            name=f"{d['emoji']} {sym}",
            value=f"**{d['price']:.2f}** 🪙\n{trend} `{chg:+.1f}%`",
            inline=True
        )
    e.set_footer(text=ft("Atsinaujina kas 5 min."))
    return e

def embed_horoscope(sign, zodiac, luck, love, work, pred):
    e = discord.Embed(
        title=f"{zodiac['emoji']} ═══ {sign.capitalize()} Horoskopas ═══ {zodiac['emoji']}",
        color=C.PURPLE
    )
    e.description = f"```\n{zodiac['dates']}\n```\n*{pred}*"
    e.add_field(name="🍀 Sėkmė",  value=stars(luck), inline=True)
    e.add_field(name="❤️ Meilė",  value=stars(love), inline=True)
    e.add_field(name="💼 Darbas", value=stars(work), inline=True)
    e.set_footer(text=ft("Dienos horoskopas"))
    return e

def embed_achievements(member, achievements, achieved_list):
    done = len([a for a in achievements if a in achieved_list])
    total = len(achievements)
    bar = pb(done, total)
    e = discord.Embed(title=f"🏆 ═══ {member.display_name} Pasiekimai ═══ 🏆", color=C.GOLD)
    e.description = (
        f"```\n"
        f"  Pasiekta: {done}/{total}\n"
        f"  {bar}\n"
        f"```"
    )
    for ach_id, ach in achievements.items():
        status = "✅" if ach_id in achieved_list else "🔒"
        e.add_field(
            name=f"{status} {ach['emoji']} {ach['name']}",
            value=f"*{ach['desc']}*\n💰 +{ach['reward']:,} 🪙",
            inline=True
        )
    e.set_thumbnail(url=member.display_avatar.url)
    e.set_footer(text=ft())
    return e

def embed_referral(member, referred, bonus):
    e = discord.Embed(title="🤝 Referral Bonus!", color=C.GOLD)
    e.description = (
        f"**{member.display_name}** pakvietė **{referred.display_name}**!\n\n"
        f"Abu gavo **+{bonus:,}** 🪙! 🎉"
    )
    e.set_footer(text=ft())
    return e

def embed_vip(member, perks):
    e = discord.Embed(title="💎 VIP Statusas", color=C.GOLD)
    e.set_author(name=member.display_name, icon_url=member.display_avatar.url)
    e.description = (
        f"```\n"
        f"╔══════════════════════════╗\n"
        f"║    💎 VIP NARYS 💎       ║\n"
        f"╚══════════════════════════╝\n"
        f"```"
    )
    for perk in perks:
        e.add_field(name=perk["name"], value=perk["desc"], inline=True)
    e.set_footer(text=ft())
    return e

def embed_webhook_order(order, guild_name):
    e = discord.Embed(title=f"🛍️ Naujas Užsakymas! #{order['id']:04d}", color=C.WARNING)
    e.add_field(name="📦 Produktas",  value=order["product_name"],         inline=True)
    e.add_field(name="👤 Pirkėjas",   value=order["username"],              inline=True)
    e.add_field(name="💰 Suma",        value=f"{order['price']}€",          inline=True)
    e.add_field(name="📋 Statusas",    value="⏳ Laukiama apmokėjimo",      inline=True)
    e.add_field(name="🏠 Serveris",    value=guild_name,                    inline=True)
    e.set_footer(text=ft("!complete [ID] užbaigti"))
    return e

def embed_mod_log(action, target, mod, reason, color):
    e = discord.Embed(title=f"🛡️ Moderavimas — {action}", color=color)
    e.add_field(name="👤 Narys",       value=f"{target.mention}\n`{target.id}`", inline=True)
    e.add_field(name="🔨 Moderatorius",value=mod.mention,                         inline=True)
    e.add_field(name="📋 Priežastis",  value=reason,                              inline=False)
    e.set_thumbnail(url=target.display_avatar.url)
    e.set_footer(text=ft("Moderavimo log"))
    return e
