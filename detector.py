"""
FaceGuard - Real-time behavioral awareness system
Detects:
  1. Frustrated face  — brow furrow + lip compression vs your personal baseline
  2. Face touching    — any fingertip entering the face region
  3. Eye squinting    — sustained low Eye Aspect Ratio (EAR), blink-filtered

Run:  python detector.py
Keys: Q = quit | R = recalibrate | G = toggle glasses mode | +/- = sensitivity
"""

# ─────────────────────────────────────────────────────────────────────────────
# IMPORTS
# ─────────────────────────────────────────────────────────────────────────────
import cv2
import mediapipe as mp
import numpy as np
import time
from datetime import datetime
from alert import AlertSystem
from session import SessionLogger
from helpers.constants import LEFT_EYE_LANDMARKS, RIGHT_EYE_LANDMARKS
from helpers.face_geometry_helper import get_brow_distance, get_lip_compression, get_face_width
from helpers.eye_helper import get_ear
from helpers.face_touch_helper import is_hand_near_face

# ─────────────────────────────────────────────────────────────────────────────
# MEDIAPIPE SOLUTION HANDLES
# ─────────────────────────────────────────────────────────────────────────────

try:
    mp_face_mesh = mp.solutions.face_mesh
    mp_hands     = mp.solutions.hands
    mp_drawing   = mp.solutions.drawing_utils
except AttributeError:
    from mediapipe.python.solutions import face_mesh as _fm
    from mediapipe.python.solutions import hands as _h
    from mediapipe.python.solutions import drawing_utils as _du
    mp_face_mesh = _fm # 468-point (+ iris) face landmark model
    mp_hands     = _h # 21-point hand landmark model
    mp_drawing   = _du # Helper for drawing landmarks (unused visually but kept for debugging)

# ─────────────────────────────────────────────────────────────────────────────
# DETECTION TOGGLES — set False to fully disable a detector (no compute, no alerts)
# ─────────────────────────────────────────────────────────────────────────────

DETECT_FRUSTRATED  = False
DETECT_FACE_TOUCH  = True
DETECT_SQUINT      = False
DETECT_BLINK_RATE  = True

# ─────────────────────────────────────────────────────────────────────────────
# CALIBRATION CONFIG
# ─────────────────────────────────────────────────────────────────────────────

# How many video frames to collect for baseline calibration
# At 30fps this is ~2 seconds. Increase if you want a longer calibration window.
CALIBRATION_FRAMES = 60

# ─────────────────────────────────────────────────────────────────────────────
# SQUINT DETECTION CONFIG
# These are the main values to tweak if squint detection is too sensitive or not
# sensitive enough for you.
# ─────────────────────────────────────────────────────────────────────────────

# How long (seconds) eyes must stay squinted before alert fires
# Increase this if normal reading focus triggers false alerts
# Decrease if you want faster detection
SQUINT_SUSTAIN_SECONDS = 2.0

# EAR must drop this much BELOW your calibrated baseline to count as a squint
# E.g. 0.20 means "20% below your normal open eye EAR"
# Increase (e.g. 0.25) if normal blinking is causing alerts
# Decrease (e.g. 0.15) if your squint is subtle and not being caught
SQUINT_DROP_THRESHOLD = 0.20

# Glasses mode adds extra tolerance to the EAR threshold
# because thick frames or lens glare can make eyes appear slightly more closed
# This value is added to SQUINT_DROP_THRESHOLD when glasses mode is ON
# Tweak: if glasses mode still gives false positives, increase this (e.g. 0.08)
GLASSES_EAR_TOLERANCE = 0.05

# Blink filter: if EAR recovers within this many frames, it was a blink not a squint
# Increase if rapid repeated blinks are being counted as squints
BLINK_FRAME_TOLERANCE = 3

# ─────────────────────────────────────────────────────────────────────────────
# BLINK RATE CONFIG
# ─────────────────────────────────────────────────────────────────────────────

# EAR must fall below (baseline * this ratio) to register as a blink
# 0.65 means 65% of your open-eye baseline — catches full and partial blinks
# Tweak: lower to 0.55 if subtle blinks aren't being counted
BLINK_EAR_RATIO = 0.65

# Max consecutive low-EAR frames that still counts as a blink (not a squint)
# At 30fps: 10 frames ≈ 333ms — covers slow/lazy blinks
BLINK_MAX_FRAMES = 10

# Seconds without a detected blink before the "blink more" alert fires
# Tweak: raise to 8 if 5 seconds feels too frequent
BLINK_ALERT_SECONDS = 5


# ─────────────────────────────────────────────────────────────────────────────
# MAIN DETECTOR CLASS
# ─────────────────────────────────────────────────────────────────────────────

class FaceGuard:
    def __init__(self, sensitivity=1.0):
        # sensitivity: multiplier on detection scores
        # 1.0 = default, 0.5 = harder to trigger, 2.0 = very easy to trigger
        self.sensitivity = sensitivity

        self.alert  = AlertSystem()    # Handles beep sounds
        self.logger = SessionLogger()  # Handles session JSON logging

        # ── Calibration state ──────────────────────────────────────────────
        self.calibrated = False  # Becomes True after CALIBRATION_FRAMES collected

        # Raw collected values during calibration phase
        self.calibration_data = {"brow": [], "lip": [], "ear": []}

        # Baseline values — set once calibration completes
        self.baseline_brow = None   # Your neutral brow distance
        self.baseline_lip  = None   # Your neutral lip gap
        self.baseline_ear  = None   # Your natural open-eye EAR

        # ── Cooldown tracking ─────────────────────────────────────────────
        # Stores timestamp of last alert per type — prevents rapid-fire beeping
        self.cooldown = {
            "frustrated": 0,
            "face_touch": 0,
            "squint":     0,
            "low_blink":  0,
        }
        # Seconds between repeat alerts for each type
        # Tweak: reduce to 5 for more frequent reminders, raise to 15 for fewer
        self.cooldown_duration = 8

        # ── Session stats ─────────────────────────────────────────────────
        self.stats = {
            "frustrated_count": 0,
            "face_touch_count": 0,
            "squint_count":     0,
            "blink_total":      0,
            "low_blink_count":  0,
            "session_start":    time.time(),  # Unix timestamp of session start
        }

        # ── Smoothing buffers ─────────────────────────────────────────────
        # Rolling average over last N frames to reduce jitter/noise
        self.brow_buffer = []
        self.lip_buffer  = []
        self.ear_buffer  = []
        # Number of frames to average over
        # Tweak: 5 = faster response but noisier; 12 = smoother but more lag
        self.buffer_size = 8

        # ── Squint sustain tracking ───────────────────────────────────────
        # Timestamp when squint was first detected in current sustained episode
        self.squint_start_time = None

        # Counter for blink filter: how many consecutive frames EAR was low
        self.squint_frame_count = 0

        # ── Glasses mode ─────────────────────────────────────────────────
        # When True, EAR threshold is relaxed by GLASSES_EAR_TOLERANCE
        # Toggle with G key at runtime
        self.glasses_mode = False

        # ── Blink rate tracking ───────────────────────────────────────────
        self.last_blink_time   = time.time()  # Timestamp of most recent detected blink
        self.blink_ear_low     = False        # Was EAR below blink threshold on last frame?
        self.blink_low_frames  = 0            # Consecutive frames where EAR is below threshold

    # ── CALIBRATION ───────────────────────────────────────────────────────────

    def calibrate(self, brow_dist, lip_dist, avg_ear):
        """
        Collects measurements during the calibration window.
        Once CALIBRATION_FRAMES are collected, computes and locks in baselines.
        Returns progress as float 0.0-1.0 for the progress bar.
        """
        self.calibration_data["brow"].append(brow_dist)
        self.calibration_data["lip"].append(lip_dist)
        self.calibration_data["ear"].append(avg_ear)

        progress = len(self.calibration_data["brow"])  # How many frames collected

        if progress >= CALIBRATION_FRAMES:
            # Average all collected frames to get stable baselines
            self.baseline_brow = np.mean(self.calibration_data["brow"])
            self.baseline_lip  = np.mean(self.calibration_data["lip"])
            self.baseline_ear  = np.mean(self.calibration_data["ear"])
            self.calibrated = True
            self.last_blink_time = time.time()  # Start blink timer fresh after calibration
            print(f"Calibrated | brow={self.baseline_brow:.1f}px | lip={self.baseline_lip:.1f}px | EAR={self.baseline_ear:.3f}")
            self.alert.beep("calibrated")

        return progress / CALIBRATION_FRAMES  # 0.0 to 1.0

    # ── SMOOTHING ─────────────────────────────────────────────────────────────

    def smooth(self, buffer, value):
        """
        Appends value to rolling buffer, trims to buffer_size, returns mean.
        This prevents single noisy frames from triggering false alerts.
        """
        buffer.append(value)
        if len(buffer) > self.buffer_size:
            buffer.pop(0)  # Remove oldest frame value
        return np.mean(buffer)

    # ── FRUSTRATION DETECTION ────────────────────────────────────────────────

    def check_frustrated(self, brow_dist, lip_dist, face_width):
        """
        Compares current brow/lip measurements to calibrated baseline.
        Returns (is_frustrated: bool, score: float 0-1 for the progress bar).

        Score formula:
          brow_drop: how much brow distance shrank relative to baseline (0.65 weight)
          lip_drop:  how much lip gap shrank relative to baseline (0.35 weight)
          score = weighted sum * sensitivity multiplier

        Tweak the weights (0.65 / 0.35) if your frustration shows more in lips vs brows.
        Tweak the threshold (0.12) if you get too many or too few detections.
        """
        if not self.calibrated:
            return False, 0.0  # Cannot detect without a baseline

        # Apply rolling average to reduce frame-to-frame noise
        smooth_brow = self.smooth(self.brow_buffer, brow_dist)
        smooth_lip  = self.smooth(self.lip_buffer,  lip_dist)

        # Normalize by face width so distance from camera does not matter
        brow_ratio      = smooth_brow / face_width
        base_brow_ratio = self.baseline_brow / face_width

        lip_ratio      = smooth_lip / face_width
        base_lip_ratio = self.baseline_lip / face_width

        # How much each metric dropped below baseline (positive = dropped = more frustrated)
        brow_drop = (base_brow_ratio - brow_ratio) / base_brow_ratio
        lip_drop  = (base_lip_ratio  - lip_ratio)  / base_lip_ratio

        # Weighted composite score — brows carry more weight than lips
        score = (brow_drop * 0.65 + lip_drop * 0.35) * self.sensitivity

        # 12% deviation from your baseline triggers detection
        # Tweak: raise to 0.15 if you are getting false positives during normal focus
        #        lower to 0.08 if your frustrated face is subtle
        is_frustrated = score > 0.12

        # Clamp score to 0-1 range for the UI progress bar
        return is_frustrated, max(0.0, min(1.0, score / 0.25))

    # ── SQUINT DETECTION ────────────────────────────────────────────────────

    def check_squint(self, avg_ear):
        """
        Detects sustained eye squinting using Eye Aspect Ratio (EAR).

        Logic:
          1. Smooth EAR over buffer to filter noise
          2. Compare smoothed EAR to baseline — compute how much it dropped
          3. If drop exceeds threshold AND sustained for SQUINT_SUSTAIN_SECONDS, alert
          4. Blink filter: reset sustain timer if EAR recovers within BLINK_FRAME_TOLERANCE frames

        Returns (is_squinting: bool, ear_score: float 0-1 for UI bar)
        """
        if not self.calibrated:
            return False, 0.0

        smooth_ear = self.smooth(self.ear_buffer, avg_ear)

        # How much EAR dropped relative to your personal open-eye baseline
        ear_drop = (self.baseline_ear - smooth_ear) / self.baseline_ear

        # Add extra tolerance in glasses mode (reflections and frames reduce EAR slightly)
        effective_threshold = SQUINT_DROP_THRESHOLD
        if self.glasses_mode:
            # Glasses make eyes appear slightly more closed, so we require a bigger drop
            effective_threshold += GLASSES_EAR_TOLERANCE

        # Apply sensitivity multiplier
        adjusted_drop = ear_drop * self.sensitivity

        currently_low = adjusted_drop > effective_threshold  # Is EAR low right now?

        if currently_low:
            self.squint_frame_count += 1  # Count consecutive low-EAR frames

            if self.squint_start_time is None:
                # First frame of this squint episode — start the sustain timer
                self.squint_start_time = time.time()

            # Check if it has been sustained long enough to count as squinting, not blinking
            sustained = (time.time() - self.squint_start_time) >= SQUINT_SUSTAIN_SECONDS
        else:
            # EAR recovered — could be end of squint or end of blink
            if self.squint_frame_count <= BLINK_FRAME_TOLERANCE:
                # Recovered too quickly — this was a blink, not a squint. Reset everything.
                self.squint_start_time = None
                self.squint_frame_count = 0
            else:
                # Sustained squint episode just ended — clear the timer
                self.squint_start_time = None
                self.squint_frame_count = 0

            sustained = False

        # Score for UI bar: how far EAR has dropped relative to threshold
        ear_score = max(0.0, min(1.0, adjusted_drop / (effective_threshold * 2)))

        return sustained, ear_score

    # ── BLINK RATE DETECTION ────────────────────────────────────────────────

    def check_blink_rate(self, avg_ear):
        """
        Detects individual blinks. If no blink is detected for BLINK_ALERT_SECONDS,
        returns is_low=True to trigger the "blink more" alert.

        A blink is: EAR drops below (baseline * BLINK_EAR_RATIO) then recovers
        within BLINK_MAX_FRAMES. Longer drops are squints, not blinks.

        Returns (is_low: bool, secs_since_blink: float)
        """
        if not self.calibrated:
            return False, 0.0

        is_low_now = avg_ear < self.baseline_ear * BLINK_EAR_RATIO

        if is_low_now:
            self.blink_low_frames += 1
            self.blink_ear_low = True
        else:
            if self.blink_ear_low and self.blink_low_frames <= BLINK_MAX_FRAMES:
                self.last_blink_time = time.time()
                self.stats["blink_total"] += 1
            self.blink_ear_low = False
            self.blink_low_frames = 0

        secs_since_blink = time.time() - self.last_blink_time
        return secs_since_blink >= BLINK_ALERT_SECONDS, secs_since_blink

    # ── ALERT SYSTEM ────────────────────────────────────────────────────────

    def can_alert(self, alert_type):
        """Returns True if enough time has passed since the last alert of this type."""
        return time.time() - self.cooldown[alert_type] > self.cooldown_duration

    def trigger_alert(self, alert_type):
        """Fires a beep alert if cooldown has passed, then records the event."""
        if self.can_alert(alert_type):
            self.cooldown[alert_type] = time.time()  # Reset cooldown timer
            self.alert.beep(alert_type)              # Play the beep sound
            self.stats[f"{alert_type}_count"] += 1  # Increment session counter
            self.logger.log_event(alert_type)        # Write to session log

    # ── UI OVERLAY ──────────────────────────────────────────────────────────

    def draw_overlay(self, frame, cal_progress,
                     is_frustrated, frustration_score,
                     is_touching,   touch_point,
                     is_squinting,  ear_score,
                     blink_secs,    is_low_blink,
                     h, w):
        """
        Draws the semi-transparent sidebar and all status indicators onto the frame.
        Everything in this function is purely visual — no detection logic here.
        """

        # Draw a dark semi-transparent rectangle for the sidebar background
        overlay = frame.copy()
        cv2.rectangle(overlay, (0, 0), (300, h), (10, 10, 20), -1)
        # Blend sidebar with camera feed: 0.6 = sidebar opacity, 0.4 = camera bleed-through
        # Tweak the 0.6 value if you want the sidebar darker or lighter
        cv2.addWeighted(overlay, 0.6, frame, 0.4, 0, frame)

        # App title and version
        cv2.putText(frame, "FACEGUARD", (12, 35), cv2.FONT_HERSHEY_DUPLEX, 0.8, (80, 220, 120), 2)
        cv2.putText(frame, "v2.0", (200, 35), cv2.FONT_HERSHEY_PLAIN, 1.0, (100, 100, 100), 1)

        # Session timer — counts up from launch
        elapsed = int(time.time() - self.stats["session_start"])
        mins, secs = divmod(elapsed, 60)
        cv2.putText(frame, f"Session  {mins:02d}:{secs:02d}", (12, 60),
                    cv2.FONT_HERSHEY_PLAIN, 1.1, (160, 160, 160), 1)

        # Glasses mode indicator
        glasses_label = "GLASSES ON" if self.glasses_mode else "NO GLASSES"
        glasses_color = (200, 180, 80) if self.glasses_mode else (80, 80, 80)
        cv2.putText(frame, glasses_label, (12, 78), cv2.FONT_HERSHEY_PLAIN, 0.95, glasses_color, 1)

        # ── CALIBRATION PHASE UI ──────────────────────────────────────────
        if not self.calibrated:
            bar_w = int(270 * cal_progress)  # Width of progress bar in pixels

            # Background track for progress bar
            cv2.rectangle(frame, (12, 95), (282, 115), (40, 40, 60), -1)
            # Filled portion of progress bar
            cv2.rectangle(frame, (12, 95), (12 + bar_w, 115), (80, 200, 120), -1)

            cv2.putText(frame, f"Calibrating... {int(cal_progress*100)}%", (12, 111),
                        cv2.FONT_HERSHEY_PLAIN, 1.0, (220, 220, 220), 1)
            cv2.putText(frame, "Keep neutral face, eyes open", (12, 130),
                        cv2.FONT_HERSHEY_PLAIN, 1.0, (180, 180, 100), 1)
            cv2.putText(frame, "Press G first if wearing glasses", (12, 148),
                        cv2.FONT_HERSHEY_PLAIN, 0.9, (120, 120, 80), 1)

        # ── LIVE DETECTION UI ─────────────────────────────────────────────
        else:
            y = 100  # Starting y position for first indicator — increments as we go down

            # ── 1. FRUSTRATED FACE ────────────────────────────────────────
            cv2.putText(frame, "FRUSTRATED", (12, y), cv2.FONT_HERSHEY_PLAIN, 1.0, (140, 140, 140), 1)

            bar_w = int(270 * frustration_score)  # Bar width proportional to score
            # Color shifts to red-ish when score is high, green when low
            bar_color = (60, 80, 220) if frustration_score > 0.5 else (60, 180, 80)
            cv2.rectangle(frame, (12, y+5),  (282, y+20), (40, 40, 60), -1)   # Background track
            cv2.rectangle(frame, (12, y+5),  (12 + bar_w, y+20), bar_color, -1)  # Fill

            f_label = "DETECTED" if is_frustrated else "OK"
            f_color = (80, 80, 255) if is_frustrated else (80, 220, 80)
            cv2.putText(frame, f_label, (12, y+36), cv2.FONT_HERSHEY_DUPLEX, 0.55, f_color, 1)
            y += 55

            # ── 2. FACE TOUCH ─────────────────────────────────────────────
            cv2.putText(frame, "FACE TOUCH", (12, y), cv2.FONT_HERSHEY_PLAIN, 1.0, (140, 140, 140), 1)
            t_label = "TOUCHING" if is_touching else "CLEAR"
            t_color = (80, 80, 255) if is_touching else (80, 220, 80)
            cv2.putText(frame, t_label, (12, y+18), cv2.FONT_HERSHEY_DUPLEX, 0.55, t_color, 1)
            y += 45

            # ── 3. SQUINT ─────────────────────────────────────────────────
            cv2.putText(frame, "SQUINTING", (12, y), cv2.FONT_HERSHEY_PLAIN, 1.0, (140, 140, 140), 1)

            bar_w = int(270 * ear_score)  # How closed eyes are relative to threshold
            ear_color = (60, 120, 220) if ear_score > 0.5 else (60, 180, 80)
            cv2.rectangle(frame, (12, y+5),  (282, y+20), (40, 40, 60), -1)
            cv2.rectangle(frame, (12, y+5),  (12 + bar_w, y+20), ear_color, -1)

            # Shows build-up progress while squinting but not yet past sustain threshold
            if self.squint_start_time is not None and not is_squinting:
                time_held = time.time() - self.squint_start_time
                sustain_pct = int((time_held / SQUINT_SUSTAIN_SECONDS) * 100)
                sq_label = f"holding... {sustain_pct}%"
                sq_color = (180, 140, 60)
            else:
                sq_label = "DETECTED" if is_squinting else "OK"
                sq_color = (80, 80, 255) if is_squinting else (80, 220, 80)

            cv2.putText(frame, sq_label, (12, y+36), cv2.FONT_HERSHEY_DUPLEX, 0.55, sq_color, 1)
            y += 55

            # ── 4. BLINK RATE ─────────────────────────────────────────────
            cv2.putText(frame, "BLINK RATE", (12, y), cv2.FONT_HERSHEY_PLAIN, 1.0, (140, 140, 140), 1)
            blink_label = f"last blink {blink_secs:.0f}s ago  {'BLINK!' if is_low_blink else 'OK'}"
            blink_color = (80, 80, 255) if is_low_blink else (80, 220, 80)
            cv2.putText(frame, blink_label, (12, y+18), cv2.FONT_HERSHEY_DUPLEX, 0.55, blink_color, 1)
            y += 42

            # ── ALERT COUNTS ──────────────────────────────────────────────
            cv2.putText(frame, f"Frustrated : {self.stats['frustrated_count']}",
                        (12, y), cv2.FONT_HERSHEY_PLAIN, 1.05, (200, 200, 200), 1)
            cv2.putText(frame, f"Face touch : {self.stats['face_touch_count']}",
                        (12, y+18), cv2.FONT_HERSHEY_PLAIN, 1.05, (200, 200, 200), 1)
            cv2.putText(frame, f"Squinting  : {self.stats['squint_count']}",
                        (12, y+36), cv2.FONT_HERSHEY_PLAIN, 1.05, (200, 200, 200), 1)
            cv2.putText(frame, f"Blinks     : {self.stats['blink_total']}",
                        (12, y+54), cv2.FONT_HERSHEY_PLAIN, 1.05, (200, 200, 200), 1)
            y += 75

            # ── COOLDOWN TIMERS ───────────────────────────────────────────
            # Shows seconds remaining until next alert is possible for each type
            for label, key in [("Expr", "frustrated"), ("Touch", "face_touch"), ("Squint", "squint"), ("Blink", "low_blink")]:
                left = max(0, self.cooldown_duration - (time.time() - self.cooldown[key]))
                color = (80, 80, 180) if left > 0 else (80, 180, 80)  # Purple = waiting, green = ready
                cv2.putText(frame, f"{label} cd: {left:.0f}s",
                            (12, y), cv2.FONT_HERSHEY_PLAIN, 0.95, color, 1)
                y += 18

        # ── ALERT FLASH ───────────────────────────────────────────────────
        # Tints the camera feed area slightly red when any alert is active
        if is_frustrated or is_touching or is_squinting or is_low_blink:
            flash = frame.copy()
            cv2.rectangle(flash, (300, 0), (w, h), (0, 0, 160), -1)
            # 0.08 = very subtle red tint — increase to 0.15 for more dramatic flash
            cv2.addWeighted(flash, 0.08, frame, 0.92, 0, frame)

        # ── TOUCH POINT INDICATOR ─────────────────────────────────────────
        # Draws a circle where the fingertip is detected near the face
        if is_touching and touch_point is not None:
            cv2.circle(frame, (int(touch_point[0]), int(touch_point[1])), 15, (0, 80, 255), 3)
            cv2.circle(frame, (int(touch_point[0]), int(touch_point[1])), 5,  (0, 80, 255), -1)

        # ── SENSITIVITY DISPLAY ───────────────────────────────────────────
        cv2.putText(frame, f"Sensitivity: {self.sensitivity:.1f}",
                    (12, h - 28), cv2.FONT_HERSHEY_PLAIN, 0.95, (100, 100, 100), 1)

        # ── KEY HINT BAR ──────────────────────────────────────────────────
        cv2.putText(frame, "Q=quit | R=recal | G=glasses | +/-=sens",
                    (12, h - 10), cv2.FONT_HERSHEY_PLAIN, 0.88, (70, 70, 70), 1)

        return frame

    # ── MAIN LOOP ────────────────────────────────────────────────────────────

    def run(self):
        """
        Main detection loop:
          1. Opens webcam
          2. Processes each frame through MediaPipe face mesh + hands
          3. Runs all three detectors
          4. Draws overlay
          5. Handles key input
          6. Saves session on quit
        """
        cap = cv2.VideoCapture(0)  # 0 = default webcam. Change to 1 if using external cam.
        if not cap.isOpened():
            print("Could not open webcam.")
            return

        # Request 720p — MediaPipe works well at this resolution
        # Tweak: use 1920x1080 for sharper landmark tracking (slightly slower)
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

        print("FaceGuard started.")
        print("  Keep a NEUTRAL face with EYES OPEN for calibration (~2 sec)")
        print("  Press G BEFORE calibrating if you are wearing glasses")

        # Initialize both models inside a context manager (auto-cleanup on exit)
        with mp_face_mesh.FaceMesh(
            max_num_faces=1,          # Only track one face (you)
            refine_landmarks=True,    # Enables iris landmarks — needed for EAR accuracy
            min_detection_confidence=0.6,   # Min confidence to detect a face in a frame
            min_tracking_confidence=0.6     # Min confidence to keep tracking frame to frame
                                            # Tweak both lower = more detections but more jitter
        ) as face_mesh, mp_hands.Hands(
            max_num_hands=2,                # Track up to both hands
            min_detection_confidence=0.6,
            min_tracking_confidence=0.6
        ) as hands:

            cal_progress = 0.0  # Progress bar value during calibration phase

            while True:
                ret, frame = cap.read()  # Capture one frame from webcam
                if not ret:
                    # Frame capture failed — usually means webcam disconnected
                    print("Frame capture failed. Check webcam connection.")
                    break

                frame = cv2.flip(frame, 1)  # Mirror horizontally — more natural to look at
                h, w = frame.shape[:2]       # Get frame dimensions for coordinate math

                # MediaPipe requires RGB input; OpenCV captures BGR by default
                rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

                # Run both models on the current frame
                face_results = face_mesh.process(rgb)
                hand_results = hands.process(rgb)

                # Default values if nothing is detected this frame
                is_frustrated   = False
                frustration_score = 0.0
                is_touching     = False
                touch_point     = None
                is_squinting    = False
                ear_score       = 0.0
                is_low_blink    = False
                blink_secs      = 0.0

                # Only run detection if at least one face is found in the frame
                if face_results.multi_face_landmarks:
                    # Get the landmark list for the first (only) face
                    lms = face_results.multi_face_landmarks[0].landmark

                    # ── Extract raw measurements from landmarks ───────────
                    brow_dist  = get_brow_distance(lms, w, h)
                    lip_dist   = get_lip_compression(lms, w, h)
                    face_width = get_face_width(lms, w, h)

                    # Average EAR of both eyes — more stable than using just one eye
                    left_ear  = get_ear(lms, LEFT_EYE_LANDMARKS,  w, h)
                    right_ear = get_ear(lms, RIGHT_EYE_LANDMARKS, w, h)
                    avg_ear   = (left_ear + right_ear) / 2.0

                    if not self.calibrated:
                        # Still collecting calibration frames — update progress bar
                        cal_progress = self.calibrate(brow_dist, lip_dist, avg_ear)
                    else:
                        # ── Run enabled detectors ────────────────────────

                        if DETECT_FRUSTRATED:
                            is_frustrated, frustration_score = self.check_frustrated(
                                brow_dist, lip_dist, face_width)
                            if is_frustrated:
                                self.trigger_alert("frustrated")

                        if DETECT_FACE_TOUCH:
                            hand_lms_list = hand_results.multi_hand_landmarks or []
                            is_touching, touch_point = is_hand_near_face(lms, hand_lms_list, w, h)
                            if is_touching:
                                self.trigger_alert("face_touch")

                        if DETECT_SQUINT:
                            is_squinting, ear_score = self.check_squint(avg_ear)
                            if is_squinting:
                                self.trigger_alert("squint")

                        if DETECT_BLINK_RATE:
                            is_low_blink, blink_secs = self.check_blink_rate(avg_ear)
                            if is_low_blink:
                                self.trigger_alert("low_blink")

                # Draw all UI elements on top of the current frame
                frame = self.draw_overlay(
                    frame, cal_progress,
                    is_frustrated,  frustration_score,
                    is_touching,    touch_point,
                    is_squinting,   ear_score,
                    blink_secs,     is_low_blink,
                    h, w
                )

                cv2.imshow("FaceGuard", frame)  # Display the annotated frame

                # ── KEYBOARD INPUT ────────────────────────────────────────
                # waitKey(1) = process one frame then wait max 1ms for a key press
                key = cv2.waitKey(1) & 0xFF

                if key == ord('q'):
                    # Quit the app gracefully
                    break

                elif key == ord('r'):
                    # Full recalibration — resets all baselines and buffers
                    print("Recalibrating... keep neutral face with eyes open")
                    self.calibrated = False
                    self.calibration_data = {"brow": [], "lip": [], "ear": []}
                    self.brow_buffer = []
                    self.lip_buffer  = []
                    self.ear_buffer  = []
                    self.squint_start_time = None
                    self.squint_frame_count = 0
                    self.last_blink_time  = time.time()
                    self.blink_ear_low    = False
                    self.blink_low_frames = 0

                elif key == ord('g'):
                    # Toggle glasses mode on/off
                    self.glasses_mode = not self.glasses_mode
                    mode_str = "ON" if self.glasses_mode else "OFF"
                    print(f"Glasses mode: {mode_str}")
                    print("  Press R to recalibrate with this glasses setting")

                elif key in (ord('+'), ord('=')):
                    # Increase sensitivity — all three detectors trigger more easily
                    self.sensitivity = min(2.0, self.sensitivity + 0.1)
                    print(f"Sensitivity: {self.sensitivity:.1f}")

                elif key == ord('-'):
                    # Decrease sensitivity — harder to trigger, fewer false positives
                    self.sensitivity = max(0.3, self.sensitivity - 0.1)
                    print(f"Sensitivity: {self.sensitivity:.1f}")

        # ── CLEANUP ───────────────────────────────────────────────────────
        cap.release()             # Release webcam handle back to OS
        cv2.destroyAllWindows()   # Close the OpenCV display window
        self.logger.save_session(self.stats)   # Write session summary to JSON
        print("Session saved. Check session_log.json for your stats.")


# ─────────────────────────────────────────────────────────────────────────────
# ENTRY POINT
# ─────────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    # Starting sensitivity of 1.0 — adjust at runtime with +/- keys
    guard = FaceGuard(sensitivity=1.0)
    guard.run()
