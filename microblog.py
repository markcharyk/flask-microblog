from flask import Flask
from flask.ext.sqlalchemy import SQLAlchemy
from datetime import datetime
from flask.ext.script import Manager
from flask.ext.migrate import Migrate, MigrateCommand

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql:///microblog'
db = SQLAlchemy(app)
migrate = Migrate(app, db)

manager = Manager(app)
manager.add_command('db', MigrateCommand)


class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(128))
    body = db.Column(db.Text)
    time = db.Column(db.DateTime)

    def __init__(self, title, body):
        self.title = title
        self.body = body
        self.time = datetime.utcnow()

    def __repr__(self):
        return '<Post %r>' % self.title


def write_post(title, text):
    new_post = Post(title, text)
    db.session.add(new_post)
    db.session.commit()


def read_posts():
    result = []
    for i in reversed(db.session.query(Post).all()):
        result.append(i)
    return result


def read_post(id):
    post = db.session.query(Post).filter_by(id=id).first()
    if post is not None:
        return post
    raise IndexError


if __name__ == '__main__':
    manager.run()
