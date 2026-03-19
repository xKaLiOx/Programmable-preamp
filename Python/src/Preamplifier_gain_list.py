import numpy as np
import pyvisa
import time
import os
import struct
#usb-i2c converter
import settings
from ch341_usb_i2c import *
from setup_functions import *


start_time = time.time()
rm = pyvisa.ResourceManager()

CreateFolders()

#connect to the devices
if settings.CONNECT_I2C == True:
    try:
        i2c = CH341()
        print("CH341 I2C Device Initialized")
        i2c.set_speed(20) # 20 khz slow i2c
    except ConnectionError as err:
        print(err)

try:
    generator = rm.open_resource("USB0::0xF4EC::0x1101::SDG6XEBX4R0162::INSTR")
    oscilloscope = rm.open_resource(
        "USB0::0x1AB1::0x0610::HDO4A244801408::INSTR")
except pyvisa.errors.VisaIOError as err:
    print("Could not open VISA device")
    print(rm.list_resources())
    print(f"ERR: {err}")

#send DAC start stop step values
ReceiveDACIndex()
# reset both instruments
generator.write("*RST")
oscilloscope.write("*RST")
time.sleep(0.1)

# setup generator sync with oscilloscope
generator.write("ROSCillator INT")
generator.write("ROSC 10MOUT,ON")
generator.write("C1:SYNC ON,TYPE,CH1")

GeneratorSetSine(generator, 1, settings.FREQUENCY, settings.input_voltage)
time.sleep(0.1)
generator.write("C2:OUTP OFF,HZ")
generator.write("C1:OUTP ON,HZ")
time.sleep(0.1)
# setup the oscilloscope
oscilloscope.write(":STOP")

for x in range(1, 5):
    oscilloscope.write(f":CHANnel{x}:DISPlay OFF")

oscilloscope.write(":SYSTem:RCLock CINPut")
# trigger
oscilloscope.write(":TRIGger:MODE EDGE")
oscilloscope.write(":TRIGger:EDGE:SOURce CHAN1") #CHAN1/2 EXT
oscilloscope.write(f":TRIGger:EDGE:LEVel 0")  # In Volts
oscilloscope.write(f":TRIGger:HOLDoff {settings.HOLDOFF}")
oscilloscope.write(":TRIGger:EDGE:SLOPe POSitive")
oscilloscope.write(":TRIGger:SWEep AUTO")

# acquire
oscilloscope.write(f":ACQuire:AVERages {settings.AVERAGE}")
oscilloscope.write(f":ACQuire:MDEPth {int(settings.MEM_DEPTH)}")
oscilloscope.write(":ACQuire:TYPE NORMal")

oscilloscope.write(f":WAVeform:MODE {settings.WAV_MODE}")
oscilloscope.write(f":WAVeform:FORMat {settings.WAV_FORMAT}")

time.sleep(0.02)

# timebase
oscilloscope.write(":TIMebase:DELay:ENABle OFF")
NUM_OF_SINES = 10
time_div = ((1 / settings.FREQUENCY) * NUM_OF_SINES) / 10
# REMARKS TIMEDIV
oscilloscope.write(f":TIMebase:MAIN:SCALe {time_div}")

# channel setup
for x in settings.USED_CHANNELS:
    oscilloscope.write(f":CHANnel{x}:DISPlay ON")
    oscilloscope.write(f":CHANnel{x}:OFFSet 0")
    oscilloscope.write(f":CHANnel{x}:PROBe {settings.PROBE_RATIO}")


oscilloscope.write(f":CHANnel1:COUPling DC")
oscilloscope.write(":CHANnel1:IMPedance OMEG")
oscilloscope.write(":CHANnel2:IMPedance FIFTy")

###################################################


print("--- %s seconds ---" % (round(time.time() - start_time, 2)))
print("Starting the loop")
for index in range(settings.dac_start, settings.dac_stop, settings.dac_step):
    ## SET WITH USB-I2C CONVERTER INDEX
    
    #sets false if the values are not exceeding, else resample
    settings.Resample_data = True
    while(settings.Resample_data == True):
        #set vertical scaling of CH2 CH1 and amplitude of gen
        #vga_output_voltage = GetVGAOutputVoltage(input_voltage, index, VGA_PA_HILO_PIN)
        #VOLTAGE AT OUTPUT FIXED, CALCULATE IN BASED ON THE OUT
        Input_voltage = GetVGAInputVoltage(index,settings.VGA_PA_HILO_PIN)
        #set the voltage at a generator
        GeneratorSetSine(generator, 1, settings.FREQUENCY, Input_voltage)
        
        oscilloscope.write("*WAI")
        time.sleep(0.05)
        oscilloscope.write(":RUN")
        time.sleep(.8)
        oscilloscope.write(":STOP")
        
        for channel in range(1, len(settings.USED_CHANNELS) + 1):
            # GET CHANNEL DATA
            
            SetWAVParams(oscilloscope, channel, 1, int(settings.MEM_DEPTH))
            # save received params to file
            ReceivePreamble(oscilloscope, channel, index)
            GetRawChannel(oscilloscope, channel, index, settings.WAV_FORMAT)
                
print("--- %s seconds ---" % (round(time.time() - start_time, 2)))
print("end of loop")
print("Saved RAW data to the folder")
