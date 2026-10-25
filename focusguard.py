"""FocusGuard: an on-device AI study/work companion.

Watches the webcam with YOLOv8n and classifies every moment as
FOCUSED, PHONE or AWAY. Nothing leaves the machine and no frame is saved;
only the state timeline is written to logs/ when you quit.

Usage:
    python focusguard.py                # default webcam
    python focusguard.py --camera 1     # another camera
    python focusguard.py --alert 20     # remind after 20 s of distraction

Keys: q = quit and write the report, s = save a screenshot.
"""

import argparse
import csv
import os
import sys
import time
from datetime import datetime

import cv2
from ultralytics import YOLO

PERSON, PHONE = 0, 67  # COCO class ids

FOCUSED, ON_PHONE, AWAY = "FOCUSED", "PHONE", "AWAY"
COLORS_BGR = {FOCUSED: (91, 138, 31), ON_PHONE: (46, 122, 224), AWAY: (158, 148, 138)}
COLORS_HEX = {FOCUSED: "#1F8A5B", ON_PHONE: "#E07A2E", AWAY: "#8A949E"}


class StateMachine:
    """Debounced state logic, so one missed frame doesn't flip the state."""

    def __init__(self, phone_after=2.0, away_after=3.0, back_after=1.0):
        self.phone_after = phone_after
        self.away_after = away_after
        self.back_after = back_after
        self.state = FOCUSED
        self.since = None          # when the current state started
        self.phone_seen = None     # when the phone was first seen continuously
        self.person_lost = None    # when the person was last lost
        self.clear_since = None    # when "person, no phone" started
        self.changes = []          # (timestamp, state)

    def update(self, now, person, phone):
        if self.since is None:
            self.since = now
            self.changes.append((now, self.state))

        self.phone_seen = (self.phone_seen or now) if phone else None
        self.person_lost = None if person else (self.person_lost or now)
        self.clear_since = (self.clear_since or now) if person and not phone else None

        target = self.state
        if self.person_lost and now - self.person_lost >= self.away_after:
            target = AWAY
        elif self.phone_seen and now - self.phone_seen >= self.phone_after:
            target = ON_PHONE
        elif self.clear_since and now - self.clear_since >= self.back_after:
            target = FOCUSED

        if target != self.state:
            self.state = target
            self.since = now
            self.changes.append((now, target))
        return self.state


def beep():
    if sys.platform.startswith("win"):
        import winsound
        winsound.Beep(880, 300)
    else:
        print("\a", end="", flush=True)


def draw_overlay(frame, state, elapsed, totals, alert):
    h, w = frame.shape[:2]
    cv2.rectangle(frame, (0, 0), (w, 60), COLORS_BGR[state], -1)
    cv2.putText(frame, f"{state}  {int(elapsed)}s", (16, 42),
                cv2.FONT_HERSHEY_SIMPLEX, 1.2, (255, 255, 255), 3)
    total = sum(totals.values()) or 1
    focus_pct = 100 * totals[FOCUSED] / total
    cv2.putText(frame, f"Focus {focus_pct:.0f}%", (w - 220, 42),
                cv2.FONT_HERSHEY_SIMPLEX, 1.0, (255, 255, 255), 2)
    if alert:
        msg = "Put the phone down!" if state == ON_PHONE else "Time to get back to work!"
        cv2.rectangle(frame, (0, h - 70), (w, h), (40, 40, 200), -1)
        cv2.putText(frame, msg, (16, h - 22), cv2.FONT_HERSHEY_SIMPLEX, 1.1, (255, 255, 255), 3)


def totals_from(changes, end):
    totals = {FOCUSED: 0.0, ON_PHONE: 0.0, AWAY: 0.0}
    for (t, s), nxt in zip(changes, changes[1:] + [(end, None)]):
        totals[s] += nxt[0] - t
    return totals


def write_report(changes, start, end, out_dir="logs"):
    os.makedirs(out_dir, exist_ok=True)
    stamp = datetime.fromtimestamp(start).strftime("%Y%m%d_%H%M%S")
    base = os.path.join(out_dir, f"session_{stamp}")
    totals = totals_from(changes, end)
    total = sum(totals.values()) or 1
    pickups = sum(1 for _, s in changes if s == ON_PHONE)

    with open(base + ".csv", "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["start", "end", "state", "seconds"])
        for (t, s), nxt in zip(changes, changes[1:] + [(end, None)]):
            writer.writerow([datetime.fromtimestamp(t).isoformat(timespec="seconds"),
                             datetime.fromtimestamp(nxt[0]).isoformat(timespec="seconds"),
                             s, round(nxt[0] - t, 1)])

    lines = [f"FocusGuard session {stamp}",
             f"Duration: {total / 60:.1f} min"]
    for s in (FOCUSED, ON_PHONE, AWAY):
        lines.append(f"{s:8s} {totals[s] / 60:6.1f} min  ({100 * totals[s] / total:4.1f}%)")
    lines.append(f"Phone pick-ups: {pickups}")
    summary = "\n".join(lines)
    with open(base + "_summary.txt", "w") as f:
        f.write(summary + "\n")

    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots(figsize=(12, 2.2))
    for (t, s), nxt in zip(changes, changes[1:] + [(end, None)]):
        ax.barh(0, (nxt[0] - t) / 60, left=(t - start) / 60, color=COLORS_HEX[s], height=0.6)
    ax.set_yticks([])
    ax.set_xlabel("Minutes")
    ax.set_title(f"Focus {100 * totals[FOCUSED] / total:.0f}%  |  "
                 f"Phone {100 * totals[ON_PHONE] / total:.0f}%  |  "
                 f"Away {100 * totals[AWAY] / total:.0f}%  |  {pickups} pick-ups", loc="left")
    handles = [plt.Rectangle((0, 0), 1, 1, color=COLORS_HEX[s]) for s in (FOCUSED, ON_PHONE, AWAY)]
    ax.legend(handles, ["Focused", "Phone", "Away"], loc="lower right",
              bbox_to_anchor=(1.0, 1.15), ncol=3, frameon=False)
    ax.set_ylim(-0.5, 0.5)
    for side in ("top", "right", "left"):
        ax.spines[side].set_visible(False)
    fig.tight_layout()
    fig.savefig(base + ".png", dpi=150)
    plt.close(fig)

    print("\n" + summary)
    print(f"\nSaved {base}.csv, {base}_summary.txt and {base}.png")


def main():
    parser = argparse.ArgumentParser(description="FocusGuard: on-device focus companion")
    parser.add_argument("--camera", type=int, default=0)
    parser.add_argument("--model", default="yolov8n.pt")
    parser.add_argument("--conf", type=float, default=0.4, help="detection confidence")
    parser.add_argument("--phone", type=float, default=2.0, help="seconds of phone before PHONE")
    parser.add_argument("--away", type=float, default=3.0, help="seconds of absence before AWAY")
    parser.add_argument("--alert", type=float, default=10.0, help="seconds distracted before reminder")
    args = parser.parse_args()

    model = YOLO(args.model)
    cap = cv2.VideoCapture(args.camera)
    if not cap.isOpened():
        sys.exit(f"Cannot open camera {args.camera}")

    sm = StateMachine(phone_after=args.phone, away_after=args.away)
    start = time.time()
    beeped_for = None
    print("FocusGuard running. Press q to quit, s for a screenshot.")

    while True:
        ok, frame = cap.read()
        if not ok:
            break
        now = time.time()
        result = model(frame, classes=[PERSON, PHONE], conf=args.conf, verbose=False)[0]
        ids = result.boxes.cls.int().tolist()
        state = sm.update(now, PERSON in ids, PHONE in ids)

        frame = result.plot()
        elapsed = now - sm.since
        alert = state != FOCUSED and elapsed >= args.alert
        if alert and beeped_for != sm.since:
            beep()
            beeped_for = sm.since
        draw_overlay(frame, state, elapsed, totals_from(sm.changes, now), alert)
        cv2.imshow("FocusGuard", frame)

        key = cv2.waitKey(1) & 0xFF
        if key == ord("q"):
            break
        if key == ord("s"):
            os.makedirs("logs", exist_ok=True)
            path = os.path.join("logs", f"screenshot_{state}_{int(now)}.png")
            cv2.imwrite(path, frame)
            print("Saved", path)

    cap.release()
    cv2.destroyAllWindows()
    if sm.changes:
        write_report(sm.changes, start, time.time())


if __name__ == "__main__":
    main()
