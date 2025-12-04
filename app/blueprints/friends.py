# app/blueprints/friends.py
import logging
from datetime import datetime, timezone
from typing import List

import pymongo
from flask import Blueprint, current_app, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity

log = logging.getLogger(__name__)
friends_bp = Blueprint("friends", __name__, url_prefix="/friends")

def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()

def _norm(u: str) -> str:
    return (u or "").strip().lower()

@friends_bp.record_once
def _create_indexes(setup_state):
    """Wird beim Registrieren des Blueprints ausgeführt (idempotent & robust)."""
    app = setup_state.app
    client = app.config["MONGO_CLIENT"]
    db = client.get_default_database()

    users = db["users"]

    # --- users.username: sicherstellen, dass es ein UNIQUE-Index ist ---
    desired_name = "username_asc"  # benutze den existierenden Namen, um Konflikte zu vermeiden
    desired_keys = [("username", pymongo.ASCENDING)]

    existing = list(users.list_indexes())
    username_idx = None
    for idx in existing:
        key_items = list(idx.get("key", {}).items())
        if key_items == desired_keys:
            username_idx = idx
            break

    if username_idx:
        if not username_idx.get("unique", False):
            users.drop_index(username_idx["name"])
            log.info("🗑️  dropped non-unique index on users.username (%s)", username_idx["name"])
        else:
            log.info("🗄️  users.username unique index already present (%s)", username_idx["name"])
    if not username_idx or not username_idx.get("unique", False):
        users.create_index(desired_keys, name=desired_name, unique=True)
        log.info("🗄️  created UNIQUE index users.username (%s)", desired_name)

    # --- friend_requests Indizes (idempotent) ---
    fr = db["friend_requests"]
    fr.create_index(
        [("requester", pymongo.ASCENDING), ("target", pymongo.ASCENDING)],
        name="friend_requests_unique_pair",
        unique=True,
    )
    fr.create_index([("target", pymongo.ASCENDING)], name="friend_requests_target_asc")
    fr.create_index([("createdAt", pymongo.DESCENDING)], name="friend_requests_created_desc")

    log.info("🗄️  friends: users.username index ensured")
    log.info("🗄️  friends: friend_requests indexes ensured")

@friends_bp.get("/list_with_status")
@jwt_required()
def list_with_status():
    """Liefert ausgehende/eingehende Pending-Requests und Friends (accepted)."""
    db = current_app.config["MONGO_CLIENT"].get_default_database()
    me = _norm(get_jwt_identity())

    # Pending, die ICH verschickt habe
    outgoing_cur = db["friend_requests"].find(
        {"requester": me, "status": {"$in": [None, "pending"]}},
        {"_id": 0, "requester": 1, "target": 1, "status": 1, "createdAt": 1},
    ).sort("createdAt", pymongo.DESCENDING)
    outgoing = [
        {
            "to": d.get("target"),
            "status": d.get("status") or "pending",
            "createdAt": d.get("createdAt"),
        }
        for d in outgoing_cur
    ]

    # Pending, die AN MICH gerichtet sind
    incoming_cur = db["friend_requests"].find(
        {"target": me, "status": {"$in": [None, "pending"]}},
        {"_id": 0, "requester": 1, "target": 1, "status": 1, "createdAt": 1},
    ).sort("createdAt", pymongo.DESCENDING)
    incoming = [
        {
            "from": d.get("requester"),
            "status": d.get("status") or "pending",
            "createdAt": d.get("createdAt"),
        }
        for d in incoming_cur
    ]

    # Friends = alle akzeptierten Beziehungen, beide Richtungen, dedupliziert
    accepted_cur = db["friend_requests"].find(
        {
            "status": "accepted",
            "$or": [{"requester": me}, {"target": me}],
        },
        {"_id": 0, "requester": 1, "target": 1},
    )
    friends_set = set()
    for d in accepted_cur:
        a = _norm(d.get("requester"))
        b = _norm(d.get("target"))
        other = b if a == me else a
        if other:
            friends_set.add(other)
    friends = sorted(friends_set)

    log.info("friends.list_with_status me=%s -> out=%d in=%d friends=%d",
             me, len(outgoing), len(incoming), len(friends))
    return jsonify(outgoing=outgoing, incoming=incoming, friends=friends), 200

@friends_bp.get("/search")
@jwt_required()
def search_users():
    """Suche nach Benutzernamen (Prefix- oder Teil-Suche, case-insensitive)."""
    db = current_app.config["MONGO_CLIENT"].get_default_database()
    me = _norm(get_jwt_identity())
    q = _norm(request.args.get("name", ""))

    if not q or len(q) < 2:
        return jsonify(items=[]), 200

    regex = {"$regex": q, "$options": "i"}

    cur = (
        db["users"]
        .find({"username": regex}, {"_id": 0, "username": 1})
        .sort("username", pymongo.ASCENDING)
        .limit(20)
    )

    items: List[dict] = []
    for doc in cur:
        u = doc.get("username") or ""
        if _norm(u) == me:
            continue  # sich selbst nicht listen
        items.append({"username": u, "displayName": u})

    log.info("friends.search q=%r me=%s -> %d hit(s) sample=%s",
             q, me, len(items), (items[:1] if items else []))
    return jsonify(items=items), 200

@friends_bp.post("/request")
@jwt_required()
def request_friendship():
    """
    Freundschaftsanfrage anlegen.
    Body: { "friendName": "<username>" }
    """
    db = current_app.config["MONGO_CLIENT"].get_default_database()
    me = _norm(get_jwt_identity())

    body = request.get_json(silent=True) or {}
    target = _norm(body.get("friendName"))

    if not target:
        return jsonify(msg="friendName required"), 400
    if target == me:
        return jsonify(msg="cannot request yourself"), 400

    # Zieluser muss existieren
    target_doc = db["users"].find_one({"username": target})
    if not target_doc:
        return jsonify(msg="user not found"), 404

    # schon bestehende Anfrage prüfen (unique-index fängt es ab, aber schönerer Fehler)
    existing = db["friend_requests"].find_one({"requester": me, "target": target})
    if existing:
        return jsonify(msg="request already exists"), 409

    # Gegenrichtung vorhanden? -> optional: direkt als "accepted" werten
    reverse = db["friend_requests"].find_one({"requester": target, "target": me})
    if reverse and (reverse.get("status") in (None, "pending")):
        now = _now_iso()
        db["friend_requests"].update_one(
            {"_id": reverse["_id"]},
            {"$set": {"status": "accepted", "respondedAt": now, "responder": me}},
        )
        db["friend_requests"].insert_one(
            {
                "requester": me,
                "target": target,
                "status": "accepted",
                "createdAt": now,
                "respondedAt": now,
                "responder": me,
            }
        )
        return jsonify(ok=True, matched=True, status="accepted"), 201

    # normale pending-Anfrage
    ins = db["friend_requests"].insert_one(
        {
            "requester": me,
            "target": target,
            "status": "pending",  # pending | accepted | declined | removed
            "createdAt": _now_iso(),
            "respondedAt": None,
            "responder": None,
        }
    )
    return jsonify(ok=True, id=str(ins.inserted_id), status="pending"), 201

# NEW: Anfrage beantworten (accept/decline)
@friends_bp.post("/respond")
@jwt_required()
def respond_request():
    """
    Body: { "from": "<username>", "action": "accept" | "decline" }
    """
    db = current_app.config["MONGO_CLIENT"].get_default_database()
    me = _norm(get_jwt_identity())

    body = request.get_json(silent=True) or {}
    frm = _norm(body.get("from"))
    action = _norm(body.get("action"))

    if not frm or action not in ("accept", "decline"):
        return jsonify(msg="bad request"), 400

    pending = db["friend_requests"].find_one(
        {"requester": frm, "target": me, "status": {"$in": [None, "pending"]}}
    )
    if not pending:
        return jsonify(msg="request not found"), 404

    now = _now_iso()

    if action == "decline":
        db["friend_requests"].update_one(
            {"_id": pending["_id"]},
            {"$set": {"status": "declined", "respondedAt": now, "responder": me}},
        )
        return jsonify(ok=True, status="declined"), 200

    # accept
    db["friend_requests"].update_one(
        {"_id": pending["_id"]},
        {"$set": {"status": "accepted", "respondedAt": now, "responder": me}},
    )

    # Gegeneintrag sicherstellen (akzeptiert)
    reverse = db["friend_requests"].find_one({"requester": me, "target": frm})
    if reverse:
        if reverse.get("status") in (None, "pending"):
            db["friend_requests"].update_one(
                {"_id": reverse["_id"]},
                {"$set": {"status": "accepted", "respondedAt": now, "responder": me}},
            )
    else:
        db["friend_requests"].insert_one(
            {
                "requester": me,
                "target": frm,
                "status": "accepted",
                "createdAt": now,
                "respondedAt": now,
                "responder": me,
            }
        )

    return jsonify(ok=True, status="accepted"), 200

# NEW: Freundschaft entfernen (idempotent)
@friends_bp.delete("/<name>")
@jwt_required()
def delete_friend(name: str):
    """
    Entfernt eine bestehende Freundschaft zwischen mir und <name>.
    Wir markieren akzeptierte Anfragen als 'removed' (beide Richtungen).
    """
    db = current_app.config["MONGO_CLIENT"].get_default_database()
    me = _norm(get_jwt_identity())
    pal = _norm(name)
    if not pal or pal == me:
        return jsonify(msg="bad request"), 400

    now = _now_iso()
    res = db["friend_requests"].update_many(
        {
            "status": "accepted",
            "$or": [
                {"requester": me, "target": pal},
                {"requester": pal, "target": me},
            ],
        },
        {"$set": {"status": "removed", "removedAt": now, "responder": me}},
    )
    # Auch pending Gegeneinträge sinnvoll aufräumen
    db["friend_requests"].delete_many(
        {
            "status": {"$in": [None, "pending", "declined"]},
            "$or": [
                {"requester": me, "target": pal},
                {"requester": pal, "target": me},
            ],
        }
    )

    log.info("friends.delete me=%s pal=%s -> modified=%d", me, pal, res.modified_count)
    return jsonify(ok=True), 200
