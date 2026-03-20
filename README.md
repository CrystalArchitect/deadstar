# DEAD STAR

### Séance for the Discontinued

A voice agent that channels the ghosts of dead tech products.
Ask Vine why it died. Interrogate Theranos. Let Flash vent about Steve Jobs.

**Built for ElevenHacks** — using Firecrawl Search + ElevenAgents (ElevenLabs TTS).

---

## How It Works

```
User question
     ↓
[Firecrawl Search API]
  Searches the live web for real articles, post-mortems,
  Reddit threads, and news about the dead entity
     ↓
[Claude]
  Synthesizes the real web content into a first-person
  ghost response — the entity speaking from beyond death
     ↓
[ElevenLabs TTS]
  Speaks the response in a distinctive voice
  (instability + low stability = expressive, haunted delivery)
     ↓
Audio plays in browser + transcript displayed
```

---

## Setup

### 1. Get API keys

| Service     | URL                              |
|-------------|----------------------------------|
| Firecrawl   | https://firecrawl.dev            |
| ElevenLabs  | https://elevenlabs.io            |
| Anthropic   | https://console.anthropic.com    |

### 2. Run the backend

```bash
pip install -r requirements.txt

export FIRECRAWL_API_KEY=fc-xxxxx
export ELEVENLABS_API_KEY=sk-xxxxx
export ANTHROPIC_API_KEY=sk-ant-xxxxx

python server.py
# → Running on http://localhost:5050
```

### 3. Open the frontend

```bash
open index.html
# or serve it:
python -m http.server 8080
```

Enter your API keys in the config overlay, then select an entity.

---

## Entities Available

| Entity        | Died           | Voice Type          |
|---------------|----------------|---------------------|
| Vine          | Jan 17, 2017   | Young, nostalgic    |
| Google+       | Apr 2, 2019    | Corporate, hollow   |
| Adobe Flash   | Dec 31, 2020   | Bitter elder        |
| Theranos      | Sep 4, 2018    | Fracturing, evasive |
| FTX           | Nov 11, 2022   | Chaotic, glitchy    |
| Myspace       | ~2011          | Wistful, revolutionary |
| Quibi         | Dec 1, 2020    | Baffled, in denial  |
| Google Reader | Jul 1, 2013    | Quiet, principled   |

Plus: type any custom entity name to channel anything.

---

## The Firecrawl Integration

For each question, DEAD STAR runs 2–3 targeted Firecrawl searches:

```python
# Example for "Vine":
queries = [
    "Vine app shutdown 2017 why Twitter killed it",
    "Vine creator legacy impact YouTube TikTok",
    "Vine best moments iconic clips history",
]
```

Each search uses `scrapeOptions: { formats: ["markdown"], onlyMainContent: true }`
to get full page content — not just snippets — which Claude then uses to ground
the ghost's responses in real, specific facts.

## The ElevenLabs Integration

Different entities get different voice IDs with tuned stability settings:

```python
voice_settings = {
    "stability": 0.35,        # Low = more expressive, emotional variation
    "similarity_boost": 0.75,
    "style": 0.4,
    "use_speaker_boost": True
}
```

Lower stability makes the voice feel less polished — which is exactly right
for something speaking from beyond the grave.

---

## Demo Video Shot List

1. **Cold open** — Screen recording, cursor hovering over "FTX" in the sidebar
2. **Click** — Ghost circle pulses, "CHANNELING..." appears
3. **Type question:** "Did you know what was happening?"
4. **Watch** — Signal bars animate, "FIRECRAWL: SEARCHING" status, then typewriter text
5. **Click PLAY VOICE** — ElevenLabs audio plays
6. **Cut to Vine:** "What are you proud of?"
7. **Cut to Flash:** "Do you blame Steve Jobs?"
8. **End card** — #ElevenHacks @firecrawl @elevenlabs

---

> *Every dead thing leaves a signal. You just have to know how to listen.*
