import sys

__author__ = 'bresnaha'

g_operations_dict = {}
g_operations_dict['red'] = '\x1b[31m'

g_operations_dict['bold'] = '\x1b[1m'
g_operations_dict['bold_off'] = '\x1b[22m'

g_operations_dict['italics'] = '\x1b[3m'
g_operations_dict['italics_off'] = '\x1b[23m'

g_operations_dict['underline'] = '\x1b[4m'
g_operations_dict['underline_off'] = '\x1b[24m'

g_operations_dict['inverse'] = '\x1b[7m'
g_operations_dict['inverse_off'] = '\x1b[27m'

g_operations_dict['strikethrough'] = '\x1b[9m'
g_operations_dict['strikethrough_off'] = '\x1b[29m'

g_operations_dict['reset'] = '\x1b[0m'
g_operations_dict['blink'] = '\x1b[5m'


# colors
g_colors_dict = {}
g_colors_dict['black'] = '\x1b[30m'
g_colors_dict['red'] = '\x1b[31m'
g_colors_dict['green'] = '\x1b[32m'
g_colors_dict['yellow'] = '\x1b[33m'
g_colors_dict['blue'] = '\x1b[34m'
g_colors_dict['magenta'] = '\x1b[35m'
g_colors_dict['cyan'] = '\x1b[36m'
g_colors_dict['white'] = '\x1b[37m'
g_colors_dict['default'] = '\x1b[39m'

g_background_dict = {}
g_background_dict['black'] = '\x1b[40m'
g_background_dict['red'] = '\x1b[41m'
g_background_dict['green'] = '\x1b[42m'
g_background_dict['yellow'] = '\x1b[43m'
g_background_dict['blue'] = '\x1b[44m'
g_background_dict['magenta'] = '\x1b[45m'
g_background_dict['cyan'] = '\x1b[46m'
g_background_dict['white'] = '\x1b[47m'
g_background_dict['default'] = '\x1b[49m'



def write_output(string_lvl, pgm_lvl, msg, color="default", bg_color="default", bold=False, underline=False, strikethrough=False):
    global g_colors_dict
    global g_background_dict
    global g_operations_dict

    if string_lvl > pgm_lvl:
        return

    if sys.stdout.isatty():
        msg = g_background_dict[bg_color] + g_colors_dict[color] + msg + g_operations_dict['reset']
        if bold:
            msg = g_operations_dict['bold'] + msg# + g_operations_dict['bold_off']
        if underline:
            msg = g_operations_dict['underline'] + msg
        if strikethrough:
            msg = g_operations_dict['strikethrough'] + msg


    sys.stdout.write(str(msg))
    sys.stdout.flush()