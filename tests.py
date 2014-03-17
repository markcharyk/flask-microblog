import unittest
from microblog import app, db, Post, Author, TempAuthor
from microblog import write_post, read_posts, read_post
from microblog import login_user, register_user, send_email, mail, un_temp_user
from flask import session
import tempfile
import os


class TestWritePost(unittest.TestCase):
    def setUp(self):
        db.create_all()
        new_author = Author('newuser', 'secret')
        db.session.add(new_author)
        db.session.commit()
        self.auth_id = new_author.id
        self.auth_name = 'testauthor'

    def testWriteOne(self):
        expected = Post(u"First Post", u"""
            The text containing the first post in the blog.""", self.auth_id, self.auth_name)
        write_post(u"First Post", u"""
            The text containing the first post in the blog.""", self.auth_id, self.auth_name)
        actual = Post.query.filter_by(title=u'First Post').first()
        self.assertEqual(expected.title, actual.title)
        self.assertEqual(expected.body, actual.body)
        self.assertEqual(expected.auth_name, actual.auth_name)

    def tearDown(self):
        db.session.remove()
        db.drop_all()


class TestReadPosts(unittest.TestCase):
    def setUp(self):
        db.create_all()
        new_author = Author('newuser', 'secret')
        db.session.add(new_author)
        db.session.commit()
        self.auth_id = new_author.id
        self.auth_name = 'testauthor'

    def testReadOne(self):
        expected = Post(u"New Post", u"""
            The text containing the newest post in the blog.""", self.auth_id, self.auth_name)
        write_post(u"New Post", u"""
            The text containing the newest post in the blog.""", self.auth_id, self.auth_name)
        actual = read_posts()[0]
        self.assertEqual(expected.title, actual.title)
        self.assertEqual(expected.body, actual.body)
        self.assertEqual(self.auth_id, actual.author_id)
        self.assertEqual(self.auth_name, actual.auth_name)

    def testEmpty(self):
        self.assertEqual(len(read_posts()), 0)

    def tearDown(self):
        db.session.remove()
        db.drop_all()


class TestReadPost(unittest.TestCase):
    def setUp(self):
        db.create_all()
        new_author = Author('newuser', 'secret')
        db.session.add(new_author)
        db.session.commit()
        self.auth_id = new_author.id
        self.auth_name = 'testauthor'

    def testEmpty(self):
        with self.assertRaises(IndexError):
            read_post(1)

    def testFirst(self):
        write_post(u"Newer Post", u"""
            The text containing the newer post in the blog.""", self.auth_id, self.auth_name)
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
        new_author = Author('newuser', 'secret')
        db.session.add(new_author)
        db.session.commit()
        self.auth_id = new_author.id
        self.auth_name = 'testauthor'

    def testEmpty(self):
        with app.test_request_context():
            expected = 'No posts to display'
            response = self.client.get('/').data
            assert expected in response

    def testOne(self):
        with app.test_request_context():
            write_post(u"Post Title", u"A generic blog post", self.auth_id, self.auth_name)
            expected = ('Post Title', 'A generic blog post', 'testauthor')
            response = self.client.get('/').data
            for elem in expected:
                assert elem in response

    def testMany(self):
        with app.test_request_context():
            write_post(u"Post Number One", u"Some text that makes up blog post number one", self.auth_id, self.auth_name)
            write_post(u"Post Number Two", u"Some text that makes up blog post number two", self.auth_id, self.auth_name)
            write_post(u"Post Number Three", u"Some text that makes up blog post number three", self.auth_id, self.auth_name)
            expected = ('Post Number One', 'Post Number Two', 'Post Number Three', 'Some text', 'testauthor')
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
        new_author = Author('newuser', 'secret')
        db.session.add(new_author)
        db.session.commit()
        self.auth_id = new_author.id
        self.auth_name = 'testauthor'

    def testEmpty(self):
        with app.test_request_context():
            expected = ('It seems as if', "that page isn't here")
            response = self.client.get('/post/2').data
            for elem in expected:
                assert elem in response

    def testOne(self):
        with app.test_request_context():
            write_post(u"Single Post", u"Bloggity blog post, just one this time", self.auth_id, self.auth_name)
            expected = ('Single Post', 'Bloggity blog post, just one this time', 'testauthor')
            response = self.client.get('/post/1').data
            for elem in expected:
                assert elem in response

    def testMany(self):
        with app.test_request_context():
            write_post(u"Post One", u"The first blog post in a list", self.auth_id, self.auth_name)
            write_post(u"Post Two", u"The second blog post in a list", self.auth_id, self.auth_name)
            write_post(u"Post Three", u"The third blog post in a list", self.auth_id, self.auth_name)
            expected = ('Post Three', 'The third blog post in a list', 'testauthor')
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
        new_author = Author('newuser', 'secret')
        db.session.add(new_author)
        db.session.commit()
        self.auth_id = new_author.id

    def testWithGet(self):
        with app.test_request_context():
            expected1 = 'input type="text"'
            expected2 = "Haven't registered"
            response = self.client.get('/new').data
            assert expected1 in response or expected2 in response

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


class TestRegister(unittest.TestCase):
    def setUp(self):
        self.db_fd, app.config['DATABASE'] = tempfile.mkstemp()
        app.config['TESTING'] = True
        self.client = app.test_client()
        db.create_all()
        new_author = Author('admin', 'admin')
        db.session.add(new_author)
        temp_author = TempAuthor('temp', 'admin')
        db.session.add(temp_author)
        db.session.commit()

    def testGet(self):
        expected = ('Confirm Password:', "Email Address:")
        with app.test_request_context():
            response = self.client.get('/register').data
            for elem in expected:
                self.assertIn(elem, response)

    def testBlankForms(self):
        expected = (
            'password is missing',
            'username is missing',
            'email address is missing'
            )
        with app.test_request_context():
            response = []
            response.append(self.client.post('/register', data=dict(
                username='newuser',
                password='',
                password_2='',
                email='newuser@domain.com'
                ), follow_redirects=True).data)
            response.append(self.client.post('/register', data=dict(
                username='',
                password='secret',
                password_2='secret',
                email='newuser@domain.com'
                ), follow_redirects=True).data)
            response.append(self.client.post('/register', data=dict(
                username='newuser',
                password='secret',
                password_2='supersecret',
                email=''
                ), follow_redirects=True).data)
            for i in range(3):
                self.assertIn(expected[i], response[i])

    def testExistingUser(self):
        expected = 'already taken'
        with app.test_request_context():
            response = self.client.post('/register', data=dict(
                username='admin',
                password='admin',
                password_2='admin',
                email='admin@domain.com'
                ), follow_redirects=True).data
            self.assertIn(expected, response)

    def testExistingTempUser(self):
        expected = 'already taken'
        with app.test_request_context():
            response = self.client.post('/register', data=dict(
                username='temp',
                password='admin',
                password_2='admin',
                email='temp@domain.com'
                ), follow_redirects=True).data
            self.assertIn(expected, response)

    def testUnmatchedPasswords(self):
        expected = 'make sure the passwords match'
        with app.test_request_context():
            response = self.client.post('/register', data=dict(
                username='newuser',
                password='secret',
                password_2='supersecret',
                email='newuser@domain.com'
                ), follow_redirects=True).data
            self.assertIn(expected, response)

    def testInvalidEmail(self):
        expected = 'valid email address'
        test_post = [
            '@gmail.com',
            'newuser@gmail',
            'gmail.com',
            'newuseratgmail.com'
        ]
        with app.test_request_context():
            for email in test_post:
                response = self.client.post('/register', data=dict(
                    username='newuser',
                    password='secret',
                    password_2='secret',
                    email=email
                    ), follow_redirects=True).data
                self.assertIn(expected, response)

    def testValidRegister(self):
        expected = "Please check your email"
        with app.test_request_context():
            response = self.client.post('/register', data=dict(
                username='newuser',
                password='secret',
                password_2='secret',
                email='newuser@domain.com'
                ), follow_redirects=True).data
            self.assertIn(expected, response)

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        os.close(self.db_fd)
        os.unlink(app.config['DATABASE'])


class TestRegisterUser(unittest.TestCase):
    def setUp(self):
        self.db_fd, app.config['DATABASE'] = tempfile.mkstemp()
        app.config['TESTING'] = True
        self.client = app.test_client()
        db.create_all()
        new_author = Author('admin', 'admin')
        db.session.add(new_author)
        temp_author = TempAuthor('temp', 'admin')
        db.session.add(temp_author)
        db.session.commit()

    def testBlankForms(self):
        with self.assertRaises(ValueError):
            register_user({
                'username': 'newuser',
                'first password': '',
                'second password': None,
                'email address': 'newuser@domain.com'
                })
        with self.assertRaises(ValueError):
            register_user({
                'username': '',
                'first password': 'secret',
                'second password': 'secret',
                'email address': 'newuser@domain.com'
                })
        with self.assertRaises(ValueError):
            register_user({
                'username': 'newuser',
                'first password': 'secret',
                'second password': 'secret',
                'email address': None
                })

    def testExistingUser(self):
        with self.assertRaises(ValueError):
            register_user({
                'username': 'admin',
                'first password': 'admin',
                'second password': 'admin',
                'email address': 'admin@domain.com'
                })

    def testExistingTempUser(self):
        with self.assertRaises(ValueError):
            register_user({
                'username': 'temp',
                'first password': 'admin',
                'second password': 'admin',
                'email address': 'temp@domain.com'
                })

    def testUnmatchedPasswords(self):
        with self.assertRaises(ValueError):
            register_user({
                'username': 'newuser',
                'first password': 'secret',
                'second password': 'supersecret',
                'email address': 'newuser@domain.com'
                })

    def testInvalidEmail(self):
        test_post = [
            '@gmail.com',
            'newuser@gmail',
            'gmail.com',
            'newuseratgmail.com'
        ]
        for email in test_post:
            with self.assertRaises(ValueError):
                register_user({
                    'username': 'newuser',
                    'first password': 'secret',
                    'second password': 'secret',
                    'email address': email
                    })

    def testValid(self):
        with app.test_request_context():
            self.assertIsNone(register_user({
                'username': 'newuser',
                'first password': 'secret',
                'second password': 'secret',
                'email address': 'newuser@domain.com'
                }))

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        os.close(self.db_fd)
        os.unlink(app.config['DATABASE'])


class TestEmail(unittest.TestCase):
    def setUp(self):
        self.db_fd, app.config['DATABASE'] = tempfile.mkstemp()
        self.client = app.test_client()

    def testEmail(self):
        with app.test_request_context():
            expected = 'randomly_generated_registration_key'
            with mail.record_messages() as outbox:
                send_email('user@domain.com', 'randomly_generated_registration_key')
            self.assertEqual(len(outbox), 1)
            self.assertIn('user@domain.com', outbox[0].recipients)
            self.assertIn(expected, outbox[0].body)
            self.assertIn(expected, outbox[0].html)

    def tearDown(self):
        os.close(self.db_fd)
        os.unlink(app.config['DATABASE'])


class TestConfirmation(unittest.TestCase):
    def setUp(self):
        self.db_fd, app.config['DATABASE'] = tempfile.mkstemp()
        app.config['TESTING'] = True
        self.client = app.test_client()
        db.create_all()
        temp_author = TempAuthor('temp', 'admin')
        self.reg_key = temp_author.reg_key
        db.session.add(temp_author)
        db.session.commit()

    def testWrongKey(self):
        expected = ("recognize the account",)
        with app.test_request_context():
            response = self.client.get('/confirm/NotRandom').data
            for elem in expected:
                self.assertIn(elem, response)

    def testRightKey(self):
        expected = ('Congratulations', 'head home')
        with app.test_request_context():
            response = self.client.get('/confirm/%s' % self.reg_key).data
            for elem in expected:
                self.assertIn(elem, response)

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        os.close(self.db_fd)
        os.unlink(app.config['DATABASE'])


class TestUnTempUser(unittest.TestCase):
    def setUp(self):
        self.db_fd, app.config['DATABASE'] = tempfile.mkstemp()
        app.config['TESTING'] = True
        self.client = app.test_client()
        db.create_all()
        self.temp_author = TempAuthor('temp', 'admin')
        db.session.add(self.temp_author)
        db.session.commit()

    def testUnTemp(self):
        with app.test_request_context():
            un_temp_user(self.temp_author)
            newbie = Author.query.filter_by(username=self.temp_author.username).first()
            self.assertIsNotNone(newbie)
            oldie = TempAuthor.query.filter_by(username=self.temp_author.username).first()
            self.assertIsNone(oldie)

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        os.close(self.db_fd)
        os.unlink(app.config['DATABASE'])


if __name__ == '__main__':
    unittest.main()
