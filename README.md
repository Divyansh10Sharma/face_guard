# FaceGuard 🛡️
### Real-time behavioral awareness — face habits, eye strain, and expression detection

FaceGuard uses your webcam and MediaPipe to detect four unhealthy habits in real time and reminds you via voice alerts. Every session is logged and visualized in a React dashboard.

---

## Detections

| # | Detection | Trigger | Voice Alert |
|---|---|---|---|
| 1 | **Frustrated expression** | Brow furrow + lip compression vs your personal baseline | *"Fix your expression"* |
| 2 | **Face touching** | Any fingertip enters the face oval region | *"Stop touching your face"* |
| 3 | **Squinting** | Eyes stay narrow for 2+ sustained seconds | *"Relax your eyes"* |
| 4 | **Low blink rate** | No blink detected for 5 consecutive seconds | *"Blink more"* |

All alerts are voice-only (offline TTS via `pyttsx3`, no internet needed). A *"You are all set"* voice confirmation plays after calibration completes.

---

## Setup

### Python (detector)

```bash
# 1. Clone the repo
git clone https://github.com/Divyansh10Sharma/face_guard.git
cd face_guard

# 2. Install dependencies
pip install -r requirements.txt

# 3. Run
python detector.py
```

**Requirements:** Python 3.9+, a webcam, Windows/macOS/Linux

### React Dashboard (optional)

```bash
cd Frontend
npm install
npm run dev
```

Open **http://localhost:5173** — the dashboard reads live from `session_log.json` and auto-refreshes every 30 seconds.

---

## First Run — Calibration

1. On launch, keep a **neutral, relaxed face with eyes fully open** for ~2 seconds
2. The system records YOUR personal baselines for brow spacing, lip gap, and eye openness
3. Detection is relative to your face — not a generic model threshold
4. Say **G** before calibrating if you wear glasses (adds EAR tolerance)
5. Press **R** anytime to recalibrate

---

## Controls

| Key | Action |
|---|---|
| `Q` | Quit and save session to `session_log.json` |
| `R` | Recalibrate (keep neutral face) |
| `G` | Toggle glasses mode on/off |
| `+` / `=` | Increase sensitivity |
| `-` | Decrease sensitivity |

---

## Detection Toggles

At the top of `detector.py`, set any detector to `False` to fully disable it — no computation, no alert:

```python
DETECT_FRUSTRATED  = True
DETECT_FACE_TOUCH  = True
DETECT_SQUINT      = True
DETECT_BLINK_RATE  = True
```

---

## Tuning

All key values are constants at the top of their respective files with inline comments.

### `detector.py`

| Constant | Default | Effect |
|---|---|---|
| `CALIBRATION_FRAMES` | `60` | Frames collected for baseline (~2s at 30fps) |
| `SQUINT_SUSTAIN_SECONDS` | `2.0` | How long eyes must stay narrow before alert |
| `SQUINT_DROP_THRESHOLD` | `0.20` | EAR must drop 20% below baseline to count |
| `GLASSES_EAR_TOLERANCE` | `0.05` | Extra EAR forgiveness when glasses mode is on |
| `BLINK_EAR_RATIO` | `0.65` | EAR must drop to 65% of baseline to count as a blink |
| `BLINK_MAX_FRAMES` | `10` | Max frames a blink can last (~333ms at 30fps) |
| `BLINK_ALERT_SECONDS` | `5` | Seconds without a blink before alert fires |
| `cooldown_duration` | `8` | Seconds between repeat alerts of the same type |

### `alert.py`

Voice messages are defined in a single dictionary — change the text here:

```python
VOICE_MESSAGES = {
    "calibrated": "You are all set",
    "face_touch": "Stop touching your face",
    "frustrated":  "Fix your expression",
    "squint":      "Relax your eyes",
    "low_blink":   "Blink more",
}
```

### `helpers/tts_helper.py`

```python
speak(text, rate=150, volume=1.0)
# rate: words per minute (120–180 recommended)
```

---

## How Each Detector Works

### 1. Frustrated Expression
1. **Calibration** — records your neutral brow gap (normalized to face width) and lip gap
2. **Per-frame scoring** — measures how much brows have furrowed (65% weight) and lips compressed (35% weight) vs your baseline
3. **Smoothing** — 8-frame rolling average eliminates flicker
4. **Threshold** — 12% composite drop from baseline triggers detection

### 2. Face Touching
1. MediaPipe tracks 468 face mesh points and 21 hand landmarks simultaneously
2. Each fingertip is compared to the 36-point face oval boundary
3. If any fingertip is within **18% of face width** from the oval → detection triggers
4. Scales correctly regardless of distance from camera

### 3. Squinting
1. Computes **Eye Aspect Ratio (EAR)** = `(vertical distances) / (2 × horizontal width)` for both eyes, averaged
2. If EAR drops 20%+ below your calibrated open-eye baseline AND stays there for 2 seconds → alert fires
3. Quick EAR dips (≤3 frames) are automatically classified as blinks and ignored

### 4. Blink Rate
1. A blink is detected when EAR drops below 65% of baseline and recovers within 10 frames
2. Longer drops are squints (handled separately above)
3. If no blink is detected for **5 consecutive seconds** → alert fires
4. Timer resets fresh each time you blink

---

## React Dashboard

The `Frontend/` app shows your habit improvement over all sessions:

| Widget | Description |
|---|---|
| **Habit score ring** | SVG ring — green + percentage if recent sessions are better than early ones, red if worse |
| **Stat cards** | Animated counters for total alerts of each type across all sessions |
| **Trend chart** | Stacked bar chart per session (4 alert types) + green line for alerts/minute |
| **Session list** | Clickable cards with per-type emoji badges and alerts/min rate |
| **Event timeline** | Proportional dot track showing every event in the selected session with hover tooltips |

Sessions update live — every time FaceGuard writes to `session_log.json` the dashboard picks it up within 30 seconds.

---

## File Structure

```
face_guard/
├── detector.py             # Main script — run this
├── alert.py                # Voice alert system (pyttsx3)
├── session.py              # Session event logging → session_log.json
├── requirements.txt
│
├── helpers/
│   ├── constants.py        # MediaPipe landmark index arrays
│   ├── face_geometry_helper.py  # get_brow_distance, get_lip_compression, get_face_width
│   ├── eye_helper.py       # get_ear (Eye Aspect Ratio)
│   ├── face_touch_helper.py     # is_hand_near_face
│   ├── tone_helper.py      # generate_tone (pygame audio — unused if voice-only)
│   └── tts_helper.py       # speak() — offline TTS via pyttsx3
│
├── Frontend/               # React dashboard (Vite + Recharts)
│   ├── vite.config.js      # Dev server + /api/sessions middleware
│   ├── src/
│   │   ├── App.jsx
│   │   ├── App.css
│   │   └── components/
│   │       ├── StatCard.jsx
│   │       ├── HabitScore.jsx
│   │       ├── TrendChart.jsx
│   │       ├── SessionList.jsx
│   │       └── EventTimeline.jsx
│   └── package.json
│
└── session_log.json        # Auto-created after first session (gitignored)
```

---

## Session Log Format

`session_log.json` is an array that grows across sessions:

```json
[
  {
    "date": "2026-04-19",
    "start_time": "11:26:32",
    "duration": "6m 15s",
    "frustrated_alerts": 19,
    "face_touch_alerts": 3,
    "squint_alerts": 3,
    "events": [
      { "type": "frustrated", "time": "11:27:12", "timestamp": 1776578232.48 },
      { "type": "face_touch", "time": "11:29:17", "timestamp": 1776578357.43 },
      { "type": "low_blink",  "time": "11:30:45", "timestamp": 1776578445.54 }
    ]
  }
]
```

> `low_blink` alerts appear in `events` but are not counted in the top-level summary fields — the dashboard computes the count from events directly.

---

## Tech Stack

| Layer | Technology |
|---|---|
| Face & hand tracking | [MediaPipe](https://mediapipe.dev/) (468-point face mesh + 21-point hands) |
| Computer vision | OpenCV |
| Numerics | NumPy |
| Voice alerts | pyttsx3 (offline, uses Windows SAPI / macOS say / Linux espeak) |
| Dashboard | React 18, Vite, Recharts |

---

## Resume Description

> Built a real-time behavioral awareness system using MediaPipe face mesh and hand tracking that detects four unhealthy habits — frustrated expressions, face touching, eye squinting, and low blink rate — with personalized per-user calibration. Implemented EAR-based blink detection with squint/blink discrimination, an offline TTS alert pipeline, per-session event logging, and a React dashboard with animated charts showing habit improvement over time.
