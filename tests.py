import unittest
from datetime import datetime
from microblog import app, db, Post, Author, write_post, read_posts, read_post, login_user
from flask import session
import tempfile
import os


class TestWritePost(unittest.TestCase):
    def setUp(self):
        db.create_all()

    def testWriteOne(self):
        expected = Post(u"First Post", u"""
            The text containing the first post in the blog.""")
        write_post(u"First Post", u"""
            The text containing the first post in the blog.""")
        actual = db.session.query(Post).filter_by(title=u'First Post').first()
        self.assertEqual(expected.title, actual.title)
        self.assertEqual(expected.body, actual.body)
        self.assertIsInstance(actual.time, datetime)

    def tearDown(self):
        db.session.remove()
        db.drop_all()


class TestReadPosts(unittest.TestCase):
    def setUp(self):
        db.create_all()

    def testReadOne(self):
        expected = Post(u"New Post", u"""
            The text containing the newest post in the blog.""")
        write_post(u"New Post", u"""
            The text containing the newest post in the blog.""")
        actual = read_posts()[0]
        self.assertEqual(expected.title, actual.title)
        self.assertEqual(expected.body, actual.body)
        self.assertIsInstance(actual.time, datetime)

    def testEmpty(self):
        self.assertEqual(len(read_posts()), 0)

    def tearDown(self):
        db.session.remove()
        db.drop_all()


class TestReadPost(unittest.TestCase):
    def setUp(self):
        db.create_all()

    def testEmpty(self):
        with self.assertRaises(IndexError):
            read_post(1)

    def testFirst(self):
        write_post(u"Newer Post", u"""
            The text containing the newer post in the blog.""")
        self.assertIsInstance(read_post(1), Post)

    def tearDown(self):
        db.session.remove()
        db.drop_all()


class TestListPage(unittest.TestCase):
    def setUp(self):
        self.db_fd, app.config['DATABASE'] = tempfile.mkstemp()
        app.config['TESTING'] = True
        self.client = app.test_client()
        db.create_all()

    def testEmpty(self):
        with app.test_request_context():
            expected = 'No posts to display'
            response = self.client.get('/').data
            assert expected in response

    def testOne(self):
        with app.test_request_context():
            write_post(u"Post Title", u"A generic blog post")
            expected = ('Post Title', 'A generic blog post')
            response = self.client.get('/').data
            for elem in expected:
                assert elem in response

    def testMany(self):
        with app.test_request_context():
            write_post(u"Post Number One", u"Some text that makes up blog post number one")
            write_post(u"Post Number Two", u"Some text that makes up blog post number two")
            write_post(u"Post Number Three", u"Some text that makes up blog post number three")
            expected = ('Post Number One', 'Post Number Two', 'Post Number Three', 'Some text')
            response = self.client.get('/').data
            for elem in expected:
                assert elem in response

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        os.close(self.db_fd)
        os.unlink(app.config['DATABASE'])


class TestPermaPage(unittest.TestCase):
    def setUp(self):
        self.db_fd, app.config['DATABASE'] = tempfile.mkstemp()
        app.config['TESTING'] = True
        self.client = app.test_client()
        db.create_all()

    def testEmpty(self):
        with app.test_request_context():
            expected = ('It seems as if', "that page isn't here")
            response = self.client.get('/post/2').data
            for elem in expected:
                assert elem in response

    def testOne(self):
        with app.test_request_context():
            write_post(u"Single Post", u"Bloggity blog post, just one this time")
            expected = ('Single Post', 'Bloggity blog post, just one this time')
            response = self.client.get('/post/1').data
            for elem in expected:
                assert elem in response

    def testMany(self):
        with app.test_request_context():
            write_post(u"Post One", u"The first blog post in a list")
            write_post(u"Post Two", u"The second blog post in a list")
            write_post(u"Post Three", u"The third blog post in a list")
            expected = ('Post Three', 'The third blog post in a list')
            response = self.client.get('/post/3').data
            for elem in expected:
                self.assertIn(elem, response)

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        os.close(self.db_fd)
        os.unlink(app.config['DATABASE'])


class TestAddPost(unittest.TestCase):
    def setUp(self):
        self.db_fd, app.config['DATABASE'] = tempfile.mkstemp()
        app.config['TESTING'] = True
        self.client = app.test_client()
        db.create_all()

    def testWithGet(self):
        with app.test_request_context():
            expected = 'input type="text"'
            response = self.client.get('/new').data
            assert expected in response

    def testPostNotLoggedIn(self):
        expected = ('must be logged in', )
        with app.test_request_context():
            response = self.client.post('/new', data=dict(
                post_title='My Title',
                post_body='My Body'
                ), follow_redirects=True).data
            for elem in expected:
                self.assertIn(elem, response)

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        os.close(self.db_fd)
        os.unlink(app.config['DATABASE'])


class TestLogIn(unittest.TestCase):
    def setUp(self):
        self.db_fd, app.config['DATABASE'] = tempfile.mkstemp()
        app.config['TESTING'] = True
        self.client = app.test_client()
        db.create_all()
        new_author = Author('newuser', 'secret')
        db.session.add(new_author)
        db.session.commit()

    def testWithGet(self):
        expected = (
            'type="text" name="username"',
            'type="password" name="password"'
            )
        with app.test_request_context():
            response = self.client.get('/login').data
            for elem in expected:
                assert elem in response

    def testWithUnknownUser(self):
        expected = ("Invalid username/password", )
        with app.test_request_context():
            response = self.client.post('login', data=dict(
                username='randomuser',
                password='supersecure'
                ), follow_redirects=True).data
            for elem in expected:
                assert elem in response

    def testWithWrongPassword(self):
        expected = ("Invalid username/password", )
        with app.test_request_context():
            response = self.client.post('/login', data=dict(
                username='newuser',
                password='secretsecret'
                ), follow_redirects=True).data
            for elem in expected:
                assert elem in response

    def testProperLogin(self):
        expected = ("Now logged in as newuser",)
        with app.test_request_context():
            response = self.client.post('/login', data=dict(
                username='newuser',
                password='secret'
                ), follow_redirects=True).data
            for elem in expected:
                self.assertIn(elem, response)

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        os.close(self.db_fd)
        os.unlink(app.config['DATABASE'])


class TestLogInUser(unittest.TestCase):
    def setUp(self):
        self.db_fd, app.config['DATABASE'] = tempfile.mkstemp()
        app.config['TESTING'] = True
        self.client = app.test_client()
        db.create_all()
        new_author = Author('newuser', 'secret')
        db.session.add(new_author)
        db.session.commit()

    def testWithUnknownUser(self):
        with app.test_request_context():
            with self.assertRaises(ValueError):
                login_user('randomuser', 'secret')
            self.assertFalse(session.get('logged_in', False))

    def testWithWrongPassword(self):
        with app.test_request_context():
            with self.assertRaises(ValueError):
                login_user('newuser', 'secretsecret')
            self.assertFalse(session.get('logged_in', False))

    def testProperLogin(self):
        with app.test_request_context():
            login_user('newuser', 'secret')
            self.assertTrue(session['logged_in'])

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        os.close(self.db_fd)
        os.unlink(app.config['DATABASE'])


class TestLogout(unittest.TestCase):
    def setUp(self):
        self.db_fd, app.config['DATABASE'] = tempfile.mkstemp()
        app.config['TESTING'] = True
        self.client = app.test_client()
        db.create_all()

    def testLogOut(self):
        with app.test_request_context():
            self.client.get('logout')
            self.assertFalse(session.get('logged_in', False))

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        os.close(self.db_fd)
        os.unlink(app.config['DATABASE'])


if __name__ == '__main__':
    unittest.main()
