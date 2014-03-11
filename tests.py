import unittest
from datetime import datetime
from microblog import db, Post, write_post, read_posts, read_post


class TestWritePost(unittest.TestCase):
    def setUp(self):
        db.create_all()

    def testOne(self):
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

    def testTwo(self):
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

    def testThree(self):
        write_post(u"Newer Post", u"""
            The text containing the newer post in the blog.""")
        self.assertIsInstance(read_post(1), Post)

    def tearDown(self):
        db.session.remove()
        db.drop_all()

if __name__ == '__main__':
    unittest.main()
