# FocusGuard: On-Device AI Study/Work Companion

FocusGuard watches your webcam and tells you, honestly, where your study or work time went. It runs entirely on your own device: **no frame is stored or uploaded**, and only a small timeline of states is saved.

Theme: **Everyday AI** · Track: **Lightning** · Target hardware for Stage II: **UGen300 (Hailo)**

## How it works

```
Webcam ──▶ YOLOv8n detector ──▶ State machine ──▶ Feedback
           (person, cell phone)  (debounced)       (alert + session report)
└──────────────────── all on-device ────────────────────┘
```

Every moment falls into one of three states:

| State | Rule |
|---|---|
| **FOCUSED** | You are at the desk and no phone is in view |
| **PHONE** | A phone has been in view for more than 2 s |
| **AWAY** | Nobody has been at the desk for more than 3 s |

If you are distracted for more than 10 s, FocusGuard shows a reminder on screen and beeps once. All thresholds are configurable.

## Run it

Requires Python 3.9+ and a webcam.

```bash
pip install -r requirements.txt
python focusguard.py
```

The YOLOv8n weights (~6 MB) download automatically on the first run.

| Option | Default | Meaning |
|---|---|---|
| `--camera` | `0` | Camera index |
| `--phone` | `2` | Seconds of phone before PHONE |
| `--away` | `3` | Seconds of absence before AWAY |
| `--alert` | `10` | Seconds distracted before the reminder |
| `--conf` | `0.4` | Detection confidence threshold |

Keys: `q` quits and writes the report, `s` saves a screenshot to `logs/`.

## Session report

When you quit, FocusGuard writes to `logs/`:

- `session_<time>.png`: a colour timeline (green focused, orange phone, grey away)
- `session_<time>_summary.txt`: minutes and share per state, plus phone pick-ups
- `session_<time>.csv`: every state change, for later analysis

## Tech stack

- **Detector**: YOLOv8n pretrained on COCO, using only the `person` and `cell phone` classes. No custom training.
- **State logic**: debounced so one missed frame does not flip the state.
- **Stack**: Python, OpenCV, Ultralytics, Matplotlib. Runs on any laptop CPU.

## Stage II roadmap

1. **Port to UGen300**: compile YOLOv8n to a Hailo HEF (it is a standard model in the Hailo model zoo), with INT8 quantization.
2. **Posture detection**: add a pose model to warn about slouching.
3. **Study-room mode**: track several people in a shared space, still with no video leaving the device.
4. **Daily recap with a local LLM**: turn the session statistics into a short written review, generated on-device.

## Privacy

The camera feed is processed frame by frame in memory and discarded. FocusGuard is a tool you point at yourself, for yourself.
