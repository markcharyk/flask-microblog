from flask import Flask
from flask.ext.sqlalchemy import SQLAlchemy
from datetime import datetime
from flask.ext.script import Manager
from flask.ext.migrate import Migrate, MigrateCommand
from flask import abort, request, render_template
from flask import redirect, url_for, session, flash
from flask.ext.seasurf import SeaSurf
from flask.ext.bcrypt import Bcrypt

app = Flask(__name__)
app.testing = True
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql:///microblog'
db = SQLAlchemy(app)
csrf = SeaSurf(app)
bcrypt = Bcrypt(app)
migrate = Migrate(app, db)

manager = Manager(app)
manager.add_command('db', MigrateCommand)

app.secret_key = "\x8c\x85p+\xe7\x08\x8e\x04y\xfa\xa9#\xael\xf1\x10\xa5\xc8\x96*\xd024A"


class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(127))
    body = db.Column(db.Text)
    time = db.Column(db.DateTime)
    author_id = db.Column(db.Integer, db.ForeignKey('author.id'))

    def __init__(self, title, body):
        self.title = title
        self.body = body
        self.time = datetime.utcnow()

    def __repr__(self):
        return '<Post %r>' % self.title


class Author(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(127))
    password = db.Column(db.String(127))
    posts = db.relationship('Post', backref='author')

    def __init__(self, username, password):
        self.username = username
        self.password = bcrypt.generate_password_hash(password)

    def __repr__(self):
        return '<Author %r>' % self.username


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


@app.route('/new', methods=['GET', 'POST'])
def add_post():
    if request.method == 'POST':
        write_post(request.form['post_title'], request.form['post_body'])
        return redirect(url_for('list_view'))
    return render_template('add_page.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        author = request.form['username']
        pw = request.form['password']
        existing_author = Author.query().filter_by(username=author).first()
        if bcrypt.check_password_hash(existing_author.password, pw):
            session['username'] = author
            return redirect(url_for('list_view'))
        flash("Incorrect username/password. Please try again!")
        return redirect(url_for('login'))
    return render_template('login_page.html')


@app.route('/logout')
def logout():
    if request.method == 'POST':
        session.pop('username', None)
    return redirect(url_for('list_view'))


@app.errorhandler(404)
def page_not_found(error):
    return render_template('not_found.html'), 404


if __name__ == '__main__':
    # db.create_all()
    app.run()
