import numpy as np
from .constants import LEFT_INNER_BROW, RIGHT_INNER_BROW, UPPER_LIP, LOWER_LIP, FACE_OVAL


def get_brow_distance(landmarks, w, h):
    """
    Distance between the centroids of the left and right inner brow clusters.
    Smaller = brows closer together = more furrowed/frustrated.
    """
    left_pts  = np.array([[landmarks[i].x * w, landmarks[i].y * h] for i in LEFT_INNER_BROW])
    right_pts = np.array([[landmarks[i].x * w, landmarks[i].y * h] for i in RIGHT_INNER_BROW])
    return np.linalg.norm(left_pts.mean(axis=0) - right_pts.mean(axis=0))


def get_lip_compression(landmarks, w, h):
    """
    Vertical gap between upper and lower lip center.
    Smaller = lips pressed together = tension/frustration signal.
    """
    upper = np.array([landmarks[UPPER_LIP].x * w, landmarks[UPPER_LIP].y * h])
    lower = np.array([landmarks[LOWER_LIP].x * w, landmarks[LOWER_LIP].y * h])
    return np.linalg.norm(upper - lower)


def get_face_width(landmarks, w, h):
    """
    Horizontal width of the face across the face oval.
    Used to normalize all distances so results are camera-distance independent.
    """
    pts = np.array([[landmarks[i].x * w, landmarks[i].y * h] for i in FACE_OVAL])
    return pts[:, 0].max() - pts[:, 0].min()
