"""
visualizer/app.py — Flask + Flask-SocketIO server for RagaHash visualisation.

Two browser endpoints:
  /sender   — user enters a message; sees step-by-step hash animation + audio
  /receiver — watches the same hash being verified in real time

API:
  POST /api/hash       — compute hash, broadcast steps via WebSocket
  GET  /api/melody     — download WAV melody for last hashed message
  GET  /api/match_cadence   — WAV for verification success sound
  GET  /api/mismatch_cadence — WAV for verification failure sound
"""

import sys
import os

# Allow running from project root or visualizer/ directory
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from flask import Flask, render_template, request, jsonify, send_file
from flask_socketio import SocketIO, emit

import io
import json

from ragahash import ragahash, ragahash_steps, ragachecksum
from ragahash.music import steps_to_melody, match_cadence, mismatch_cadence
from ragahash.raga_data import MELAKARTA_RAGAS

app = Flask(__name__)
app.config["SECRET_KEY"] = "ragahash-secret-2026"
socketio = SocketIO(app, cors_allowed_origins="*", async_mode="threading")

# Simple in-memory store for the last computed hash (for receiver comparison)
_last_hash_state: dict = {}


# ---------------------------------------------------------------------------
# HTTP Routes
# ---------------------------------------------------------------------------

@app.route("/")
def index():
    return render_template("sender.html")


@app.route("/sender")
def sender():
    return render_template("sender.html")


@app.route("/receiver")
def receiver():
    return render_template("receiver.html")


@app.route("/api/hash", methods=["POST"])
def api_hash():
    """
    POST /api/hash
    Body (JSON or form): { "message": str, "raga_id": int (optional) }

    Returns:
      { digest, checksum, raga_name, raga_id, steps (list), message }

    Also broadcasts each step and the final result via WebSocket so the
    receiver page updates in real time.
    """
    data = request.get_json(silent=True) or request.form
    message = data.get("message", "")
    raga_id = int(data.get("raga_id", 29))

    if not 1 <= raga_id <= 72:
        return jsonify({"error": "raga_id must be in [1..72]"}), 400

    raw = message.encode("utf-8")

    steps = ragahash_steps(raw, raga_id)
    digest = ragahash(raw, raga_id)
    cs = ragachecksum(raw, raga_id)

    # Broadcast start event
    socketio.emit("hash_start", {
        "message": message,
        "raga_id": raga_id,
        "raga_name": MELAKARTA_RAGAS[raga_id]["name"],
        "total_steps": len(steps),
    })

    # Broadcast each step (small delay handled client-side)
    for step in steps:
        socketio.emit("hash_step", {
            "step_index": step["step_index"],
            "char": step["char"],
            "swara_name": step["swara_name"],
            "lane": step["lane"],
            "note_freq": step["note_freq"],
            "state_snapshot": step["state_snapshot"],
        })

    # Broadcast final result
    result = {
        "message": message,
        "digest": digest,
        "checksum": cs["hex"],
        "raga_id": raga_id,
        "raga_name": MELAKARTA_RAGAS[raga_id]["name"],
        "step_count": len(steps),
    }
    socketio.emit("hash_complete", result)

    # Store for receiver
    _last_hash_state.update(result)
    _last_hash_state["steps"] = steps

    return jsonify(result)


@app.route("/api/ragas")
def api_ragas():
    """Return list of all 72 Melakarta ragas for the raga selector."""
    ragas = [
        {"id": rid, "name": raga["name"]}
        for rid, raga in MELAKARTA_RAGAS.items()
    ]
    return jsonify(ragas)


@app.route("/api/melody")
def api_melody():
    """Download WAV melody for the last hashed message."""
    steps = _last_hash_state.get("steps")
    if not steps:
        return jsonify({"error": "No hash computed yet"}), 404

    wav_bytes = steps_to_melody(steps)
    return send_file(
        io.BytesIO(wav_bytes),
        mimetype="audio/wav",
        as_attachment=True,
        download_name="ragahash_melody.wav",
    )


@app.route("/api/match_cadence")
def api_match_cadence():
    """Download WAV for the verification-success cadence."""
    return send_file(
        io.BytesIO(match_cadence()),
        mimetype="audio/wav",
        as_attachment=False,
        download_name="match.wav",
    )


@app.route("/api/mismatch_cadence")
def api_mismatch_cadence():
    """Download WAV for the verification-failure cadence."""
    return send_file(
        io.BytesIO(mismatch_cadence()),
        mimetype="audio/wav",
        as_attachment=False,
        download_name="mismatch.wav",
    )


# ---------------------------------------------------------------------------
# WebSocket events
# ---------------------------------------------------------------------------

@socketio.on("connect")
def on_connect():
    # Send current state to newly connected client
    if _last_hash_state.get("digest"):
        emit("hash_complete", {k: v for k, v in _last_hash_state.items() if k != "steps"})


@socketio.on("request_verify")
def on_request_verify(data):
    """
    Receiver sends its own computed hash for comparison.
    data = { "digest": str, "message": str }
    """
    sender_digest = _last_hash_state.get("digest", "")
    receiver_digest = data.get("digest", "")
    match = sender_digest.lower() == receiver_digest.lower()

    emit("verify_result", {
        "match": match,
        "sender_digest": sender_digest,
        "receiver_digest": receiver_digest,
    }, broadcast=True)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    print(f"\n  RagaHash Visualizer")
    print(f"  Sender  : http://localhost:{port}/sender")
    print(f"  Receiver: http://localhost:{port}/receiver\n")
    socketio.run(app, host="0.0.0.0", port=port, debug=False, allow_unsafe_werkzeug=True)
