
import cv2
import numpy as np
import time
import math
import argparse
from scipy.spatial.transform import Rotation
from pupil_apriltags import Detector

# Optional deps
try:
    from djitellopy import Tello
    _HAS_TELLO = True
except:
    _HAS_TELLO = False

try:
    import psutil
    _HAS_PSUTIL = True
except:
    _HAS_PSUTIL = False

# --------------------------- CONFIG --------------------------

# Camera & tag
FRAME_W, FRAME_H = 960, 720
FX, FY = 550.0, 550.0
CX, CY = FRAME_W / 2.0, FRAME_H / 2.0
TAG_SIZE_M = 0.20 / 10.0  
TO_CM = 100.0

# Gate plan (IDs) –
GATE_SEQUENCE = [1, 5, 12, 19, 23]
SUPPORT_TAGS = {  
    1: [2, 3],
    5: [6, 7],
    12: [10, 11, 13, 14],
    19: [18, 20],
    23: [22, 24]
}

# PID gains 
P_YAW,  D_YAW  = 0.018, 0.008
P_LAT,  D_LAT  = 0.003, 0.0012   
P_UP,   D_UP   = 0.003, 0.0012   
P_FWD,  D_FWD  = 0.020, 0.006    

# Limits (Tello uses -100..100 rc)
MAX_YAW = 70
MAX_LAT = 60
MAX_UP  = 60
MAX_FWD = 80

# Alignment tolerances
PX_TOL = 28      # pixel error tolerance center align
PITCH_OK = 999  

# Distances (cm)
APPROACH_DIST = 180   
PASS_CUTOFF   = 80     

# Time budgets
PER_GATE_DEADLINE = 10.0     
GLOBAL_DEADLINE   = 45.0
SEARCH_TRIGGER    = 7.0      

# Detection & smoothing
DECIMATES = [2.0, 1.5, 1.0]
MIN_DECISION_MARGIN = 30.0
MAX_HAMMING = 0
MIN_QUAD_PERIM = 40.0

ALPHA_T = 0.35  # EMA translation
ALPHA_R = 0.35  # EMA rotation

# Search pattern params
YAW_SWEEP_RATE = 35     
SWEEP_SEGMENT  = 2.0   
SPIRAL_STEP_F  = 30     
SPIRAL_SEGMENT = 1.2
BOX_STEP_F     = 35
BOX_STEP_LAT   = 35
BOX_SEGMENT    = 0.9

# ------------------- Globals -------------------

_STATE = "ACQUIRE"       
_CUR_GATE_IDX = 0
_LAST_SEEN_TIME = 0.0
_GATE_START_TIME = 0.0
_MISSION_START = 0.0
_TARGET_TAG_ID = GATE_SEQUENCE[0]

# EMA memory: id -> {"t": np.array, "rpy": np.array, "ts": t}
_SMOOTH = {}

# Derivative memory
_prev_err = {"yaw": 0.0, "lat": 0.0, "up": 0.0, "fwd": 0.0}
_prev_t   = time.time()

# Tello / Video
_USE_TELLO = False
_TELLO = None
_CAP = None

# HUD / FPS
_prev_fps_t = time.time()
_fps = 0.0

# ---------------------- Utilities ---------------------------

def clamp(x, lo, hi):
    return max(lo, min(hi, x))

def sign(x): return -1 if x < 0 else (1 if x > 0 else 0)

def _wrap_deg(a): return (a + 180.0) % 360.0 - 180.0

def ema(prev, cur, alpha):
    if prev is None: return cur
    return alpha * cur + (1.0 - alpha) * prev

def pose_to_rpy(R_3x3):
    r = Rotation.from_matrix(R_3x3)
    yaw, pitch, roll = r.as_euler("zyx", degrees=True)
    return roll, pitch, yaw

# ------------------ Detection / Preproc ---------------------

def preprocess(gray):
    # CLAHE + Unsharp
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
    g = clahe.apply(gray)
    blur = cv2.GaussianBlur(g, (0,0), 1.0)
    sharp = cv2.addWeighted(g, 1.5, blur, -0.5, 0)
    return sharp

_DET = Detector(
    families="tag36h11",
    nthreads=1,
    quad_decimate=1.0,    
    quad_sigma=0.0,
    refine_edges=1,
    decode_sharpening=0.25,
    debug=0
)

def quality_ok(tag):
    if getattr(tag, "decision_margin", 0.0) < MIN_DECISION_MARGIN: return False
    if getattr(tag, "hamming", 99) > MAX_HAMMING: return False
    per = 0.0
    c = tag.corners
    for i in range(4):
        per += np.linalg.norm(c[i] - c[(i+1) % 4])
    if per < MIN_QUAD_PERIM: return False
    return True

def smooth_state(tag_id, t_cm, rpy):
    prev = _SMOOTH.get(tag_id)
    t_cm = np.array(t_cm, dtype=float)
    rpy = np.array([_wrap_deg(x) for x in rpy], dtype=float)
    if prev is None:
        _SMOOTH[tag_id] = {"t": t_cm, "rpy": rpy, "ts": time.time()}
        return t_cm, rpy
    sm_t = ema(prev["t"], t_cm, ALPHA_T)
    pr = np.array([_wrap_deg(x) for x in prev["rpy"]])
    delta = np.array([_wrap_deg(a - b) for a, b in zip(rpy, pr)])
    sm_r = pr + ALPHA_R * delta
    sm_r = np.array([_wrap_deg(x) for x in sm_r])
    _SMOOTH[tag_id] = {"t": sm_t, "rpy": sm_r, "ts": time.time()}
    return sm_t, sm_r

def detect_tags(bgr):
    gray = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)
    proc = preprocess(gray)
    found = []


    for _ in DECIMATES:
        tags = _DET.detect(proc, estimate_tag_pose=True,
                           camera_params=(FX, FY, CX, CY), tag_size=TAG_SIZE_M)
        for tg in tags:
            if not quality_ok(tg): continue
            t_m = tg.pose_t.reshape(3)
            t_cm = (t_m[0]*TO_CM, t_m[1]*TO_CM, t_m[2]*TO_CM)
            rpy = pose_to_rpy(tg.pose_R)
            t_cm_s, rpy_s = smooth_state(tg.tag_id, t_cm, rpy)
            cx, cy = int(tg.center[0]), int(tg.center[1])
            corners = [(int(x), int(y)) for (x,y) in tg.corners]
            found.append({
                "id": int(tg.tag_id),
                "center": (cx, cy),
                "corners": corners,
                "t_cm": t_cm_s,
                "rpy": rpy_s,
                "dm": float(getattr(tg, "decision_margin", 0.0)),
                "ham": int(getattr(tg, "hamming", 0))
            })
        if found: break

    found.sort(key=lambda d: (d["dm"], -d["ham"]), reverse=True)
    return found

# ------------------ Gate Selection Logic --------------------

def pick_gate(dets, target_id):

    primary = [d for d in dets if d["id"] == target_id]
    if primary:
        return primary[0], "PRIMARY"

    for sid in SUPPORT_TAGS.get(target_id, []):
        aux = [d for d in dets if d["id"] == sid]
        if aux:
            return aux[0], "SUPPORT"

    
    if dets:
        dets2 = sorted(dets, key=lambda d: (d["center"][0]-CX)**2 + (d["center"][1]-CY)**2)
        return dets2[0], "NEAREST"

    return None, "NONE"

# ----------------------- Control (PID) ----------------------

def pid_step(err, prev_err, dt, kp, kd, limit):
    de = (err - prev_err) / max(dt, 1e-3)
    u = kp*err + kd*de
    return clamp(int(round(u)), -limit, limit), de

def compute_rc_from_error(tag):

    global _prev_err, _prev_t

    now = time.time()
    dt = now - _prev_t
    _prev_t = now

    cx, cy = tag["center"]
    err_x = (cx - CX)                  # +right
    err_y = (cy - CY)                  # +down
    tx, ty, tz = tag["t_cm"]           # cm
    roll, pitch, yaw = tag["rpy"]

    u_yaw, de_yaw = pid_step(err_x, _prev_err["yaw"], dt, P_YAW, D_YAW, MAX_YAW)
    u_lat, de_lat = pid_step(err_x, _prev_err["lat"], dt, P_LAT, D_LAT, MAX_LAT)

    u_up,  de_up  = pid_step(-err_y, _prev_err["up"],  dt, P_UP,  D_UP,  MAX_UP)


    dist_err = max(0.0, tz - APPROACH_DIST)  
    u_fwd, de_fwd = pid_step(dist_err, _prev_err["fwd"], dt, P_FWD, D_FWD, MAX_FWD)

    _prev_err["yaw"] = err_x
    _prev_err["lat"] = err_x
    _prev_err["up"]  = -err_y
    _prev_err["fwd"] = dist_err

    
    lr  = clamp(int(round(u_lat * 0.6)), -MAX_LAT, MAX_LAT)
    fb  = clamp(int(round(u_fwd)), -MAX_FWD, MAX_FWD)
    ud  = clamp(int(round(u_up)), -MAX_UP, MAX_UP)
    yw  = clamp(int(round(u_yaw)), -MAX_YAW, MAX_YAW)

    return lr, fb, ud, yw, (err_x, err_y, tz)

# ----------------------- Search Routines --------------------

_search_phase = 0
_search_t0 = 0.0
def reset_search():
    global _search_phase, _search_t0
    _search_phase = 0
    _search_t0 = time.time()

def search_rc():

    global _search_phase, _search_t0
    t = time.time()
    elapsed = t - _search_t0

    if _search_phase == 0:
        # Yaw sweep:
        seg = int(elapsed / SWEEP_SEGMENT)
        dirn = -1 if seg % 2 == 0 else 1
        rc = (0, 0, 0, dirn * YAW_SWEEP_RATE)
        if elapsed > 8.0:  # ~2*4seg
            _search_phase = 1
            _search_t0 = t
        return rc

    if _search_phase == 1:
        # Spiral forward
        seg = int(elapsed / SPIRAL_SEGMENT)
        dirn = 1 if seg % 2 == 0 else -1
        rc = (0, SPIRAL_STEP_F, 0, dirn * 25)
        if elapsed > 6.0:
            _search_phase = 2
            _search_t0 = t
        return rc

    # phase 2: Box
    leg = int(elapsed / BOX_SEGMENT) % 4
    if leg == 0:   rc = (0, BOX_STEP_F, 0, 0)     # forward
    elif leg == 1: rc = (BOX_STEP_LAT, 0, 0, 0)   # right
    elif leg == 2: rc = (0, -BOX_STEP_F, 0, 0)    # back
    else:          rc = (-BOX_STEP_LAT, 0, 0, 0)  # left
    return rc

# ------------------ Pass Decision Heuristics ----------------

def should_pass(tag, det_streak):

    _, _, tz = tag["t_cm"]
    cx, cy = tag["center"]
    ex, ey = abs(cx - CX), abs(cy - CY)

    if tz < APPROACH_DIST and ex < PX_TOL and ey < PX_TOL and det_streak > 6:
        return True, "ALIGNED_NEAR"
    if tz < PASS_CUTOFF:
        return True, "VERY_NEAR"
    return False, ""

# ----------------------- Tello / Video ----------------------

def connect_tello():
    if not _HAS_TELLO:
        print("[Tello] djitellopy not installed; falling back to webcam mode.")
        return None
    dr = Tello()
    dr.connect()
    print(f"[Tello] Battery:", dr.get_battery())
    dr.streamoff()
    dr.streamon()
    dr.takeoff()
    return dr

def read_frame():
    if _USE_TELLO and _TELLO:
        frame = _TELLO.get_frame_read().frame
        if frame is None: return False, None
        return True, cv2.resize(frame, (FRAME_W, FRAME_H))
    else:
        ok, fr = _CAP.read()
        if not ok: return False, None
        return True, cv2.resize(fr, (FRAME_W, FRAME_H))

def rc_send(lr, fb, ud, yaw):
    if _USE_TELLO and _TELLO:
        _TELLO.send_rc_control(lr, fb, ud, yaw)

def get_battery():
    if _USE_TELLO and _TELLO:
        try:
            return _TELLO.get_battery()
        except:
            return None
    if _HAS_PSUTIL and hasattr(psutil, "sensors_battery"):
        b = psutil.sensors_battery()
        if b: return int(b.percent)
    return None

# --------------------------- HUD ----------------------------

def draw_hud(img, state, target_id, tag, rc, det_mode, gate_idx, t_gate, t_total, det_streak):
    global _fps, _prev_fps_t
    now = time.time()
    dt = now - _prev_fps_t
    if dt > 0.25:
        _fps = 1.0 / max(dt, 1e-3)
        _prev_fps_t = now

    h, w = img.shape[:2]
    cv2.line(img, (int(CX)-20, int(CY)), (int(CX)+20, int(CY)), (80,80,80), 1)
    cv2.line(img, (int(CX), int(CY)-20), (int(CX), int(CY)+20), (80,80,80), 1)

    battery = get_battery()
    btxt = f"BAT:{battery}%" if battery is not None else "BAT:N/A"
    txt1 = f"STATE:{state}  GATE:{gate_idx+1}/{len(GATE_SEQUENCE)}  TARGET:{target_id}  {btxt}  FPS:{_fps:.1f}"
    cv2.putText(img, txt1, (12, 22), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255,255,255), 2)

    txt2 = f"GateTime:{t_gate:4.1f}s  Total:{t_total:4.1f}s  Streak:{det_streak}  Mode:{det_mode}"
    cv2.putText(img, txt2, (12, 45), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (220,255,220), 1)

    if tag:
        cx, cy = tag["center"]
        tx, ty, tz = tag["t_cm"]
        rr, pp, yy = tag["rpy"]
        for i in range(4):
            a = tag["corners"][i]
            b = tag["corners"][(i+1)%4]
            cv2.line(img, a, b, (0,255,255), 2)
        cv2.circle(img, (cx, cy), 6, (0, 255, 0), 2)
        cv2.putText(img, f"ID:{tag['id']} T:{tx:.0f},{ty:.0f},{tz:.0f}cm RPY:{rr:.0f},{pp:.0f},{yy:.0f}",
                    (cx+10, cy-10), cv2.FONT_HERSHEY_SIMPLEX, 0.48, (255,255,255), 1)

    if rc:
        lr, fb, ud, yaw = rc
        cv2.putText(img, f"RC lr:{lr} fb:{fb} ud:{ud} yaw:{yaw}", (12, h-12),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.48, (200,255,255), 1)

# ---------------------- Main State Logic --------------------

def main_loop(args):
    global _STATE, _CUR_GATE_IDX, _TARGET_TAG_ID
    global _LAST_SEEN_TIME, _GATE_START_TIME, _MISSION_START
    global _USE_TELLO, _TELLO, _CAP

    _USE_TELLO = (args.mode == "tello")
    if _USE_TELLO:
        _TELLO = connect_tello()
        if _TELLO is None:
            _USE_TELLO = False

    if not _USE_TELLO:
        if args.video is not None:
            _CAP = cv2.VideoCapture(args.video)
        else:
            _CAP = cv2.VideoCapture(0)
        _CAP.set(cv2.CAP_PROP_FRAME_WIDTH, FRAME_W)
        _CAP.set(cv2.CAP_PROP_FRAME_HEIGHT, FRAME_H)

    _STATE = "ACQUIRE"
    _CUR_GATE_IDX = 0
    _TARGET_TAG_ID = GATE_SEQUENCE[_CUR_GATE_IDX]
    _LAST_SEEN_TIME = time.time()
    _GATE_START_TIME = time.time()
    _MISSION_START = time.time()
    det_streak = 0
    reset_search()

    while True:
        ok, frame = read_frame()
        if not ok:
            print("Camera/Stream ended.")
            break

        t_total = time.time() - _MISSION_START
        t_gate  = time.time() - _GATE_START_TIME

        dets = detect_tags(frame)
        tag, det_mode = pick_gate(dets, _TARGET_TAG_ID)

        if tag:
            det_streak += 1
            _LAST_SEEN_TIME = time.time()
        else:
            det_streak = max(0, det_streak - 1)

        rc = (0, 0, 0, 0)

        # --- Mission time bound ---
        if t_total > GLOBAL_DEADLINE:
            _STATE = "STOP"
            rc = (0, 0, 0, 0)
            if _USE_TELLO:
                _TELLO.send_rc_control(0,0,0,0)
            draw_hud(frame, _STATE, _TARGET_TAG_ID, tag, rc, det_mode, _CUR_GATE_IDX, t_gate, t_total, det_streak)
            cv2.imshow("RACE", frame)
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'): break
            continue

        # --- Per-gate deadline fallback ---
        if t_gate > PER_GATE_DEADLINE:
            _STATE = "ACQUIRE"   # 
            _GATE_START_TIME = time.time()
            reset_search()

        # --- 7s no detection → search ---
        if (time.time() - _LAST_SEEN_TIME) > SEARCH_TRIGGER:
            if _STATE != "PROCEED":   
                _STATE = "ACQUIRE"

        # ---------------- FSM ----------------
        if _STATE == "ACQUIRE":
        
            if tag:
                _STATE = "ALIGN"
            else:
                rc = search_rc()

        elif _STATE == "ALIGN":
            if tag:
                lr, fb, ud, yaw, (ex, ey, tz) = compute_rc_from_error(tag)

                fb = int(0.6 * fb)
                rc = (lr, fb, ud, yaw)

                passed, why = should_pass(tag, det_streak)
                if passed:
                    _STATE = "PROCEED"
            else:
                rc = search_rc()

        elif _STATE == "PROCEED":
            if tag:
                lr, fb, ud, yaw, (ex, ey, tz) = compute_rc_from_error(tag)

                fb = clamp(int(fb * 1.2), -MAX_FWD, MAX_FWD)
                rc = (lr, fb, ud, yaw)
                if tz < PASS_CUTOFF:

                    _CUR_GATE_IDX += 1
                    if _CUR_GATE_IDX >= len(GATE_SEQUENCE):
                        _STATE = "DONE"
                    else:
                        _TARGET_TAG_ID = GATE_SEQUENCE[_CUR_GATE_IDX]
                        _STATE = "ACQUIRE"
                        _GATE_START_TIME = time.time()
                        det_streak = 0
                        reset_search()
            else:
            
                rc = (0, 40, 0, 0)
    
                if (time.time() - _LAST_SEEN_TIME) > 0.8:
                    _CUR_GATE_IDX += 1
                    if _CUR_GATE_IDX >= len(GATE_SEQUENCE):
                        _STATE = "DONE"
                    else:
                        _TARGET_TAG_ID = GATE_SEQUENCE[_CUR_GATE_IDX]
                        _STATE = "ACQUIRE"
                        _GATE_START_TIME = time.time()
                        det_streak = 0
                        reset_search()

        elif _STATE == "DONE":
            rc = (0, 0, 0, 0)
            if _USE_TELLO:
                _TELLO.send_rc_control(0,0,0,0)
            cv2.putText(frame, "MISSION COMPLETED", (int(FRAME_W*0.28), int(FRAME_H*0.55)),
                        cv2.FONT_HERSHEY_DUPLEX, 1.0, (0,255,0), 2)

        elif _STATE == "STOP":
            rc = (0, 0, 0, 0)

    
        rc_send(*rc)

        # HUD
        draw_hud(frame, _STATE, _TARGET_TAG_ID, tag, rc, det_mode, _CUR_GATE_IDX, t_gate, t_total, det_streak)

        cv2.imshow("RACE", frame)
        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            break

    if _USE_TELLO and _TELLO:
        try:
            _TELLO.send_rc_control(0,0,0,0)
            # _TELLO.land()
            _TELLO.streamoff()
            _TELLO.end()
        except:
            pass
    else:
        _CAP.release()
    cv2.destroyAllWindows()

# --------------------------- CLI ----------------------------

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", choices=["webcam", "tello"], default="webcam",
                    help="Video source & control mode")
    ap.add_argument("--video", type=str, default=None,
                    help="Optional video file path for replay/sim (webcam mode)")
    args = ap.parse_args()
    main_loop(args)
