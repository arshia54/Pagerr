#============================================================================

import cv2
import numpy as np
from scipy.spatial.transform import Rotation
from pupil_apriltags import Detector

#============================================================================

frame_size = [960,720]
april_cm = 1000.0   #convert tag transpose to cm 
april_focal = [550,550]

#============================================================================

at_detector = Detector(
    families="tag36h11",
    nthreads=1,
    quad_decimate=1.0,
    quad_sigma=0.0,
    refine_edges=1,
    decode_sharpening=0.25,
    debug=0,
)

#============================================================================

def get_tags(img):
    tags = at_detector.detect(
        cv2.cvtColor(img, cv2.COLOR_BGR2GRAY),
        estimate_tag_pose=True,
        camera_params=(april_focal[0], april_focal[1], int(frame_size[0]/2),int(frame_size[1]/2)),
        tag_size=0.02
    )

    res = []
    if len(tags) > 0:
        for tag in tags:
            r =  Rotation.from_matrix(tag.pose_R)
            angles = r.as_euler("zyx",degrees=True)
            T = tag.pose_t.reshape((3)).tolist()
            for i in range(3):
                T[i] = int(T[i] * april_cm)
            res.append([tag.tag_id, T[0], T[1], T[2], int(angles[1]), int(tag.center[0]), int(tag.center[1])])

    return res

#============================================================================

