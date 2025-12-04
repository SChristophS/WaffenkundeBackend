# app/blueprints/feedback.py
import json
import csv
import logging
from io import StringIO
from datetime import datetime, timezone
import os

import pymongo
from bson.objectid import ObjectId
from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity, verify_jwt_in_request

log = logging.getLogger(__name__)

# Blueprint OHNE extra url_prefix hier,
# wir registrieren das Prefix zentral in app/__init__.py
feedback_bp = Blueprint("feedback", __name__)


def _now():
    return datetime.now(timezone.utc).isoformat()


def _is_admin(user: str) -> bool:
    admins = (current_app.config.get("FEEDBACK_ADMINS") or "")
    wl = {u.strip().lower() for u in admins.split(",") if u.strip()}
    return bool(user) and user.lower() in wl


@feedback_bp.record_once
def _create_indexes(setup_state):
    """Wird beim Registrieren des Blueprints aufgerufen."""
    app = setup_state.app
    mongo_client = app.config["MONGO_CLIENT"]
    db = mongo_client.get_default_database()
    db["feedback"].create_index(
        [("createdAt", pymongo.DESCENDING)], name="createdAt_desc"
    )
    db["feedback"].create_index(
        [("questionId", pymongo.ASCENDING)], name="questionId_asc"
    )
    db["feedback"].create_index(
        [("resolved", pymongo.ASCENDING)], name="resolved_asc"
    )
    log.info("🗄️  feedback indexes ensured")


def _debug_jwt_info():
    """Debug-Helper: Zeigt im Log Infos zum Token und Secret."""
    auth_header = request.headers.get("Authorization", "")
    token_part = auth_header[:40] + "..." if auth_header else None
    log.info("[JWT DEBUG] Incoming token=%s", token_part)
    log.info("[JWT DEBUG] JWT_SECRET_KEY in app.config=%r",
             current_app.config.get("JWT_SECRET_KEY"))
    try:
        verify_jwt_in_request()
        log.info("[JWT DEBUG] Token verification succeeded for user=%s", get_jwt_identity())
    except Exception as e:
        log.warning("[JWT DEBUG] Token verification failed: %s", e)


@feedback_bp.post("")
@jwt_required(optional=True)
def create_feedback():
    _debug_jwt_info()
    db = current_app.config["MONGO_CLIENT"].get_default_database()
    user = get_jwt_identity()
    data = request.get_json(force=True, silent=False) or {}

    qid = (data.get("questionId") or "").strip()
    text = (data.get("feedback") or "").strip()
    qtxt = (data.get("questionText") or "").strip()
    meta = data.get("meta") or {}

    if not qid or not text:
        return jsonify(msg="questionId und feedback sind Pflicht"), 400

    ins = db["feedback"].insert_one(
        {
            "questionId": qid,
            "questionText": qtxt,
            "feedback": text,
            "meta": meta,
            "username": (user or "").lower() or None,
            "userAgent": request.headers.get("User-Agent"),
            "createdAt": _now(),
            "resolved": False,
            "resolvedAt": None,
            "resolver": None,
        }
    )
    return jsonify(id=str(ins.inserted_id)), 201


@feedback_bp.get("")
@jwt_required()
def list_feedback():
    _debug_jwt_info()
    db = current_app.config["MONGO_CLIENT"].get_default_database()
    user = get_jwt_identity()
    if not _is_admin(user):
        return jsonify(msg="forbidden"), 403

    q = {}
    resolved = request.args.get("resolved")
    if resolved in {"true", "false"}:
        q["resolved"] = (resolved == "true")
    qid = request.args.get("questionId")
    if qid:
        q["questionId"] = qid

    limit = min(int(request.args.get("limit", 100)), 1000)
    skip = max(int(request.args.get("skip", 0)), 0)

    cur = (
        db["feedback"]
        .find(q)
        .sort("createdAt", pymongo.DESCENDING)
        .skip(skip)
        .limit(limit)
    )
    out = []
    for d in cur:
        d["id"] = str(d.pop("_id"))
        out.append(d)
    return jsonify(items=out, count=len(out)), 200


@feedback_bp.patch("/<fid>/resolve")
@jwt_required()
def mark_resolved(fid):
    _debug_jwt_info()
    db = current_app.config["MONGO_CLIENT"].get_default_database()
    user = get_jwt_identity()
    if not _is_admin(user):
        return jsonify(msg="forbidden"), 403

    try:
        obj = ObjectId(fid)
    except Exception:
        return jsonify(msg="bad id"), 400

    body = request.get_json(silent=True) or {}
    value = bool(body.get("resolved", True))
    upd = {
        "resolved": value,
        "resolvedAt": _now() if value else None,
        "resolver": user if value else None,
    }
    res = db["feedback"].update_one({"_id": obj}, {"$set": upd})
    if res.matched_count == 0:
        return jsonify(msg="not found"), 404
    return jsonify(ok=True), 200


@feedback_bp.get("/admin_status")
@jwt_required()
def admin_status():
    """
    Liefert { username, is_admin } basierend auf FEEDBACK_ADMINS.
    Schlank, keine DB-Reads außer auf config; ideal für UI-Guards.
    """
    user = (get_jwt_identity() or "").strip().lower()
    return jsonify(username=user, is_admin=_is_admin(user)), 200
    
    
@feedback_bp.get("/export.csv")
@jwt_required()
def export_csv():
    _debug_jwt_info()
    db = current_app.config["MONGO_CLIENT"].get_default_database()
    user = get_jwt_identity()
    if not _is_admin(user):
        return jsonify(msg="forbidden"), 403

    q = {}
    resolved = request.args.get("resolved")
    if resolved in {"true", "false"}:
        q["resolved"] = (resolved == "true")

    cur = db["feedback"].find(q).sort("createdAt", pymongo.DESCENDING)
    sio = StringIO()
    w = csv.writer(sio)
    w.writerow(
        [
            "id",
            "createdAt",
            "username",
            "questionId",
            "questionText",
            "feedback",
            "resolved",
            "resolvedAt",
            "resolver",
            "meta",
        ]
    )
    for d in cur:
        w.writerow(
            [
                str(d.get("_id")),
                d.get("createdAt", ""),
                d.get("username", ""),
                d.get("questionId", ""),
                (d.get("questionText", "") or "").replace("\n", " ").strip(),
                (d.get("feedback", "") or "").replace("\n", " ").strip(),
                d.get("resolved", False),
                d.get("resolvedAt", ""),
                d.get("resolver", ""),
                json.dumps(d.get("meta") or {}, ensure_ascii=False),
            ]
        )
    return current_app.response_class(
        sio.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment; filename=feedback_export.csv"},
    )
