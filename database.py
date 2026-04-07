# -*- coding: utf-8 -*-
"""
KODAS BOT V7 — SQLite Duomenų Bazė
Greita, patikima, be JSON problemų
"""
import sqlite3
import json
import os
import pathlib
import time

DB_PATH = str(pathlib.Path(__file__).parent / "kodas_bot.db")

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn

def init_db():
    """Sukurti visas lenteles"""
    with get_db() as conn:
        conn.executescript("""
        -- Narių duomenys
        CREATE TABLE IF NOT EXISTS members (
            guild_id TEXT NOT NULL,
            user_id  TEXT NOT NULL,
            coins    INTEGER DEFAULT 0,
            xp       INTEGER DEFAULT 0,
            rep      INTEGER DEFAULT 0,
            streak   INTEGER DEFAULT 0,
            last_daily    REAL DEFAULT 0,
            last_work     REAL DEFAULT 0,
            last_rep      REAL DEFAULT 0,
            last_fish     REAL DEFAULT 0,
            last_rob      REAL DEFAULT 0,
            work_count    INTEGER DEFAULT 0,
            fish_count    INTEGER DEFAULT 0,
            casino_wins   INTEGER DEFAULT 0,
            message_count INTEGER DEFAULT 0,
            voice_minutes INTEGER DEFAULT 0,
            birthday      TEXT DEFAULT NULL,
            referral_used INTEGER DEFAULT 0,
            is_vip        INTEGER DEFAULT 0,
            bank_balance  INTEGER DEFAULT 0,
            loan_amount   INTEGER DEFAULT 0,
            loan_due      REAL DEFAULT 0,
            PRIMARY KEY (guild_id, user_id)
        );

        -- Perspėjimai
        CREATE TABLE IF NOT EXISTS warnings (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            guild_id   TEXT NOT NULL,
            user_id    TEXT NOT NULL,
            reason     TEXT NOT NULL,
            mod_id     TEXT NOT NULL,
            mod_name   TEXT NOT NULL,
            created_at REAL DEFAULT (unixepoch())
        );

        -- Produktai (parduotuvė)
        CREATE TABLE IF NOT EXISTS products (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            guild_id   TEXT NOT NULL,
            name       TEXT NOT NULL,
            description TEXT DEFAULT '',
            price      REAL NOT NULL,
            old_price  REAL DEFAULT NULL,
            category   TEXT DEFAULT 'other',
            emoji      TEXT DEFAULT '📦',
            duration   TEXT DEFAULT '1 mėn.',
            stock      INTEGER DEFAULT 99,
            active     INTEGER DEFAULT 1
        );

        -- Užsakymai
        CREATE TABLE IF NOT EXISTS orders (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            guild_id     TEXT NOT NULL,
            user_id      TEXT NOT NULL,
            username     TEXT NOT NULL,
            product_id   INTEGER NOT NULL,
            product_name TEXT NOT NULL,
            duration     TEXT NOT NULL,
            price        REAL NOT NULL,
            status       TEXT DEFAULT 'laukiama',
            channel_id   TEXT DEFAULT NULL,
            ticket_id    TEXT DEFAULT NULL,
            created_at   REAL DEFAULT (unixepoch()),
            completed_at REAL DEFAULT NULL,
            delivery_info TEXT DEFAULT NULL,
            FOREIGN KEY (product_id) REFERENCES products(id)
        );

        -- Serverio nustatymai
        CREATE TABLE IF NOT EXISTS guild_settings (
            guild_id         TEXT PRIMARY KEY,
            log_channel      TEXT DEFAULT NULL,
            welcome_channel  TEXT DEFAULT NULL,
            auto_role        TEXT DEFAULT NULL,
            support_role     TEXT DEFAULT NULL,
            vip_role         TEXT DEFAULT NULL,
            daily_channel    TEXT DEFAULT NULL,
            webhook_channel  TEXT DEFAULT NULL,
            captcha_enabled  INTEGER DEFAULT 0,
            anti_raid        INTEGER DEFAULT 1,
            ai_moderation    INTEGER DEFAULT 0,
            blacklist        TEXT DEFAULT '[]',
            payment_methods  TEXT DEFAULT '{}',
            level_rewards    TEXT DEFAULT '{}',
            prefix           TEXT DEFAULT '!'
        );

        -- Tickets
        CREATE TABLE IF NOT EXISTS tickets (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            guild_id     TEXT NOT NULL,
            channel_id   TEXT NOT NULL,
            user_id      TEXT NOT NULL,
            user_name    TEXT NOT NULL,
            category     TEXT DEFAULT 'support',
            subject      TEXT NOT NULL,
            description  TEXT DEFAULT '',
            priority     TEXT DEFAULT 'normal',
            status       TEXT DEFAULT 'open',
            claimed_by   TEXT DEFAULT NULL,
            rating       INTEGER DEFAULT NULL,
            order_id     INTEGER DEFAULT NULL,
            created_at   REAL DEFAULT (unixepoch()),
            closed_at    REAL DEFAULT NULL,
            FOREIGN KEY (order_id) REFERENCES orders(id)
        );

        -- Ticket pastabos
        CREATE TABLE IF NOT EXISTS ticket_notes (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            ticket_id  INTEGER NOT NULL,
            author_id  TEXT NOT NULL,
            author_name TEXT NOT NULL,
            note       TEXT NOT NULL,
            created_at REAL DEFAULT (unixepoch()),
            FOREIGN KEY (ticket_id) REFERENCES tickets(id)
        );

        -- Mokėjimo metodai (per ticket)
        CREATE TABLE IF NOT EXISTS payment_confirmations (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id    INTEGER NOT NULL,
            ticket_id   INTEGER NOT NULL,
            method      TEXT NOT NULL,
            screenshot_url TEXT DEFAULT NULL,
            confirmed_by TEXT DEFAULT NULL,
            confirmed_at REAL DEFAULT NULL,
            status      TEXT DEFAULT 'pending',
            FOREIGN KEY (order_id) REFERENCES orders(id)
        );

        -- Žuvys
        CREATE TABLE IF NOT EXISTS fish_stats (
            guild_id  TEXT NOT NULL,
            user_id   TEXT NOT NULL,
            fish_name TEXT NOT NULL,
            count     INTEGER DEFAULT 0,
            PRIMARY KEY (guild_id, user_id, fish_name)
        );

        -- Akcijos
        CREATE TABLE IF NOT EXISTS stocks (
            guild_id  TEXT NOT NULL,
            user_id   TEXT NOT NULL,
            symbol    TEXT NOT NULL,
            amount    INTEGER DEFAULT 0,
            avg_price REAL DEFAULT 0,
            PRIMARY KEY (guild_id, user_id, symbol)
        );

        -- Inventorius
        CREATE TABLE IF NOT EXISTS inventory (
            id        INTEGER PRIMARY KEY AUTOINCREMENT,
            guild_id  TEXT NOT NULL,
            user_id   TEXT NOT NULL,
            item_id   TEXT NOT NULL,
            quantity  INTEGER DEFAULT 1
        );

        -- Augintiniai
        CREATE TABLE IF NOT EXISTS pets (
            guild_id     TEXT NOT NULL,
            user_id      TEXT NOT NULL,
            pet_type     TEXT NOT NULL,
            pet_emoji    TEXT NOT NULL,
            pet_name     TEXT NOT NULL,
            hunger       INTEGER DEFAULT 100,
            happiness    INTEGER DEFAULT 100,
            level        INTEGER DEFAULT 1,
            xp           INTEGER DEFAULT 0,
            last_fed     REAL DEFAULT 0,
            last_played  REAL DEFAULT 0,
            PRIMARY KEY (guild_id, user_id)
        );

        -- Vedybos
        CREATE TABLE IF NOT EXISTS marriages (
            guild_id   TEXT NOT NULL,
            user1_id   TEXT NOT NULL,
            user2_id   TEXT NOT NULL,
            married_at REAL DEFAULT (unixepoch()),
            PRIMARY KEY (guild_id, user1_id)
        );

        -- Gimtadieniai
        CREATE TABLE IF NOT EXISTS birthdays (
            guild_id  TEXT NOT NULL,
            user_id   TEXT NOT NULL,
            birthday  TEXT NOT NULL,
            PRIMARY KEY (guild_id, user_id)
        );

        -- Giveaway
        CREATE TABLE IF NOT EXISTS giveaways (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            guild_id     TEXT NOT NULL,
            channel_id   TEXT NOT NULL,
            message_id   TEXT DEFAULT NULL,
            prize        INTEGER NOT NULL,
            end_time     REAL NOT NULL,
            ended        INTEGER DEFAULT 0,
            winner_id    TEXT DEFAULT NULL,
            participants TEXT DEFAULT '[]'
        );

        -- Bankas
        CREATE TABLE IF NOT EXISTS bank_transactions (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            guild_id    TEXT NOT NULL,
            user_id     TEXT NOT NULL,
            type        TEXT NOT NULL,
            amount      INTEGER NOT NULL,
            description TEXT DEFAULT '',
            created_at  REAL DEFAULT (unixepoch())
        );

        -- Paskolos
        CREATE TABLE IF NOT EXISTS loans (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            guild_id   TEXT NOT NULL,
            user_id    TEXT NOT NULL,
            amount     INTEGER NOT NULL,
            interest   REAL DEFAULT 0.1,
            due_date   REAL NOT NULL,
            paid       INTEGER DEFAULT 0,
            created_at REAL DEFAULT (unixepoch())
        );

        -- Turnyrai
        CREATE TABLE IF NOT EXISTS tournaments (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            guild_id     TEXT NOT NULL,
            name         TEXT NOT NULL,
            game_type    TEXT NOT NULL,
            prize        INTEGER NOT NULL,
            status       TEXT DEFAULT 'registracija',
            participants TEXT DEFAULT '[]',
            bracket      TEXT DEFAULT '{}',
            winner_id    TEXT DEFAULT NULL,
            created_at   REAL DEFAULT (unixepoch())
        );

        -- Pasiūlymai
        CREATE TABLE IF NOT EXISTS suggestions (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            guild_id    TEXT NOT NULL,
            user_id     TEXT NOT NULL,
            user_name   TEXT NOT NULL,
            suggestion  TEXT NOT NULL,
            status      TEXT DEFAULT 'pending',
            votes_up    INTEGER DEFAULT 0,
            votes_down  INTEGER DEFAULT 0,
            created_at  REAL DEFAULT (unixepoch())
        );

        -- Pasiekimai
        CREATE TABLE IF NOT EXISTS achievements (
            guild_id      TEXT NOT NULL,
            user_id       TEXT NOT NULL,
            achievement_id TEXT NOT NULL,
            earned_at     REAL DEFAULT (unixepoch()),
            PRIMARY KEY (guild_id, user_id, achievement_id)
        );

        -- Referral
        CREATE TABLE IF NOT EXISTS referrals (
            guild_id     TEXT NOT NULL,
            referrer_id  TEXT NOT NULL,
            referred_id  TEXT NOT NULL,
            created_at   REAL DEFAULT (unixepoch()),
            PRIMARY KEY (guild_id, referred_id)
        );

        -- Prenumeratų galiojimas
        CREATE TABLE IF NOT EXISTS subscriptions (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            guild_id     TEXT NOT NULL,
            user_id      TEXT NOT NULL,
            order_id     INTEGER NOT NULL,
            product_name TEXT NOT NULL,
            expires_at   REAL NOT NULL,
            notified_3d  INTEGER DEFAULT 0,
            notified_1d  INTEGER DEFAULT 0,
            notified_exp INTEGER DEFAULT 0,
            active       INTEGER DEFAULT 1,
            created_at   REAL DEFAULT (unixepoch())
        );

        -- Nuolaidų kodai
        CREATE TABLE IF NOT EXISTS coupons (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            guild_id     TEXT NOT NULL,
            code         TEXT NOT NULL,
            discount_pct INTEGER NOT NULL,
            max_uses     INTEGER DEFAULT 1,
            used_count   INTEGER DEFAULT 0,
            expires_at   REAL DEFAULT NULL,
            created_by   TEXT NOT NULL,
            active       INTEGER DEFAULT 1,
            created_at   REAL DEFAULT (unixepoch()),
            UNIQUE(guild_id, code)
        );

        -- Kuponų naudojimas
        CREATE TABLE IF NOT EXISTS coupon_uses (
            id        INTEGER PRIMARY KEY AUTOINCREMENT,
            coupon_id INTEGER NOT NULL,
            user_id   TEXT NOT NULL,
            order_id  INTEGER DEFAULT NULL,
            used_at   REAL DEFAULT (unixepoch()),
            FOREIGN KEY (coupon_id) REFERENCES coupons(id)
        );

        -- Automatinio pristatymo duomenys
        CREATE TABLE IF NOT EXISTS auto_delivery (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            guild_id     TEXT NOT NULL,
            product_id   INTEGER NOT NULL,
            credentials  TEXT NOT NULL,
            used         INTEGER DEFAULT 0,
            order_id     INTEGER DEFAULT NULL,
            created_at   REAL DEFAULT (unixepoch())
        );

        -- Indeksai greičiui
        CREATE INDEX IF NOT EXISTS idx_members_guild   ON members(guild_id);
        CREATE INDEX IF NOT EXISTS idx_orders_guild    ON orders(guild_id);
        CREATE INDEX IF NOT EXISTS idx_tickets_guild   ON tickets(guild_id);
        CREATE INDEX IF NOT EXISTS idx_warnings_user   ON warnings(guild_id, user_id);
        CREATE INDEX IF NOT EXISTS idx_fish_user       ON fish_stats(guild_id, user_id);
        """)
    print("✅ Duomenų bazė inicializuota!")

# ══════════════════════════════════════════════════════════════════════════════
#  MEMBER FUNCTIONS
# ══════════════════════════════════════════════════════════════════════════════
def ensure_member(gid, uid):
    with get_db() as conn:
        conn.execute(
            "INSERT OR IGNORE INTO members (guild_id, user_id) VALUES (?, ?)",
            (str(gid), str(uid))
        )

def get_member(gid, uid):
    ensure_member(gid, uid)
    with get_db() as conn:
        row = conn.execute(
            "SELECT * FROM members WHERE guild_id=? AND user_id=?",
            (str(gid), str(uid))
        ).fetchone()
        return dict(row) if row else {}

def update_member(gid, uid, **kwargs):
    ensure_member(gid, uid)
    if not kwargs: return
    sets = ", ".join(f"{k}=?" for k in kwargs)
    vals = list(kwargs.values()) + [str(gid), str(uid)]
    with get_db() as conn:
        conn.execute(f"UPDATE members SET {sets} WHERE guild_id=? AND user_id=?", vals)

def add_coins(gid, uid, amount):
    ensure_member(gid, uid)
    with get_db() as conn:
        conn.execute(
            "UPDATE members SET coins=MAX(0, coins+?) WHERE guild_id=? AND user_id=?",
            (amount, str(gid), str(uid))
        )
        row = conn.execute(
            "SELECT coins FROM members WHERE guild_id=? AND user_id=?",
            (str(gid), str(uid))
        ).fetchone()
        return row["coins"] if row else 0

def add_xp(gid, uid, amount):
    ensure_member(gid, uid)
    with get_db() as conn:
        m = conn.execute(
            "SELECT xp FROM members WHERE guild_id=? AND user_id=?",
            (str(gid), str(uid))
        ).fetchone()
        old_xp = m["xp"] if m else 0
        new_xp = old_xp + amount
        conn.execute(
            "UPDATE members SET xp=? WHERE guild_id=? AND user_id=?",
            (new_xp, str(gid), str(uid))
        )
        return old_xp // 200, new_xp // 200

def get_leaderboard_xp(gid, limit=10):
    with get_db() as conn:
        rows = conn.execute(
            "SELECT user_id, xp FROM members WHERE guild_id=? ORDER BY xp DESC LIMIT ?",
            (str(gid), limit)
        ).fetchall()
        return [(r["user_id"], r["xp"], r["xp"]//200) for r in rows]

def get_leaderboard_coins(gid, limit=10):
    with get_db() as conn:
        rows = conn.execute(
            "SELECT user_id, coins FROM members WHERE guild_id=? ORDER BY coins DESC LIMIT ?",
            (str(gid), limit)
        ).fetchall()
        return [(r["user_id"], r["coins"]) for r in rows]

# ══════════════════════════════════════════════════════════════════════════════
#  WARNINGS
# ══════════════════════════════════════════════════════════════════════════════
def add_warning(gid, uid, reason, mod_id, mod_name):
    with get_db() as conn:
        conn.execute(
            "INSERT INTO warnings (guild_id, user_id, reason, mod_id, mod_name) VALUES (?,?,?,?,?)",
            (str(gid), str(uid), reason, str(mod_id), mod_name)
        )
        count = conn.execute(
            "SELECT COUNT(*) as c FROM warnings WHERE guild_id=? AND user_id=?",
            (str(gid), str(uid))
        ).fetchone()["c"]
        return count

def get_warnings(gid, uid):
    with get_db() as conn:
        rows = conn.execute(
            "SELECT * FROM warnings WHERE guild_id=? AND user_id=? ORDER BY created_at",
            (str(gid), str(uid))
        ).fetchall()
        return [dict(r) for r in rows]

def clear_warnings(gid, uid):
    with get_db() as conn:
        conn.execute(
            "DELETE FROM warnings WHERE guild_id=? AND user_id=?",
            (str(gid), str(uid))
        )

# ══════════════════════════════════════════════════════════════════════════════
#  GUILD SETTINGS
# ══════════════════════════════════════════════════════════════════════════════
def get_settings(gid):
    with get_db() as conn:
        conn.execute(
            "INSERT OR IGNORE INTO guild_settings (guild_id) VALUES (?)", (str(gid),)
        )
        row = conn.execute(
            "SELECT * FROM guild_settings WHERE guild_id=?", (str(gid),)
        ).fetchone()
        if not row: return {}
        d = dict(row)
        d["blacklist"] = json.loads(d.get("blacklist") or "[]")
        d["payment_methods"] = json.loads(d.get("payment_methods") or "{}")
        d["level_rewards"] = json.loads(d.get("level_rewards") or "{}")
        return d

def update_settings(gid, **kwargs):
    # Serialize JSON fields
    for k in ("blacklist", "payment_methods", "level_rewards"):
        if k in kwargs and not isinstance(kwargs[k], str):
            kwargs[k] = json.dumps(kwargs[k], ensure_ascii=False)
    with get_db() as conn:
        conn.execute("INSERT OR IGNORE INTO guild_settings (guild_id) VALUES (?)", (str(gid),))
        if not kwargs: return
        sets = ", ".join(f"{k}=?" for k in kwargs)
        vals = list(kwargs.values()) + [str(gid)]
        conn.execute(f"UPDATE guild_settings SET {sets} WHERE guild_id=?", vals)

# ══════════════════════════════════════════════════════════════════════════════
#  PRODUCTS
# ══════════════════════════════════════════════════════════════════════════════
DEFAULT_PRODUCTS_DB = [
    ("Netflix Premium","4K Ultra HD, 4 ekranai",5.99,17.99,"streaming","🎬","1 mėn.",99),
    ("Netflix Premium","4K Ultra HD, 4 ekranai",14.99,49.99,"streaming","🎬","3 mėn.",99),
    ("Spotify Premium","Be reklamu, offline",3.99,10.99,"music","🎵","1 mėn.",99),
    ("YouTube Premium","Be reklamu, background",4.99,13.99,"streaming","▶️","1 mėn.",99),
    ("Disney+","Marvel, Star Wars, Pixar",4.49,11.99,"streaming","🏰","1 mėn.",99),
    ("Canva Pro","Premium dizaino įrankiai",3.99,12.99,"editing","🎨","1 mėn.",99),
    ("NordVPN","VPN, 6 prietaisai",2.99,11.99,"other","🔒","1 mėn.",99),
]

def get_products(gid):
    with get_db() as conn:
        rows = conn.execute(
            "SELECT * FROM products WHERE guild_id=? AND active=1 ORDER BY id",
            (str(gid),)
        ).fetchall()
        if not rows:
            # Įdėti numatytuosius produktus
            for p in DEFAULT_PRODUCTS_DB:
                conn.execute(
                    "INSERT INTO products (guild_id,name,description,price,old_price,category,emoji,duration,stock) VALUES (?,?,?,?,?,?,?,?,?)",
                    (str(gid),) + p
                )
            rows = conn.execute(
                "SELECT * FROM products WHERE guild_id=? AND active=1 ORDER BY id",
                (str(gid),)
            ).fetchall()
        return [dict(r) for r in rows]

def get_product(gid, pid):
    with get_db() as conn:
        row = conn.execute(
            "SELECT * FROM products WHERE guild_id=? AND id=? AND active=1",
            (str(gid), pid)
        ).fetchone()
        return dict(row) if row else None

def add_product(gid, name, desc, price, old_price, category, emoji, duration, stock=99):
    with get_db() as conn:
        cursor = conn.execute(
            "INSERT INTO products (guild_id,name,description,price,old_price,category,emoji,duration,stock) VALUES (?,?,?,?,?,?,?,?,?)",
            (str(gid), name, desc, price, old_price, category, emoji, duration, stock)
        )
        return cursor.lastrowid

def remove_product(gid, pid):
    with get_db() as conn:
        conn.execute("UPDATE products SET active=0 WHERE guild_id=? AND id=?", (str(gid), pid))

def update_stock(gid, pid, delta):
    with get_db() as conn:
        conn.execute(
            "UPDATE products SET stock=MAX(0, stock+?) WHERE guild_id=? AND id=?",
            (delta, str(gid), pid)
        )

# ══════════════════════════════════════════════════════════════════════════════
#  ORDERS
# ══════════════════════════════════════════════════════════════════════════════
def create_order(gid, uid, username, product):
    with get_db() as conn:
        # Išjungti FK patikrinimą šiai operacijai
        conn.execute("PRAGMA foreign_keys=OFF")
        cursor = conn.execute(
            """INSERT INTO orders
               (guild_id, user_id, username, product_id, product_name, duration, price)
               VALUES (?,?,?,?,?,?,?)""",
            (str(gid), str(uid), username, product.get("id", 0),
             product["name"], product.get("duration","1 men."), product["price"])
        )
        conn.execute("PRAGMA foreign_keys=ON")
        # Sumažinti stock jei produktas yra DB
        try:
            conn.execute(
                "UPDATE products SET stock=MAX(0, stock-1) WHERE guild_id=? AND id=?",
                (str(gid), product.get("id", 0))
            )
        except Exception: pass
        return cursor.lastrowid

def get_order(gid, oid):
    with get_db() as conn:
        row = conn.execute(
            "SELECT * FROM orders WHERE guild_id=? AND id=?", (str(gid), oid)
        ).fetchone()
        return dict(row) if row else None

def get_orders(gid, user_id=None, status=None):
    with get_db() as conn:
        q = "SELECT * FROM orders WHERE guild_id=?"
        params = [str(gid)]
        if user_id:
            q += " AND user_id=?"; params.append(str(user_id))
        if status:
            q += " AND status=?"; params.append(status)
        q += " ORDER BY created_at DESC"
        rows = conn.execute(q, params).fetchall()
        return [dict(r) for r in rows]

def update_order(gid, oid, **kwargs):
    if not kwargs: return
    sets = ", ".join(f"{k}=?" for k in kwargs)
    vals = list(kwargs.values()) + [str(gid), oid]
    with get_db() as conn:
        conn.execute(f"UPDATE orders SET {sets} WHERE guild_id=? AND id=?", vals)

# ══════════════════════════════════════════════════════════════════════════════
#  TICKETS
# ══════════════════════════════════════════════════════════════════════════════
def create_ticket(gid, channel_id, uid, username, category, subject, description, priority="normal", order_id=None):
    with get_db() as conn:
        cursor = conn.execute(
            """INSERT INTO tickets
               (guild_id, channel_id, user_id, user_name, category, subject, description, priority, order_id)
               VALUES (?,?,?,?,?,?,?,?,?)""",
            (str(gid), str(channel_id), str(uid), username, category, subject, description, priority, order_id)
        )
        return cursor.lastrowid

def get_ticket_by_channel(gid, channel_id):
    with get_db() as conn:
        row = conn.execute(
            "SELECT * FROM tickets WHERE guild_id=? AND channel_id=? AND status='open'",
            (str(gid), str(channel_id))
        ).fetchone()
        return dict(row) if row else None

def get_tickets(gid, status=None):
    with get_db() as conn:
        q = "SELECT * FROM tickets WHERE guild_id=?"
        params = [str(gid)]
        if status:
            q += " AND status=?"; params.append(status)
        q += " ORDER BY created_at DESC"
        rows = conn.execute(q, params).fetchall()
        return [dict(r) for r in rows]

def update_ticket(channel_id, **kwargs):
    if not kwargs: return
    sets = ", ".join(f"{k}=?" for k in kwargs)
    vals = list(kwargs.values()) + [str(channel_id)]
    with get_db() as conn:
        conn.execute(f"UPDATE tickets SET {sets} WHERE channel_id=?", vals)

def add_ticket_note(ticket_id, author_id, author_name, note):
    with get_db() as conn:
        conn.execute(
            "INSERT INTO ticket_notes (ticket_id, author_id, author_name, note) VALUES (?,?,?,?)",
            (ticket_id, str(author_id), author_name, note)
        )

def get_ticket_notes(ticket_id):
    with get_db() as conn:
        rows = conn.execute(
            "SELECT * FROM ticket_notes WHERE ticket_id=? ORDER BY created_at",
            (ticket_id,)
        ).fetchall()
        return [dict(r) for r in rows]

def get_ticket_stats(gid):
    with get_db() as conn:
        total = conn.execute("SELECT COUNT(*) as c FROM tickets WHERE guild_id=?", (str(gid),)).fetchone()["c"]
        open_ = conn.execute("SELECT COUNT(*) as c FROM tickets WHERE guild_id=? AND status='open'", (str(gid),)).fetchone()["c"]
        closed = conn.execute("SELECT COUNT(*) as c FROM tickets WHERE guild_id=? AND status='closed'", (str(gid),)).fetchone()["c"]
        avg_row = conn.execute(
            "SELECT AVG((closed_at - created_at)/60) as avg FROM tickets WHERE guild_id=? AND status='closed' AND closed_at IS NOT NULL",
            (str(gid),)
        ).fetchone()
        avg_min = avg_row["avg"] or 0
        return {"total": total, "open": open_, "closed": closed, "avg_minutes": avg_min}

# ══════════════════════════════════════════════════════════════════════════════
#  BANKAS
# ══════════════════════════════════════════════════════════════════════════════
INTEREST_RATE = 0.02  # 2% per dieną
MAX_LOAN = 10000

def deposit(gid, uid, amount):
    """Įnešti monetas į banką"""
    m = get_member(gid, uid)
    if m.get("coins", 0) < amount:
        return False, "Neturi tiek monetų!"
    add_coins(gid, uid, -amount)
    update_member(gid, uid, bank_balance=m.get("bank_balance", 0) + amount)
    with get_db() as conn:
        conn.execute(
            "INSERT INTO bank_transactions (guild_id,user_id,type,amount,description) VALUES (?,?,?,?,?)",
            (str(gid), str(uid), "deposit", amount, "Įnešimas į banką")
        )
    return True, m.get("bank_balance", 0) + amount

def withdraw(gid, uid, amount):
    """Išimti monetas iš banko"""
    m = get_member(gid, uid)
    if m.get("bank_balance", 0) < amount:
        return False, "Neturi tiek banke!"
    update_member(gid, uid, bank_balance=m.get("bank_balance", 0) - amount)
    add_coins(gid, uid, amount)
    with get_db() as conn:
        conn.execute(
            "INSERT INTO bank_transactions (guild_id,user_id,type,amount,description) VALUES (?,?,?,?,?)",
            (str(gid), str(uid), "withdraw", amount, "Išėmimas iš banko")
        )
    return True, m.get("bank_balance", 0) - amount

def apply_interest(gid, uid):
    """Pridėti palūkanas"""
    m = get_member(gid, uid)
    bal = m.get("bank_balance", 0)
    if bal <= 0: return 0
    interest = int(bal * INTEREST_RATE)
    update_member(gid, uid, bank_balance=bal + interest)
    return interest

def take_loan(gid, uid, amount):
    """Imti paskolą"""
    m = get_member(gid, uid)
    if m.get("loan_amount", 0) > 0:
        return False, "Jau turi paskolą! Pirmiausia grąžink."
    if amount > MAX_LOAN:
        return False, f"Maksimali paskola: {MAX_LOAN:,} 🪙"
    due = time.time() + 7 * 86400  # 7 dienos
    update_member(gid, uid, loan_amount=amount, loan_due=due)
    add_coins(gid, uid, amount)
    with get_db() as conn:
        conn.execute(
            "INSERT INTO loans (guild_id,user_id,amount,due_date) VALUES (?,?,?,?)",
            (str(gid), str(uid), amount, due)
        )
    return True, amount

def repay_loan(gid, uid):
    """Grąžinti paskolą"""
    m = get_member(gid, uid)
    loan = m.get("loan_amount", 0)
    if loan <= 0:
        return False, "Neturi paskolos!"
    # Palūkanos 10%
    total = int(loan * 1.1)
    if m.get("coins", 0) < total:
        return False, f"Reikia **{total:,}** 🪙 (paskola + 10% palūkanos)"
    add_coins(gid, uid, -total)
    update_member(gid, uid, loan_amount=0, loan_due=0)
    return True, total

def get_bank_history(gid, uid, limit=10):
    with get_db() as conn:
        rows = conn.execute(
            "SELECT * FROM bank_transactions WHERE guild_id=? AND user_id=? ORDER BY created_at DESC LIMIT ?",
            (str(gid), str(uid), limit)
        ).fetchall()
        return [dict(r) for r in rows]

# ══════════════════════════════════════════════════════════════════════════════
#  FISH STATS
# ══════════════════════════════════════════════════════════════════════════════
def add_fish(gid, uid, fish_name):
    with get_db() as conn:
        conn.execute(
            """INSERT INTO fish_stats (guild_id, user_id, fish_name, count) VALUES (?,?,?,1)
               ON CONFLICT(guild_id, user_id, fish_name) DO UPDATE SET count=count+1""",
            (str(gid), str(uid), fish_name)
        )

def get_fish_stats(gid, uid):
    with get_db() as conn:
        rows = conn.execute(
            "SELECT fish_name, count FROM fish_stats WHERE guild_id=? AND user_id=? ORDER BY count DESC",
            (str(gid), str(uid))
        ).fetchall()
        return {r["fish_name"]: r["count"] for r in rows}

# ══════════════════════════════════════════════════════════════════════════════
#  STOCKS
# ══════════════════════════════════════════════════════════════════════════════
def get_user_stocks(gid, uid):
    with get_db() as conn:
        rows = conn.execute(
            "SELECT symbol, amount, avg_price FROM stocks WHERE guild_id=? AND user_id=? AND amount>0",
            (str(gid), str(uid))
        ).fetchall()
        return {r["symbol"]: {"amount": r["amount"], "avg_price": r["avg_price"]} for r in rows}

def add_stock_db(gid, uid, symbol, amount, price):
    with get_db() as conn:
        existing = conn.execute(
            "SELECT amount, avg_price FROM stocks WHERE guild_id=? AND user_id=? AND symbol=?",
            (str(gid), str(uid), symbol)
        ).fetchone()
        if existing:
            new_amount = existing["amount"] + amount
            new_avg = ((existing["avg_price"] * existing["amount"]) + (price * amount)) / new_amount if new_amount > 0 else 0
            conn.execute(
                "UPDATE stocks SET amount=?, avg_price=? WHERE guild_id=? AND user_id=? AND symbol=?",
                (new_amount, new_avg, str(gid), str(uid), symbol)
            )
        else:
            conn.execute(
                "INSERT INTO stocks (guild_id, user_id, symbol, amount, avg_price) VALUES (?,?,?,?,?)",
                (str(gid), str(uid), symbol, amount, price)
            )

def remove_stock_db(gid, uid, symbol, amount):
    with get_db() as conn:
        existing = conn.execute(
            "SELECT amount FROM stocks WHERE guild_id=? AND user_id=? AND symbol=?",
            (str(gid), str(uid), symbol)
        ).fetchone()
        if not existing or existing["amount"] < amount:
            return False
        conn.execute(
            "UPDATE stocks SET amount=amount-? WHERE guild_id=? AND user_id=? AND symbol=?",
            (amount, str(gid), str(uid), symbol)
        )
        return True

# ══════════════════════════════════════════════════════════════════════════════
#  ACHIEVEMENTS
# ══════════════════════════════════════════════════════════════════════════════
def check_achievement_db(gid, uid, ach_id, reward_amount):
    with get_db() as conn:
        existing = conn.execute(
            "SELECT 1 FROM achievements WHERE guild_id=? AND user_id=? AND achievement_id=?",
            (str(gid), str(uid), ach_id)
        ).fetchone()
        if not existing:
            conn.execute(
                "INSERT INTO achievements (guild_id, user_id, achievement_id) VALUES (?,?,?)",
                (str(gid), str(uid), ach_id)
            )
            add_coins(gid, uid, reward_amount)
            return True
    return False

def get_achievements_db(gid, uid):
    with get_db() as conn:
        rows = conn.execute(
            "SELECT achievement_id FROM achievements WHERE guild_id=? AND user_id=?",
            (str(gid), str(uid))
        ).fetchall()
        return [r["achievement_id"] for r in rows]

# ══════════════════════════════════════════════════════════════════════════════
#  GIVEAWAY
# ══════════════════════════════════════════════════════════════════════════════
def create_giveaway(gid, channel_id, prize, end_time):
    with get_db() as conn:
        cursor = conn.execute(
            "INSERT INTO giveaways (guild_id, channel_id, prize, end_time) VALUES (?,?,?,?)",
            (str(gid), str(channel_id), prize, end_time)
        )
        return cursor.lastrowid

def join_giveaway(ga_id, uid):
    with get_db() as conn:
        row = conn.execute("SELECT participants FROM giveaways WHERE id=?", (ga_id,)).fetchone()
        if not row: return False
        participants = json.loads(row["participants"])
        uid_s = str(uid)
        if uid_s in participants:
            participants.remove(uid_s)
            joined = False
        else:
            participants.append(uid_s)
            joined = True
        conn.execute(
            "UPDATE giveaways SET participants=? WHERE id=?",
            (json.dumps(participants), ga_id)
        )
        return joined, len(participants)

def get_active_giveaways():
    with get_db() as conn:
        rows = conn.execute(
            "SELECT * FROM giveaways WHERE ended=0 AND end_time<=?", (time.time(),)
        ).fetchall()
        return [dict(r) for r in rows]

def end_giveaway(ga_id, winner_id=None):
    with get_db() as conn:
        conn.execute(
            "UPDATE giveaways SET ended=1, winner_id=? WHERE id=?",
            (str(winner_id) if winner_id else None, ga_id)
        )

# ══════════════════════════════════════════════════════════════════════════════
#  PETS
# ══════════════════════════════════════════════════════════════════════════════
def get_pet(gid, uid):
    with get_db() as conn:
        row = conn.execute(
            "SELECT * FROM pets WHERE guild_id=? AND user_id=?",
            (str(gid), str(uid))
        ).fetchone()
        return dict(row) if row else None

def create_pet(gid, uid, pet_type, pet_emoji, pet_name):
    with get_db() as conn:
        conn.execute(
            """INSERT OR REPLACE INTO pets
               (guild_id, user_id, pet_type, pet_emoji, pet_name, hunger, happiness, level, xp, last_fed, last_played)
               VALUES (?,?,?,?,?,100,100,1,0,?,?)""",
            (str(gid), str(uid), pet_type, pet_emoji, pet_name, time.time(), time.time())
        )

def update_pet(gid, uid, **kwargs):
    if not kwargs: return
    sets = ", ".join(f"{k}=?" for k in kwargs)
    vals = list(kwargs.values()) + [str(gid), str(uid)]
    with get_db() as conn:
        conn.execute(f"UPDATE pets SET {sets} WHERE guild_id=? AND user_id=?", vals)

# ══════════════════════════════════════════════════════════════════════════════
#  MARRIAGES
# ══════════════════════════════════════════════════════════════════════════════
def get_marriage(gid, uid):
    with get_db() as conn:
        row = conn.execute(
            "SELECT * FROM marriages WHERE guild_id=? AND (user1_id=? OR user2_id=?)",
            (str(gid), str(uid), str(uid))
        ).fetchone()
        if not row: return None
        d = dict(row)
        d["partner_id"] = d["user2_id"] if d["user1_id"] == str(uid) else d["user1_id"]
        return d

def create_marriage(gid, uid1, uid2):
    with get_db() as conn:
        conn.execute(
            "INSERT OR REPLACE INTO marriages (guild_id, user1_id, user2_id) VALUES (?,?,?)",
            (str(gid), str(uid1), str(uid2))
        )

def delete_marriage(gid, uid):
    with get_db() as conn:
        conn.execute(
            "DELETE FROM marriages WHERE guild_id=? AND (user1_id=? OR user2_id=?)",
            (str(gid), str(uid), str(uid))
        )

# ══════════════════════════════════════════════════════════════════════════════
#  BIRTHDAYS
# ══════════════════════════════════════════════════════════════════════════════
def set_birthday(gid, uid, birthday):
    with get_db() as conn:
        conn.execute(
            "INSERT OR REPLACE INTO birthdays (guild_id, user_id, birthday) VALUES (?,?,?)",
            (str(gid), str(uid), birthday)
        )

def get_birthdays(gid):
    with get_db() as conn:
        rows = conn.execute(
            "SELECT user_id, birthday FROM birthdays WHERE guild_id=?", (str(gid),)
        ).fetchall()
        return {r["user_id"]: r["birthday"] for r in rows}

# ══════════════════════════════════════════════════════════════════════════════
#  REFERRALS
# ══════════════════════════════════════════════════════════════════════════════
def process_referral_db(gid, referrer_id, new_uid):
    with get_db() as conn:
        existing = conn.execute(
            "SELECT 1 FROM referrals WHERE guild_id=? AND referred_id=?",
            (str(gid), str(new_uid))
        ).fetchone()
        if existing: return False
        conn.execute(
            "INSERT INTO referrals (guild_id, referrer_id, referred_id) VALUES (?,?,?)",
            (str(gid), str(referrer_id), str(new_uid))
        )
        add_coins(gid, referrer_id, 500)
        add_coins(gid, new_uid, 500)
        return True

# ══════════════════════════════════════════════════════════════════════════════
#  PAYMENT CONFIRMATIONS
# ══════════════════════════════════════════════════════════════════════════════
def create_payment_confirmation(order_id, ticket_id, method):
    with get_db() as conn:
        cursor = conn.execute(
            "INSERT INTO payment_confirmations (order_id, ticket_id, method) VALUES (?,?,?)",
            (order_id, ticket_id, method)
        )
        return cursor.lastrowid

def confirm_payment(conf_id, confirmed_by):
    with get_db() as conn:
        conn.execute(
            "UPDATE payment_confirmations SET status='confirmed', confirmed_by=?, confirmed_at=? WHERE id=?",
            (str(confirmed_by), time.time(), conf_id)
        )

# ══════════════════════════════════════════════════════════════════════════════
#  TURNYRAI
# ══════════════════════════════════════════════════════════════════════════════
def create_tournament(gid, name, game_type, prize):
    with get_db() as conn:
        cursor = conn.execute(
            "INSERT INTO tournaments (guild_id, name, game_type, prize) VALUES (?,?,?,?)",
            (str(gid), name, game_type, prize)
        )
        return cursor.lastrowid

def join_tournament(tid, uid):
    with get_db() as conn:
        row = conn.execute("SELECT participants, status FROM tournaments WHERE id=?", (tid,)).fetchone()
        if not row or row["status"] != "registracija": return False
        participants = json.loads(row["participants"])
        if str(uid) in participants: return False
        participants.append(str(uid))
        conn.execute(
            "UPDATE tournaments SET participants=? WHERE id=?",
            (json.dumps(participants), tid)
        )
        return True

def get_tournament(tid):
    with get_db() as conn:
        row = conn.execute("SELECT * FROM tournaments WHERE id=?", (tid,)).fetchone()
        if not row: return None
        d = dict(row)
        d["participants"] = json.loads(d["participants"])
        d["bracket"] = json.loads(d["bracket"])
        return d

def get_active_tournaments(gid):
    with get_db() as conn:
        rows = conn.execute(
            "SELECT * FROM tournaments WHERE guild_id=? AND status!='baigtas'",
            (str(gid),)
        ).fetchall()
        result = []
        for r in rows:
            d = dict(r)
            d["participants"] = json.loads(d["participants"])
            result.append(d)
        return result

def start_tournament(tid):
    """Sukurti turnyrų bracket"""
    t = get_tournament(tid)
    if not t: return None
    participants = t["participants"]
    random.shuffle(participants) if __import__('random').shuffle(participants) else None
    bracket = {"rounds": [], "current_round": 0}
    # Sukurti pirmą ratą
    pairs = [(participants[i], participants[i+1] if i+1 < len(participants) else "bye")
             for i in range(0, len(participants), 2)]
    bracket["rounds"].append([{"p1": p[0], "p2": p[1], "winner": None} for p in pairs])
    with get_db() as conn:
        conn.execute(
            "UPDATE tournaments SET status='vyksta', bracket=? WHERE id=?",
            (json.dumps(bracket), tid)
        )
    return bracket

if __name__ == "__main__":
    init_db()
    print("✅ Duomenų bazė paruošta!")

# ══════════════════════════════════════════════════════════════════════════════
#  PRENUMERATOS
# ══════════════════════════════════════════════════════════════════════════════
def create_subscription(gid, uid, order_id, product_name, duration_days):
    expires = time.time() + duration_days * 86400
    with get_db() as conn:
        cursor = conn.execute(
            "INSERT INTO subscriptions (guild_id,user_id,order_id,product_name,expires_at) VALUES (?,?,?,?,?)",
            (str(gid), str(uid), order_id, product_name, expires)
        )
        return cursor.lastrowid, expires

def get_expiring_subscriptions(hours_until=72):
    """Gauti prenumeratas kurios baigiasi per X valandų"""
    deadline = time.time() + hours_until * 3600
    with get_db() as conn:
        rows = conn.execute(
            "SELECT * FROM subscriptions WHERE active=1 AND expires_at<=? AND expires_at>?",
            (deadline, time.time())
        ).fetchall()
        return [dict(r) for r in rows]

def get_expired_subscriptions():
    with get_db() as conn:
        rows = conn.execute(
            "SELECT * FROM subscriptions WHERE active=1 AND expires_at<=?",
            (time.time(),)
        ).fetchall()
        return [dict(r) for r in rows]

def mark_notified(sub_id, field):
    with get_db() as conn:
        conn.execute(f"UPDATE subscriptions SET {field}=1 WHERE id=?", (sub_id,))

def deactivate_subscription(sub_id):
    with get_db() as conn:
        conn.execute("UPDATE subscriptions SET active=0 WHERE id=?", (sub_id,))

def get_user_subscriptions(gid, uid):
    with get_db() as conn:
        rows = conn.execute(
            "SELECT * FROM subscriptions WHERE guild_id=? AND user_id=? AND active=1 ORDER BY expires_at",
            (str(gid), str(uid))
        ).fetchall()
        return [dict(r) for r in rows]

# ══════════════════════════════════════════════════════════════════════════════
#  NUOLAIDŲ KODAI
# ══════════════════════════════════════════════════════════════════════════════
def create_coupon(gid, code, discount_pct, max_uses, expires_days, created_by):
    expires = time.time() + expires_days * 86400 if expires_days else None
    with get_db() as conn:
        try:
            cursor = conn.execute(
                "INSERT INTO coupons (guild_id,code,discount_pct,max_uses,expires_at,created_by) VALUES (?,?,?,?,?,?)",
                (str(gid), code.upper(), discount_pct, max_uses, expires, str(created_by))
            )
            return cursor.lastrowid
        except Exception:
            return None  # Kodas jau egzistuoja

def get_coupon(gid, code):
    with get_db() as conn:
        row = conn.execute(
            "SELECT * FROM coupons WHERE guild_id=? AND code=? AND active=1",
            (str(gid), code.upper())
        ).fetchone()
        return dict(row) if row else None

def validate_coupon(gid, code, uid):
    """Patikrinti ar kuponas galioja ir narys jo nenaudojo"""
    c = get_coupon(gid, code)
    if not c: return None, "Kuponas nerastas!"
    if c["expires_at"] and time.time() > c["expires_at"]: return None, "Kuponas pasibaigė!"
    if c["used_count"] >= c["max_uses"]: return None, "Kuponas jau panaudotas!"
    with get_db() as conn:
        used = conn.execute(
            "SELECT 1 FROM coupon_uses WHERE coupon_id=? AND user_id=?",
            (c["id"], str(uid))
        ).fetchone()
    if used: return None, "Jau naudojai šį kuponą!"
    return c, "OK"

def use_coupon(coupon_id, uid, order_id=None):
    with get_db() as conn:
        conn.execute(
            "INSERT INTO coupon_uses (coupon_id,user_id,order_id) VALUES (?,?,?)",
            (coupon_id, str(uid), order_id)
        )
        conn.execute(
            "UPDATE coupons SET used_count=used_count+1 WHERE id=?", (coupon_id,)
        )

def get_coupons(gid):
    with get_db() as conn:
        rows = conn.execute(
            "SELECT * FROM coupons WHERE guild_id=? ORDER BY created_at DESC",
            (str(gid),)
        ).fetchall()
        return [dict(r) for r in rows]

def deactivate_coupon(gid, code):
    with get_db() as conn:
        conn.execute(
            "UPDATE coupons SET active=0 WHERE guild_id=? AND code=?",
            (str(gid), code.upper())
        )

# ══════════════════════════════════════════════════════════════════════════════
#  AUTOMATINIS PRISTATYMAS
# ══════════════════════════════════════════════════════════════════════════════
def add_auto_delivery(gid, product_id, credentials):
    with get_db() as conn:
        cursor = conn.execute(
            "INSERT INTO auto_delivery (guild_id,product_id,credentials) VALUES (?,?,?)",
            (str(gid), product_id, credentials)
        )
        return cursor.lastrowid

def get_auto_delivery(gid, product_id):
    """Gauti nepanaudotą pristatymo įrašą"""
    with get_db() as conn:
        row = conn.execute(
            "SELECT * FROM auto_delivery WHERE guild_id=? AND product_id=? AND used=0 ORDER BY id LIMIT 1",
            (str(gid), product_id)
        ).fetchone()
        return dict(row) if row else None

def mark_delivery_used(delivery_id, order_id):
    with get_db() as conn:
        conn.execute(
            "UPDATE auto_delivery SET used=1, order_id=? WHERE id=?",
            (order_id, delivery_id)
        )

def get_delivery_stock(gid, product_id):
    """Kiek nepanaudotų pristatymų liko"""
    with get_db() as conn:
        row = conn.execute(
            "SELECT COUNT(*) as c FROM auto_delivery WHERE guild_id=? AND product_id=? AND used=0",
            (str(gid), product_id)
        ).fetchone()
        return row["c"] if row else 0

def get_all_deliveries(gid, product_id=None):
    with get_db() as conn:
        if product_id:
            rows = conn.execute(
                "SELECT * FROM auto_delivery WHERE guild_id=? AND product_id=?",
                (str(gid), product_id)
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM auto_delivery WHERE guild_id=?", (str(gid),)
            ).fetchall()
        return [dict(r) for r in rows]
