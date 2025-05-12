#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Backend für Lern-App  – 2025-05-12
──────────────────────────────────
• Rolling Log (log.txt)
• _id → id in allen Games-Antworten
• Detailliertes Answer-Logging (NEU)
"""

import os, sys, json, logging, datetime as dt, eventlet
eventlet.monkey_patch()

from logging.handlers import RotatingFileHandler
from flask import Flask, request, jsonify, Blueprint
from flask_cors import CORS
from flask_socketio import SocketIO, emit, join_room
from flask_jwt_extended import (
    JWTManager, create_access_token, create_refresh_token,
    jwt_required, get_jwt_identity
)
import pymongo
from bson.objectid import ObjectId, InvalidId
from dotenv import load_dotenv

# ───────── Logging ─────────────────────────────
LOG_FILE = os.path.join(os.path.dirname(__file__), "log.txt")
fmt = "%(asctime)s %(levelname)-8s [%(filename)s:%(lineno)d] %(message)s"

console = logging.StreamHandler(sys.stdout)
console.setFormatter(logging.Formatter(fmt))
file = RotatingFileHandler(LOG_FILE, maxBytes=5_000_000,
                           backupCount=3, encoding="utf-8")
file.setFormatter(console.formatter)
logging.basicConfig(level=logging.DEBUG, handlers=[console, file])
log = logging.getLogger(__name__)
log.info("🚀  Backend startet …")

# ───────── Config / DB ─────────────────────────
from config import Config
from models import create_user, verify_password
load_dotenv()

app = Flask(__name__)
app.config.from_object(Config)
CORS(app, supports_credentials=True, origins="*")
jwt = JWTManager(app)
socketio = SocketIO(app, cors_allowed_origins="*", async_mode="eventlet",
                    ping_timeout=25, ping_interval=10)

mongo = pymongo.MongoClient(app.config["MONGO_URI"])
db = mongo.get_default_database()
log.info("🗄️  MongoDB verbunden – DB: %s", db.name)

users_coll, chat_coll, friends_coll  = db["users"], db["chat"], db["friends"]
games_coll, friend_requests_coll     = db["games"], db["friend_requests"]



@app.before_request
def dbg_route():
    if request.path == "/games/new":
        log.warning("📥  >>> POST /games/new kommt in DIESEM Prozess an")
        
# ───────── Helper ──────────────────────────────
_now = lambda: dt.datetime.now(dt.timezone.utc).isoformat()

def expose_id(doc: dict) -> dict:
    if "_id" in doc:
        doc["id"] = str(doc.pop("_id"))
    return doc

def reduced_game_doc(g: dict) -> dict:
    gid = g.get("id") or g.get("_id")
    return {
        "id"            : str(gid),
        "hostName"      : g["hostName"],
        "friendName"    : g["friendName"],
        "totalQuestions": len(g["questions"]),
        "hostAnswered"  : len(g["hostAnswers"]),
        "friendAnswered": len(g["friendAnswers"]),
    }

def _open_games_with_badge(user: str):
    cur = games_coll.find(
        {"finished": {"$ne": True},
         "$or": [{"hostName": user}, {"friendName": user}]},
        sort=[("createdAt", pymongo.ASCENDING)]
    )
    games, unseen = [], 0
    for g in cur:
        expose_id(g)
        doc = reduced_game_doc(g)
        opp_done = (doc["hostAnswered"]==doc["totalQuestions"] or
                    doc["friendAnswered"]==doc["totalQuestions"])
        me_done  = ((user==g["hostName"] and doc["hostAnswered"]==doc["totalQuestions"]) or
                    (user==g["friendName"] and doc["friendAnswered"]==doc["totalQuestions"]))
        if opp_done and not me_done:
            unseen += 1
        games.append(doc)
    return games, unseen

   
def _open_games(user: str) -> list[dict]:
    """Immer frisches Ergebnis, sortiert nach Erstellzeit."""
    cursor = games_coll.find(
        {"finished": {"$ne": True},
         "$or"     : [{"hostName": user}, {"friendName": user}]},
        sort=[("createdAt", pymongo.ASCENDING)]
    )
    out = [reduced_game_doc(g) for g in cursor]
    log.debug("📤 openGames(%s) → %d Treffer", user, len(out))
    return out    

user_sid: dict[str, set[str]] = {}
sid_user: dict[str, str]      = {}

# ───────── Auth / Freunde ───────────────────────
auth_bp = Blueprint("auth", __name__, url_prefix="/auth")

def _tokens(u):  # JWT-Paar
    return {"access": create_access_token(identity=u),
            "refresh": create_refresh_token(identity=u)}

@auth_bp.post("/register")
def register():
    d = request.json or {}
    name, pw = d.get("name","").lower().strip(), d.get("password","")
    if len(name) < 3 or len(pw) < 6:
        return jsonify(msg="Name ≥3 / PW ≥6"), 400
    if users_coll.find_one({"name": name}):
        return jsonify(msg="Name belegt"), 409
    create_user(db, name, email=d.get("email"), password=pw)
    log.info("➕  User %s registriert", name)
    return jsonify(_tokens(name)), 201

@auth_bp.post("/login")
def login():
    d = request.json or {}
    name, pw = d.get("name","").lower().strip(), d.get("password","")
    if not verify_password(db, name, pw):
        return jsonify(msg="Login fehlgeschlagen"), 401
    log.info("🔑  Login OK für %s", name)
    return jsonify(_tokens(name))

@auth_bp.post("/refresh")
@jwt_required(refresh=True)
def refresh():
    return jsonify(access=create_access_token(identity=get_jwt_identity()))

# ------------- Freundschaft ----------------------
def _friendship_status(a,b):
    if friends_coll.find_one({"user": a, "friend": b}):
        return "friends"
    if friend_requests_coll.find_one(
        {"from_user":a,"to_user":b,"status":"pending"}) or \
       friend_requests_coll.find_one(
        {"from_user":b,"to_user":a,"status":"pending"}):
        return "pending"
    return None

@auth_bp.post("/friends/request")
@jwt_required()
def send_request():
    me = get_jwt_identity()
    pal = (request.json or {}).get("friendName","").lower().strip()
    if not pal or pal == me:
        return jsonify(msg="Ungültiger Name"), 400
    if not users_coll.find_one({"name": pal}):
        return jsonify(msg="User existiert nicht"), 404
    if _friendship_status(me, pal):
        return jsonify(msg="Schon Freunde / Anfrage offen"), 409
    friend_requests_coll.insert_one(
        {"from_user":me,"to_user":pal,"status":"pending","timestamp":_now()})
    log.info("🤝  Anfrage %s → %s", me, pal)
    for sid in user_sid.get(pal,()):
        socketio.emit("friend_request_received", {"from_user":me}, room=sid)
    return jsonify(msg="Anfrage gesendet"), 200

@auth_bp.get("/friends/list_with_status")
@jwt_required()
def friends_and_requests():
    me = get_jwt_identity()
    friends = [f["friend"] for f in
               friends_coll.find({"user":me},{"friend":1})]
    pending = list(friend_requests_coll.find(
        {"to_user":me,"status":"pending"},{"from_user":1,"timestamp":1}))
    for r in pending: r["_id"] = str(r["_id"])
    return jsonify(friends=friends, pending_requests=pending), 200

@auth_bp.post("/friends/requests/respond")
@jwt_required()
def respond_request():
    me = get_jwt_identity()
    d = request.json or {}
    frm, act = d.get("from_user","").lower(), d.get("action","").lower()
    req = friend_requests_coll.find_one(
        {"from_user":frm,"to_user":me,"status":"pending"})
    if not req:
        return jsonify(msg="Keine Anfrage"), 404
    if act == "accept":
        friend_requests_coll.update_one({"_id":req["_id"]},
                                        {"$set":{"status":"accepted"}})
        friends_coll.update_one({"user":me,"friend":frm},
                                {"$set":{"since":_now()}}, upsert=True)
        friends_coll.update_one({"user":frm,"friend":me},
                                {"$set":{"since":_now()}}, upsert=True)
        return jsonify(msg="Angenommen"), 200
    friend_requests_coll.delete_one({"_id":req["_id"]})
    return jsonify(msg="Abgelehnt"), 200

app.register_blueprint(auth_bp)

# ───────── Games ──────────────────────────────────
games_bp = Blueprint("games", __name__, url_prefix="/games")

@games_bp.post("/new")
@jwt_required()
def games_new():
    host = get_jwt_identity().lower()
    d = request.json or {}
    friend = (d.get("friendName") or "").lower().strip()
    qs     = d.get("questions", [])
    if not friend or friend == host or not qs:
        return jsonify(msg="Bad data"), 400
    gid = games_coll.insert_one({
        "hostName"        : host,
        "friendName"      : friend,
        "questions"       : qs,
        "hostAnswers"     : [],
        "friendAnswers"   : [],
        "createdAt"       : _now(),
        "finished"        : False,
        "hostSeenResult"  : False,
        "friendSeenResult": False,
        "hostCorrect"     : 0,
        "friendCorrect"   : 0
    }).inserted_id
    log.info("🎲  Spiel %s (%s vs %s, %d Fragen)", gid, host, friend, len(qs))
    
    gid_str = str(gid)
    log.info("🎲  Spiel %s (%s vs %s, %d Fragen)",
             gid_str, host, friend, len(qs))
    return jsonify(id=gid_str, gameId=gid_str), 200 

@games_bp.get("/open/<user>")
@jwt_required()
def games_open(user):
    games, unseen = _open_games_with_badge(user.lower())
    return jsonify(openGames=games, unseenOpen=unseen), 200
    
@games_bp.get("/<gid>")
@jwt_required()
def games_get(gid):
    try:
        g = games_coll.find_one({"_id": ObjectId(gid)})
    except (InvalidId, TypeError):
        return jsonify(msg="Bad ID"), 400
    if not g:
        return jsonify(msg="Not found"), 404
    expose_id(g); return jsonify(g), 200

@games_bp.patch("/<gid>/seen")
@jwt_required()
def games_seen(gid):
    user = get_jwt_identity().lower()
    try:
        obj = ObjectId(gid)
    except (InvalidId, TypeError):
        return jsonify(msg="bad id"), 400
    g = games_coll.find_one({"_id": obj})
    if not g or not g.get("finished"):
        return jsonify(msg="not found / not finished"), 404
    fld = ("hostSeenResult" if user == g["hostName"].lower() else
           "friendSeenResult" if user == g["friendName"].lower() else None)
    if fld is None:
        return jsonify(msg="no access"), 403
    games_coll.update_one({"_id": obj}, {"$set": {fld: True}})
    return jsonify(ok=True), 200

# ───────────────────────────────────────────────────────────
#   PATCH /games/<gid>/answer   –  erweitert mit Debug-Logs
# ───────────────────────────────────────────────────────────
@games_bp.patch("/<gid>/answer")
@jwt_required()
def games_answer(gid):
    user = get_jwt_identity().lower()

    # rohen Body + Meta loggen
    raw_body = request.get_data(as_text=True)
    log.debug("↘️  PATCH /games/%s/answer  user=%s  ip=%s  raw=%s",
              gid, user, request.remote_addr, raw_body[:300])

    # JSON sicher parsen
    try:
        data = request.get_json(force=True, silent=False)
    except Exception as e:
        log.warning("❌  invalid JSON in PATCH /games/%s/answer – %s", gid, e)
        return jsonify(msg="invalid json"), 400

    ans = (data or {}).get("answers", [])
    if not ans:
        log.warning("❌  no answers field – body=%s", raw_body)
        return jsonify(msg="no answers"), 400

    try:
        obj = ObjectId(gid)
    except (InvalidId, TypeError):
        return jsonify(msg="bad id"), 400

    game = games_coll.find_one({"_id": obj})
    if not game:
        return jsonify(msg="not found"), 404

    field = ("hostAnswers" if user == game["hostName"].lower()
             else "friendAnswers" if user == game["friendName"].lower()
             else None)
    if field is None:
        return jsonify(msg="not participant"), 403

    qids = [a["questionId"] for a in ans]
    res1 = games_coll.update_one({"_id": obj},
        {"$pull": {field: {"questionId": {"$in": qids}}}})
    res2 = games_coll.update_one({"_id": obj},
        {"$push": {field: {"$each": ans}}})
        
            # --- Auto-Finish prüfen ---------------------------------
    game = games_coll.find_one({"_id": obj})  # frisch holen
    total_q    = len(game["questions"])
    host_cnt   = len(game["hostAnswers"])
    friend_cnt = len(game["friendAnswers"])

    if (not game.get("finished")
        and host_cnt >= total_q and friend_cnt >= total_q):

        def _cnt_ok(arr): return sum(1 for a in arr if a["isCorrect"])
        host_ok   = _cnt_ok(game["hostAnswers"])
        friend_ok = _cnt_ok(game["friendAnswers"])

        games_coll.update_one({"_id": obj}, {"$set": {
            "finished"        : True,
            "finishedAt"      : _now(),
            "hostCorrect"     : host_ok,
            "friendCorrect"   : friend_ok,
            "hostSeenResult"  : False,
            "friendSeenResult": False
        }})
        log.info("🏁  Spiel %s automatisch beendet", gid)

    log.debug("📝  %s -> %s | %s  qids=%s  mongo pull=%s push=%s",
              user, gid, field, qids,
              res1.modified_count, res2.modified_count)
    return jsonify(ok=True), 200

@games_bp.get("/finished/<user>")
@jwt_required()
def games_finished(user):
    user = user.lower()
    cur = games_coll.find(
        {"finished": True,
         "$or": [{"hostName": user}, {"friendName": user}]},
        sort=[("finishedAt", pymongo.DESCENDING)]
    )

    finished, unseen = [], 0
    for g in cur:
        me_is_host = (user == g["hostName"].lower())
        expose_id(g)
        item = {
            "id"        : g["id"],
            "friendName": g["friendName"] if me_is_host else g["hostName"],
            "total"     : len(g["questions"]),
            "myCorrect" : g["hostCorrect"] if me_is_host else g["friendCorrect"],
            "oppCorrect": g["friendCorrect"] if me_is_host else g["hostCorrect"],
            "mySeen"    : g["hostSeenResult"] if me_is_host else g["friendSeenResult"],
            "finishedAt": g.get("finishedAt")
        }
        if not item["mySeen"]:
            unseen += 1
        finished.append(item)
    return jsonify(finishedGames=finished, unseenFinished=unseen), 200


# finish / delete Endpunkte bleiben unverändert …
@games_bp.post("/finish")
@jwt_required()
def games_finish():
    user = get_jwt_identity().lower()
    gid  = (request.json or {}).get("gameId","")
    try:
        obj = ObjectId(gid)
    except (InvalidId, TypeError):
        return jsonify(msg="Bad ID"), 400
    r = games_coll.update_one(
        {"_id":obj,"$or":[{"hostName":user},{"friendName":user}]},
        {"$set":{"finished":True,"finishedAt":_now()}})
    if not r.matched_count:
        return jsonify(msg="Not found / no access"), 404
    log.info("🏁  Spiel %s beendet von %s", gid, user)
    return jsonify(ok=True), 200

@games_bp.delete("/<gid>")
@jwt_required()
def games_delete(gid):
    user = get_jwt_identity().lower()
    try:
        obj = ObjectId(gid)
    except (InvalidId, TypeError):
        return jsonify(msg="Bad ID"), 400
    g = games_coll.find_one({"_id":obj})
    if not g or user not in {g["hostName"].lower(), g["friendName"].lower()}:
        return jsonify(msg="Not found / no access"), 404
    if g.get("finished"):
        return jsonify(msg="Already finished"), 409
    games_coll.delete_one({"_id":obj})
    log.warning("🗑️  Spiel %s von %s gelöscht", gid, user)
    return jsonify(ok=True), 200

app.register_blueprint(games_bp)

# ───────── Socket.IO ─────────────────────────────
@socketio.on("connect")
def s_connect():
    log.debug("🔌  client %s connected", request.sid)

@socketio.on("disconnect")
def s_disconnect():
    name = sid_user.pop(request.sid, None)
    if name:
        user_sid[name].discard(request.sid)
        if not user_sid[name]:
            user_sid.pop(name)
    log.debug("🔌  client %s disconnected", request.sid)

@socketio.on("init_username")
def s_init(name):
    name = (name or "").lower()
    sid_user[request.sid] = name
    user_sid.setdefault(name, set()).add(request.sid)
    join_room(name)
    emit("notification_reset", {
        "unreadMessages": chat_coll.count_documents(
            {"to":name,"read":{"$ne":True}}),
        "openGames": len(_open_games(name)),
        "pendingFriendRequests": friend_requests_coll.count_documents(
            {"to_user":name,"status":"pending"})
    }, room=request.sid)

# ───────── Hooks / Health ─────────────────────────
@app.before_request
def _log_req():
    log.debug("⇢ %s %s", request.method, request.path)

@app.after_request
def _log_resp(resp):
    log.debug("⇠ %s (%s %s)", resp.status, request.method, request.path)
    return resp

@app.errorhandler(500)
def _err_500(err):
    import traceback
    log.error("✖️  500 Internal\n%s", traceback.format_exc())
    return jsonify(msg="Interner Serverfehler"), 500

@app.get("/health")
def health():
    return {"ok": True, "time": _now()}

# ───────── Main ──────────────────────────────────
for r in app.url_map.iter_rules():
    if "games.new" in r.endpoint or "/games/new" in r.rule:
        log.warning("🔎  Route: %-20s  methods=%s  endpoint=%s",
                    r.rule, sorted(r.methods), r.endpoint)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 2001))
    debug= os.environ.get("FLASK_DEBUG","false").lower()=="true"
    log.info("🚀  Server läuft auf 0.0.0.0:%d (debug=%s)", port, debug)
    socketio.run(app, host="0.0.0.0", port=port,
                 debug=debug, use_reloader=debug)
