from flask import Flask, render_template, request, jsonify
from reply_engine import suggest_replies, TONES

app = Flask(__name__)

@app.route("/")
def home():
    return render_template("index.html", tones=TONES)

@app.route("/api/suggest", methods=["POST"])
def api_suggest():
    data = request.get_json(force=True)
    try:
        out = suggest_replies(data.get("email", ""), data.get("tone", "Professional"),
                              data.get("name", ""))
        return jsonify(out)
    except ValueError as e:
        return jsonify({"error": str(e)}), 400

if __name__ == "__main__":
    app.run(debug=True)
