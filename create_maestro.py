import sys
import glob
from tqdm import tqdm
import multiprocessing
import midi_augmentation
import midi_ddsp_synthesize
import audio_mixing
import data_postprocess.postprocess_cocochorales as postprocess_cocochorales
from midi_ddsp.midi_ddsp_synthesize import synthesize_midi, load_pretrained_model
from utils.file_utils import get_config

import multiprocessing
from functools import partial


def parse_synthesis_midi_files(
    midi_dir=None,
    midi_path=None,
    pitch_offset=0,
    speed_rate=1.0,
    sf2_path=None,
    output_dir=None,
    use_fluidsynth=False,
    synthesis_generator_weight_path=None,
    expression_generator_weight_path=None,
    skip_existing_files=False,
    save_metadata=False,
):
    """
    Synthesize MIDI files using MIDI-DDSP with specified parameters.

    :param midi_dir: Directory containing MIDI files.
    :param midi_path: Path to a specific MIDI file.
    :param pitch_offset: Pitch offset to transpose in semitone.
    :param speed_rate: The speed to synthesize the MIDI file(s).
    :param sf2_path: Path to a sf2 soundfont file.
    :param output_dir: Directory for output audio.
    :param use_fluidsynth: Use FluidSynth for synthesizing midi instruments not contained in MIDI-DDSP.
    :param synthesis_generator_weight_path: Path to the Synthesis Generator weights.
    :param expression_generator_weight_path: Path to the expression generator weights.
    :param skip_existing_files: Skip synthesizing MIDI files if they already exist in the output folder.
    :param save_metadata: Save metadata including instrument_id, note expression controls, and synthesis parameters.
    """

    if output_dir is None:
        print("Output directory not specified. Output to current directory.")
        output_dir = "./"
    else:
        output_dir = output_dir

    if midi_dir and midi_path:
        print("Both midi_dir and midi_path are provided. Will use midi_dir.")
    elif not midi_dir and not midi_path:
        raise ValueError(
            "None of midi_dir or midi_path is provided. Please provide at least one."
        )
    return (
        midi_dir,
        midi_path,
        pitch_offset,
        speed_rate,
        sf2_path,
        output_dir,
        use_fluidsynth,
        synthesis_generator_weight_path,
        expression_generator_weight_path,
        skip_existing_files,
        save_metadata,
    )


def process_midi_file_wrapper(
    midi_file,
    synthesis_generator_weight_path,
    expression_generator_weight_path,
    pitch_offset,
    speed_rate,
    output_dir,
    sf2_path,
    use_fluidsynth,
    skip_existing_files,
    save_metadata,
):
    try:
        synthesis_generator, expression_generator = load_pretrained_model(
            synthesis_generator_path=synthesis_generator_weight_path,
            expression_generator_path=expression_generator_weight_path,
        )
        synthesize_midi(
            synthesis_generator,
            expression_generator,
            midi_file,
            pitch_offset=pitch_offset,
            speed_rate=speed_rate,
            output_dir=output_dir,
            sf2_path=sf2_path,
            use_fluidsynth=use_fluidsynth,
            display_progressbar=False,
            skip_existing_files=skip_existing_files,
            save_metadata=save_metadata,
        )
    except Exception as e:
        print(f"Error processing {midi_file}: {e}")


if __name__ == "__main__":
    sys.path.append("/home/chou150/depot/code/chamber-ensemble-generator/")

    config = get_config()

    # MIDI Augmentation - This step is preparing the MIDI files for synthesis
    midi_augmentation.augment_midi_files(
        midi_dir="/home/chou150/depot/datasets/cocochorales_full/org_chunked_midi/brass/0",
        output_dir="/home/chou150/depot/datasets/cocochorals_exp/cocochorales_midi",
        num_tracks_each_ensemble=60000,
    )

    ensemble_names = ["string", "brass", "woodwind", "random"]

    # for ensemble_name in ensemble_names:
    #     (
    #         midi_dir,
    #         midi_path,
    #         pitch_offset,
    #         speed_rate,
    #         sf2_path,
    #         output_dir,
    #         use_fluidsynth,
    #         synthesis_generator_weight_path,
    #         expression_generator_weight_path,
    #         skip_existing_files,
    #         save_metadata,
    #     ) = parse_synthesis_midi_files(
    #         midi_dir=f"/home/chou150/depot/datasets/cocochorals_exp/cocochorales_midi/{ensemble_name}",
    #         output_dir="/home/chou150/depot/datasets/cocochorals_exp/synthesized_midi",
    #         skip_existing_files=True,
    #         save_metadata=True,
    #     )

    #     process_midi_file_with_context = partial(
    #         process_midi_file_wrapper,
    #         synthesis_generator_weight_path=synthesis_generator_weight_path,
    #         expression_generator_weight_path=expression_generator_weight_path,
    #         pitch_offset=pitch_offset,
    #         speed_rate=speed_rate,
    #         output_dir=output_dir,
    #         sf2_path=sf2_path,
    #         use_fluidsynth=use_fluidsynth,
    #         skip_existing_files=skip_existing_files,
    #         save_metadata=save_metadata,
    #     )

    #     # if midi_dir:
    #     #     midi_file_list = glob.glob(midi_dir + "/*.mid")
    #     #     if len(midi_file_list) == 0:
    #     #         raise FileNotFoundError("No MIDI files found in the directory.")

    #     #     for midi_file in tqdm(midi_file_list, desc="Generating files: "):
    #     #         process_midi_file(midi_file)

    #     if midi_dir:
    #         midi_file_list = glob.glob(midi_dir + "/*.mid")
    #         if len(midi_file_list) == 0:
    #             raise FileNotFoundError("No MIDI files found in the directory.")

    #         num_cores = multiprocessing.cpu_count()
    #         num_processes = num_cores // 2
    #         print(f"Using {num_processes} processes for parallel processing")
    #         with multiprocessing.Pool(processes=num_processes) as pool:
    #             list(
    #                 tqdm(
    #                     pool.imap_unordered(
    #                         process_midi_file_with_context, midi_file_list
    #                     ),
    #                     total=len(midi_file_list),
    #                     desc="Generating files: ",
    #                 )
    #             )

    #     elif midi_path:
    #         synthesize_midi(
    #             synthesis_generator,
    #             expression_generator,
    #             midi_path,
    #             pitch_offset=pitch_offset,
    #             speed_rate=speed_rate,
    #             output_dir=output_dir,
    #             sf2_path=sf2_path,
    #             use_fluidsynth=use_fluidsynth,
    #             display_progressbar=True,
    #             skip_existing_files=skip_existing_files,
    #             save_metadata=save_metadata,
    #         )
    # For ensemble audio mixing, not necessary for now
    # # Audio Mixing, might need parallization to speed up slightly
    # audio_mixing.audio_normalization_main(
    #     multi_synthesis_dir="/home/chou150/depot/datasets/cocochorals_exp/synthesized_midi"
    # )

    # Post Processing - Done after all parallel tasks complete, pretty fast
    postprocess_cocochorales.postprocess_dataset(
        midi_dir="/home/chou150/depot/datasets/cocochorals_exp/cocochorales_midi",
        synthesis_dir="/home/chou150/depot/datasets/cocochorals_exp/synthesized_midi",
        output_dir="/home/chou150/depot/datasets/cocochorals_exp/cocochorales_full",
    )
