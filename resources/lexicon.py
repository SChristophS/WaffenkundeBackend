from flask_restful import Resource
from utils.database import db
from models.lexicon_entry import LexiconEntry
import logging

class LexiconList(Resource):
    def get(self):
        try:
            lexicon_cursor = db.lexicon.find()
            lexicon = [LexiconEntry(l).to_dict() for l in lexicon_cursor]
            logging.info(f"Retrieved {len(lexicon)} lexicon entries")
            return lexicon, 200
        except Exception as e:
            logging.error(f"Error retrieving lexicon: {e}")
            return {'message': 'Error retrieving lexicon entries'}, 500
