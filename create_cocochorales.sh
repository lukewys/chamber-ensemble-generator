# Suppose the MIDI files generated from Coconet is saved in the root directory as ./coconet_midi_240k

# Step 1: MIDI Augmentation
python midi_augmentation.py \
  --midi_dir ./coconet_midi_240k \
  --output_dir ./cocochorales_midi \
  --num_tracks_each_ensemble 60000

for ensemble_name in string brass woodwind random; do
  # Step 2: Render MIDI to audio
  midi_ddsp_synthesize \
    --midi_dir ./cocochorales_midi/${ensemble_name} \
    --output_dir ./synthesized_midi \
    --skip_existing_files \
    --save_metadata

  # Optional Step: Note Expression Augmentation
  # python expression_augmentation.py --multi_synthesis_dir ./synthesized_midi

  # Optional Step: Synthesis Augmentation
  # python synth_params_augmentation.py --multi_synthesis_dir ./synthesized_midi

  # Optional Step: Reverb Augmentation
  # python audio_augmentation.py --multi_synthesis_dir ./synthesized_midi

  # Step 3: Mix audio
  python audio_mixing.py --multi_synthesis_dir ./synthesized_midi
done

# Step 4: Post Process
python data_postprocess/postprocess.py \
  --midi_dir ./cocochorales_midi \
  --synthesis_dir ./synthesized_midi \
  --output_dir ./cocochorales_full
