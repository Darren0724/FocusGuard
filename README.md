# FocusGuard

**A webcam app that tells you when you're distracted, and shows you where your study time went. Everything runs on your own computer.**

FocusGuard watches you through your laptop camera and puts every moment into one of three states:

| State | What it means |
|---|---|
| 🟢 **FOCUSED** | You're at your desk and there's no phone in sight |
| 🟠 **PHONE** | You've had your phone out for more than 2 seconds |
| ⚪ **AWAY** | You've left your desk for more than 3 seconds |

If you stay distracted for more than 10 seconds, it shows a reminder and beeps. When you quit, it gives you a report of the whole session.

> Project for the ASUS UGen AI League 2026 (Theme: Everyday AI · Track: Lightning).

---

## Quick start

You need **Python 3.9 or newer** and a **webcam**.

```bash
git clone https://github.com/Darren0724/CN.git
cd CN
pip install -r requirements.txt
python focusguard.py
```

The first run downloads a small AI model (about 6 MB). After that, a window opens with your camera feed.

> **Windows users:** run this in **PowerShell or Command Prompt**, not WSL. WSL can't see your webcam, so you'll get `Cannot open camera 0`.

<details>
<summary>Using uv instead of pip</summary>

```bash
uv venv
uv pip install -r requirements.txt
uv run python focusguard.py
```
</details>

## Using it

- The **coloured bar at the top** shows your current state and how long you've been in it.
- The **number at the top right** is your focus percentage so far.
- Press **`s`** to save a screenshot.
- Press **`q`** to quit and get your report.

## Your session report

After you press `q`, three files appear in the `logs/` folder:

| File | What's in it |
|---|---|
| `session_<time>.png` | A colour timeline of your session (green = focused, orange = phone, grey = away) |
| `session_<time>_summary.txt` | Minutes and percentage in each state, plus how many times you picked up your phone |
| `session_<time>.csv` | Every state change with timestamps, for your own analysis |

## Settings

All settings are optional. For example, `python focusguard.py --alert 30` waits 30 seconds before reminding you.

| Option | Default | What it does |
|---|---|---|
| `--alert` | `10` | Seconds of distraction before the reminder |
| `--phone` | `2` | Seconds a phone must be visible before it counts as PHONE |
| `--away` | `3` | Seconds you must be gone before it counts as AWAY |
| `--camera` | `0` | Which camera to use (try `1` if the wrong one opens) |
| `--conf` | `0.4` | How sure the AI must be before it counts a detection (0 to 1) |

## Troubleshooting

| Problem | Fix |
|---|---|
| `Cannot open camera 0` | On Windows, make sure you're not in WSL. Close other apps using the camera (Zoom, Teams). Try `--camera 1`. |
| Black window or wrong camera | Try `--camera 1` or `--camera 2` |
| Phone isn't detected | Hold it so the camera can see the phone's outline clearly, or lower the threshold: `--conf 0.3` |
| No beep | The beep only works reliably on Windows; the on-screen reminder always works |

## How it works

```
Webcam  →  AI detector  →  State logic  →  Reminder + report
           (finds people     (decides which
            and phones)       of the 3 states)
```

1. **AI detector:** each camera frame goes through [YOLOv8n](https://docs.ultralytics.com/models/yolov8/), a small, fast object detector. It's used as-is (no extra training) and only looks for two things: a **person** and a **cell phone**.
2. **State logic:** the state only changes after a short delay (2–3 seconds). This stops it from flickering if the detector misses you for a single frame.
3. **Privacy:** frames are processed in memory and thrown away. No video is saved or uploaded; only the timeline of states goes into `logs/`.

## Files in this repo

| File | Purpose |
|---|---|
| `focusguard.py` | The whole app |
| `requirements.txt` | Python packages to install |

## What's next (Stage II)

1. **Run on the ASUS UGen300 AI accelerator** so the laptop CPU stays free and power use stays low.
2. **Posture warnings** when you slouch.
3. **A daily summary written by a small AI model** that runs on your own computer.
4. **Study-room mode** for several people at once, still fully on-device.

---

## 中文說明

**FocusGuard 是一個用筆電鏡頭判斷你有沒有專心的小程式，所有運算都在你自己的電腦上，不會上傳任何影像。**

**三種狀態：** 🟢 專注（在座位上、沒拿手機）、🟠 滑手機（手機出現超過 2 秒）、⚪ 離座（離開超過 3 秒）。分心超過 10 秒會跳提醒並嗶一聲。

**怎麼跑：**

```bash
pip install -r requirements.txt
python focusguard.py
```

- Windows 請在 **PowerShell** 執行，不要用 WSL（WSL 讀不到鏡頭）。
- 按 `s` 截圖，按 `q` 結束。結束後 `logs/` 資料夾會有時間軸圖、統計摘要和 CSV。
- 開錯鏡頭或黑畫面，試試 `python focusguard.py --camera 1`。
