import numpy as np


def get_ear(landmarks, eye_lms, w, h):
    """
    Eye Aspect Ratio for one eye.
    Formula: EAR = (|P2-P6| + |P3-P5|) / (2 * |P1-P4|)
    ~0.25-0.35 when open, ~0.0 when fully closed, ~0.15 when squinting.
    """
    p1 = np.array([landmarks[eye_lms["p1"]].x * w, landmarks[eye_lms["p1"]].y * h])
    p2 = np.array([landmarks[eye_lms["p2"]].x * w, landmarks[eye_lms["p2"]].y * h])
    p3 = np.array([landmarks[eye_lms["p3"]].x * w, landmarks[eye_lms["p3"]].y * h])
    p4 = np.array([landmarks[eye_lms["p4"]].x * w, landmarks[eye_lms["p4"]].y * h])
    p5 = np.array([landmarks[eye_lms["p5"]].x * w, landmarks[eye_lms["p5"]].y * h])
    p6 = np.array([landmarks[eye_lms["p6"]].x * w, landmarks[eye_lms["p6"]].y * h])

    vertical_a = np.linalg.norm(p2 - p6)
    vertical_b = np.linalg.norm(p3 - p5)
    horizontal = np.linalg.norm(p1 - p4)

    if horizontal < 1e-6:
        return 0.3  # Sane default if landmarks collapse

    return (vertical_a + vertical_b) / (2.0 * horizontal)
