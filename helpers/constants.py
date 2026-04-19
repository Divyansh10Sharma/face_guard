"""
MediaPipe face mesh and hand landmark indices.
Full map: https://mediapipe.dev/images/mobile/face_mesh_full_landmark.png
"""

# Inner brow corners — pull together when furrowing/frowning
LEFT_INNER_BROW  = [55, 65, 52, 53]
RIGHT_INNER_BROW = [285, 295, 282, 283]

# Center of upper and lower lip
UPPER_LIP = 13
LOWER_LIP = 14

# 36-point boundary of the face oval
FACE_OVAL = [10, 338, 297, 332, 284, 251, 389, 356, 454, 323,
             361, 288, 397, 365, 379, 378, 400, 377, 152, 148,
             176, 149, 150, 136, 172, 58, 132, 93, 234, 127,
             162, 21, 54, 103, 67, 109]

# Fingertip indices in the MediaPipe hand model
# 4=thumb, 8=index, 12=middle, 16=ring, 20=pinky
FINGERTIPS = [4, 8, 12, 16, 20]

# Left eye: 6 points forming an ellipse (P1=left corner, P4=right corner, P2/P6=top pair, P3/P5=bottom pair)
LEFT_EYE_LANDMARKS = {
    "p1": 362,
    "p2": 385,
    "p3": 387,
    "p4": 263,
    "p5": 373,
    "p6": 380,
}

# Right eye: same structure, mirrored
RIGHT_EYE_LANDMARKS = {
    "p1": 33,
    "p2": 160,
    "p3": 158,
    "p4": 133,
    "p5": 153,
    "p6": 144,
}
