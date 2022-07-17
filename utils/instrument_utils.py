"""Utilities for instrument assignment."""

from midi_ddsp.data_handling.instrument_name_utils import INST_NAME_TO_MIDI_PROGRAM_DICT
import numpy as np

USEFUL_INST_PROG = list(INST_NAME_TO_MIDI_PROGRAM_DICT.values())[:-1]  # except guitar

FOUR_BACH_PARTS = ['Soprano', 'Alto', 'Tenor', 'Bass']

AVAILABLE_ENSEMBLES = ['string', 'brass', 'woodwind', 'random']

STRING_ENSEMBLE = {
    'Soprano': 'violin',
    'Alto': 'violin',
    'Tenor': 'viola',
    'Bass': 'cello',
}

WOODWIND_ENSEMBLE = {
    'Soprano': 'flute',
    'Alto': 'oboe',
    'Tenor': 'clarinet',
    'Bass': 'bassoon',
}

BRASS_ENSEMBLE = {
    'Soprano': 'trumpet',
    'Alto': 'horn',
    'Tenor': 'trombone',
    'Bass': 'tuba',
}

RANDOM_ENSEMBLE = {
    'Soprano': [
        'violin',
        'flute',
        'trumpet',
        'clarinet',
        'oboe',
    ],
    'Alto': [
        'violin',
        'viola',
        'flute',
        'clarinet',
        'oboe',
        'saxophone',
        'trumpet',
        'horn'
    ],
    'Tenor': [
        'viola',
        'cello',
        'clarinet',
        'saxophone',
        'trombone',
        'horn'
    ],
    'Bass': [
        'cello',
        'double bass',
        'bassoon',
        'tuba'
    ],
}


def get_instrument_by_part(ensemble, part):
    if ensemble == 'string':
        instrument = STRING_ENSEMBLE[part]
    elif ensemble == 'brass':
        instrument = BRASS_ENSEMBLE[part]
    elif ensemble == 'woodwind':
        instrument = WOODWIND_ENSEMBLE[part]
    elif ensemble == 'random':
        instrument = np.random.choice(RANDOM_ENSEMBLE[part])
    else:
        raise ValueError('Band name not supported.')
    return instrument


INSTRUMENT_INTERCHANGE = {
    'violin': ['trumpet', 'oboe', 'flute', 'clarinet', 'viola'],
    'viola': ['violin', 'horn', 'trumpet', 'oboe', 'flute', 'clarinet'],
    'cello': ['double bass', 'viola', 'clarinet', 'tuba', 'bassoon', 'trombone', 'saxophone', 'horn'],
    'double bass': ['cello', 'tuba', 'bassoon'],
    'flute': ['trumpet', 'oboe', 'violin', 'clarinet', 'viola'],
    'oboe': ['trumpet', 'clarinet', 'violin', 'flute', 'viola'],
    'clarinet': ['trumpet', 'oboe', 'violin', 'flute', 'viola'],
    'saxophone': ['viola', 'clarinet', 'bassoon', 'trombone', 'horn'],
    'bassoon': ['cello', 'tuba', 'double bass'],
    'trumpet': ['violin', 'oboe', 'flute', 'clarinet', 'viola'],
    'horn': ['viola', 'clarinet', 'bassoon', 'trombone', 'saxophone'],
    'trombone': ['viola', 'clarinet', 'tuba', 'bassoon', 'horn', 'saxophone'],
    'tuba': ['cello', 'double bass', 'bassoon']
}
