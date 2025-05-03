from modules.print_colorx.print_color.print_colorx import print as print_colorx
from LauncherBase import Base
import inspect
import os

signature = inspect.signature(print)
valid_keys = {
    name for name, param in signature.parameters.items()
    if param.kind in (param.KEYWORD_ONLY, param.POSITIONAL_ONLY)
}


def print_color(*args, **kwargs):
    if not Base.DontPrintColor:
        text_color = kwargs.pop('color', None)
        print_colorx(*args, color=text_color, **kwargs)
    else:
        cleaned_kwargs = {k: v for k, v in kwargs.items() if k in valid_keys}
        print(*args, **cleaned_kwargs)


def clear():
    clear_command = None
    if os.name == "posix":
        clear_command = "clear"
    elif os.name == "nt":
        clear_command = "cls"

    if not Base.DontPrintColor:
        if clear_command is not None: os.system(clear_command)
