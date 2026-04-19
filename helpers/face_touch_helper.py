import numpy as np
from .constants import FACE_OVAL, FINGERTIPS
from .face_geometry_helper import get_face_width


def is_hand_near_face(face_landmarks, hand_landmarks_list, w, h, threshold_ratio=0.18):
    """
    Returns (True, fingertip_point) if any fingertip is within
    threshold_ratio * face_width of the face oval boundary.
    Returns (False, None) if no hands or no contact detected.

    threshold_ratio=0.18 means within 18% of face width.
    Tweak: increase to 0.25 to catch near-misses; decrease to 0.12 for stricter contact.
    """
    if not hand_landmarks_list:
        return False, None

    face_pts = np.array([[face_landmarks[i].x * w, face_landmarks[i].y * h] for i in FACE_OVAL])
    threshold = get_face_width(face_landmarks, w, h) * threshold_ratio

    for hand_lms in hand_landmarks_list:
        for tip_idx in FINGERTIPS:
            tip = hand_lms.landmark[tip_idx]
            tip_pt = np.array([tip.x * w, tip.y * h])
            if np.linalg.norm(face_pts - tip_pt, axis=1).min() < threshold:
                return True, tip_pt

    return False, None
