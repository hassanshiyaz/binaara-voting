from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO
import pandas as pd
import os
import csv

app = Flask(__name__)
socketio = SocketIO(app)

# CSV to store votes
VOTE_FILE = "votes.csv"

# Ensure vote file exists
if not os.path.exists(VOTE_FILE):
    with open(VOTE_FILE, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["email", "male", "female"])
        writer.writeheader()

def read_names(filename):
    try:
        df = pd.read_excel(filename, header=None)
        names = df.iloc[:,0].dropna().astype(str).tolist()
        return list(dict.fromkeys(names))  # remove duplicates
    except:
        return []

@app.route("/")
def vote_page():
    return render_template("vote.html")

@app.route("/dashboard")
def dashboard():
    return render_template("dashboard.html")

@app.route("/api/male")
def male_names():
    return jsonify(read_names("male.xlsx"))

@app.route("/api/female")
def female_names():
    return jsonify(read_names("female.xlsx"))

@app.route("/vote", methods=["POST"])
def vote():
    data = request.get_json()
    email = data.get("email")
    male = data.get("male")
    female = data.get("female")
    if not email or not male or not female:
        return jsonify({"success": False, "error": "Missing data"})

    # Check if email has already voted
    votes_df = pd.read_csv(VOTE_FILE)
    if email in votes_df['email'].values:
        return jsonify({"success": False, "error": "You have already voted."})

    # Record vote
    with open(VOTE_FILE, "a", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["email","male","female"])
        writer.writerow({"email": email, "male": male, "female": female})

    # Broadcast new vote
    votes_df = pd.read_csv(VOTE_FILE)
    male_counts = votes_df['male'].value_counts().to_dict()
    female_counts = votes_df['female'].value_counts().to_dict()
    socketio.emit("vote_update", {"male": male_counts, "female": female_counts})

    return jsonify({"success": True})

@app.route("/api/results")
def results():
    votes_df = pd.read_csv(VOTE_FILE)
    male_counts = votes_df['male'].value_counts().to_dict()
    female_counts = votes_df['female'].value_counts().to_dict()
    return jsonify({"male": male_counts, "female": female_counts})

if __name__ == "__main__":
    socketio.run(app, debug=True)
