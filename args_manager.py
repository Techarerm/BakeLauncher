import os
import json
import print_color
import __init__
from print_color import print
from __init__ import GetPlatformName
from __init__ import ClearOutput
from __init__ import timer

def argsman():
    ClearOutput(GetPlatformName.check_platform_valid_and_return())
    print("Modify Launch arguments are coming soon :)", color='g' )
    timer(8)
