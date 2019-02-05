import requests
import os
from flask import Flask, render_template, request
from werkzeug import secure_filename
app = Flask(__name__)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/start", methods=["POST"])
def start():
    file = request.files['submission']
    slug = request.form['slug']

    filename = secure_filename(file.filename)
    filepath = os.path.join("uploads/", filename)
    file.save(filepath)

    with open(filepath, "rb") as f:
        r = requests.post(f"http://localhost:5000/start/{slug}", files={"file": f})
    response = r.json()

    return response['id']

@app.route("/get/<id>")
def get(id):
    return requests.get(f"http://localhost:5000/get/{id}").content

if __name__ == "__main__":
    app.run(port=4000)
