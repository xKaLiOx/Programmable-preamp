import numpy as np
import pyvisa
import time
import os
import struct

from setup_functions import *


DirPath = "C:/Users/Arthur/Documents/Linas_B"
rm = pyvisa.ResourceManager()


#VGA HI/LO PIN FOR ESTIMATED GAIN MEASUREMENT
VGA_PA_HILO_PIN = 0 # 0 OFF 1 ON

#MEASUREMENT GENERATOR INPUT
#################
START_INPUT_VOLTAGE = .1 #100 mV
FREQUENCY = 1E6
#################

#OSCILLOSCOPE SETTINGS
#################
USED_CHANNELS = [1,2]
MEM_DEPTH = 10e3 # 10k default 
#1k, 10k, 100k,1M, 10M, 25M, 50M, 100M, 125M
BITS = 12
AVERAGE = 1 # 2^n
PROBE_RATIO = 1
WAV_MODE_LIST = ["NORMal MAXimum RAW"] # NORMal MAXimum RAW
WAV_MODE = "RAW"
WAV_FORMAT_LIST = ["ASCii BYTE WORD"]
WAV_FORMAT = "ASCii"
#################


CreateFolder()

try:
    generator = rm.open_resource("USB0::0xF4EC::0x1101::SDG6XEBX4R0162::INSTR")
    oscilloscope = rm.open_resource("USB0::0x1AB1::0x0610::HDO4A244801408::INSTR")
except pyvisa.errors.VisaIOError as err:
    print("Could not open VISA device")
    print(rm.list_resources())
    print(f"ERR: {err}")
    
#apply sine to generator
generator.write("C1:BSWV WVTP,SINE")
generator.write(f"C1:BSWV FRQ,{FREQUENCY}")
generator.write(f"C1:BSWV AMP,{START_INPUT_VOLTAGE}")
time.sleep(0.2)
generator.write("C2:OUTP OFF,HZ")
generator.write("C1:OUTP ON,HZ")
time.sleep(1)


#setup the oscilloscope
oscilloscope.write(":STOP")

for x in range(1,5):
    oscilloscope.write(f":CHANnel{x}:DISPlay OFF")

#trigger
oscilloscope.write(":TRIGger:MODE EDGE")
oscilloscope.write(":TRIGger:EDGE:SOURce CHAN1")
oscilloscope.write(f":TRIGger:EDGE:LEVel {START_INPUT_VOLTAGE/4}") # In Volts
oscilloscope.write(":TRIGger:EDGE:SLOPe POSitive")
oscilloscope.write(":TRIGger:SWEep AUTO")

#acquire
oscilloscope.write(":ACQuire:AVERages 1")
oscilloscope.write(f":ACQuire:MDEPth {int(MEM_DEPTH)}")
oscilloscope.write(":ACQuire:TYPE NORMal")
time.sleep(0.02)

#timebase
oscilloscope.write(":TIMebase:DELay:ENABle OFF")
NUM_OF_SINES = 10
time_div = ((1/FREQUENCY) * NUM_OF_SINES)/10
#REMARKS TIMEDIV
oscilloscope.write(f":TIMebase:MAIN:SCALe {time_div}")

#channel setup
for x in USED_CHANNELS:
    oscilloscope.write(f":CHANnel{x}:DISPlay ON")
    oscilloscope.write(f":CHANnel{x}:OFFSet 0")
    oscilloscope.write(f":CHANnel{x}:PROBe {PROBE_RATIO}")


oscilloscope.write(f":CHANnel1:COUPling DC")
oscilloscope.write(":CHANnel1:IMPedance OMEG")
oscilloscope.write(":CHANnel2:IMPedance FIFTy")

#horizontal automatic scaling
horizontal_div = round((START_INPUT_VOLTAGE/8)/0.7,2)
oscilloscope.write(f":CHANnel1:SCALe {horizontal_div}")
horizontal_div = 2
oscilloscope.write(f":CHANnel2:SCALe {horizontal_div}")

oscilloscope.write(":RUN")

#GET RAW DATA
time.sleep(.5)
oscilloscope.write(":STOP")
oscilloscope.write(":WAVeform:SOURce CHAN1")
oscilloscope.write(f":WAVeform:MODE {WAV_MODE}")
oscilloscope.write(f":WAVeform:FORMat {WAV_FORMAT}")
point_value = oscilloscope.query(":WAVeform:POINts?")
print("Reading "+str(int(point_value))+" of RAW data") # removed \n
oscilloscope.write(":WAVeform:STARt 1")
Received_data = oscilloscope.query(":WAVeform:DATA?")
Received_params = oscilloscope.query(":WAVeform:PREamble?")
oscilloscope.write(":RUN")


# TEST THE PREAMBLE FOR DATA RECEIVED


match WAV_FORMAT:
    case 'ASCii':
        print("ITS ASCII")
        
    case 'BYTE':
        print("ITS BYTE")
        
    case 'WORD':
        print("ITS WORD")
        
print(Received_params)
        