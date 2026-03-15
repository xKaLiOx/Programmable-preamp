import numpy as np
import pyvisa
import time
import os
import struct

from setup_functions import *
from settings import *

rm = pyvisa.ResourceManager()

CreateFolders()

try:
    generator = rm.open_resource("USB0::0xF4EC::0x1101::SDG6XEBX4R0162::INSTR")
    oscilloscope = rm.open_resource(
        "USB0::0x1AB1::0x0610::HDO4A244801408::INSTR")
except pyvisa.errors.VisaIOError as err:
    print("Could not open VISA device")
    print(rm.list_resources())
    print(f"ERR: {err}")

# reset both instruments
generator.write("*RST")
oscilloscope.write("*RST")

# apply sine to generator
GeneratorSetSine(generator, 1, FREQUENCY, input_voltage)
time.sleep(0.1)
generator.write("C2:OUTP OFF,HZ")
generator.write("C1:OUTP ON,HZ")
time.sleep(.5)


# setup the oscilloscope
oscilloscope.write(":STOP")

for x in range(1, 5):
    oscilloscope.write(f":CHANnel{x}:DISPlay OFF")

# trigger
oscilloscope.write(":TRIGger:MODE EDGE")
oscilloscope.write(":TRIGger:EDGE:SOURce CHAN1")
oscilloscope.write(f":TRIGger:EDGE:LEVel {input_voltage/4}")  # In Volts
oscilloscope.write(":TRIGger:EDGE:SLOPe POSitive")
oscilloscope.write(":TRIGger:SWEep AUTO")

# acquire
oscilloscope.write(":ACQuire:AVERages 1")
oscilloscope.write(f":ACQuire:MDEPth {int(MEM_DEPTH)}")
oscilloscope.write(":ACQuire:TYPE NORMal")

oscilloscope.write(f":WAVeform:MODE {WAV_MODE}")
oscilloscope.write(f":WAVeform:FORMat {WAV_FORMAT}")

time.sleep(0.02)

# timebase
oscilloscope.write(":TIMebase:DELay:ENABle OFF")
NUM_OF_SINES = 10
time_div = ((1 / FREQUENCY) * NUM_OF_SINES) / 10
# REMARKS TIMEDIV
oscilloscope.write(f":TIMebase:MAIN:SCALe {time_div}")

# channel setup
for x in USED_CHANNELS:
    oscilloscope.write(f":CHANnel{x}:DISPlay ON")
    oscilloscope.write(f":CHANnel{x}:OFFSet 0")
    oscilloscope.write(f":CHANnel{x}:PROBe {PROBE_RATIO}")


oscilloscope.write(f":CHANnel1:COUPling DC")
oscilloscope.write(":CHANnel1:IMPedance OMEG")
oscilloscope.write(":CHANnel2:IMPedance FIFTy")

# vertical automatic scaling for CH1
vertical_div_ch1 = round((input_voltage / 8) / 0.7, 3)
oscilloscope.write(f":CHANnel1:SCALe {vertical_div_ch1}")



###################################################



for index in range(dac_start, dac_stop, dac_step):
    
    ## SET WITH USB-I2C CONVERTER INDEX
    
    
    #set vertical scaling CH2
    vga_output_voltage = GetVGAOutputVoltage(input_voltage, index, VGA_PA_HILO_PIN)
    
    if(vga_output_voltage > 4.4): #VGA clamped at 4.5V
        #########################
        # AUTOMATIC GENERATOR VOLTAGE SCALING?
        print("clamped")
    
    vertical_div_ch2 = round((vga_output_voltage / 8) / 0.7, 3)
    oscilloscope.write(f":CHANnel2:SCALe {vertical_div_ch2}")
    
    oscilloscope.write(":RUN")
    time.sleep(.8)
    oscilloscope.write(":STOP")
    
    for channel in range(1, len(USED_CHANNELS) + 1):
        # GET CHANNEL DATA
        SetWAVParams(oscilloscope, channel, 1, int(MEM_DEPTH))
        # save received params to file
        ReceivePreamble(oscilloscope, channel, index)
        GetRawChannel(oscilloscope, channel, index, WAV_FORMAT)

print("Saved RAW data to the folder")

