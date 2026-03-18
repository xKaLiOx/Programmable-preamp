import numpy as np
import pyvisa
import time
import os
import struct
from settings import *

def GetVGAOutputVoltage(input_voltage: float,index: int, VGA_PA_HILO_PIN: int):
    # voltage divider
    dac_voltage = index * (DAC_VCC / (2**DAC_BITS - 1))  # 3.3V 12 bit DAC
    amp_ctrl = dac_voltage * 15.8e3 / (15.8e3+34e3) # voltage divider
    if VGA_PA_HILO_PIN == 0:
        gain_estimation_dB = 50 * amp_ctrl - 6.5 #HILO = LO
    else:
        gain_estimation_dB = 50 * amp_ctrl + 5.5 #HILO = HI
    vga_output_times = 10 ** (gain_estimation_dB / 20)#log convert
    return vga_output_times * input_voltage

def GeneratorSetSine(generator : pyvisa.resources.Resource,channel: int, frequency: float, voltage: float):
    generator.write(f"C{channel}:BSWV WVTP,SINE")
    generator.write(f"C{channel}:BSWV FRQ,{frequency}")
    generator.write(f"C{channel}:BSWV AMP,{voltage}")

def CreateFolders():
    try:
        os.mkdir(f"{DirPath}.\{FolderName}")
    except FileExistsError:
        print(f"{FolderName} folder exists")
        pass
    except Exception as err:
        print(str(err))

    try:
        os.mkdir(f"{DirPath}.{FolderName}" + SaveDir)
        print("Created folder:  " + SaveDir)
    except Exception as err:
        print("ERR:" + str(err))
        exit()
        

def GetRawChannel(oscilloscope : pyvisa.resources.Resource,Channel:int,index:int,WAV_FORMAT:str):
    # save raw data from oscilloscope to file
    oscilloscope.write("*WAI")
    oscilloscope.write(":WAVeform:DATA?")
    data_w_header = oscilloscope.read_raw()

    # TEST THE PREAMBLE FOR DATA RECEIVED
    match WAV_FORMAT:
        case "ASCii":
            print("ASCII NOT SUPPORTED")

        case "BYTE":
            print("BYTE NOT SUPPORTED")

        case "WORD":
            print("writing WORD RAW CH:"+str(Channel)+", index:" +str(index))
            # number to show the samples
            header_byte_size = int(chr(data_w_header[1]))
            # get the sample
            data_wo_header = data_w_header[header_byte_size + 2: -1]

    with open(DirPath+FolderName+SaveDir+f"/RAW_CH{Channel}"+"_"
            + str(index)
            + ".bin", "wb") as binary_file:
        binary_file.write(data_wo_header)
    
    
def SetWAVParams(oscilloscope : pyvisa.resources.Resource, source_channel:int,start_point:int,stop_point:int):
    oscilloscope.write(":WAVeform:SOURce CHAN" + str(source_channel))
    oscilloscope.write(":WAVeform:STARt " + str(start_point))
    oscilloscope.write(":WAVeform:STOP " + str(stop_point))

def ReceiveDACIndex():
    DAC_PARAMS = f"DAC_START_STEP_STOP,{dac_start},{dac_step},{dac_stop}"
    with open(
        DirPath+FolderName+SaveDir+f"/DACIndex" + ".txt", "w"
    ) as f:
        f.write(DAC_PARAMS)
    print("DAC parameters sent")

def ReceivePreamble(oscilloscope : pyvisa.resources.Resource,channel:int,index:int):
    # receive oscilloscope preamble for data reconstruction in MatLab
    # set the params to dict
    
    oscilloscope.write("*WAI")
    Preamble_str = oscilloscope.query(":WAVeform:PREamble?")
    Received_params_list = Preamble_str[0:-1].split(',')  # list of params
    preamble_oscill = dict.fromkeys(
        ['points', 'average', "xincrement", 'xorigin', 'xreference', 'yincrement', 'yorigin', 'yreference'])
    preamble_oscill['points'] = int(Received_params_list[2])
    preamble_oscill['average'] = int(Received_params_list[3])

    preamble_oscill['xincrement'] = float(Received_params_list[4])
    preamble_oscill['xorigin'] = float(Received_params_list[5])
    preamble_oscill['xreference'] = float(Received_params_list[6])

    preamble_oscill['yincrement'] = float(Received_params_list[7])
    preamble_oscill['yorigin'] = int(Received_params_list[8])
    preamble_oscill['yreference'] = int(Received_params_list[9])


    with open(
        DirPath+FolderName+SaveDir+f"/PREAMBLE_CH{channel}_" + str(index) + ".txt", "w"
    ) as f:
        f.write(Preamble_str)
