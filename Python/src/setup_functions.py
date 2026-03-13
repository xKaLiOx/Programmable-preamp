import numpy as np
import pyvisa
import time
import os
import struct

DirPath = "C:/Users/Arthur/Documents/Linas_B"
def CreateFolder():
    try:
        os.mkdir(f"{DirPath}.\Measurement_data")
    except FileExistsError:
        print("Measurement_data folder exists")
        pass
    except Exception as err:
        print(err)

    SaveDir = (
        "/Gain_list_" + time.strftime("%Y_%m_%d") + "_" + time.strftime("%H_%M_%S")
    )
    try:
        os.mkdir(f"{DirPath}.\Measurement_data" + SaveDir)
        print("Created folder:  " + SaveDir)
    except:
        print("ERR:" + err)