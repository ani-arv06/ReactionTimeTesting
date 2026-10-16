"""F1 starting-light reaction-time task (PsychoPy 2026.1.3, pyglet).

Frame-scheduled visual transitions; mouse event timestamps relative to the
lights-out flip callback. Hardware/display latency is not calibrated.
"""
from psychopy import visual, core, event, gui, logging
from pathlib import Path
import csv
import math
import random
import re

logging.console.setLevel(logging.WARNING)

info = {'Participant ID': ''}
dlg = gui.DlgFromDict(info, title='F1 Reaction Time Test')
if not dlg.OK:
    core.quit()
participant = info['Participant ID'].strip()
if not participant:
    raise ValueError('Participant ID cannot be empty')
safe_id = re.sub(r'[^A-Za-z0-9_-]', '_', participant)

TARGET_VALID = 10
MIN_DELAY = 1.0
MAX_DELAY = 5.0
MIN_RT = 0.130
MAX_RT = 1.500
INTER_TRIAL = 5.0

folder = Path.home() / 'Desktop' / 'ReactionTimeData'
folder.mkdir(parents=True, exist_ok=True)
filename = folder / f'F1_RT_{safe_id}.csv'

win = visual.Window(fullscr=True, color='black', units='pix', winType='pyglet')
mouse = event.Mouse(win=win, visible=False)
refresh = win.getActualFrameRate()
if refresh is None or not math.isfinite(refresh) or refresh <= 0:
    refresh = 60.0
    print('WARNING: refresh measurement unavailable; using 60 Hz estimate')
print(f'Frame rate used for scheduling: {refresh:.3f} Hz')
FRAMES_PER_SECOND = max(1, round(refresh))
win.refreshThreshold = (1.0 / refresh) + 0.004


# Fixed light size and positions
w, h = win.size

radius = 100
positions = [-500, -250, 0, 250, 500]

lights = [
    visual.Circle(
        win,
        radius=radius,
        pos=(x, 0),
        fillColor='dimgray',
        lineColor='white'
    )
    for x in positions
]

# Text stimulus used by show_text() for instructions and feedback.
# It must exist before show_text() is first called.
message = visual.TextStim(
    win,
    text='',
    color='white',
    height=35,
    wrapWidth=min(1100, win.size[0] - 80)
)


def escape_pressed():
    return 'escape' in event.getKeys(keyList=['escape'])


def draw_lights():
    for light in lights:
        light.draw()


def show_text(text):
    message.text = text
    message.draw()
    win.flip()


def wait_seconds(seconds):
    """Keep the event loop responsive during timed breaks."""
    clock = core.Clock()
    while clock.getTime() < seconds:
        if escape_pressed():
            return False
        core.wait(.01)
    return True


def button_down():
    return bool(mouse.getPressed()[0])


def run_trial(trial_number):
    """Returns (rt, status, delay_frames, dropped_frames)."""
    # Wait for release so a previous click cannot carry into the next trial.
    while button_down():
        if escape_pressed():
            return None
        core.wait(.002)

    # Fixation before the lights; the following pause is outside frame tracking.
    show_text('+')
    if not wait_seconds(1.0):
        return None

    # Warm-up flip absorbs intentional pause before tracking critical frames.
    win.flip()
    win.recordFrameIntervals = True
    win.frameIntervals = []
    win.nDroppedFrames = 0
    for light in lights:
        light.fillColor = 'dimgray'

    delay_frames = random.randint(round(MIN_DELAY * refresh),
                                  round(MAX_DELAY * refresh))
    # Each step lasts exactly the scheduled number of flips.
    for i in range(5):
        lights[i].fillColor = 'red'
        for _ in range(FRAMES_PER_SECOND):
            if escape_pressed():
                return None
            draw_lights()
            win.flip()
            if button_down():
                dropped = win.nDroppedFrames
                win.recordFrameIntervals = False
                return (None, 'FalseStart', delay_frames, dropped)

    for _ in range(delay_frames):
        if escape_pressed():
            return None
        draw_lights()
        win.flip()
        if button_down():
            dropped = win.nDroppedFrames
            win.recordFrameIntervals = False
            return (None, 'FalseStart', delay_frames, dropped)

    # Prevent a press held across the transition from counting as a response.
    if button_down():
        dropped = win.nDroppedFrames
        win.recordFrameIntervals = False
        return (None, 'FalseStart', delay_frames, dropped)

    # Blank backbuffer = all lights disappear together on the next flip.
    # Reset event timestamps as close to the flip as PsychoPy permits.
    win.callOnFlip(mouse.clickReset)
    win.flip()
    response_clock = core.Clock()  # timeout only; NOT used to calculate RT
    rt = None
    status = 'NoResponse'
    while response_clock.getTime() < MAX_RT + .05:
        if escape_pressed():
            return None
        buttons, times = mouse.getPressed(getTime=True)
        if buttons[0]:
            # Button timestamp is relative to mouse.clickReset on the flip.
            rt = float(times[0])
            if rt < MIN_RT:
                status = 'Anticipatory'
            elif rt > MAX_RT:
                status = 'TooSlow'
            else:
                status = 'Valid'
            break
        # Poll the Pyglet event queue without blocking on screen refresh.
        core.wait(0.001)

    dropped = win.nDroppedFrames
    win.recordFrameIntervals = False
    return (rt, status, delay_frames, dropped)


fields = ['ParticipantID', 'Trial', 'RandomDelay_seconds',
          'RandomDelay_frames', 'RT_seconds', 'Status', 'DroppedFrames',
          'FrameRate_Hz']
valid_count = 0
trial_number = 1
try:
    show_text('F1 START LIGHT REACTION TEST\n\n'
              'Wait until all five red lights go out.\n'
              'LEFT CLICK as fast as possible.\n\n'
              'Do not click before lights-out.\n'
              'The test ends after 7 valid responses.\n\n'
              'Press S to begin.')
    event.clearEvents()
    while not event.getKeys(keyList=['s']):
        if escape_pressed():
            core.quit()
        core.wait(.01)

    # Write each trial immediately, so ESC still preserves completed trials.
    with open(filename, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        f.flush()
        while valid_count < TARGET_VALID:
            if trial_number > 1:
                show_text('Next Trial Starting...')
                if not wait_seconds(INTER_TRIAL):
                    break
            outcome = run_trial(trial_number)
            if outcome is None:
                break
            rt, status, delay_frames, dropped = outcome
            writer.writerow({
                'ParticipantID': participant,
                'Trial': trial_number,
                'RandomDelay_seconds': round(delay_frames / refresh, 6),
                'RandomDelay_frames': delay_frames,
                'RT_seconds': '' if rt is None else round(rt, 6),
                'Status': status,
                'DroppedFrames': dropped,
                'FrameRate_Hz': round(refresh, 4)
            })
            f.flush()
            print(f'Trial {trial_number}: {status}, RT={rt}, dropped={dropped}')
            if status == 'Valid':
                valid_count += 1
            trial_number += 1
            if valid_count == TARGET_VALID:
                break
            if status == 'FalseStart':
                show_text('FALSE START\n\nPlease wait until the lights go out.')
            elif rt is None:
                show_text('No Response')
            else:
                show_text(f'{status}\n\n{rt * 1000:.0f} ms')
            if not wait_seconds(1.5):
                break

    show_text(('Thank You For Participating' if valid_count == TARGET_VALID
               else 'Session Ended') +
              f'\n\nData saved to:\n{filename}\n\nPress ESC to exit.')
    event.clearEvents()
    event.waitKeys(keyList=['escape'])
finally:
    win.close()
    core.quit()
