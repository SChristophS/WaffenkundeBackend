# app/sockets.py
import logging
from bson.objectid import ObjectId
from flask import request
from .utils import _open_games_with_badge, _news_counts, get_db

log = logging.getLogger(__name__)

user_sid: dict[str, set[str]] = {}
sid_user: dict[str, str]      = {}

def register_socketio_handlers(socketio):

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
        socketio.emit("notification_reset", _news_counts(name), room=request.sid)
        log.debug("🔗  s_init: %s -> %s", request.sid, name)

    @socketio.on("refresh_notifications")
    def s_refresh(_):
        name = sid_user.get(request.sid)
        if name:
            socketio.emit("notification_reset", _news_counts(name), room=request.sid)

    @socketio.on("game_progress")
    def s_game_progress(data):
        user = sid_user.get(request.sid)
        if not user:
            log.warning("⚠️  game_progress von unbekanntem Socket %s", request.sid); return
        gid = data.get("gameId"); ans = data.get("answered")
        if not gid or not isinstance(ans, int):
            log.warning("⚠️  Ungültiger Fortschritts-Datensatz: %s", data); return

        try:
            obj = ObjectId(gid)
        except Exception:
            log.warning("❌  Ungültige ObjectId: %s", gid); return

        db = get_db()
        g = db.games.find_one({"_id": obj})
        if not g: return
        field = "hostAnswers" if user == g["hostName"].lower() else ("friendAnswers" if user == g["friendName"].lower() else None)
        if not field: return

        other = g["friendName"] if user == g["hostName"].lower() else g["hostName"]
        unseen_open = _open_games_with_badge(other.lower())[1]
        socketio.emit("notification", {"openGames": unseen_open,
                                       "progressUpdate":{"gameId":gid,"answered":ans,"from":user}},
                      room=other.lower())
        socketio.emit("game_progress", {"gameId": gid, "answered": ans}, room=other.lower(), include_self=False)
