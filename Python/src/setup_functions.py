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
        
def ReceivePreamble(Preamble_str : str):
    #receive oscilloscope preamble for data reconstruction in MatLab
    #set the params to dict
    Received_params_list = Preamble_str[0:-1].split(',') #list of params
    preamble_oscill = dict.fromkeys(['points','average',"xincrement",'xorigin','xreference','yincrement','yorigin','yreference'])
    preamble_oscill['points'] = int(Received_params_list[2])
    preamble_oscill['average'] = int(Received_params_list[3])

    preamble_oscill['xincrement'] = float(Received_params_list[4])
    preamble_oscill['xorigin'] = float(Received_params_list[5])
    preamble_oscill['xreference'] = float(Received_params_list[6])

    preamble_oscill['yincrement'] = float(Received_params_list[7])
    preamble_oscill['yorigin'] = int(Received_params_list[8])
    preamble_oscill['yreference'] = int(Received_params_list[9])
    
    return preamble_oscill
    