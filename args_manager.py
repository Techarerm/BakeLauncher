import os
import json
import print_color
import __function__
from print_color import print
from __function__ import GetPlatformName
from __function__ import ClearOutput
from __function__ import timer

def argsman():
    ClearOutput(GetPlatformName.check_platform_valid_and_return())
    print("Modify Launch arguments are coming soon :)", color='g' )
    timer(8)
