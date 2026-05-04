from data import  db_session
from data.notes import Note
from flask_restful import reqparse, abort, Resource
from flask import jsonify

parser = reqparse.RequestParser()
parser.add_argument('title', required=True)
parser.add_argument('content', required=True)
parser.add_argument('directory', required=True)
parser.add_argument('type', required=True)
parser.add_argument('public', required=True, type=bool)
parser.add_argument('user_id', required=True, type=int)

def abort_if_news_not_found(id):
    session = db_session.create_session()
    note = session.query(Note).get(id)
    if not note:
        abort(404, message=f"note {id} not found")

class NoteResource(Resource):
    def get(self, id):
        abort_if_news_not_found(id)
        db_sess = db_session.create_session()
        note = db_sess.get(Note, id)
        return jsonify({'note': note.to_dict(
            only=('title', 'content', 'directory', 'type', 'public', 'user_id'))})

    def delete(self, id):
        abort_if_news_not_found(id)
        session = db_session.create_session()
        note = session.get(Note, id)
        session.delete(note)
        session.commit()
        return jsonify({'success': 'OK'})


class NoteListResource(Resource):
    def get(self):
        session = db_session.create_session()
        notes = session.query(Note).all()
        return jsonify({'note': [i.to_dict(
            only=('id','title', 'content', 'directory', 'type', 'public', 'user_id')) for i in notes]})

    def post(self):
        args = parser.parse_args()
        session = db_session.create_session()
        note = Note(
            title=args['title'],
            content=args['content'],
            directory=args['directory'],
            type=args['type'],
            public=args['public'],
            user_id=args['user_id'],
        )
        session.add(note)
        session.commit()
        return jsonify({'success': 'OK'})