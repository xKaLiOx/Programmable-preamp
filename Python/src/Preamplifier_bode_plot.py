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
    exit()

#send DAC start stop step values
CreateFolders(settings.SaveDirBode)
ReceiveParameters("BODE_PLOT")
# reset both instruments
generator.write("*RST")
oscilloscope.write("*RST")
time.sleep(0.1)

# setup generator sync with oscilloscope and turn off channel outputs
generator.write("ROSCillator INT")
generator.write("ROSC 10MOUT,ON")
generator.write("C1:SYNC ON,TYPE,CH1")

generator.write("C2:OUTP OFF,HZ")
generator.write("C1:OUTP OFF,HZ")
time.sleep(0.1)

# setup the oscilloscope
oscilloscope.write(":STOP")
for x in range(1, 5):
    oscilloscope.write(f":CHANnel{x}:DISPlay OFF")
oscilloscope.write(":SYSTem:RCLock CINPut")
# trigger

SetupOscTrigger(oscilloscope,"EDGE","DC",30e-9,"AUTO")
oscilloscope.write(f":TRIGger:EDGE:SOURce CHAN1") #CHAN1/2 EXT
oscilloscope.write(f":TRIGger:EDGE:SLOPe POSitive")
oscilloscope.write(f":TRIGger:EDGE:LEVel 0")  # In Volts

# acquire
oscilloscope.write(f":ACQuire:TYPE {settings.ACQUIRE_TYPE}")
oscilloscope.write(f":ACQuire:AVERages {settings.AVERAGE}")
oscilloscope.write(f":ACQuire:MDEPth {int(settings.MEM_DEPTH)}")

oscilloscope.write(f":WAVeform:MODE {settings.WAV_MODE}")
oscilloscope.write(f":WAVeform:FORMat {settings.WAV_FORMAT}")

time.sleep(0.02)

# timebase
oscilloscope.write(":TIMebase:DELay:ENABle OFF")

# channel setup
for x in settings.USED_CHANNELS:
    oscilloscope.write(f":CHANnel{x}:DISPlay ON")
    oscilloscope.write(f":CHANnel{x}:OFFSet 0")
    oscilloscope.write(f":CHANnel{x}:PROBe {settings.PROBE_RATIO}")


oscilloscope.write(f":CHANnel1:COUPling DC")
oscilloscope.write(":CHANnel1:IMPedance OMEG")
oscilloscope.write(":CHANnel2:IMPedance FIFTy")

###################################################

#send to USB-I2C gain point
if settings.CONNECT_I2C == True:
    data = [0,0,0,0,0,0,0,0]
    i2c.stm32_send_frame(settings.STM_I2C_ADDR,settings.SEND_TO_DAC,settings.CALIBRATED_DAC_VALUE,data)

print("--- %s seconds ---" % (round(time.time() - start_time, 2)))
print("Starting the loop")

for frequency in settings.FREQUENCY_LIST:
    #sets false if the values of oscilloscope are not overflowing, else resize and resample
    settings.Resample_data = True
    while(settings.Resample_data == True):

        #VOLTAGE AT INPUT FIXED
        GeneratorSetSine(generator, 1, frequency, settings.GENERATOR_VOLTAGE)
        oscilloscope.write("*WAI")
        time.sleep(0.05)
        oscilloscope.write(":RUN")
        time.sleep(.7)
        oscilloscope.write(":STOP")
        
        for channel in range(1, len(settings.USED_CHANNELS) + 1):
            # GET CHANNEL DATA
            
            SetWAVParams(oscilloscope, channel, 1, int(settings.MEM_DEPTH))
            time.sleep(0.1)
            # save received params to file
            ReceivePreamble(oscilloscope,settings.SaveDirBode, channel, frequency)
            GetRawChannel(oscilloscope,settings.SaveDirBode, channel, frequency, settings.WAV_FORMAT)
            #exit the loop if 1st channel already needs resampling
            if settings.Resample_data == True:
                break
                
print("--- %s seconds ---" % (round(time.time() - start_time, 2)))
print("end of loop")
print("Saved RAW data to the folder")
