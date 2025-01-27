class LexiconEntry:
    def __init__(self, data):
        self.id = str(data.get('_id', ''))
        self.term = data.get('term', '')
        self.definition = data.get('definition', '')

    def to_dict(self):
        return {
            'id': self.id,
            'term': self.term,
            'definition': self.definition,
        }
