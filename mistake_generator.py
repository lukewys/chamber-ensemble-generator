import sys
import mistake_augmentations
from mistake_augmentations import add_screwups, add_pitch_bends

sys.path.append("/home/chou150/depot/code/chamber-ensemble-generator/")
import pretty_midi
import numpy as np


def generate_mistakes(midi_path):
    midi = pretty_midi.PrettyMIDI(midi_path)
    add_screwups(
        midi=midi,
        lambda_occur=0.5,  # 0.03
        stdev_pitch_delta=1,
        mean_duration=1,
        stdev_duration=0.02,
        shift_probability=0.5,
        allow_overlap=True,
    )
    add_pitch_bends(
        midi=midi,
        lambda_occur=2,
        mean_delta=0,
        stdev_delta=np.sqrt(1000),
        step_size=0.01,
    )
    # Remove the '.mid' extension and append '_modified.midi'
    base_path = os.path.splitext(midi_path)[0]  # Removes the extension
    modified_midi_path = (
        base_path + "_modified.mid"
    )  # Adds the new part of the filename

    print(modified_midi_path)
    midi.write(modified_midi_path)


generate_mistakes(
    "/home/chou150/depot/code/chamber-ensemble-generator/data/Abide_by_Me.midi"
)
