import unittest
from app import app, db
from models import User, SearchHistory

class FlaskAppTestCase(unittest.TestCase):
    def setUp(self):
        app.config['TESTING'] = True
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        app.config['WTF_CSRF_ENABLED'] = False
        self.client = app.test_client()
        with app.app_context():
            db.create_all()
            user = User(username="testuser")
            user.set_password("testpass")
            db.session.add(user)
            db.session.commit()
            self.user_id = user.id

    def login(self):
        return self.client.post('/login', data=dict(
            username="testuser",
            password="testpass"
        ), follow_redirects=True)

    def test_signup_login_logout(self):
        res = self.client.post('/signup', data=dict(username="newuser", password="newpass"), follow_redirects=True)
        self.assertIn(b"Search a Word", res.data)

        res = self.client.post('/login', data=dict(username="newuser", password="newpass"), follow_redirects=True)
        self.assertIn(b"Search a Word", res.data)

        res = self.client.get('/logout', follow_redirects=True)
        self.assertIn(b"Login", res.data)

    def test_search_word(self):
        self.login()
        res = self.client.post("/", data={"word": "test"}, follow_redirects=True)
        self.assertIn(b"Definition", res.data)

    def test_fuzzy_search(self):
        res = self.client.get('/fuzzy?q=tes')
        self.assertEqual(res.status_code, 200)
        self.assertIn(b"[", res.data)

    def test_search_history(self):
        self.login()
        self.client.post("/", data={"word": "example"}, follow_redirects=True)
        res = self.client.get("/dashboard")
        self.assertIn(b"example", res.data)

    def tearDown(self):
        with app.app_context():
            db.session.remove()
            db.drop_all()
