from flask_restful import Resource
from utils.database import db
from models.questions import Question
import logging

class QuestionsList(Resource):
    def get(self):
        try:
            questions_cursor = db.questions.find()
            questions = [Question(q).to_dict() for q in questions_cursor]
            logging.info(f"Retrieved {len(questions)} questions")
            return questions, 200
        except Exception as e:
            logging.error(f"Error retrieving questions: {e}")
            return {'message': 'Error retrieving questions'}, 500
