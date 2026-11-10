"""Experimental MediaPipe pose client for SquashAnalytics.

This script extracts 2D image-space position and a rough torso-lean proxy. It
cannot infer real-world stride length, bilateral asymmetry, knee valgus, or
heart rate from a single uncalibrated camera view. Supply those values from
validated sensors/calibration; this is not a medical or injury-detection tool.
"""

import argparse
import math
import time
from typing import Optional

import cv2
import mediapipe as mp
import requests


def parse_args():
    parser = argparse.ArgumentParser(description="Send experimental pose telemetry to SquashAnalytics API")
    parser.add_argument("video", help="Video file path or camera index, e.g. 0")
    parser.add_argument("--api-url", default="http://localhost:8000/telemetry/frame")
    parser.add_argument("--partido-id", type=int, required=True)
    parser.add_argument("--jugador-id", type=int, required=True)
    parser.add_argument("--stride-cm", type=float, required=True, help="Measured/calibrated stride input (cm)")
    parser.add_argument("--asymmetry-percent", type=float, required=True, help="Measured asymmetry input (0-100)")
    parser.add_argument("--valgus-deg", type=float, required=True, help="Valgus measurement from a validated/calibrated source; not inferred by this 2D script")
    parser.add_argument("--rotation-deg", type=float, required=True, help="Measured/calibrated torso rotation input")
    parser.add_argument("--heart-rate", type=int, help="Heart rate from a sensor, bpm; not inferred from video")
    parser.add_argument("--heart-rate-zone", type=int, choices=range(1, 6))
    parser.add_argument("--every-n-frames", type=int, default=5)
    parser.add_argument("--court-width-m", type=float, default=6.4)
    parser.add_argument("--court-length-m", type=float, default=9.75)
    parser.add_argument("--send", action="store_true", help="Actually POST telemetry; without this flag only prints the payload")
    parser.add_argument("--show", action="store_true", help="Show annotated video window (requires desktop display)")
    args = parser.parse_args()
    if args.every_n_frames < 1:
        parser.error("--every-n-frames must be at least 1")
    if args.heart_rate_zone is not None and args.heart_rate is None:
        parser.error("--heart-rate-zone requires --heart-rate")
    if args.heart_rate is not None and not 30 <= args.heart_rate <= 250:
        parser.error("--heart-rate must be between 30 and 250 bpm")
    if not 0 <= args.asymmetry_percent <= 100:
        parser.error("--asymmetry-percent must be between 0 and 100")
    return args


def source_from_arg(value: str):
    return int(value) if value.isdigit() else value


def torso_lean_proxy(hip, shoulder) -> float:
    """Return 2D torso inclination from image vertical; not lumbar flexion."""
    dx = shoulder[0] - hip[0]
    dy = shoulder[1] - hip[1]
    return math.degrees(math.atan2(abs(dx), abs(dy)))


def main():
    args = parse_args()
    capture = cv2.VideoCapture(source_from_arg(args.video))
    if not capture.isOpened():
        raise SystemExit(f"Could not open video source: {args.video}")

    pose_api = mp.solutions.pose
    frame_index = 0
    session = requests.Session()
    print("Experimental 2D pose processing started. Ctrl+C or close the preview to stop.")
    if not args.send:
        print("DRY RUN: no API requests will be sent. Add --send to enable POSTs.")

    try:
        with pose_api.Pose(min_detection_confidence=0.6, min_tracking_confidence=0.6) as pose:
            while capture.isOpened():
                ok, frame = capture.read()
                if not ok:
                    break
                frame_index += 1
                height, width = frame.shape[:2]
                result = pose.process(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))

                if result.pose_landmarks and frame_index % args.every_n_frames == 0:
                    points = result.pose_landmarks.landmark
                    hip_lm = points[pose_api.PoseLandmark.RIGHT_HIP.value]
                    shoulder_lm = points[pose_api.PoseLandmark.RIGHT_SHOULDER.value]
                    if min(hip_lm.visibility, shoulder_lm.visibility) >= 0.6:
                        hip_x, hip_y = hip_lm.x * width, hip_lm.y * height
                        shoulder_x, shoulder_y = shoulder_lm.x * width, shoulder_lm.y * height
                        lean = torso_lean_proxy((hip_x, hip_y), (shoulder_x, shoulder_y))
                        payload = {
                            "partido_id": args.partido_id,
                            "jugador_id": args.jugador_id,
                            "frame_index": frame_index,
                            "longitud_zancada_cm": args.stride_cm,
                            "simetria_zancada_abi": args.asymmetry_percent,
                            "angulo_valgo_rodilla_deg": args.valgus_deg,
                            "flexion_lumbar_deg": lean,
                            "rotacion_toraco_lumbar_deg": args.rotation_deg,
                            "coordenada_x": round(max(0.0, min(args.court_width_m, hip_x / width * args.court_width_m)), 3),
                            "coordenada_y": round(max(0.0, min(args.court_length_m, hip_y / height * args.court_length_m)), 3),
                            "en_zona_riesgo_esquina": False,
                            "fc_actual": args.heart_rate,
                            "zona_fc": args.heart_rate_zone,
                        }
                        print(f"Frame {frame_index}: {payload}")
                        if args.send:
                            try:
                                response = session.post(args.api_url, json=payload, timeout=5)
                                response.raise_for_status()
                            except requests.RequestException as exc:
                                print(f"POST failed for frame {frame_index}: {exc}")

                if args.show:
                    cv2.imshow("SquashAnalytics - experimental pose", frame)
                    if cv2.waitKey(1) & 0xFF == ord("q"):
                        break
    except KeyboardInterrupt:
        print("Stopped by user.")
    finally:
        capture.release()
        session.close()
        if args.show:
            cv2.destroyAllWindows()

    print("Finished. The 2D torso-lean value is only an image-based proxy, not lumbar angle.")


if __name__ == "__main__":
    main()
