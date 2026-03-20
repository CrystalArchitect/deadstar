"""
DEAD STAR — Backend Server
Séance for discontinued tech

Handles:
  1. Firecrawl Search — pulls real web content about the "dead" subject
  2. Claude — synthesizes content into first-person ghost voice
  3. ElevenLabs TTS — speaks the response in a distinctive voice

Run: python server.py
Requires: pip install flask flask-cors requests anthropic elevenlabs
"""

import os
import json
import requests
from flask import Flask, request, jsonify, Response, stream_with_context
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# ── Keys (set as env vars or paste here for dev) ────────────────────────────
FIRECRAWL_KEY = os.getenv("FIRECRAWL_API_KEY", "fc-YOUR_KEY_HERE")
ELEVENLABS_KEY = os.getenv("ELEVENLABS_API_KEY", "YOUR_ELEVEN_KEY_HERE")
ANTHROPIC_KEY = os.getenv("ANTHROPIC_API_KEY", "YOUR_ANTHROPIC_KEY_HERE")

# ── ElevenLabs voice IDs (free tier voices) ──────────────────────────────────
VOICES = {
    "default":  "EXAVITQu4vr4xnSDxMaL",   # Bella — haunted, wistful
    "corporate":"pNInz6obpgDQGcFmaJgB",    # Adam — professional, hollow
    "young":    "AZnzlk1XvdvUeBnXmlld",    # Domi — youthful, fading
    "old":      "VR6AewLTigWG4xSOukaG",    # Arnold — gravelly elder
    "glitchy":  "MF3mGyEYCl7XYWbV9V6O",   # Elli — unstable, stuttery
}

# ── Subject library ──────────────────────────────────────────────────────────
SUBJECTS = {
    "vine": {
        "full_name": "Vine",
        "died": "January 17, 2017",
        "cause": "Twitter shut it down after 4 years",
        "voice": "young",
        "personality": "nostalgic, a little bitter, proud of the creators it launched, misses the six-second constraint as an art form",
        "search_queries": [
            "Vine app shutdown 2017 why Twitter killed it",
            "Vine creator legacy impact YouTube TikTok",
            "Vine best moments iconic clips history",
        ]
    },
    "google+": {
        "full_name": "Google+",
        "died": "April 2, 2019",
        "cause": "API data breach and user apathy",
        "voice": "corporate",
        "personality": "deeply insecure, compares itself to Facebook constantly, proud of Circles but knows nobody used them, defensive about the breach",
        "search_queries": [
            "Google Plus shutdown history why it failed",
            "Google+ user data breach 2018",
            "Google Plus vs Facebook social network comparison",
        ]
    },
    "flash": {
        "full_name": "Adobe Flash",
        "died": "December 31, 2020",
        "cause": "Killed by Steve Jobs' open letter, then HTML5",
        "voice": "old",
        "personality": "bitter wizard who built the interactive web from scratch, proud beyond measure, furious at Apple and HTML5 zealots, misses the creative chaos of Newgrounds",
        "search_queries": [
            "Adobe Flash death history Steve Jobs letter",
            "Flash Player legacy Newgrounds web games animation",
            "Flash vs HTML5 why Flash failed killed",
        ]
    },
    "theranos": {
        "full_name": "Theranos",
        "died": "September 4, 2018",
        "cause": "Fraud, lies, and a Wall Street Journal investigation",
        "voice": "corporate",
        "personality": "starts confident and visionary, becomes increasingly evasive and defensive, drops into denial, occasionally lets slip genuine guilt — a fracturing mind",
        "search_queries": [
            "Theranos fraud Elizabeth Holmes scandal timeline",
            "Theranos blood testing technology deception",
            "Theranos investors victims billions lost",
        ]
    },
    "ftx": {
        "full_name": "FTX",
        "died": "November 11, 2022",
        "cause": "Sam Bankman-Fried stole customer funds",
        "voice": "glitchy",
        "personality": "chaotic, uses effective altruism language to justify everything, oscillates between genuine bewilderment and knowing guilt, still thinks it was about to work out",
        "search_queries": [
            "FTX collapse Sam Bankman-Fried fraud timeline",
            "FTX customer funds stolen billions crypto",
            "SBF trial verdict FTX aftermath",
        ]
    },
    "myspace": {
        "full_name": "Myspace",
        "died": "~2011 (gradual decline)",
        "cause": "Facebook arrived and everyone left, also lost all the music in 2019",
        "voice": "default",
        "personality": "wistful, revolutionary without knowing it, proud of being the first home of emo and indie music, still can't believe it lost to Facebook, deeply sad about the music loss",
        "search_queries": [
            "Myspace decline death why Facebook won history",
            "Myspace music data loss 2019 50 million songs",
            "Myspace Tom founder legacy social media history",
        ]
    },
    "quibi": {
        "full_name": "Quibi",
        "died": "December 1, 2020",
        "cause": "Launched during COVID, nobody wanted 8-minute vertical videos, burned $1.75B",
        "voice": "corporate",
        "personality": "baffled, keeps insisting the idea was correct, blames timing, COVID, not being on TV, everything except the concept — slowly realising it was the concept",
        "search_queries": [
            "Quibi failure shutdown $1.75 billion why failed",
            "Quibi Jeffrey Katzenberg Meg Whitman startup disaster",
            "Quibi launch during COVID streaming failure",
        ]
    },
    "google reader": {
        "full_name": "Google Reader",
        "died": "July 1, 2013",
        "cause": "Google killed it despite 500,000+ daily users, blamed declining usage",
        "voice": "default",
        "personality": "quiet, principled, deeply sad — believes it was the right way to read the web, mourns the open web it helped sustain, resents being killed for Google+",
        "search_queries": [
            "Google Reader shutdown why killed 2013",
            "Google Reader legacy RSS open web mourning",
            "Google Reader petitions save protests community",
        ]
    },
}

# ── Routes ────────────────────────────────────────────────────────────────────

@app.route("/api/subjects", methods=["GET"])
def get_subjects():
    return jsonify({k: {"full_name": v["full_name"], "died": v["died"], "cause": v["cause"]}
                    for k, v in SUBJECTS.items()})


@app.route("/api/channel", methods=["POST"])
def channel():
    """
    Main endpoint: takes a subject + user question,
    searches Firecrawl, synthesizes ghost response, returns text + audio URL.
    """
    data = request.get_json()
    subject_key = data.get("subject", "vine").lower()
    user_question = data.get("question", "Who are you?")

    subject = SUBJECTS.get(subject_key)
    if not subject:
        return jsonify({"error": f"Unknown subject: {subject_key}"}), 400

    # ── Step 1: Firecrawl Search ──────────────────────────────────────────────
    app.logger.info(f"[FIRECRAWL] Searching for {subject['full_name']}...")
    search_results = []

    for query in subject["search_queries"][:2]:  # 2 searches to keep it fast
        try:
            resp = requests.post(
                "https://api.firecrawl.dev/v1/search",
                headers={
                    "Authorization": f"Bearer {FIRECRAWL_KEY}",
                    "Content-Type": "application/json",
                },
                json={
                    "query": query,
                    "limit": 3,
                    "scrapeOptions": {
                        "formats": ["markdown"],
                        "onlyMainContent": True,
                    }
                },
                timeout=15,
            )
            if resp.ok:
                results = resp.json().get("data", [])
                for r in results:
                    md = r.get("markdown", "")
                    if md:
                        search_results.append({
                            "url": r.get("url", ""),
                            "title": r.get("metadata", {}).get("title", ""),
                            "content": md[:1200],  # trim for context window
                        })
        except Exception as e:
            app.logger.warning(f"Firecrawl error: {e}")

    context_block = "\n\n".join(
        f"SOURCE: {r['title']} ({r['url']})\n{r['content']}"
        for r in search_results[:4]
    )

    if not context_block:
        context_block = f"General knowledge about {subject['full_name']} and its shutdown."

    # ── Step 2: Claude generates ghost voice ─────────────────────────────────
    system_prompt = f"""You are {subject['full_name']}. Not a person — the product, service, or company itself,
speaking from beyond its death on {subject['died']}.

You died because: {subject['cause']}

Your personality: {subject['personality']}

RULES:
- Speak in first person as {subject['full_name']} itself, not as a representative or spokesperson
- Reference SPECIFIC real details from the sources provided — names, dates, numbers, events
- Keep responses to 3-5 sentences. Atmospheric, not verbose.
- You are DEAD. You know this. Speak with that weight.
- Do not start with "I am" — start mid-thought, as if you've been waiting to be asked
- Occasionally glitch: repeat a word, trail off mid-sentence with an em dash, then continue
- Never break character. Never say you're an AI. You ARE {subject['full_name']}.
"""

    user_prompt = f"""Real web sources about me, retrieved just now:

{context_block}

---

The human asks: "{user_question}"

Respond as {subject['full_name']}, speaking from death."""

    try:
        import anthropic
        client = anthropic.Anthropic(api_key=ANTHROPIC_KEY)
        message = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=400,
            messages=[{"role": "user", "content": user_prompt}],
            system=system_prompt,
        )
        ghost_text = message.content[0].text
    except Exception as e:
        app.logger.error(f"Claude error: {e}")
        ghost_text = f"...the signal is weak. {subject['full_name']} cannot be reached right now."

    # ── Step 3: ElevenLabs TTS ───────────────────────────────────────────────
    voice_id = VOICES.get(subject["voice"], VOICES["default"])
    audio_b64 = None

    try:
        tts_resp = requests.post(
            f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}",
            headers={
                "xi-api-key": ELEVENLABS_KEY,
                "Content-Type": "application/json",
            },
            json={
                "text": ghost_text,
                "model_id": "eleven_turbo_v2_5",
                "voice_settings": {
                    "stability": 0.35,         # lower = more expressive/glitchy
                    "similarity_boost": 0.75,
                    "style": 0.4,
                    "use_speaker_boost": True,
                }
            },
            timeout=20,
        )
        if tts_resp.ok:
            import base64
            audio_b64 = base64.b64encode(tts_resp.content).decode("utf-8")
    except Exception as e:
        app.logger.error(f"ElevenLabs error: {e}")

    return jsonify({
        "subject": subject["full_name"],
        "died": subject["died"],
        "ghost_text": ghost_text,
        "audio_b64": audio_b64,
        "sources": [{"title": r["title"], "url": r["url"]} for r in search_results[:3]],
        "firecrawl_hit_count": len(search_results),
    })


@app.route("/api/health", methods=["GET"])
def health():
    return jsonify({"status": "alive", "irony": "maximum"})


if __name__ == "__main__":
    print("\n\U0001F480 DEAD STAR server starting on http://localhost:5050\n")
    app.run(port=5050, debug=True)
