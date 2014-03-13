from flask import Flask
from flask.ext.sqlalchemy import SQLAlchemy
from datetime import datetime
from flask.ext.script import Manager
from flask.ext.migrate import Migrate, MigrateCommand
from flask import abort, render_template

app = Flask(__name__)
app.testing = True
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


# class User(db.Model):
#     pass


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


@app.route('/')
def list_view():
    posts = read_posts()
    return render_template('list_page.html', list=posts)


@app.route('/post/<id>')
def perma_view(id):
    try:
        return render_template('permalink_page.html', post=read_post(id))
    except IndexError:
        abort(404)


@app.route('/new')
def add_post():
    pass


@app.errorhandler(404)
def page_not_found(error):
    return render_template('not_found.html'), 404


if __name__ == '__main__':
    # db.create_all()
    app.run()
