# Visuomotor Response Time (VMRT) Task (F1 Starting Lights)

A PsychoPy visuomotor response time (VMRT) task modeled on a Formula 1 starting-light sequence.
Participants watch five lights turn red one at a time, wait for all of them to go
out, and left-click as fast as possible.

This repository contains the task script and the system specifications used to
reproduce the visuomotor response time (VMRT) assessment done.

## Files

| File | Description |
|------|-------------|
| `ReactionTime_Final.py` | The task (PsychoPy 2026.1.3, pyglet window) |
| `SYSTEM_REQUIREMENTS.txt` | Hardware, display, OS, and mouse specs of the reference setup |
| `requirements.txt` | Python dependency (`psychopy==2026.1.3`) |

## Setup

```bash
python -m venv .venv
.venv\Scripts\activate          # Windows (macOS/Linux: source .venv/bin/activate)
pip install -r requirements.txt
```

Use a Python version supported by PsychoPy 2026.1.3. Alternatively, install
PsychoPy's standalone distribution and run the script from the PsychoPy Coder.

## Running the task

```bash
python ReactionTime_Final.py
```

1. Enter a **Participant ID** in the dialog.
2. Read the instructions and press **S** to begin.
3. Press **ESC** at any time to stop. Completed trials are already saved.

## Task procedure

Each trial:

1. A fixation cross (`+`) is shown for 1 s.
2. Five lights turn red one after another, one per second (frame-scheduled).
3. All lights stay red for a random delay of **1.0 to 5.0 s**.
4. All lights go out simultaneously (the go signal).
5. The participant left-clicks as fast as possible.

Trials are separated by a 5 s inter-trial interval. The session ends after
**7 valid responses**.

### Response classification

| Status | Meaning |
|--------|---------|
| `Valid` | RT between 130 ms and 1500 ms |
| `Anticipatory` | RT below 130 ms |
| `TooSlow` | RT above 1500 ms |
| `FalseStart` | Mouse button down before lights-out |
| `NoResponse` | No click within the response window |

Only `Valid` trials count toward the 7 required.

## Output

One CSV per participant is saved to:

```
~/Desktop/ReactionTimeData/F1_RT_<ParticipantID>.csv
```

Each trial is written immediately, so an ESC exit preserves completed trials.

| Column | Description |
|--------|-------------|
| `ParticipantID` | ID entered at start |
| `Trial` | Trial number (includes invalid trials) |
| `RandomDelay_seconds` | Delay between last light and lights-out |
| `RandomDelay_frames` | Same delay in frames |
| `RT_seconds` | Response time in seconds (blank for false starts / no response) |
| `Status` | Classification (see above) |
| `DroppedFrames` | Frames dropped during the trial |
| `FrameRate_Hz` | Measured display refresh rate |

## Timing notes

- Visual transitions are scheduled by frame count, using the refresh rate
  measured at startup.
- RT is taken from mouse event timestamps relative to the lights-out flip
  (`win.callOnFlip(mouse.clickReset)`).
- Absolute RTs include display, mouse, and OS latency, so use the same setup across participants and
  see `SYSTEM_REQUIREMENTS.txt` for the reference configuration.

## Reference setup

HP Laptop 14-dq4xxx, Intel Core i5-1155G7, 12 GB RAM, Intel Iris Xe graphics,
1920x1080 60 Hz display, Windows 11 Home 25H2, Razer DeathAdder Essential mouse
(1000 Hz polling). Full details are in `SYSTEM_REQUIREMENTS.txt`.


