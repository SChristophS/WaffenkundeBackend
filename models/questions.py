class Question:
    def __init__(self, data):
        self.id = str(data.get('_id', ''))
        self.question = data.get('question', '')
        self.answer_options = data.get('answerOptions', [])
        self.correct_index = data.get('correctIndex', 0)
        self.references = data.get('references', [])

    def to_dict(self):
        return {
            'id': self.id,
            'question': self.question,
            'answerOptions': self.answer_options,
            'correctIndex': self.correct_index,
            'references': self.references,
        }
