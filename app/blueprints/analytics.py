# app/blueprints/analytics.py
import logging, pymongo, datetime as dt
from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from ..utils import get_db

log = logging.getLogger(__name__)
analytics_bp = Blueprint("analytics", __name__, url_prefix="/analytics")

@analytics_bp.route("/stats/mine", methods=["GET"])
@jwt_required()
def stats_mine():
    """
    Liefert Gegner-aggregierte Stats für den eingeloggten User.
    Response:
      { "rows": [
          { "opponent": str, "games": int, "wins": int, "losses": int,
            "myCorrect": int, "oppCorrect": int }
        ] }
    """
    db = get_db()
    user = get_jwt_identity()

    pipeline = [
        # Nur fertige Spiele des Users
        {"$match": {
            "finished": True,
            "$or": [{"hostName": user}, {"friendName": user}]
        }},
        # Pro Spiel: Gegnername + meine/deren Corrects + Sieg/Niederlage
        {"$project": {
            "opponent": {
                "$cond": [{"$eq": ["$hostName", user]}, "$friendName", "$hostName"]
            },
            "myCorrect": {
                "$cond": [{"$eq": ["$hostName", user]}, "$hostCorrect", "$friendCorrect"]
            },
            "oppCorrect": {
                "$cond": [{"$eq": ["$hostName", user]}, "$friendCorrect", "$hostCorrect"]
            },
        }},
        {"$addFields": {
            "win": {"$cond": [{"$gt": ["$myCorrect", "$oppCorrect"]}, 1, 0]},
            "loss": {"$cond": [{"$lt": ["$myCorrect", "$oppCorrect"]}, 1, 0]}
        }},
        # Aggregation pro Gegner
        {"$group": {
            "_id": "$opponent",
            "games": {"$sum": 1},
            "wins": {"$sum": "$win"},
            "losses": {"$sum": "$loss"},
            "myCorrect": {"$sum": "$myCorrect"},
            "oppCorrect": {"$sum": "$oppCorrect"},
        }},
        # Ausgabeformat
        {"$project": {
            "_id": 0,
            "opponent": "$_id",
            "games": 1,
            "wins": 1,
            "losses": 1,
            "myCorrect": 1,
            "oppCorrect": 1
        }},
        # optional: meist gespielte zuerst
        {"$sort": {"games": -1, "opponent": 1}}
    ]

    rows = list(db.games.aggregate(pipeline))
    return jsonify({"rows": rows}), 200
    
@analytics_bp.route("/analytics/<username>")
def get_analytics(username):
    db = current_app.config["MONGO_CLIENT"].get_default_database()

    pipeline = [
        {"$match": {"$or": [{"player1": username}, {"player2": username}]}},
        {
            "$project": {
                "myCorrect": {
                    "$cond": [
                        {"$eq": ["$player1", username]},
                        "$player1Correct",
                        "$player2Correct"
                    ]
                },
                "oppCorrect": {
                    "$cond": [
                        {"$eq": ["$player1", username]},
                        "$player2Correct",
                        "$player1Correct"
                    ]
                }
            }
        },
        {
            "$group": {
                "_id": None,
                "wins": {
                    "$sum": {
                        "$cond": [
                            {"$gt": ["$myCorrect", "$oppCorrect"]},
                            1,
                            0
                        ]
                    }
                },
                "losses": {
                    "$sum": {
                        "$cond": [
                            {"$lt": ["$myCorrect", "$oppCorrect"]},
                            1,
                            0
                        ]
                    }
                },
                "draws": {
                    "$sum": {
                        "$cond": [
                            {"$eq": ["$myCorrect", "$oppCorrect"]},
                            1,
                            0
                        ]
                    }
                }
            }
        }
    ]

    stats = list(db.games.aggregate(pipeline))
    return jsonify(stats[0] if stats else {"wins": 0, "losses": 0, "draws": 0})

@analytics_bp.route("/attempts/batch", methods=["POST"])
@jwt_required()
def attempts_batch():
    db = get_db()
    user = get_jwt_identity()
    data = request.get_json(force=True) or {}
    attempts = data.get("attempts", [])
    if not isinstance(attempts, list) or not attempts:
        return jsonify(msg="invalid payload"), 400

    docs = []
    now = dt.datetime.now(dt.timezone.utc).isoformat()
    for a in attempts:
        docs.append({
            "username"       : user,
            "questionId"     : a.get("questionId"),
            "timestamp"      : a.get("timestamp") or now,
            "isCorrect"      : bool(a.get("isCorrect")),
            "sessionId"      : a.get("sessionId", ""),
            "chapterTitle"   : a.get("chapterTitle", ""),
            "subchapterId"   : a.get("subchapterId", ""),
            "subchapterTitle": a.get("subchapterTitle", ""),
        })
    if docs:
        db["question_attempts"].insert_many(docs)
    return jsonify(inserted=len(docs)), 200
