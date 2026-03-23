import time
import struct
import numpy as np
#folder paths
DirPath = "C:/Users/Arthur/Documents/Linas_B"
DirMeasurementName = "/Measurement_data"
ParameterName = "/ParameterList.txt"

# VGA HI/LO PIN FOR ESTIMATED GAIN MEASUREMENT
VGA_PA_HILO_PIN = 0  # 0 OFF 1 ON

#ATTENUATOR ON INPUT
ATTENUATOR_USED = True
ATTENUATOR_dB = 10 # dB voltage attenuation, about 3.16 times

# INITIAL MEASUREMENT GENERATOR INPUT
#################
input_voltage = 0.05
FREQUENCY = 1e6

FIXED_OUT_VOLTAGE = 1 ##voltage at output, changing the generator input signal
#################

#I2C CONFIGURATION COMMANDS
CONNECT_I2C = False
STM_I2C_ADDR = 0x25

ERASE_ALL = 0
FLASHING_DAC = 1
SEND_TO_DAC = 2
RETRIEVE_FROM_FLASH = 3
FLASHING_MAGIC_NUMBER = 4

#MAGIC NUMBER FOR MCU FLASHING
MAGIC_NUMBER = 0x1324576886754231
MAGIC_NUMBER_BYTES = struct.pack(">Q", MAGIC_NUMBER) # Little-endian 8-byte representation

# MCU AND DAC SETTINGS
#################
dac_start = 0
dac_stop = 50
dac_step = 1  # 0-4095
DAC_VCC = 3.3
DAC_BITS = 12

# OSCILLOSCOPE SETTINGS
#################
USED_CHANNELS = [1, 2]
MEM_DEPTH = 10e3  # 10k default
# 1k, 10k, 100k,1M, 10M, 25M, 50M, 100M, 125M
BITS = 12
ACQUIRE_TYPE = "NORMal"#{NORMal|PEAK|AVERages|HRESolution|ULTRa}
AVERAGE = 1  # 2^n
PROBE_RATIO = 1
WAV_MODE_LIST = ["NORMal MAXimum RAW"]  # NORMal MAXimum RAW
WAV_MODE = "RAW"
WAV_FORMAT_LIST = ["ASCii BYTE WORD"]
WAV_FORMAT = "WORD"
#default vertical div settings (voltage/div) and scaling flag
vertical_div = [round((input_voltage / 8) / 0.7, 4),0.1]
Resample_data = False
#################

#specific settings for gain list
SaveDirGain = (
    "/Gain_list_" + time.strftime("%Y_%m_%d") + "_" + time.strftime("%H_%M")
)

#specific settings for bode plot script
SaveDirBode = (
    "/Bode_plot_" + time.strftime("%Y_%m_%d") + "_" + time.strftime("%H_%M")
)

#measurements from 100kHz to 40 MHz
FREQUENCY_START = 100e3
FREQUENCY_STOP = 40e6
FREQ_NUM = 100
#set a constant DAC value of calibrated gain at certain frequency
CALIBRATED_DAC_VALUE = 400
GENERATOR_VOLTAGE = 0.5 #0.5Vpp generator output
FREQUENCY_LIST = np.geomspace(FREQUENCY_START,FREQUENCY_STOP,FREQ_NUM,dtype=np.uint64)