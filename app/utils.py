# app/utils.py
import datetime as dt
import pymongo
from flask import current_app

def _now():
    return dt.datetime.now(dt.timezone.utc).isoformat()

def get_db():
    """Convenience: hole die Default-DB aus dem globalen MongoClient."""
    return current_app.config["MONGO_CLIENT"].get_default_database()

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
    db = get_db()
    cur = db["games"].find(
        {"finished": {"$ne": True},
         "$or"     : [{"hostName": user}, {"friendName": user}]},
        sort=[("createdAt", pymongo.ASCENDING)]
    )
    games, unseen = [], 0
    for g in cur:
        expose_id(g)
        doc = reduced_game_doc(g)
        me_done = (
            (user == g["hostName"]   and doc["hostAnswered"]  == doc["totalQuestions"]) or
            (user == g["friendName"] and doc["friendAnswered"] == doc["totalQuestions"])
        )
        if not me_done:
            unseen += 1
        games.append(doc)
    return games, unseen

def _open_games(user: str):
    db = get_db()
    cursor = db["games"].find(
        {"finished": {"$ne": True},
         "$or"     : [{"hostName": user}, {"friendName": user}]},
        sort=[("createdAt", pymongo.ASCENDING)]
    )
    return [reduced_game_doc(g) for g in cursor]

def _unread_chat(name: str) -> int:
    return get_db()["chat"].count_documents({"to": name, "read": {"$ne": True}})

def _pending_requests(name: str) -> int:
    return get_db()["friend_requests"].count_documents({"to_user": name, "status": "pending"})

def _news_counts(name: str) -> dict:
    _, unseen_open = _open_games_with_badge(name)
    return {
        "unreadMessages": _unread_chat(name),
        "openGames": unseen_open,
        "pendingFriendRequests": _pending_requests(name),
    }
