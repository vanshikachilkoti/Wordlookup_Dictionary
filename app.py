from flask import Flask, render_template, request, redirect, session, url_for, jsonify
from models import db, User, SearchHistory
from config import Config
from flask_migrate import Migrate
from bs4 import BeautifulSoup
import requests
import os

app = Flask(__name__)
app.config.from_object(Config)
db.init_app(app)
migrate = Migrate(app, db)

# Ensure DB is initialized
with app.app_context():
    db.create_all()

# Load word list
WORDS = []
if os.path.exists("wordlist.txt"):
    with open("wordlist.txt") as f:
        WORDS = [line.strip() for line in f if line.strip()]

# Scraper function
def get_definition(word):
    try:
        url = f"https://www.oxfordlearnersdictionaries.com/definition/english/{word}"
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code != 200:
            return "Definition not found."
        soup = BeautifulSoup(response.text, "html.parser")
        definition_div = soup.find("span", class_="def")
        return definition_div.text.strip() if definition_div else "Definition not found."
    except Exception as e:
        return f"Error: {str(e)}"

# Hugging Face inference API call
def get_ai_fuzzy_matches(query, limit=5):
    token = os.getenv("HF_TOKEN")  # Or set in config.py
    if not token:
        return []

    try:
        headers = {
            "Authorization": f"Bearer {token}"
        }
        payload = {
            "inputs": {
                "source_sentence": query,
                "sentences": WORDS
            }
        }
        response = requests.post(
            "https://api-inference.huggingface.co/models/sentence-transformers/all-MiniLM-L6-v2",
            headers=headers,
            json=payload
        )
        results = response.json()
        if isinstance(results, list):
            scored = list(zip(WORDS, results))
            scored.sort(key=lambda x: x[1], reverse=True)
            return [word for word, _ in scored[:limit]]
    except Exception as e:
        print("AI fuzzy error:", e)
    return []

@app.route("/", methods=["GET", "POST"])
def home():
    if "user_id" not in session:
        return redirect(url_for("login"))

    word = ""
    definition = ""
    if request.method == "POST":
        word = request.form.get("word", "").strip().lower()
        if word:
            definition = get_definition(word)
            user = User.query.get(session["user_id"])
            if user:
                search = SearchHistory(word=word, definition=definition, user_id=user.id)
                db.session.add(search)
                db.session.commit()
    return render_template("index.html", word=word, definition=definition)

@app.route("/fuzzy")
def fuzzy():
    query = request.args.get("q", "").strip()
    if not query:
        return jsonify([])
    matches = get_ai_fuzzy_matches(query)
    return jsonify(matches)

@app.route("/dashboard")
def dashboard():
    if "user_id" not in session:
        return redirect(url_for("login"))
    user = User.query.get(session["user_id"])
    history = SearchHistory.query.filter_by(user_id=user.id).order_by(SearchHistory.timestamp.desc()).all()
    return render_template("dashboard.html", history=history)

@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        if User.query.filter_by(username=username).first():
            return "Username already exists"
        user = User(username=username)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        session["user_id"] = user.id
        return redirect(url_for("home"))
    return render_template("signup.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            session["user_id"] = user.id
            return redirect(url_for("home"))
        return "Invalid credentials"
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.pop("user_id", None)
    return redirect(url_for("login"))

if __name__ == "__main__":
    app.run(debug=True)
