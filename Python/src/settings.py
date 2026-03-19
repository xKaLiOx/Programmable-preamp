import time
import struct
#folder paths
DirPath = "C:/Users/Arthur/Documents/Linas_B"
FolderName = "/Measurement_data"
SaveDir = (
    "/Gain_list_" + time.strftime("%Y_%m_%d") + "_" + time.strftime("%H_%M")
)

# VGA HI/LO PIN FOR ESTIMATED GAIN MEASUREMENT
VGA_PA_HILO_PIN = 0  # 0 OFF 1 ON

# INITIAL MEASUREMENT GENERATOR INPUT
#################
input_voltage = 0.05
FREQUENCY = 1e6

FIXED_OUT_VOLTAGE = 1 ##voltage at output, changing the generator input signal
#################

#I2C CONFIGURATION COMMANDS
CONNECT_I2C = False

ERASE_ALL = 0
FLASHING_DAC = 1
SEND_TO_DAC = 2
RETRIEVE_FROM_FLASH = 3
FLASHING_MAGIC_NUMBER = 4

#MAGIC NUMBER
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
AVERAGE = 1  # 2^n
PROBE_RATIO = 1
HOLDOFF = 30e-9
WAV_MODE_LIST = ["NORMal MAXimum RAW"]  # NORMal MAXimum RAW
WAV_MODE = "RAW"
WAV_FORMAT_LIST = ["ASCii BYTE WORD"]
WAV_FORMAT = "WORD"
#default vertical div settings (voltage/div) and scaling flag
vertical_div = [round((input_voltage / 8) / 0.7, 4),0.1]
Resample_data = False
#################

