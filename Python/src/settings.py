import time

#folder paths
DirPath = "C:/Users/Arthur/Documents/Linas_B"
FolderName = "Measurement_data"
SaveDir = (
    "/Gain_list_" + time.strftime("%Y_%m_%d") + "_" + time.strftime("%H_%M")
)

# VGA HI/LO PIN FOR ESTIMATED GAIN MEASUREMENT
VGA_PA_HILO_PIN = 0  # 0 OFF 1 ON

# MEASUREMENT GENERATOR INPUT
#################
input_voltage = 0.1
FREQUENCY = 1e6
#################

# MCU AND DAC SETTINGS
#################
dac_start = 0
dac_stop = 5
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
WAV_MODE_LIST = ["NORMal MAXimum RAW"]  # NORMal MAXimum RAW
WAV_MODE = "RAW"
WAV_FORMAT_LIST = ["ASCii BYTE WORD"]
WAV_FORMAT = "WORD"
#################

