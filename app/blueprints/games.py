# app/blueprints/games.py
import logging
from bson.objectid import ObjectId, InvalidId
import pymongo

from flask import Blueprint, request, jsonify, current_app

from flask_jwt_extended import jwt_required, get_jwt_identity

from ..extensions import socketio
from ..utils import (
    _now, expose_id, reduced_game_doc, get_db,
    _open_games, _open_games_with_badge, _news_counts
)

log = logging.getLogger(__name__)
games_bp = Blueprint("games", __name__, url_prefix="/games")

@games_bp.get("/open/<username>")
@jwt_required()
def games_open(username):
    db = current_app.config["MONGO_CLIENT"].get_default_database()
    me = (get_jwt_identity() or "").strip().lower()
    u  = (username or "").strip()

    # optional: Schutz, damit niemand fremde Daten ziehen kann
    if me != u.lower():
        return jsonify(msg="forbidden"), 403

    cur = db["games"].find(
        {"$or": [{"hostName": u}, {"friendName": u}], "finishedAt": None}
    ).sort("createdAt", pymongo.DESCENDING)

    open_games = []
    unseen_open = 0
    
    for g in cur:
        host_cnt   = len(g.get("hostAnswers", []) or [])
        friend_cnt = len(g.get("friendAnswers", []) or [])
        total_q    = len(g.get("questions", []) or [])

        open_games.append({
            "id": str(g.get("_id")),
            "hostName": g.get("hostName"),
            "friendName": g.get("friendName"),
            "hostAnswered": host_cnt,
            "friendAnswered": friend_cnt,
            "totalQuestions": total_q,
        })
    return jsonify(openGames=open_games, unseenOpen=unseen_open), 200


@games_bp.get("/finished/<username>")
@jwt_required()
def games_finished(username):
    db = current_app.config["MONGO_CLIENT"].get_default_database()
    me = (get_jwt_identity() or "").strip().lower()
    u  = (username or "").strip()

    if me != u.lower():
        return jsonify(msg="forbidden"), 403

    cur = db["games"].find(
        {
            "$or": [{"hostName": u}, {"friendName": u}],
            "finishedAt": {"$ne": None},
        }
    ).sort("finishedAt", pymongo.DESCENDING)

    finished = []
    for g in cur:
        finished.append({
            "id": str(g.get("_id")),
            "friendName": g.get("friendName") if g.get("hostName") == u else g.get("hostName"),
            "total": g.get("totalQuestions", 0),
            "myCorrect": g.get("hostCorrect", 0) if g.get("hostName") == u else g.get("friendCorrect", 0),
            "oppCorrect": g.get("friendCorrect", 0) if g.get("hostName") == u else g.get("hostCorrect", 0),
            "mySeen": bool(g.get("hostSeen")) if g.get("hostName") == u else bool(g.get("friendSeen")),
            "finishedAt": g.get("finishedAt"),
        })
    return jsonify(finishedGames=finished), 200
    
@games_bp.post("/new")
@jwt_required()
def games_new():
    db = get_db()
    host = get_jwt_identity().lower()
    d = request.json or {}
    friend = (d.get("friendName") or "").lower().strip()
    qs     = d.get("questions", [])
    if not friend or friend == host or not qs:
        return jsonify(msg="Bad data"), 400
    gid = db.games.insert_one({
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
    unseen_open = _open_games_with_badge(friend)[1]
    socketio.emit("notification", {"openGames": unseen_open}, room=friend)
    gid_str = str(gid)
    return jsonify(id=gid_str, gameId=gid_str), 200



@games_bp.get("/<gid>")
@jwt_required()
def games_get(gid):
    db = get_db()
    try:
        g = db.games.find_one({"_id": ObjectId(gid)})
    except (InvalidId, TypeError):
        return jsonify(msg="Bad ID"), 400
    if not g:
        return jsonify(msg="Not found"), 404
    expose_id(g); return jsonify(g), 200

@games_bp.patch("/<gid>/answer")
@jwt_required()
def games_answer(gid):
    db = get_db()
    user = get_jwt_identity().lower()
    raw_body = request.get_data(as_text=True)
    log.debug("↘️  PATCH /games/%s/answer user=%s raw=%s", gid, user, raw_body[:300])

    try:
        data = request.get_json(force=True, silent=False)
    except Exception:
        return jsonify(msg="invalid json"), 400

    ans = (data or {}).get("answers", [])
    if not ans:
        return jsonify(msg="no answers"), 400

    try:
        obj = ObjectId(gid)
    except (InvalidId, TypeError):
        return jsonify(msg="bad id"), 400

    game = db.games.find_one({"_id": obj})
    if not game:
        return jsonify(msg="not found"), 404

    field = ("hostAnswers" if user == game["hostName"].lower()
             else "friendAnswers" if user == game["friendName"].lower()
             else None)
    if field is None:
        return jsonify(msg="not participant"), 403

    qids = [a["questionId"] for a in ans]
    db.games.update_one({"_id": obj}, {"$pull": {field: {"questionId": {"$in": qids}}}})
    db.games.update_one({"_id": obj}, {"$push": {field: {"$each": ans}}})

    game = db.games.find_one({"_id": obj})
    total_q    = len(game["questions"])
    host_cnt   = len(game["hostAnswers"])
    friend_cnt = len(game["friendAnswers"])

    if (not game.get("finished") and host_cnt >= total_q and friend_cnt >= total_q):
        def _cnt_ok(arr): return sum(1 for a in arr if a.get("isCorrect"))
        host_ok   = _cnt_ok(game["hostAnswers"])
        friend_ok = _cnt_ok(game["friendAnswers"])
        db.games.update_one({"_id": obj}, {"$set": {
            "finished"        : True,
            "finishedAt"      : _now(),
            "hostCorrect"     : host_ok,
            "friendCorrect"   : friend_ok,
            "hostSeenResult"  : False,
            "friendSeenResult": False,
            "hostAnswered":   host_cnt,
            "friendAnswered": friend_cnt,
            "totalQuestions": total_q,
        }})
    return jsonify(ok=True), 200



@games_bp.patch("/<gid>/seen")
@jwt_required()
def games_seen(gid):
    db = get_db()
    user = get_jwt_identity().lower()
    try:
        obj = ObjectId(gid)
    except (InvalidId, TypeError):
        return jsonify(msg="bad id"), 400
    g = db.games.find_one({"_id": obj})
    if not g or not g.get("finished"):
        return jsonify(msg="not found / not finished"), 404
    fld = ("hostSeenResult" if user == g["hostName"].lower()
           else "friendSeenResult" if user == g["friendName"].lower()
           else None)
    if fld is None:
        return jsonify(msg="no access"), 403
    db.games.update_one({"_id": obj}, {"$set": {fld: True}})
    return jsonify(ok=True), 200

@games_bp.post("/finish")
@jwt_required()
def games_finish():
    db = get_db()
    user = get_jwt_identity().lower()
    gid  = (request.json or {}).get("gameId", "")
    try:
        obj = ObjectId(gid)
    except (InvalidId, TypeError):
        return jsonify(msg="Bad ID"), 400
    g = db.games.find_one({"_id": obj})
    if not g or user not in {g["hostName"].lower(), g["friendName"].lower()}:
        return jsonify(msg="Not found / no access"), 404
    if g.get("finished"):
        return jsonify(msg="Already finished"), 409
    db.games.update_one({"_id": obj}, {"$set": {"finished": True, "finishedAt": _now()}})
    for u in (g["hostName"].lower(), g["friendName"].lower()):
        socketio.emit("notification_reset", _news_counts(u), room=u)
    return jsonify(ok=True), 200

@games_bp.delete("/<gid>")
@jwt_required()
def games_delete(gid):
    db = get_db()
    user = get_jwt_identity().lower()
    try:
        obj = ObjectId(gid)
    except (InvalidId, TypeError):
        return jsonify(msg="Bad ID"), 400
    g = db.games.find_one({"_id": obj})
    if not g or user not in {g["hostName"].lower(), g["friendName"].lower()}:
        return jsonify(msg="Not found / no access"), 404
    if g.get("finished"):
        return jsonify(msg="Already finished"), 409
    db.games.delete_one({"_id": obj})
    for u in (g["hostName"].lower(), g["friendName"].lower()):
        socketio.emit("notification_reset", _news_counts(u), room=u)
    return jsonify(ok=True), 200
