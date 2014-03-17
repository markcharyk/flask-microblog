from flask import Flask
from flask.ext.sqlalchemy import SQLAlchemy
from datetime import datetime
from flask.ext.script import Manager
from flask.ext.migrate import Migrate, MigrateCommand
from flask import abort, request, render_template
from flask import redirect, url_for, session, flash
from flask.ext.seasurf import SeaSurf
from flask.ext.bcrypt import Bcrypt
import random
import re
from flask.ext.mail import Mail, Message
import sys
from werkzeug.contrib.fixers import ProxyFix

app = Flask(__name__)
app.config.from_pyfile('config.py')
db = SQLAlchemy(app)
csrf = SeaSurf(app)
bcrypt = Bcrypt(app)
migrate = Migrate(app, db)

manager = Manager(app)
manager.add_command('db', MigrateCommand)

mail = Mail(app)

app.wsgi_app = ProxyFix(app.wsgi_app)
instance = 'http://ec2-54-186-73-177.us-west-2.compute.amazonaws.com'


class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(128))
    body = db.Column(db.Text)
    time = db.Column(db.DateTime)
    author_id = db.Column(db.Integer, db.ForeignKey('author.id'))
    auth_name = db.Column(db.String(128))

    def __init__(self, title, body, auth_id, auth_name):
        self.title = title
        self.body = body
        self.author_id = auth_id
        self.auth_name = auth_name
        self.time = datetime.utcnow()

    def __repr__(self):
        return '<Post %r>' % self.title


class Author(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(128))
    password = db.Column(db.String(128))
    posts = db.relationship('Post', backref='author')

    def __init__(self, username, password):
        self.username = username
        self.password = bcrypt.generate_password_hash(password)

    def __repr__(self):
        return '<Author %r>' % self.username


class TempAuthor(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(128))
    password = db.Column(db.String(128))
    reg_key = db.Column(db.String(32))
    time = db.Column(db.DateTime)

    def __init__(self, username, password):
        self.username = username
        self.password = password
        self.reg_key = random.randint(
            1000000000000000,
            9999999999999999
            )
        self.time = datetime.utcnow()


def write_post(title, text, auth_id, auth_name):
    new_post = Post(title, text, auth_id, auth_name)
    db.session.add(new_post)
    try:
        db.session.commit()
    except:
        print sys.exc_info()[0]


def read_posts():
    return Post.query.order_by(Post.time.desc()).all()


def read_post(id):
    post = Post.query.get(id)
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
        if session.get('logged_in', False):
            author = Author.query.filter_by(username=session['user']).first()
            write_post(
                request.form['post_title'],
                request.form['post_body'],
                author.id,
                author.username
                )
            return redirect(url_for('list_view'))
        else:
            flash("You must be logged in to perform this action.")
            return redirect(url_for('login'))
    return render_template('add_page.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        author = request.form['username']
        pw = request.form['password']
        try:
            login_user(author, pw)
        except ValueError:
            flash("Invalid username/password. Please try again.")
            return redirect(url_for('login'))
        flash("Now logged in as %s" % author)
        return redirect(url_for('list_view'))
    return render_template('login_page.html')


def login_user(username, password, newly_confirmed=False):
    existing_author = Author.query.filter_by(username=username).first()
    if not newly_confirmed:
        if existing_author is None:
            raise ValueError
        if not bcrypt.check_password_hash(existing_author.password, password):
            raise ValueError
    session['user'] = username
    session['logged_in'] = True


@app.route('/logout')
def logout():
    session.pop('user', None)
    session.pop('logged_in', None)
    return redirect(url_for('list_view'))


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        try:
            register_user({
                'username': request.form['username'],
                'first password': request.form['password'],
                'second password': request.form['password_2'],
                'email address': request.form['email']
                })
        except ValueError as e:
            flash(str(e))
            return redirect(url_for('register'))
        flash("""Great! You're well on your way! Please check your email
            and then you can log in below""")
        return redirect(url_for('login'))
    else:
        return render_template('register.html')


def register_user(info):
    for k, v in info.iteritems():
        if v is None or v == '':
            raise ValueError("The %s is missing" % k)
    extant_author = Author.query.filter_by(username=info['username']).first()
    extant_temp = TempAuthor.query.filter_by(username=info['username']).first()
    if extant_author is not None or extant_temp is not None:
        raise ValueError("I'm sorry, that username is already taken.")
    elif info['first password'] != info['second password']:
        raise ValueError("Please make sure the passwords match and try again.")
    elif not re.match(r"[^@]+@[^@]+\.[^@]+", info['email address']):
        # Credit for the regex to StackOverflow user 'Thomas'
        # http://stackoverflow.com/questions/8022530/python-check-for-valid-email-address
        raise ValueError("Not a valid email address.")
    temp_user = TempAuthor(info['username'], info['first password'])
    db.session.add(temp_user)
    db.session.commit()
    send_email(info['email address'], temp_user.reg_key)


def send_email(email, reg_key):
    msg = Message(
        "Subject",
        sender='markcharyk@gmail.com',
        recipients=[email])
    msg.body = """Click the link below to confirm your registration!
    /confirm/%s""" % reg_key
    msg.html = """<b>Click the link below to confirm your registration!<br>
    <a href="%s/confirm/%s">Confirm</a></b>""" % (instance, reg_key)
    mail.send(msg)


@app.route('/confirm/<reg_key>')
def confirm(reg_key):
    try:
        confirmed = TempAuthor.query.filter_by(reg_key=reg_key).first()
    except:
        confirmed = None
    if confirmed is None:
        flash("""Sorry!
            We don't recognize the account you're trying to confirm.""")
        return render_template('un-confirm.html')
    else:
        un_temp_user(confirmed)
        flash("""Congratulations! You've been confirmed!
            Please log in below""")
    return render_template('confirm.html')


def un_temp_user(user):
    new_author = Author(user.username, user.password)
    db.session.delete(user)
    db.session.add(new_author)
    db.session.commit()


@app.errorhandler(404)
def page_not_found(error):
    return render_template('not_found.html'), 404


if __name__ == '__main__':
    db.create_all()
    app.run()
