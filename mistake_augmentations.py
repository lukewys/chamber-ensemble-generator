from music21 import *
import pretty_midi as pm
import numpy as np
from scipy.stats import truncnorm
from utils.file_utils import get_config

rng = np.random.default_rng()
""" 
Usage:
add_pitch_bends(midi=midi, lambda_occur=2, mean_delta=0, stdev_delta=np.sqrt(1000), step_size=0.01)
add_screwups(midi=midi, lambda_occur=0.03, stdev_pitch_delta=1)
"""


def make_instrument_mono(instrument):
    """
    Make the instrument monophonic by adjusting the note durations.

    Args:
        instrument (Instrument): The instrument to make monophonic.

    Returns:
        None
    """
    all_notes = instrument.notes
    for i in range(len(all_notes)):
        if i != len(all_notes) - 1:
            if all_notes[i].end > all_notes[i + 1].start:
                all_notes[i].end = all_notes[i + 1].start
    instrument.notes = all_notes


# Not used for piano due to the piano having "keys" instead of "strings"
# TODO: check the usablity of this function
def add_pitch_bends(midi, lambda_occur, mean_delta, stdev_delta, step_size):
    for inst in midi.instruments:
        inst.pitch_bends = []
        # Flatten note times list
        single_notes = []
        last_time = 0.0
        for note in inst.notes:
            if note.start >= last_time:
                single_notes.append(note)
                last_time = note.end

        fixed_bend_points = []
        # Add fixed point pitch bends
        for note in single_notes:
            # Do 1 pitch bend at start of each note
            # Define the boundaries of the truncated normal distribution
            clip_a, clip_b = -8192, 8191

            # Calculate the parameters for the truncated normal distribution
            a, b = (clip_a - mean_delta) / (stdev_delta * stdev_delta), (
                clip_b - mean_delta
            ) / (stdev_delta * stdev_delta)

            # Generate a random number from the truncated normal distribution and scale it
            bend = int(truncnorm(a, b).rvs() * (stdev_delta * stdev_delta) + mean_delta)

            # The generated number is guaranteed to be within the range [-8192, 8191] due to the truncation
            fixed_bend_points.append(pm.PitchBend(bend, note.start))
            # Add more randomly
            occurrences = rng.poisson(lam=lambda_occur * (note.end - note.start))
            for i in range(occurrences):
                time = rng.uniform(low=note.start, high=note.end)
                bend = int(
                    truncnorm(a, b).rvs() * (stdev_delta * stdev_delta) + mean_delta
                )
                fixed_bend_points.append(pm.PitchBend(bend, time))

        # Sort by time from least to greatest
        fixed_bend_points.sort(key=(lambda x: x.time))

        # Linear interpolation
        inst.pitch_bends = fixed_bend_points.copy()
        for i in range(len(fixed_bend_points) - 1):
            left_pitch_bend = fixed_bend_points[i]
            right_pitch_bend = fixed_bend_points[i + 1]
            n_points_to_add = int(
                np.floor((right_pitch_bend.time - left_pitch_bend.time) / step_size)
            )
            for j in range(1, n_points_to_add + 1):
                time = left_pitch_bend.time + j * step_size
                bend = int(
                    left_pitch_bend.pitch
                    + (
                        (right_pitch_bend.pitch - left_pitch_bend.pitch)
                        * (j / (n_points_to_add + 1))
                    )
                )
                if bend > 8191:
                    bend = 8191
                elif bend < -8192:
                    bend = -8192
                inst.pitch_bends.append(pm.PitchBend(bend, time))


def get_thirty_second_note_duration(tempo, midi):
    """
    Calculate the duration of a sixteenth note given the tempo and MIDI resolution.
    """
    ticks_per_beat = midi.resolution
    beats_per_second = tempo / 60.0
    ticks_per_second = ticks_per_beat * beats_per_second
    thirty_second_duration_seconds = (
        1 / 8
    ) / beats_per_second  # Quarter note divided by 4
    return thirty_second_duration_seconds


def adjust_for_overlap(inst, idx, duration, start_time, shift_probability):
    if idx < len(inst.notes) - 1:
        next_note = inst.notes[idx + 1]
        if start_time + duration > next_note.start:
            if rng.random() < shift_probability:
                # Shift subsequent notes
                shift_amount = start_time + duration - next_note.start
                for n in range(idx + 1, len(inst.notes)):
                    inst.notes[n].start += shift_amount
                    inst.notes[n].end += shift_amount
            else:
                # Adjust current note to avoid overlap
                duration = next_note.start - start_time
    return duration


def add_screwups(
    midi,
    lambda_occur=2,
    stdev_pitch_delta=1,
    mean_duration=0,
    stdev_duration=0.02,
    shift_probability=0.5,
    allow_overlap=False,
    fixed_screwup_type=None,
    config=get_config(),
):
    """
    Add screwups to the MIDI file by introducing mistakes in the notes.

    Args:
        midi (pretty_midi.PrettyMIDI): The MIDI object to modify.
        lambda_occur (float): The rate parameter for the Poisson distribution
            determining the rate of screwup occurrences per note.
        stdev_pitch_delta (float): The standard deviation of the pitch delta
            used to introduce pitch mistakes.
        mean_duration (float): The mean duration used to introduce extra notes
            or timing inaccuracies.
        stdev_duration (float): The standard deviation of the duration used to
            introduce extra notes or timing inaccuracies.
        shift_probability (float): The probability of shifting subsequent notes
            to avoid overlap.
        allow_overlap (bool, optional): Whether to allow overlap between notes.
            Defaults to False.
        fixed_screwup_type (int, optional): The fixed screwup type to apply to
            all notes. If None, a random screwup type will be chosen for each note.
            Defaults to None.
        config (dict, optional): The configuration parameters for augmentation.
            Defaults to get_config().

    Returns:
        None
    """
    for inst in midi.instruments:
        inst.notes.sort(key=lambda x: x.start)

        occurrences = rng.poisson(lam=lambda_occur * inst.notes[-1].end)
        print(f"occurrences: {occurrences}")
        print(f"instrument: {inst.name}")
        for _ in range(occurrences):
            if len(inst.notes) == 0:
                break

            idx = rng.integers(0, len(inst.notes))
            note = inst.notes[idx]
            if note.end <= note.start:
                del inst.notes[idx]  # TODO: or screwup type = 0
                continue
            note_duration = note.end - note.start
            if fixed_screwup_type is not None:
                screwup_type = fixed_screwup_type
            else:
                screwup_type = rng.integers(
                    0, 3
                )  # Now includes 0, 1, 2, and 3 as screwup types

            if screwup_type == 0:  # Didn't play notes
                del inst.notes[idx]

            elif screwup_type == 1:  # Messed up pitches
                pitch_delta = 0
                while -1 < pitch_delta < 1:
                    pitch_delta = int(rng.normal(loc=0, scale=stdev_pitch_delta))
                note.pitch = np.clip(note.pitch + int(pitch_delta), 0, 127)

            elif screwup_type == 2:  # Add extra notes
                add_extra_note(
                    inst,
                    note,
                    idx,
                    mean_duration,
                    stdev_duration,
                    stdev_pitch_delta,
                    allow_overlap,
                    shift_probability,
                )

            elif screwup_type == 3:  # Timing inaccuracies
                add_timing_inaccuracies(
                    inst,
                    note,
                    idx,
                    mean_duration,
                    stdev_duration,
                    stdev_pitch_delta,
                    allow_overlap,
                    shift_probability,
                    config,
                )

        inst.notes.sort(key=lambda x: x.start)
        if allow_overlap is False:
            make_instrument_mono(inst)


def add_extra_note(
    inst,
    note,
    idx,
    mean_duration,
    stdev_duration,
    stdev_pitch_delta,
    allow_overlap,
    shift_probability,
):
    rng = np.random.default_rng()
    note_duration = note.end - note.start
    duration_var = rng.gamma(
        shape=mean_duration / (stdev_duration**2),
        scale=stdev_duration**2,
    )
    # randomize note duration by a gamma distribution
    duration = min(note_duration / duration_var, note_duration * duration_var)
    duration = max(0, duration)

    start_time = rng.uniform(low=note.start, high=note.end)
    pitch_delta = 0
    while -1 < pitch_delta < 1:
        pitch_delta = int(rng.normal(loc=0, scale=stdev_pitch_delta))
    new_pitch = np.clip(note.pitch + pitch_delta, 0, 127)

    # Debugging: Output generated values before adding the note
    print(f"Original note duration: {note_duration}")
    print(f"Randomized duration for extra note: {duration}")
    print(f"Chosen start time for extra note: {start_time}")
    print(f"Chosen pitch for extra note: {new_pitch}")
    if allow_overlap is False:
        duration = adjust_for_overlap(
            inst, idx, duration, start_time, shift_probability
        )

    # Debugging: Output final values before adding the note
    print(f"Final duration for extra note: {duration}")
    print(
        f"Final start and end times for extra note: {start_time}, {start_time + duration}"
    )

    # Add the new note
    extra_note = pm.Note(
        velocity=note.velocity,
        pitch=new_pitch,
        start=start_time,
        end=start_time + duration,
    )
    inst.notes.append(extra_note)

    # Debugging: Confirm addition and sorting
    print(f"Added extra note: {extra_note}")
    inst.notes.sort(key=lambda x: x.start)
    print(f"Notes sorted. Number of notes for instrument: {len(inst.notes)}")


def add_timing_inaccuracies(
    inst,
    note,
    idx,
    mean_duration,
    stdev_duration,
    stdev_pitch_delta,
    allow_overlap,
    shift_probability,
    config,
):
    rng = np.random.default_rng()
    note_duration = note.end - note.start
    duration_var = rng.gamma(
        shape=mean_duration / (stdev_duration**2),
        scale=stdev_duration**2,
    )
    current_tempo = midi.estimate_tempo()  # Simplification: assuming a constant tempo
    error_range = get_thirty_second_note_duration(
        current_tempo, midi
    )  # for timing, start time should be +- 1/32 of a beat for a decent player
    # randomize note duration by a gamma distribution
    note_duration = max(0, (note_duration * duration_var))

    # Generate a timing shift using a normal distribution
    timing_shift_seconds = rng.normal(
        loc=config["expressive_timing_mean_ms"] / 1000.0,
        scale=config["expressive_timing_std_ms"] / 1000.0,
    )

    # Apply the timing shift without labelling it an error if it's within the bounds of a 32nd note
    if abs(timing_shift_seconds) <= error_range:
        note.start += timing_shift_seconds

        note.end = note.start + note_duration
    else:
        # Handle timing error outside of acceptable bounds
        print(
            f"Timing error for note {note.pitch} at {note.start} with shift {timing_shift_seconds}s"
        )
        note.start += timing_shift_seconds
        note.end = note.start + note_duration
    if allow_overlap is False:
        # Adjust for potential overlap with adjacent notes
        if idx > 0:
            previous_note = inst.notes[idx - 1]
            if note.start < previous_note.end:
                previous_note.end = min(previous_note.end, note.start)

        if idx < len(inst.notes) - 1:
            next_note = inst.notes[idx + 1]
            if note.end > next_note.start:
                if rng.random() < shift_probability:
                    # Shift subsequent notes
                    shift_amount = note.end - next_note.start
                    for n in range(idx + 1, len(inst.notes)):
                        inst.notes[n].start += shift_amount
                        inst.notes[n].end += shift_amount
                else:
                    # Adjust current note to avoid overlap
                    note.end = min(note.end, next_note.start)
