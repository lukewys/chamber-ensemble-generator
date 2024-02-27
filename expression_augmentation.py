"""Random manipulate of note expression"""

import os
import numpy as np
import glob
import argparse
from midi_ddsp.utils.audio_io import save_wav
from midi_ddsp.utils.inference_utils import ensure_same_length
from midi_ddsp.utils.midi_synthesis_utils import batch_conditioning_df_to_audio
from midi_ddsp.midi_ddsp_synthesize import load_pretrained_model
from utils.metadata_utils import load_metadata
from utils.file_utils import get_config
from utils.file_utils import pickle_load, pickle_dump

# Load pre-trained model
synthesis_generator, expression_generator = load_pretrained_model()


def note_expression_edit(conditioning_df_all, config):
    """
    Randomly manipulates the note expression values in the conditioning dataframes.

    Args:
        conditioning_df_all (list): List of conditioning dataframes.
        config (Config): The configuration object.

    Returns:
        list: List of modified conditioning dataframes.
        bool: Indicates whether any modifications were made.
    """
    conditioning_df_all_new = []

    for conditioning_df in conditioning_df_all:
        # keep the note expression value of rest notes to be 0.
        pitch = conditioning_df["pitch"].to_numpy()
        pitch_mask = np.where(pitch != 0, 1, 0)

        # vibrato
        vibrato_ori = conditioning_df["vibrato"].to_numpy()
        vibrato_edited = (
            np.random.uniform(
                config.vibrato_range[0], config.vibrato_range[1], vibrato_ori.shape
            )
            * pitch_mask
        )
        conditioning_df["vibrato"] = vibrato_edited

        # volume
        volume_ori = conditioning_df["volume"].to_numpy()
        volume_edited = (
            np.random.uniform(
                config.volume_range[0], config.volume_range[1], volume_ori.shape
            )
            * pitch_mask
        )
        conditioning_df["volume"] = volume_edited

        # volume fluctuation
        volume_fluc_ori = conditioning_df["vol_fluc"].to_numpy()
        volume_fluc_edited = (
            np.random.uniform(
                config.volume_fluctuation_range[0],
                config.volume_fluctuation_range[1],
                volume_fluc_ori.shape,
            )
            * pitch_mask
        )
        conditioning_df["vol_fluc"] = volume_fluc_edited

        # volume peak position
        vol_peak_pos_ori = conditioning_df["vol_peak_pos"].to_numpy()
        vol_peak_pos_edited = (
            np.random.uniform(
                config.volume_peak_position_range[0],
                config.volume_peak_position_range[1],
                vol_peak_pos_ori.shape,
            )
            * pitch_mask
        )
        conditioning_df["vol_peak_pos"] = vol_peak_pos_edited

        # attack
        attack_ori = conditioning_df["attack"].to_numpy()
        attack_edited = (
            np.random.uniform(
                config.attack_level_range[0],
                config.attack_level_range[1],
                attack_ori.shape,
            )
            * pitch_mask
        )
        conditioning_df["attack"] = attack_edited

        conditioning_df_all_new.append(conditioning_df)

    edited = True

    return conditioning_df_all_new, edited


def expression_augmentation(data_dir, output_dir, config):
    """
    Perform expression augmentation on the given data directory.

    Args:
        data_dir (str): The path to the data directory.
        output_dir (str): The path to the output directory.
        config (Config): The configuration object.

    Returns:
        None
    """
    # if output_dir is provided, then save to the output_dir.
    if output_dir:
        output_dir = os.path.join(output_dir, os.path.basename(data_dir))
        os.makedirs(output_dir, exist_ok=True)

    # load metadata
    pickle_path = os.path.join(data_dir, "metadata.pickle")
    instrument, conditioning_df_all, synthesis_parameters, residual_metadata = (
        load_metadata(pickle_path)
    )
    instrument_id_all, instrument_name_all = instrument

    conditioning_df_all, edited = note_expression_edit(conditioning_df_all, config)

    if edited:
        midi_audio, midi_control_params, midi_synth_params = (
            batch_conditioning_df_to_audio(
                synthesis_generator,
                conditioning_df_all,
                instrument_id_all,
                display_progressbar=True,
            )
        )
        midi_synth_params = midi_synth_params[
            "inputs"
        ]  # discard rest of the values other than inputs

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
                config.sample_rate,
            )

        # save mix
        save_wav(
            midi_audio_mix, os.path.join(output_dir, f"mix.wav"), config.sample_rate
        )

        # make metadata with each item as dict
        metadata = {
            "instrument_id": {i: instrument_id_all[i].numpy()[0] for i in range(4)},
            "note_expression_control": {i: conditioning_df_all[i] for i in range(4)},
            "synthesis_parameters": {
                i: {k: v[i].numpy() for k, v in midi_synth_params.items()}
                for i in range(4)
            },
            "random_note_expression": edited,
        }
        metadata = {
            **metadata,
            **residual_metadata,
        }  # merge changed metadata from rest of metadata
    else:
        metadata = pickle_load(pickle_path)
        metadata["random_note_expression"] = edited

    pickle_dump(metadata, os.path.join(output_dir, "metadata.pickle"))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Expression augmentation")
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
    args = parser.parse_args()

    config = get_config()

    if args.synthesis_dir:
        synth_dir_list = [args.synthesis_dir]
    elif args.multi_synthesis_dir:
        synth_dir_list = glob.glob(f"{args.multi_synthesis_dir}/*/")
    else:
        raise ValueError(
            "Either synthesis_dir or multi_synthesis_dir should be specified."
        )

    for synth_dir in synth_dir_list:
        expression_augmentation(synth_dir, args.output_dir, config)
