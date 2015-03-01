from collections import OrderedDict

HARMONIC_NOTES = OrderedDict()
HARMONIC_NOTES[1] = 'do'

HARMONIC_NOTES[2] = 'do'

HARMONIC_NOTES[3] = 'sol'
HARMONIC_NOTES[4] = 'do'

HARMONIC_NOTES[5] = 're'
HARMONIC_NOTES[6] = 'sol'
HARMONIC_NOTES[7] = 'si-b'
HARMONIC_NOTES[8] = 'do'

HARMONIC_NOTES[9] = 're'
HARMONIC_NOTES[10] = 'mi'
HARMONIC_NOTES[11] = ''
HARMONIC_NOTES[12] = 'sol'
HARMONIC_NOTES[13] = ''
HARMONIC_NOTES[14] = 'si-b'
HARMONIC_NOTES[15] = 'si'
HARMONIC_NOTES[16] = 'do'

HARMONIC_NOTES[17] = ''
HARMONIC_NOTES[18] = 're'
HARMONIC_NOTES[19] = ''
HARMONIC_NOTES[20] = 'mi'
HARMONIC_NOTES[21] = ''
HARMONIC_NOTES[22] = ''
HARMONIC_NOTES[23] = ''
HARMONIC_NOTES[24] = 'sol'

# http://www.w3.org/TR/SVG/types.html#ColorKeywords
NOTES_COLORS = {
    'si': 'mediumvioletred',
    'si-b': 'blueviolet',
    'la': 'blue',
    'sol': 'deepskyblue',
    'fa': 'lime',
    'mi': 'yellow',
    're': 'orange',
    'do': 'red',
    '': '#bbb',
}

HARMONIC_COLORS = OrderedDict([
    (harmonic, NOTES_COLORS[note])
    for harmonic, note in HARMONIC_NOTES.items()
])
