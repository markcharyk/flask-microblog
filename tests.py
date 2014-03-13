import unittest
from datetime import datetime
from microblog import app, db, Post, write_post, read_posts, read_post
from microblog import list_view, perma_view, add_post
from werkzeug.exceptions import NotFound


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
        db.create_all()

    def testEmpty(self):
        with app.test_request_context():
            expected = ''
            actual = list_view().split('div>')[1][:-2].strip()
            self.assertEqual(expected, actual)

    def testOne(self):
        with app.test_request_context():
            write_post(u"Post Title", u"A generic blog post")
            expected = read_posts()[0].title
            actual = list_view().split('h2>')[1][:-2]
            self.assertEqual(expected, actual)

    def testMany(self):
        with app.test_request_context():
            write_post(u"Post Number One", u"Some text that makes up blog post number one")
            write_post(u"Post Number Two", u"Some text that makes up blog post number two")
            write_post(u"Post Number Three", u"Some text that makes up blog post number three")
            expected = [read_posts()[0].title, read_posts()[1].title, read_posts()[2].title]
            actual = [list_view().split('h2>')[1][:-2], list_view().split('h2>')[3][:-2], list_view().split('h2>')[5][:-2]]
            self.assertEqual(expected, actual)

    def tearDown(self):
        db.session.remove()
        db.drop_all()


class TestPermaPage(unittest.TestCase):
    def setUp(self):
        db.create_all()

    def testEmpty(self):
        with app.test_request_context():
            with self.assertRaises(NotFound):
                return perma_view(1)

    def testOne(self):
        with app.test_request_context():
            write_post(u"Single Post", u"Bloggity blog post, just one this time")
            title = perma_view(1).split('h2>')[1][:-2]
            self.assertEqual(u"Single Post", title)

    def testMany(self):
        with app.test_request_context():
            write_post(u"Post One", u"The first blog post in a list")
            write_post(u"Post Two", u"The second blog post in a list")
            write_post(u"Post Three", u"The third blog post in a list")
            title = perma_view(3).split('h2>')[1][:-2]
            self.assertEqual(u"Post Three", title)

    def tearDown(self):
        db.session.remove()
        db.drop_all()


class TestAddPost(unittest.TestCase):
    def setUp(self):
        db.create_all()

    def withGet(self):
        actual = add_post().count('input type="text"')
        self.assertEqual(2, actual)

    def withPost(self):
        pass

    def tearDown(self):
        db.session.remove()
        db.drop_all()


if __name__ == '__main__':
    unittest.main()
