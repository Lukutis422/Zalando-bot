# -*- coding: utf-8 -*-
"""
KODAS BOT V7 — Pirkimo per Ticket Sistema
Paspaudžia produktą → automatinis ticket → pasirenka mokėjimą → staff patvirtina → gauna į DM
"""
import discord
from discord import ui
import time
import asyncio
import datetime
from designs_v6 import C, ft, TICKET_CATEGORIES_V2

# ══════════════════════════════════════════════════════════════════════════════
#  MOKĖJIMO METODŲ MYGTUKAI
# ══════════════════════════════════════════════════════════════════════════════
PAY_META = {
    "revolut":  {"icon": "💜", "label": "Revolut",         "color": discord.ButtonStyle.blurple},
    "paypal":   {"icon": "💙", "label": "PayPal",           "color": discord.ButtonStyle.blurple},
    "crypto":   {"icon": "🪙", "label": "Crypto",           "color": discord.ButtonStyle.grey},
    "bankas":   {"icon": "🏦", "label": "Banko pavedimas",  "color": discord.ButtonStyle.grey},
    "paysera":  {"icon": "🟢", "label": "Paysera",          "color": discord.ButtonStyle.green},
}

class PaymentMethodButton(ui.Button):
    def __init__(self, method: str, details: str, order_id: int, price: float):
        meta = PAY_META.get(method, {"icon": "💳", "label": method, "color": discord.ButtonStyle.grey})
        super().__init__(
            label=f"{meta['icon']} {meta['label']}",
            style=meta["color"],
            custom_id=f"pay_{method}_{order_id}"
        )
        self.method = method
        self.details = details
        self.order_id = order_id
        self.price = price
        self.meta = meta

    async def callback(self, interaction: discord.Interaction):
        # Siųsti privačią žinutę su mokėjimo duomenimis
        e = discord.Embed(
            title=f"{self.meta['icon']} Mokėjimas per {self.meta['label']}",
            color=C.GOLD
        )
        e.description = (
            f"```\n"
            f"╔══════════════════════════════╗\n"
            f"║    MOKĖJIMO INSTRUKCIJA      ║\n"
            f"╚══════════════════════════════╝\n"
            f"```"
        )
        e.add_field(
            name="💳 Mokėjimo duomenys",
            value=f"```\n{self.details}\n```",
            inline=False
        )
        e.add_field(name="💰 Suma",           value=f"**{self.price}€**",        inline=True)
        e.add_field(name="📋 Užsakymo nr.",   value=f"`#{self.order_id:04d}`",    inline=True)
        e.add_field(
            name="📋 Žingsniai",
            value=(
                f"**1.** Perveskite **{self.price}€** aukščiau nurodytais duomenimis\n"
                f"**2.** Pervedimo apraše nurodykite: `#{self.order_id:04d}`\n"
                f"**3.** Įkelkite mokėjimo screenshot'ą šiame kanale\n"
                f"**4.** Staff patikrins ir suaktyvins prenumeratą! ✅"
            ),
            inline=False
        )
        e.set_footer(text=ft(f"#{self.order_id:04d} • {self.meta['label']}"))

        # Pakeisti mygtukų stilių — paryškintas pasirinktas
        for item in self.view.children:
            if isinstance(item, ui.Button):
                item.style = discord.ButtonStyle.secondary
                item.disabled = False
        self.style = discord.ButtonStyle.green
        self.disabled = False

        try:
            await interaction.response.edit_message(view=self.view)
            await interaction.followup.send(embed=e, ephemeral=True)
        except Exception:
            await interaction.response.send_message(embed=e, ephemeral=True)


class PaymentSelectView(ui.View):
    def __init__(self, methods: dict, order_id: int, price: float):
        super().__init__(timeout=3600)
        self.order_id = order_id
        row = 0
        for i, (method, details) in enumerate(methods.items()):
            btn = PaymentMethodButton(method, details, order_id, price)
            btn.row = i // 3
            self.add_item(btn)

    async def on_timeout(self):
        for item in self.children:
            item.disabled = True


# ══════════════════════════════════════════════════════════════════════════════
#  STAFF PATVIRTINIMO MYGTUKAI
# ══════════════════════════════════════════════════════════════════════════════
class StaffOrderView(ui.View):
    def __init__(self, order_id: int, user_id: int, product_name: str, delivery_channel_id: int = None):
        super().__init__(timeout=None)
        self.order_id = order_id
        self.user_id = user_id
        self.product_name = product_name
        self.delivery_channel_id = delivery_channel_id

    @ui.button(label="✅ Patvirtinti ir pristatyti", style=discord.ButtonStyle.green, custom_id="order_approve")
    async def approve(self, interaction: discord.Interaction, button: ui.Button):
        if not interaction.user.guild_permissions.manage_channels:
            await interaction.response.send_message("Tik staff gali patvirtinti!", ephemeral=True)
            return

        modal = DeliveryModal(self.order_id, self.user_id, self.product_name)
        await interaction.response.send_modal(modal)

    @ui.button(label="❌ Atmesti", style=discord.ButtonStyle.red, custom_id="order_reject")
    async def reject(self, interaction: discord.Interaction, button: ui.Button):
        if not interaction.user.guild_permissions.manage_channels:
            await interaction.response.send_message("Tik staff gali atmesti!", ephemeral=True)
            return

        modal = RejectModal(self.order_id, self.user_id, self.product_name)
        await interaction.response.send_modal(modal)

    @ui.button(label="⏳ Laukiama patikrinimo", style=discord.ButtonStyle.grey, custom_id="order_pending", disabled=True)
    async def pending(self, interaction: discord.Interaction, button: ui.Button):
        pass


class DeliveryModal(ui.Modal, title="📦 Pristatymo informacija"):
    delivery_info = ui.TextInput(
        label="Prisijungimo duomenys / informacija",
        style=discord.TextStyle.paragraph,
        placeholder="El. paštas: example@email.com\nSlaptažodis: ********\nArba kita reikalinga informacija...",
        max_length=1500
    )
    note = ui.TextInput(
        label="Pastaba klientui (neprivaloma)",
        required=False,
        placeholder="Pvz: Prenumerata aktyvuota! Džiaukitės!",
        max_length=500
    )

    def __init__(self, order_id, user_id, product_name):
        super().__init__()
        self.order_id = order_id
        self.user_id = user_id
        self.product_name = product_name

    async def on_submit(self, interaction: discord.Interaction):
        # Siųsti pristatymą klientui į DM
        member = interaction.guild.get_member(self.user_id)
        delivery_embed = discord.Embed(
            title="🎉 Tavo užsakymas pristatytas!",
            color=C.GOLD
        )
        delivery_embed.description = (
            f"```\n"
            f"╔══════════════════════════════════╗\n"
            f"║   ✅ PRENUMERATA SUAKTYVINTA! ✅  ║\n"
            f"╚══════════════════════════════════╝\n"
            f"```"
        )
        delivery_embed.add_field(
            name="📦 Produktas",
            value=f"**{self.product_name}**",
            inline=True
        )
        delivery_embed.add_field(
            name="📋 Užsakymo nr.",
            value=f"`#{self.order_id:04d}`",
            inline=True
        )
        delivery_embed.add_field(
            name="🔑 Prisijungimo informacija",
            value=f"```\n{self.delivery_info.value}\n```",
            inline=False
        )
        if self.note.value:
            delivery_embed.add_field(
                name="📝 Pastaba",
                value=self.note.value,
                inline=False
            )
        delivery_embed.add_field(
            name="⚠️ Svarbu",
            value=(
                "• Niekada nesidalinkite šia informacija su kitais\n"
                "• Pakeiskite slaptažodį jei įmanoma\n"
                "• Iškilus problemoms — sukurkite ticket"
            ),
            inline=False
        )
        delivery_embed.set_footer(text=ft("Ačiū už pirkimą! 🙏"))

        sent = False
        if member:
            try:
                await member.send(embed=delivery_embed)
                sent = True
            except discord.Forbidden:
                pass

        # Atnaujinti ticket embed
        confirm_embed = discord.Embed(
            title="✅ Užsakymas įvykdytas!",
            color=C.SUCCESS
        )
        confirm_embed.add_field(name="📦 Produktas",   value=self.product_name,                inline=True)
        confirm_embed.add_field(name="👤 Klientas",    value=f"<@{self.user_id}>",             inline=True)
        confirm_embed.add_field(name="✉️ DM Išsiųsta", value="✅ Taip" if sent else "❌ Nepavyko (DM uždarytos)", inline=True)
        confirm_embed.add_field(name="👮 Staff",       value=interaction.user.mention,          inline=True)
        confirm_embed.set_footer(text=ft())

        # Atnaujinti mygtukus — išjungti
        for item in interaction.message.components:
            pass  # Disable handled below

        await interaction.response.send_message(embed=confirm_embed)

        if not sent and member:
            # Pabandyti parašyti į kanalą
            await interaction.channel.send(
                f"{member.mention} ⬆️ Tavo prisijungimo informacija yra aukščiau esančioje žinutėje!",
                embed=delivery_embed
            )


class RejectModal(ui.Modal, title="❌ Atmetimo priežastis"):
    reason = ui.TextInput(
        label="Atmetimo priežastis",
        placeholder="Pvz: Mokėjimas nepatvirtintas, neatitinka sumos...",
        max_length=500
    )

    def __init__(self, order_id, user_id, product_name):
        super().__init__()
        self.order_id = order_id
        self.user_id = user_id
        self.product_name = product_name

    async def on_submit(self, interaction: discord.Interaction):
        member = interaction.guild.get_member(self.user_id)

        reject_embed = discord.Embed(
            title="❌ Užsakymas atmestas",
            color=C.ERROR
        )
        reject_embed.add_field(name="📦 Produktas",     value=self.product_name,       inline=True)
        reject_embed.add_field(name="📋 Užsakymo nr.", value=f"`#{self.order_id:04d}`", inline=True)
        reject_embed.add_field(name="❌ Priežastis",    value=self.reason.value,        inline=False)
        reject_embed.add_field(
            name="ℹ️ Ką daryti?",
            value="Jei manote, kad tai klaida — sukurkite naują ticket.",
            inline=False
        )
        reject_embed.set_footer(text=ft())

        if member:
            try:
                await member.send(embed=reject_embed)
            except discord.Forbidden:
                pass

        await interaction.response.send_message(
            embed=discord.Embed(
                description=f"❌ Užsakymas **#{self.order_id:04d}** atmestas. Klientas informuotas.",
                color=C.ERROR
            )
        )


# ══════════════════════════════════════════════════════════════════════════════
#  PIRKIMO MODALAS (kai paspaudžia "Pirkti")
# ══════════════════════════════════════════════════════════════════════════════
class PurchaseConfirmModal(ui.Modal, title="🛍️ Patvirtinti pirkimą"):
    def __init__(self, product, guild, payment_methods, bot):
        super().__init__()
        self.product = product
        self.guild = guild
        self.payment_methods = payment_methods
        self.bot = bot

    note = ui.TextInput(
        label="Pastaba (neprivaloma)",
        required=False,
        placeholder="Pvz: Noriu 1 mėn. prenumeratos...",
        max_length=300
    )

    async def on_submit(self, interaction: discord.Interaction):
        from database import create_order, create_ticket, update_order, update_ticket, get_settings, get_db

        guild = interaction.guild
        member = interaction.user
        product = self.product

        # Sukurti užsakymą DB (su produkto sinchronizavimu)
        # Įsitikinti kad produktas yra DB
        try:
            with get_db() as _conn:
                _conn.execute(
                    """INSERT OR IGNORE INTO products
                       (id, guild_id, name, description, price, old_price, category, emoji, duration, stock)
                       VALUES (?,?,?,?,?,?,?,?,?,?)""",
                    (product["id"], str(guild.id), product["name"],
                     product.get("desc", product.get("description","")),
                     product["price"], product.get("old_price"),
                     product.get("category","other"), product.get("emoji","📦"),
                     product.get("duration","1 men."), product.get("stock",99))
                )
        except Exception: pass

        order_id = create_order(
            guild.id, member.id, member.display_name, {
                "id": product["id"],
                "name": product["name"],
                "duration": product.get("duration","1 men."),
                "price": product["price"]
            }
        )

        # Patikrinti ar yra automatinis pristatymas
        from database import get_auto_delivery, mark_delivery_used, create_subscription, get_db as _get_db
        auto_del = get_auto_delivery(guild.id, product["id"])

        # Sukurti privatų kanalą
        categ = discord.utils.get(guild.categories, name="🛍️ Užsakymai")
        if not categ:
            try:
                categ = await guild.create_category("🛍️ Užsakymai")
            except Exception:
                categ = None

        settings = get_settings(guild.id)
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(view_channel=False),
            member: discord.PermissionOverwrite(
                view_channel=True, send_messages=True,
                read_message_history=True, attach_files=True
            ),
            guild.me: discord.PermissionOverwrite(
                view_channel=True, send_messages=True,
                manage_channels=True, manage_messages=True
            ),
        }
        # Support rolė
        support_role_id = settings.get("support_role")
        if support_role_id:
            role = guild.get_role(int(support_role_id))
            if role:
                overwrites[role] = discord.PermissionOverwrite(
                    view_channel=True, send_messages=True
                )
        # Admins
        for role in guild.roles:
            if role.permissions.administrator:
                overwrites[role] = discord.PermissionOverwrite(view_channel=True, send_messages=True)

        try:
            ch_name = f"🛍️-užsakymas-{order_id:04d}"
            order_ch = await guild.create_text_channel(
                ch_name, category=categ, overwrites=overwrites,
                topic=f"Užsakymas #{order_id:04d} | {product['name']} | {member.display_name}"
            )

            # Atnaujinti order DB
            update_order(guild.id, order_id, channel_id=str(order_ch.id))

            # ── TICKET ID ──
            from database import create_ticket as ct
            ticket_id = ct(
                guild.id, order_ch.id, member.id, member.display_name,
                "shop", f"Užsakymas #{order_id:04d} — {product['name']}",
                f"{product['name']} ({product['duration']}) — {product['price']}€\n\n{self.note.value or 'Nėra pastabų'}",
                "normal", order_id
            )

            # ── UŽSAKYMO EMBED ──
            order_embed = discord.Embed(
                title=f"🛍️ Užsakymas #{order_id:04d}",
                color=C.SHOP
            )
            order_embed.description = (
                f"```\n"
                f"┌──────────────────────────────────┐\n"
                f"│  {product['emoji']} {product['name'][:28]:<28}│\n"
                f"│  {product['duration']:<15} │  {product['price']}€{'':>12}│\n"
                f"└──────────────────────────────────┘\n"
                f"```"
            )
            order_embed.add_field(name="👤 Pirkėjas",   value=member.mention,           inline=True)
            order_embed.add_field(name="📋 Statusas",   value="⏳ Laukiama apmokėjimo", inline=True)
            order_embed.add_field(name="🎫 Ticket",     value=f"#{ticket_id:04d}",       inline=True)
            if self.note.value:
                order_embed.add_field(name="📝 Pastaba", value=self.note.value, inline=False)
            order_embed.set_thumbnail(url=member.display_avatar.url)
            order_embed.set_footer(text=ft(f"#{order_id:04d}"))

            await order_ch.send(content=member.mention, embed=order_embed)

            # ── MOKĖJIMO PASIRINKIMAS ──
            if self.payment_methods:
                pay_embed = discord.Embed(
                    title="💳 Pasirink mokėjimo būdą",
                    color=C.GOLD
                )
                pay_embed.description = (
                    f"Užsakymo suma: **{product['price']}€**  •  Nr. `#{order_id:04d}`\n\n"
                    f"Spausk norimo mokėjimo būdo mygtuką — gausi tikslias instrukcijas.\n"
                    f"Po apmokėjimo **įkelk screenshot'ą** šiame kanale. ⬇️"
                )
                pay_embed.set_footer(text=ft("Pasirink mokėjimo būdą"))

                await order_ch.send(
                    embed=pay_embed,
                    view=PaymentSelectView(self.payment_methods, order_id, product["price"])
                )

                # ── STAFF PATVIRTINIMO ZONA ──
                staff_embed = discord.Embed(
                    title="⚙️ Staff — Užsakymo valdymas",
                    color=C.INFO
                )
                staff_embed.description = (
                    f"**Klientas:** {member.mention}\n"
                    f"**Produktas:** {product['emoji']} {product['name']}\n"
                    f"**Suma:** **{product['price']}€**\n\n"
                    f"Kai klientas įkels mokėjimo screenshot'ą — patvirtinkite ir pristatykite."
                )
                staff_embed.set_footer(text=ft("Staff valdymas"))

                await order_ch.send(
                    embed=staff_embed,
                    view=StaffOrderView(order_id, member.id, product["name"], order_ch.id)
                )

            else:
                # Nėra mokėjimo metodų
                no_pay = discord.Embed(
                    description="⚠️ Mokėjimo būdai nenustatyti. Susisiek su administratoriumi tiesiogiai.",
                    color=C.WARNING
                )
                await order_ch.send(embed=no_pay)

            # ── PATVIRTINIMAS VARTOTOJUI ──
            confirm = discord.Embed(
                title="✅ Užsakymas sukurtas!",
                description=(
                    f"Eik į {order_ch.mention} — ten rasi mokėjimo instrukcijas.\n\n"
                    f"**Produktas:** {product['emoji']} {product['name']}\n"
                    f"**Suma:** {product['price']}€\n"
                    f"**Užsakymo nr.:** `#{order_id:04d}`"
                ),
                color=C.SUCCESS
            )
            confirm.set_footer(text=ft())
            await interaction.response.send_message(embed=confirm, ephemeral=True)

        except discord.Forbidden:
            await interaction.response.send_message(
                "❌ Neturiu teisių sukurti kanalo! Susisiek su administratoriumi.",
                ephemeral=True
            )
        except Exception as ex:
            await interaction.response.send_message(
                f"❌ Klaida: {ex}",
                ephemeral=True
            )


# ══════════════════════════════════════════════════════════════════════════════
#  PARDUOTUVĖS PANEL SU MYGTUKAIS
# ══════════════════════════════════════════════════════════════════════════════
class ShopProductButton(ui.Button):
    def __init__(self, product: dict, payment_methods: dict, bot):
        stk = "🟢" if product.get("stock", 0) > 0 else "🔴"
        super().__init__(
            label=f"{stk} {product['emoji']} {product['name']} — {product['price']}€",
            style=discord.ButtonStyle.blurple if product.get("stock", 0) > 0 else discord.ButtonStyle.grey,
            custom_id=f"shop_buy_{product['id']}",
            row=product.get("row", 0)
        )
        self.product = product
        self.payment_methods = payment_methods
        self.bot_ref = bot

    async def callback(self, interaction: discord.Interaction):
        if self.product.get("stock", 0) <= 0:
            await interaction.response.send_message(
                "❌ Šis produktas šiuo metu nepasiekiamas!", ephemeral=True
            )
            return

        modal = PurchaseConfirmModal(
            self.product,
            interaction.guild,
            self.payment_methods,
            self.bot_ref
        )
        await interaction.response.send_modal(modal)


class ShopPanelView(ui.View):
    def __init__(self, products: list, payment_methods: dict, bot):
        super().__init__(timeout=None)
        for i, product in enumerate(products[:20]):  # Max 20 mygtukų
            product["row"] = i // 5  # 5 mygtukų per eilutę
            btn = ShopProductButton(product, payment_methods, bot)
            self.add_item(btn)


def build_shop_embed(guild_name: str, products: list, payment_methods: dict) -> discord.Embed:
    e = discord.Embed(color=C.SHOP)
    e.set_author(name=f"🛍️ {guild_name} — Prenumeratų Parduotuvė")
    e.description = (
        f"```\n"
        f"╔══════════════════════════════════════╗\n"
        f"║      💎 PREMIUM PRENUMERATOS 💎       ║\n"
        f"╚══════════════════════════════════════╝\n"
        f"```\n"
        f"✅ Greitas pristatymas  •  🔒 Saugus pirkimas\n"
        f"💬 24/7 Pagalba  •  🔄 Grąžinimo garantija\n\n"
        f"**Spausk produkto mygtuką žemiau norėdamas pirkti! ↓**"
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
            disc = ""
            if p.get("old_price"):
                pct = int((1 - p["price"] / p["old_price"]) * 100)
                disc = f"🏷️ `-{pct}%`"
            lines.append(
                f"{stk} **{p['emoji']} {p['name']}** — {p['duration']}\n"
                f"　{old}**{p['price']}€** {disc}\n"
                f"　*{p.get('description', p.get('desc', ''))}*"
            )
        e.add_field(name=f"{emoji} {cat_name}", value="\n".join(lines), inline=False)

    if payment_methods:
        pay_icons = {"revolut":"💜","paypal":"💙","crypto":"🪙","bankas":"🏦","paysera":"🟢"}
        pay_str = "  ".join(f"{pay_icons.get(k,'💳')} {k.capitalize()}" for k in payment_methods)
        e.add_field(name="💳 Priimami mokėjimai", value=pay_str, inline=False)

    e.set_footer(text=ft("Spausk mygtuką pirkti ↓"))
    return e


# ══════════════════════════════════════════════════════════════════════════════
#  STAFF NOTIFICATIONS (kai gaunamas naujas užsakymas)
# ══════════════════════════════════════════════════════════════════════════════
async def notify_staff(guild, order_id, product, member, channel, settings):
    """Pranešti staff kanalui apie naują užsakymą"""
    staff_ch_id = settings.get("webhook_channel") or settings.get("log_channel")
    if not staff_ch_id:
        return

    staff_ch = guild.get_channel(int(staff_ch_id))
    if not staff_ch:
        return

    e = discord.Embed(
        title="🔔 Naujas Užsakymas!",
        color=C.WARNING
    )
    e.add_field(name="📦 Produktas",    value=f"{product['emoji']} {product['name']} ({product['duration']})", inline=True)
    e.add_field(name="👤 Klientas",    value=member.mention,                                                   inline=True)
    e.add_field(name="💰 Suma",         value=f"**{product['price']}€**",                                      inline=True)
    e.add_field(name="📋 Užsakymas",   value=f"`#{order_id:04d}`",                                            inline=True)
    e.add_field(name="📂 Kanalas",     value=channel.mention,                                                  inline=True)
    e.set_thumbnail(url=member.display_avatar.url)
    e.set_footer(text=ft("Naujas užsakymas!"))

    await staff_ch.send(embed=e)


# ══════════════════════════════════════════════════════════════════════════════
#  POKER ŽAIDIMAS
# ══════════════════════════════════════════════════════════════════════════════
POKER_HANDS = [
    "Royal Flush", "Straight Flush", "Four of a Kind", "Full House",
    "Flush", "Straight", "Three of a Kind", "Two Pair", "One Pair", "High Card"
]

class PokerGame:
    def __init__(self, players: list, bet: int):
        self.players = players  # [(user_id, display_name)]
        self.bet = bet
        self.deck = self._make_deck()
        self.player_hands = {}
        self.community = []
        self.pot = bet * len(players)
        self.phase = "preflop"  # preflop, flop, turn, river, showdown
        self.folded = set()
        self.current_bet = bet
        self._deal()

    def _make_deck(self):
        suits = ["♠","♥","♦","♣"]
        ranks = ["2","3","4","5","6","7","8","9","10","J","Q","K","A"]
        deck = [f"{r}{s}" for r in ranks for s in suits]
        import random; random.shuffle(deck)
        return deck

    def _deal(self):
        for uid, _ in self.players:
            self.player_hands[uid] = [self.deck.pop(), self.deck.pop()]

    def next_phase(self):
        if self.phase == "preflop":
            self.community = [self.deck.pop() for _ in range(3)]
            self.phase = "flop"
        elif self.phase == "flop":
            self.community.append(self.deck.pop())
            self.phase = "turn"
        elif self.phase == "turn":
            self.community.append(self.deck.pop())
            self.phase = "river"
        elif self.phase == "river":
            self.phase = "showdown"
        return self.phase

    def hand_display(self, uid):
        hand = self.player_hands.get(uid, [])
        return " ".join(f"`{c}`" for c in hand)

    def community_display(self):
        return " ".join(f"`{c}`" for c in self.community) if self.community else "*Neatidengtos*"

    def evaluate_hand(self, hand):
        """Paprastas hand evaluator (demo)"""
        import random
        return random.choice(POKER_HANDS[4:])  # Random hand nuo flush žemyn

    def get_winner(self):
        active = [(uid, name) for uid, name in self.players if uid not in self.folded]
        if len(active) == 1:
            return active[0]
        # Evaluate hands
        best = None; best_idx = 0
        for uid, name in active:
            hand = self.player_hands[uid] + self.community
            rank = self.evaluate_hand(hand)
            idx = POKER_HANDS.index(rank)
            if best is None or idx < best_idx:
                best = (uid, name, rank); best_idx = idx
        return best


class PokerView(ui.View):
    def __init__(self, game: PokerGame, channel_id: int):
        super().__init__(timeout=300)
        self.game = game
        self.channel_id = channel_id
        self.current_player_idx = 0
        self.actions_this_round = {}

    def current_player(self):
        active = [(uid,n) for uid,n in self.game.players if uid not in self.game.folded]
        if not active: return None
        return active[self.current_player_idx % len(active)]

    @ui.button(label="✅ Check/Call", style=discord.ButtonStyle.green, custom_id="poker_call")
    async def call(self, interaction: discord.Interaction, button: ui.Button):
        cp = self.current_player()
        if not cp or interaction.user.id != cp[0]:
            await interaction.response.send_message("Ne tavo eilė!", ephemeral=True); return
        self.actions_this_round[cp[0]] = "call"
        self.current_player_idx += 1
        await self._check_round_end(interaction)

    @ui.button(label="📈 Raise", style=discord.ButtonStyle.blurple, custom_id="poker_raise")
    async def raise_btn(self, interaction: discord.Interaction, button: ui.Button):
        cp = self.current_player()
        if not cp or interaction.user.id != cp[0]:
            await interaction.response.send_message("Ne tavo eilė!", ephemeral=True); return
        self.game.pot += self.game.bet
        self.game.current_bet = int(self.game.current_bet * 1.5)
        self.actions_this_round[cp[0]] = "raise"
        self.current_player_idx += 1
        await self._check_round_end(interaction)

    @ui.button(label="❌ Fold", style=discord.ButtonStyle.red, custom_id="poker_fold")
    async def fold(self, interaction: discord.Interaction, button: ui.Button):
        cp = self.current_player()
        if not cp or interaction.user.id != cp[0]:
            await interaction.response.send_message("Ne tavo eilė!", ephemeral=True); return
        self.game.folded.add(cp[0])
        self.actions_this_round[cp[0]] = "fold"
        await self._check_round_end(interaction)

    async def _check_round_end(self, interaction):
        active = [(uid,n) for uid,n in self.game.players if uid not in self.game.folded]

        # Visi padarė veiksmus arba liko 1
        if len(active) <= 1 or all(uid in self.actions_this_round for uid,_ in active):
            phase = self.game.next_phase()
            self.actions_this_round = {}
            self.current_player_idx = 0

            if phase == "showdown" or len(active) <= 1:
                winner = self.game.get_winner()
                e = discord.Embed(title="🃏 ═══ POKERIS — PABAIGA ═══ 🃏", color=C.GOLD)
                e.description = f"```\nBendros kortelės: {self.game.community_display()}\n```"
                for uid, name in active:
                    e.add_field(
                        name=f"{'🏆' if uid == winner[0] else '👤'} {name}",
                        value=f"Rankoje: {self.game.hand_display(uid)}\n{self.game.evaluate_hand([])}",
                        inline=True
                    )
                e.add_field(name="🏆 Laimėtojas", value=f"**{winner[1]}**", inline=False)
                e.add_field(name="💰 Prizas",     value=f"**{self.game.pot:,}** 🪙", inline=True)
                for item in self.children: item.disabled = True
                await interaction.response.edit_message(embed=e, view=self)
                return

        # Tęsti žaidimą
        cp = self.current_player()
        e = discord.Embed(title="🃏 ═══ POKERIS ═══ 🃏", color=C.CASINO)
        e.add_field(name="🎴 Bendros kortelės", value=self.game.community_display(), inline=False)
        e.add_field(name="💰 Puodas", value=f"**{self.game.pot:,}** 🪙", inline=True)
        e.add_field(name="📋 Fazė",   value=f"**{self.game.phase.upper()}**", inline=True)
        if cp:
            e.add_field(name="⏳ Eilė", value=f"**{cp[1]}**", inline=True)
        await interaction.response.edit_message(embed=e, view=self)


# ══════════════════════════════════════════════════════════════════════════════
#  TURNYRŲ SISTEMA
# ══════════════════════════════════════════════════════════════════════════════
class TournamentView(ui.View):
    def __init__(self, tournament_id: int, game_type: str):
        super().__init__(timeout=None)
        self.tournament_id = tournament_id
        self.game_type = game_type

    @ui.button(label="🎮 Registruotis", style=discord.ButtonStyle.green, custom_id="tournament_join")
    async def join(self, interaction: discord.Interaction, button: ui.Button):
        from database import join_tournament
        success = join_tournament(self.tournament_id, interaction.user.id)
        if success:
            await interaction.response.send_message(
                f"✅ Užsiregistravai į turnyrą! Laukk pradžios.", ephemeral=True
            )
        else:
            await interaction.response.send_message(
                "❌ Jau užsiregistravai arba registracija baigėsi!", ephemeral=True
            )

    @ui.button(label="🚀 Pradėti", style=discord.ButtonStyle.blurple, custom_id="tournament_start")
    async def start(self, interaction: discord.Interaction, button: ui.Button):
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("Tik adminai gali pradėti!", ephemeral=True); return
        from database import get_tournament, start_tournament
        t = get_tournament(self.tournament_id)
        if not t:
            await interaction.response.send_message("Turnyras nerastas!", ephemeral=True); return
        if len(t["participants"]) < 2:
            await interaction.response.send_message(
                "Reikia bent 2 dalyvių!", ephemeral=True
            ); return
        bracket = start_tournament(self.tournament_id)
        e = discord.Embed(title=f"🏆 {t['name']} — PRADĖTAS!", color=C.GOLD)
        e.description = f"**Dalyviai:** {len(t['participants'])}\n**Prizas:** {t['prize']:,} 🪙"
        round_txt = ""
        for match in bracket["rounds"][0]:
            p1 = interaction.guild.get_member(int(match["p1"]))
            p2_id = match["p2"]
            if p2_id == "bye":
                round_txt += f"• {p1.display_name if p1 else '?'} — **BYE** (automatiškai tęsiasi)\n"
            else:
                p2 = interaction.guild.get_member(int(p2_id))
                round_txt += f"• {p1.display_name if p1 else '?'} ⚔️ {p2.display_name if p2 else '?'}\n"
        e.add_field(name="📋 1 Ratas", value=round_txt, inline=False)
        button.disabled = True
        await interaction.response.edit_message(embed=e, view=self)
