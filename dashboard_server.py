# -*- coding: utf-8 -*-
"""
KODAS BOT — Realus Web Dashboard
Paleisti: python dashboard_server.py
Atidaryti: http://localhost:5000
"""
from flask import Flask, jsonify, request, send_file
import sqlite3, json, os, time, datetime, pathlib

app = Flask(__name__)
DB_PATH = str(pathlib.Path(__file__).parent / "kodas_bot.db")
DATA_FILE = str(pathlib.Path(__file__).parent / "data.json")

# ══════════════════════════════════════════════════════════════════════════════
#  DB HELPERS
# ══════════════════════════════════════════════════════════════════════════════
def db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def load_json():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except: pass
    return {}

def has_db():
    return os.path.exists(DB_PATH)

# ══════════════════════════════════════════════════════════════════════════════
#  API ENDPOINTS
# ══════════════════════════════════════════════════════════════════════════════

@app.route("/api/overview")
def overview():
    if has_db():
        with db() as conn:
            members    = conn.execute("SELECT COUNT(*) as c FROM members").fetchone()["c"]
            orders     = conn.execute("SELECT COUNT(*) as c FROM orders WHERE status!='ivykdyta'").fetchone()["c"]
            tickets    = conn.execute("SELECT COUNT(*) as c FROM tickets WHERE status='open'").fetchone()["c"]
            warns      = conn.execute("SELECT COUNT(*) as c FROM warnings").fetchone()["c"]
            total_coins= conn.execute("SELECT COALESCE(SUM(coins),0) as s FROM members").fetchone()["s"]
            bank_total = conn.execute("SELECT COALESCE(SUM(bank_balance),0) as s FROM members").fetchone()["s"]
            products   = conn.execute("SELECT COUNT(*) as c FROM products WHERE active=1").fetchone()["c"]
    else:
        D = load_json()
        members = 0; orders = 0; tickets = 0; warns = 0
        total_coins = 0; bank_total = 0; products = 0
        for gid, users in D.get("coins", {}).items():
            members = max(members, len(users))
            total_coins += sum(users.values())
        for gid, ts in D.get("tickets", {}).items():
            tickets += len(ts)
        for gid, ws in D.get("warnings", {}).items():
            for uid, wl in ws.items():
                warns += len(wl)
        for gid, os_ in D.get("orders", {}).items():
            orders += sum(1 for o in os_ if o.get("status") != "ivykdyta")
        for gid, ps in D.get("products", {}).items():
            products += len(ps)

    return jsonify({
        "members": members, "orders": orders, "tickets": tickets,
        "warns": warns, "total_coins": total_coins,
        "bank_total": bank_total, "products": products
    })

@app.route("/api/members")
def members():
    sort_by = request.args.get("sort", "xp")
    limit   = int(request.args.get("limit", 50))
    search  = request.args.get("search", "").lower()

    valid_sorts = {"xp","coins","rep","streak","message_count"}
    if sort_by not in valid_sorts: sort_by = "xp"

    if has_db():
        with db() as conn:
            rows = conn.execute(
                f"SELECT * FROM members ORDER BY {sort_by} DESC LIMIT ?", (limit,)
            ).fetchall()
            result = [dict(r) for r in rows]
    else:
        D = load_json()
        result = []
        coins_data = D.get("coins", {})
        xp_data    = D.get("xp", {})
        rep_data   = D.get("rep", {})
        all_uids   = set()
        for gid in list(coins_data.keys())[:1]:
            all_uids = set(coins_data.get(gid, {}).keys())
            for uid in all_uids:
                result.append({
                    "user_id":       uid,
                    "guild_id":      gid,
                    "coins":         coins_data.get(gid,{}).get(uid,0),
                    "xp":            xp_data.get(gid,{}).get(uid,0),
                    "rep":           rep_data.get(gid,{}).get(uid,0),
                    "streak":        D.get("streaks",{}).get(f"{gid}:{uid}",{}).get("count",0),
                    "message_count": D.get("message_counts",{}).get(gid,{}).get(uid,0),
                    "is_vip":        0,
                    "bank_balance":  D.get("bank",{}).get(gid,{}).get(uid,0),
                })
        result.sort(key=lambda x: x.get(sort_by, 0), reverse=True)

    if search:
        result = [r for r in result if search in str(r.get("user_id","")).lower()]

    return jsonify(result[:limit])

@app.route("/api/leaderboard/<type>")
def leaderboard(type):
    if type not in ("xp","coins","rep"): type = "xp"
    limit = int(request.args.get("limit", 10))

    if has_db():
        with db() as conn:
            rows = conn.execute(
                f"SELECT user_id, {type}, xp FROM members ORDER BY {type} DESC LIMIT ?", (limit,)
            ).fetchall()
            return jsonify([dict(r) for r in rows])
    else:
        D = load_json()
        data = {}
        field = D.get(type if type != "rep" else "rep", D.get("xp",{}))
        for gid, users in list(field.items())[:1]:
            for uid, val in users.items():
                data[uid] = val
        sorted_data = sorted(data.items(), key=lambda x: x[1], reverse=True)[:limit]
        return jsonify([{"user_id": uid, type: val, "xp": val} for uid, val in sorted_data])

@app.route("/api/orders")
def orders():
    status = request.args.get("status", "all")
    limit  = int(request.args.get("limit", 50))

    if has_db():
        with db() as conn:
            if status == "all":
                rows = conn.execute("SELECT * FROM orders ORDER BY created_at DESC LIMIT ?", (limit,)).fetchall()
            else:
                rows = conn.execute("SELECT * FROM orders WHERE status=? ORDER BY created_at DESC LIMIT ?", (status, limit)).fetchall()
            return jsonify([dict(r) for r in rows])
    else:
        D = load_json()
        result = []
        for gid, os_ in D.get("orders", {}).items():
            for o in os_:
                if status == "all" or o.get("status") == status:
                    result.append(o)
        result.sort(key=lambda x: x.get("ts", 0), reverse=True)
        return jsonify(result[:limit])

@app.route("/api/orders/<int:order_id>/complete", methods=["POST"])
def complete_order(order_id):
    if has_db():
        with db() as conn:
            conn.execute(
                "UPDATE orders SET status='ivykdyta', completed_at=? WHERE id=?",
                (time.time(), order_id)
            )
        return jsonify({"success": True})
    else:
        D = load_json()
        for gid, os_ in D.get("orders", {}).items():
            for o in os_:
                if o.get("id") == order_id:
                    o["status"] = "ivykdyta"
                    with open(DATA_FILE, "w", encoding="utf-8") as f:
                        json.dump(D, f, indent=2, ensure_ascii=False)
                    return jsonify({"success": True})
        return jsonify({"success": False, "error": "Nerastas"}), 404

@app.route("/api/tickets")
def tickets():
    status = request.args.get("status", "open")
    limit  = int(request.args.get("limit", 50))

    if has_db():
        with db() as conn:
            if status == "all":
                rows = conn.execute("SELECT * FROM tickets ORDER BY created_at DESC LIMIT ?", (limit,)).fetchall()
            else:
                rows = conn.execute("SELECT * FROM tickets WHERE status=? ORDER BY created_at DESC LIMIT ?", (status, limit)).fetchall()
            return jsonify([dict(r) for r in rows])
    else:
        D = load_json()
        result = []
        for gid, ts in D.get("tickets", {}).items():
            for ch_id, t in ts.items():
                entry = dict(t)
                entry["channel_id"] = ch_id
                entry["guild_id"] = gid
                entry["status"] = entry.get("status", "open")
                if status == "all" or entry["status"] == status:
                    result.append(entry)
        return jsonify(result[:limit])

@app.route("/api/tickets/stats")
def ticket_stats():
    if has_db():
        with db() as conn:
            total  = conn.execute("SELECT COUNT(*) as c FROM tickets").fetchone()["c"]
            open_  = conn.execute("SELECT COUNT(*) as c FROM tickets WHERE status='open'").fetchone()["c"]
            closed = conn.execute("SELECT COUNT(*) as c FROM tickets WHERE status='closed'").fetchone()["c"]
            avg_r  = conn.execute(
                "SELECT AVG((closed_at-created_at)/60) as a FROM tickets WHERE status='closed' AND closed_at IS NOT NULL"
            ).fetchone()["a"] or 0
            avg_rating = conn.execute(
                "SELECT AVG(rating) as a FROM tickets WHERE rating IS NOT NULL"
            ).fetchone()["a"] or 0
            return jsonify({"total":total,"open":open_,"closed":closed,"avg_minutes":round(avg_r,1),"avg_rating":round(avg_rating,1)})
    else:
        D = load_json()
        total = open_ = closed = 0
        for gid, ts in D.get("tickets", {}).items():
            for ch_id, t in ts.items():
                total += 1
                if t.get("status","open") == "open": open_ += 1
                else: closed += 1
        return jsonify({"total":total,"open":open_,"closed":closed,"avg_minutes":0,"avg_rating":0})

@app.route("/api/products")
def products():
    if has_db():
        with db() as conn:
            rows = conn.execute("SELECT * FROM products WHERE active=1 ORDER BY id").fetchall()
            return jsonify([dict(r) for r in rows])
    else:
        D = load_json()
        result = []
        for gid, ps in D.get("products", {}).items():
            for p in ps:
                p2 = dict(p)
                p2["guild_id"] = gid
                p2["active"] = 1
                p2["description"] = p2.get("desc", "")
                result.append(p2)
        return jsonify(result)

@app.route("/api/products", methods=["POST"])
def add_product():
    data = request.json
    if has_db():
        with db() as conn:
            cursor = conn.execute(
                "INSERT INTO products (guild_id,name,description,price,old_price,category,emoji,duration,stock) VALUES (?,?,?,?,?,?,?,?,?)",
                (data.get("guild_id","0"), data["name"], data.get("description",""),
                 data["price"], data.get("old_price"), data.get("category","other"),
                 data.get("emoji","📦"), data.get("duration","1 men."), data.get("stock",99))
            )
            return jsonify({"success": True, "id": cursor.lastrowid})
    return jsonify({"success": False, "error": "Naudok JSON duomenų bazę"}), 400

@app.route("/api/products/<int:pid>", methods=["DELETE"])
def delete_product(pid):
    if has_db():
        with db() as conn:
            conn.execute("UPDATE products SET active=0 WHERE id=?", (pid,))
        return jsonify({"success": True})
    return jsonify({"success": False}), 400

@app.route("/api/products/<int:pid>/stock", methods=["PATCH"])
def update_stock_api(pid):
    data = request.json
    new_stock = data.get("stock", 0)
    if has_db():
        with db() as conn:
            conn.execute("UPDATE products SET stock=? WHERE id=?", (new_stock, pid))
        return jsonify({"success": True})
    return jsonify({"success": False}), 400

@app.route("/api/settings/<gid>")
def get_settings_api(gid):
    if has_db():
        with db() as conn:
            conn.execute("INSERT OR IGNORE INTO guild_settings (guild_id) VALUES (?)", (gid,))
            row = conn.execute("SELECT * FROM guild_settings WHERE guild_id=?", (gid,)).fetchone()
            if row:
                d = dict(row)
                for k in ("blacklist","payment_methods","level_rewards"):
                    try: d[k] = json.loads(d.get(k) or "[]" if k=="blacklist" else "{}")
                    except: d[k] = [] if k=="blacklist" else {}
                return jsonify(d)
    D = load_json()
    return jsonify({
        "payment_methods": D.get("payment_methods", {}),
        "log_channel": D.get("log_channels", {}).get("0"),
        "blacklist": [],
        "level_rewards": D.get("level_rewards", {})
    })

@app.route("/api/settings/<gid>", methods=["PATCH"])
def update_settings_api(gid):
    data = request.json
    if has_db():
        with db() as conn:
            conn.execute("INSERT OR IGNORE INTO guild_settings (guild_id) VALUES (?)", (gid,))
            for key, val in data.items():
                if isinstance(val, (dict, list)):
                    val = json.dumps(val, ensure_ascii=False)
                try:
                    conn.execute(f"UPDATE guild_settings SET {key}=? WHERE guild_id=?", (val, gid))
                except: pass
        return jsonify({"success": True})
    return jsonify({"success": False}), 400

@app.route("/api/warnings")
def warnings_api():
    limit = int(request.args.get("limit", 20))
    if has_db():
        with db() as conn:
            rows = conn.execute("SELECT * FROM warnings ORDER BY created_at DESC LIMIT ?", (limit,)).fetchall()
            return jsonify([dict(r) for r in rows])
    else:
        D = load_json()
        result = []
        for gid, users in D.get("warnings", {}).items():
            for uid, warns in users.items():
                for w in warns:
                    result.append({
                        "guild_id": gid, "user_id": uid,
                        "reason": w.get("reason","?"),
                        "mod_name": w.get("mod","?"),
                        "created_at": w.get("ts", 0)
                    })
        result.sort(key=lambda x: x.get("created_at",0), reverse=True)
        return jsonify(result[:limit])

@app.route("/api/bank/transactions")
def bank_transactions():
    limit = int(request.args.get("limit", 20))
    if has_db():
        with db() as conn:
            rows = conn.execute("SELECT * FROM bank_transactions ORDER BY created_at DESC LIMIT ?", (limit,)).fetchall()
            return jsonify([dict(r) for r in rows])
    return jsonify([])

@app.route("/api/economy/stats")
def economy_stats():
    if has_db():
        with db() as conn:
            total  = conn.execute("SELECT COALESCE(SUM(coins),0) as s FROM members").fetchone()["s"]
            bank   = conn.execute("SELECT COALESCE(SUM(bank_balance),0) as s FROM members").fetchone()["s"]
            loans  = conn.execute("SELECT COALESCE(SUM(loan_amount),0) as s FROM members").fetchone()["s"]
            count  = conn.execute("SELECT COUNT(*) as c FROM members WHERE coins>0").fetchone()["c"]
            avg    = int(total / count) if count else 0
            top    = conn.execute("SELECT MAX(coins) as m FROM members").fetchone()["m"] or 0
            return jsonify({"total":total,"bank":bank,"loans":loans,"avg":avg,"top":top,"count":count})
    else:
        D = load_json()
        total = 0; count = 0
        for gid, users in D.get("coins",{}).items():
            for uid, c in users.items():
                total += c; count += 1
        return jsonify({"total":total,"bank":0,"loans":0,"avg":int(total/count) if count else 0,"top":0,"count":count})

@app.route("/api/fish/leaderboard")
def fish_leaderboard():
    limit = int(request.args.get("limit", 10))
    if has_db():
        with db() as conn:
            rows = conn.execute(
                "SELECT user_id, SUM(count) as total FROM fish_stats GROUP BY user_id ORDER BY total DESC LIMIT ?",
                (limit,)
            ).fetchall()
            return jsonify([dict(r) for r in rows])
    return jsonify([])

@app.route("/api/giveaways")
def giveaways_api():
    if has_db():
        with db() as conn:
            rows = conn.execute("SELECT * FROM giveaways WHERE ended=0 ORDER BY end_time").fetchall()
            result = []
            for r in rows:
                d = dict(r)
                d["participants"] = json.loads(d.get("participants","[]"))
                d["participants_count"] = len(d["participants"])
                result.append(d)
            return jsonify(result)
    return jsonify([])

@app.route("/api/members/<uid>/coins", methods=["PATCH"])
def update_coins(uid):
    data = request.json
    amount = data.get("amount", 0)
    gid = data.get("guild_id", "0")
    if has_db():
        with db() as conn:
            conn.execute(
                "UPDATE members SET coins=MAX(0,coins+?) WHERE guild_id=? AND user_id=?",
                (amount, gid, uid)
            )
        return jsonify({"success": True})
    return jsonify({"success": False}), 400

@app.route("/api/stats/activity")
def activity_stats():
    """Žinučių aktyvumas per paskutines 7 dienas"""
    if has_db():
        with db() as conn:
            # Jei yra message_log lentelė
            try:
                rows = conn.execute(
                    "SELECT date(created_at,'unixepoch') as day, COUNT(*) as count FROM message_log GROUP BY day ORDER BY day DESC LIMIT 7"
                ).fetchall()
                return jsonify([dict(r) for r in rows])
            except:
                pass
    # Demo data jei nėra
    days = []
    for i in range(6, -1, -1):
        d = datetime.datetime.now() - datetime.timedelta(days=i)
        days.append({"day": d.strftime("%Y-%m-%d"), "count": 0})
    return jsonify(days)

@app.route("/api/guilds")
def guilds():
    """Serverio sąrašas"""
    if has_db():
        with db() as conn:
            rows = conn.execute("SELECT DISTINCT guild_id FROM guild_settings").fetchall()
            return jsonify([r["guild_id"] for r in rows])
    D = load_json()
    gids = set()
    for section in ("coins","xp","orders","tickets"):
        gids.update(D.get(section,{}).keys())
    return jsonify(list(gids))

# ══════════════════════════════════════════════════════════════════════════════
#  SERVE DASHBOARD HTML
# ══════════════════════════════════════════════════════════════════════════════
@app.route("/")
def index():
    html_path = pathlib.Path(__file__).parent / "dashboard_real.html"
    if html_path.exists():
        return send_file(str(html_path))
    return "<h1>dashboard_real.html nerastas!</h1>", 404

if __name__ == "__main__":
    print("=" * 50)
    print("  💎 Kodas Bot — Web Dashboard")
    print("  http://localhost:5000")
    print("=" * 50)
    app.run(host="0.0.0.0", port=5000, debug=False)
