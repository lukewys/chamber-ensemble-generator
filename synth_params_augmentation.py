"""Manipulate synthesis parameters

This module provides functions for manipulating synthesis parameters used in the chamber ensemble generator. It includes functions for expanding intonation augmentation coefficients, performing intonation augmentation, and synthesizing audio using DDSP.

Functions:
- expand_intonation_aug_coefficient: Expand note-wise intonation augmentation coefficient to frame-wise.
- intonation_augmentation: Perform random amount of pitch correction.
- synth_params_augmentation: Perform synthesis parameters augmentation.

Usage:
1. Import the module:
    from synth_params_augmentation import expand_intonation_aug_coefficient, intonation_augmentation, synth_params_augmentation

2. Call the functions as needed:
    - expand_intonation_aug_coefficient(coefficient, conditioning_df)
    - intonation_augmentation(synthesis_parameters, conditioning_df_all, config)
    - synth_params_augmentation(data_dir, output_dir, config)
"""

"""Manipulate synthesis parameters"""

import glob
import argparse
import ast
from tqdm import tqdm
import os
import numpy as np
import tensorflow as tf
import ddsp.training
from ddsp.core import midi_to_hz

from utils.metadata_utils import load_metadata
from utils.file_utils import get_config
from midi_ddsp.utils.audio_io import save_wav
from midi_ddsp.utils.inference_utils import ensure_same_length
from midi_ddsp.modules.interpretable_conditioning import get_pitch_deviation
from midi_ddsp.utils.inference_utils import conditioning_df_to_midi_features, to_length
from midi_ddsp.utils.inference_utils import get_process_group
from midi_ddsp.midi_ddsp_synthesize import load_pretrained_model
from utils.file_utils import pickle_load, pickle_dump

# Load pre-trained model
synthesis_generator, expression_generator = load_pretrained_model()


def expand_intonation_aug_coefficient(coefficient, conditioning_df):
    """
    Expand note-wise intonation augmentation coefficient to frame-wise.

    Parameters:
    coefficient (numpy.ndarray): Note-wise intonation augmentation coefficient.
    conditioning_df (pandas.DataFrame): Dataframe containing conditioning information.

    Returns:
    numpy.ndarray: Frame-wise intonation augmentation coefficient.
    """
    total_length = conditioning_df.tail(1)["offset"].values[0]
    coefficient_frame_wise = np.zeros((1, total_length, 1), dtype=np.float32)
    for i, note in conditioning_df.iterrows():
        on = int(note["onset"])
        off = int(note["offset"])
        coefficient_frame_wise[:, on : off + 1, :] = coefficient[i]
    return coefficient_frame_wise


def intonation_augmentation(
    synthesis_parameters, conditioning_df_all, config, strict_pitch_correction=False
):
    """Random amount of pitch correction"""

    f0_new_all = []
    correction_amount_all = {}
    max_length = synthesis_parameters["f0_hz"][0].shape[0]
    for i, conditioning_df in enumerate(conditioning_df_all):
        f0_ori = synthesis_parameters["f0_hz"][i][tf.newaxis, ...]
        midi_features = conditioning_df_to_midi_features(conditioning_df)
        q_pitch, q_vel, f0_loss_weights, onsets, offsets = midi_features

        # Different parts have different midi length, but during synthesis,
        # all f0s are padded to the maximum length.
        # So here we need to take the f0's original length for each part.
        f0_ori = f0_ori[:, : q_pitch.shape[1], :]
        f0_midi = midi_to_hz(q_pitch, midi_zero_silence=True)

        # Get pitch deviation in Hz scale
        pitch_deviation = f0_ori - f0_midi

        # Get the note mask and calculate the average pitch deviation across notex
        note_mask = ddsp.training.nn.get_note_mask_from_onset(q_pitch, onsets)
        pv_mean = ddsp.training.nn.pool_over_notes(
            pitch_deviation, note_mask, return_std=False
        )

        # Get the frame-wise pitch correction amount (\alpha in eq.1 of the paper)
        num_notes = len(conditioning_df.index)
        if strict_pitch_correction:
            correction_amount_note_wise = np.full(
                shape=num_notes,
                fill_value=config["max_pitch_correction"],
            )

        else:
            correction_amount_note_wise = np.random.uniform(
                config["min_pitch_correction"],
                config["max_pitch_correction"],
                size=num_notes,
            )
        correction_amount = expand_intonation_aug_coefficient(
            correction_amount_note_wise, conditioning_df
        )
        correction_amount = to_length(
            correction_amount, dst_length=f0_ori.shape[1], axis=1
        )

        f0_corrected = f0_ori - correction_amount * pv_mean
        # we do not apply pitch correction on silence notes.
        f0_corrected = tf.where(q_pitch != 0, f0_corrected, f0_ori)
        f0_corrected = to_length(
            f0_corrected, dst_length=max_length, axis=1
        )  # pad f0 to max_length
        f0_new_all.append(f0_corrected)
        correction_amount_all[i] = correction_amount_note_wise.tolist()

    synthesis_parameters["f0_hz"] = tf.concat(f0_new_all, axis=0)
    return synthesis_parameters, correction_amount_all


def synth_params_augmentation(
    data_dir, output_dir, config, strict_pitch_correction=False
):
    """
    Perform augmentation on synthesis parameters and generate audio stems.

    Args:
        data_dir (str): The directory path of the input data.
        output_dir (str): The directory path to save the augmented data. If None, the augmented data will be saved in the same directory as the input data.
        config (dict): A dictionary containing configuration parameters.

    Returns:
        None
    """
    # if output_dir is provided, then save to the output_dir.
    if output_dir:
        output_dir = os.path.join(output_dir, os.path.basename(data_dir))
        os.makedirs(output_dir, exist_ok=True)
    else:  # else, change in place
        output_dir = data_dir

    # load metadata
    pickle_path = os.path.join(data_dir, "metadata.pickle")
    instrument, conditioning_df_all, synthesis_parameters, residual_metadata = (
        load_metadata(pickle_path)
    )
    instrument_id_all, instrument_name_all = instrument
    instrument_id = tf.concat(instrument_id_all, 0)

    synthesis_parameters, correction_amount_all = intonation_augmentation(
        synthesis_parameters, conditioning_df_all, config, strict_pitch_correction=False
    )

    # Re synthesize the audio using DDSP
    processor_group = get_process_group(
        synthesis_parameters["amplitudes"].shape[1], use_angular_cumsum=True
    )
    midi_audio = processor_group(synthesis_parameters, verbose=False)
    midi_audio = synthesis_generator.reverb_module(
        midi_audio, reverb_number=instrument_id, training=False
    )

    midi_audio_mix = np.sum(
        np.stack(
            ensure_same_length(
                [
                    midi_audio[i].numpy().astype(np.float64)
                    for i in range(midi_audio.shape[0])
                ],
                axis=0,
            ),
            axis=-1,
        ),
        axis=-1,
    )

    # save stem
    for part_number, instrument_name in enumerate(instrument_name_all):
        audio = midi_audio[part_number].numpy().astype(np.float64)
        save_wav(
            audio,
            os.path.join(output_dir, f"{part_number}_{instrument_name}.wav"),
            config["sample_rate"],
        )

    # save mix
    save_wav(
        midi_audio_mix, os.path.join(output_dir, f"mix.wav"), config["sample_rate"]
    )

    # make metadata with each item as dict
    metadata = {
        "instrument_id": {i: instrument_id_all[i].numpy()[0] for i in range(4)},
        "note_expression_control": {i: conditioning_df_all[i] for i in range(4)},
        "synthesis_parameters": {
            i: {k: v[i].numpy() for k, v in synthesis_parameters.items()}
            for i in range(4)
        },
        "pitch_correction_amount": correction_amount_all,
    }
    metadata = {
        **metadata,
        **residual_metadata,
    }  # merge changed metadata from rest of metadata

    pickle_dump(metadata, os.path.join(output_dir, "metadata.pickle"))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Synthesis Parameters augmentation")
    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        "--synthesis_dir",
        type=str,
        default=None,
        metavar="N",
        help="the directory generated by MIDI-DDSP synthesis.",
    )
    group.add_argument(
        "--multi_synthesis_dir",
        type=str,
        default=None,
        metavar="N",
        help="the directory containing multiple folders generated by MIDI-DDSP synthesis.",
    )
    parser.add_argument(
        "--output_dir",
        type=str,
        default=None,
        metavar="N",
        help="the directory for output.",
    )
    parser.add_argument(
        "--strict_pitch_correction",
        type=ast.literal_eval,
        default=False,
        help="whether to perform strict pitch correction.",
    )
    args = parser.parse_args()

    config = get_config()

    if args.synthesis_dir:
        synth_dir_list = [args.synthesis_dir]
    elif args.multi_synthesis_dir:
        synth_dir_list = glob.glob(f"{args.multi_synthesis_dir}/*/")
    else:
        raise ValueError("Please specify either synthesis_dir or multi_synthesis_dir.")

    for synth_dir in tqdm(synth_dir_list):
        synth_params_augmentation(
            synth_dir, args.output_dir, config, strict_pitch_correction=False
        )
