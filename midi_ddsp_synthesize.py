import glob
from tqdm import tqdm
from midi_ddsp.midi_ddsp_synthesize import synthesize_midi, load_pretrained_model


def synthesize_midi_files(
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

    synthesis_generator, expression_generator = load_pretrained_model(
        synthesis_generator_path=synthesis_generator_weight_path,
        expression_generator_path=expression_generator_weight_path,
    )

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
    elif midi_dir:
        midi_file_list = glob.glob(midi_dir + "/*.mid")
        if len(midi_file_list) == 0:
            raise FileNotFoundError("No MIDI files found in the directory.")
        for midi_file in tqdm(midi_file_list, desc="Generating files: "):
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
    elif midi_path:
        synthesize_midi(
            synthesis_generator,
            expression_generator,
            midi_path,
            pitch_offset=pitch_offset,
            speed_rate=speed_rate,
            output_dir=output_dir,
            sf2_path=sf2_path,
            use_fluidsynth=use_fluidsynth,
            display_progressbar=True,
            skip_existing_files=skip_existing_files,
            save_metadata=save_metadata,
        )
