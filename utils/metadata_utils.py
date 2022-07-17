import tensorflow as tf
from utils.file_utils import pickle_load, pickle_dump
import numpy as np
from midi_ddsp.data_handling.instrument_name_utils import INST_ID_TO_NAME_DICT


def load_metadata(pickle_path):
    """load metadata and convert them to tensorflow tensor such that they can be input to the model."""
    metadata = pickle_load(pickle_path)
    instrument_id_all = list(metadata['instrument_id'].values())
    instrument_name_all = [INST_ID_TO_NAME_DICT[i] for i in instrument_id_all]
    instrument_id_all = [tf.convert_to_tensor([i], tf.int64) for i in instrument_id_all]
    conditioning_df_all = list(metadata['note_expression_control'].values())
    synthesis_parameters = list(metadata['synthesis_parameters'].values())
    synthesis_parameters = {k: np.stack([s[k] for s in synthesis_parameters], axis=0) for k in
                            synthesis_parameters[0].keys()}
    synthesis_parameters = {k: tf.convert_to_tensor(v) for k, v in synthesis_parameters.items()}
    residual_metadata = {k: v for k, v in metadata.items() if
                         k not in ['instrument_id', 'note_expression_control', 'synthesis_parameters']}

    instrument = instrument_id_all, instrument_name_all

    return instrument, conditioning_df_all, synthesis_parameters, residual_metadata
