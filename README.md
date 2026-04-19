# FaceGuard 🛡️
### Real-time behavioral awareness — frustrated face + face touch detection

---

## What It Does

| Detection | Trigger | Alert |
|---|---|---|
| Frustrated expression | Brow furrow + lip compression from your personal baseline | Two soft low beeps |
| Face touching | Any fingertip near face oval region | One sharp high beep |

---

## Setup

```bash
# 1. Clone / download this folder

# 2. Install dependencies
pip install -r requirements.txt

# 3. Run
python detector.py
```

---

## First Run — Calibration
- On launch, keep a **neutral, relaxed face** for ~2 seconds
- The system records YOUR baseline brow distance and lip position
- Detection is relative to your face, not a generic dataset
- Press **R** anytime to recalibrate

---

## Controls

| Key | Action |
|---|---|
| `Q` | Quit and save session |
| `R` | Recalibrate (neutral face) |
| `+` / `=` | Increase sensitivity |
| `-` | Decrease sensitivity |

---

## Tuning Tips

- If getting false positives → press `-` to reduce sensitivity
- If missing your frustrated face → press `+` to increase sensitivity  
- Default sensitivity: 1.0 | Range: 0.3 – 2.0
- Cooldown between alerts: 8 seconds (change `cooldown_duration` in `detector.py`)

---

## Session Log

Every session is saved to `session_log.json`:
```json
{
  "date": "2025-04-19",
  "duration": "23m 10s",
  "frustrated_alerts": 4,
  "face_touch_alerts": 7,
  "events": [...]
}
```

---

## How the Frustration Detection Works

1. **Calibration** — records your neutral brow spacing and lip gap (normalized to face width)
2. **Per-frame scoring** — measures how much brow has furrowed (65% weight) and lip has compressed (35% weight) vs your baseline
3. **Smoothing** — 8-frame rolling average to avoid flickering
4. **Threshold** — 12% deviation from baseline triggers detection
5. **Cooldown** — 8 second gap between alerts so it's not annoying

## How Face Touch Detection Works

1. MediaPipe tracks both your face mesh (468 points) and hand landmarks simultaneously
2. Each fingertip position is compared against face oval boundary points
3. If distance < 18% of your face width → detection triggers
4. Works for touching, rubbing eyes, resting chin on hand

---

## File Structure

```
face_guard/
├── detector.py     # Main script — run this
├── alert.py        # Beep sound generator
├── session.py      # Session logging
├── requirements.txt
├── README.md
└── session_log.json  (auto-created after first session)
```

---

## Resume Description

> Built a real-time behavioral awareness system using MediaPipe face mesh and hand tracking that detects frustrated facial expressions and face-touching habits. Implemented personalized calibration to establish per-user baselines, a hybrid landmark + confidence-score detection pipeline, and session analytics logging — designed for preventive health and habit correction use cases.
