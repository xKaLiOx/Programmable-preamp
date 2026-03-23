import numpy as np
import pyvisa
import time
import sys
import os
import struct

import settings


def GetVGAInputVoltage(index: int, VGA_PA_HILO_PIN: int):
    # output voltage 1, estimated gain
    dac_voltage = index * (
        settings.DAC_VCC / (2**settings.DAC_BITS - 1)
    )  # 3.3V 12 bit DAC
    amp_ctrl = dac_voltage * 15.8e3 / (15.8e3 + 34e3)  # voltage divider
    if VGA_PA_HILO_PIN == 0:
        gain_estimation_dB = 50 * amp_ctrl - 6.5  # HILO = LO
    else:
        gain_estimation_dB = 50 * amp_ctrl + 5.5  # HILO = HI

    difference_times = 10 ** (gain_estimation_dB / 20)  # log convert
    return settings.FIXED_OUT_VOLTAGE / difference_times


def GetVGAOutputVoltage(input_voltage: float, index: int, VGA_PA_HILO_PIN: int):
    # voltage divider
    dac_voltage = index * (
        settings.DAC_VCC / (2**settings.DAC_BITS - 1)
    )  # 3.3V 12 bit DAC
    amp_ctrl = dac_voltage * 15.8e3 / (15.8e3 + 34e3)  # voltage divider
    if VGA_PA_HILO_PIN == 0:
        gain_estimation_dB = 50 * amp_ctrl - 6.5  # HILO = LO
    else:
        gain_estimation_dB = 50 * amp_ctrl + 5.5  # HILO = HI
    vga_output_times = 10 ** (gain_estimation_dB / 20)  # log convert
    return vga_output_times * input_voltage


def GeneratorSetSine(
    generator: pyvisa.resources.Resource, channel: int, frequency: float, voltage: float
):
    if voltage <= 10 and voltage >= 2e-3:  # limit vout to 10 vpp
        generator.write(f"C{channel}:BSWV WVTP,SINE")
        generator.write(f"C{channel}:BSWV FRQ,{frequency}")
        generator.write(f"C{channel}:BSWV AMP,{voltage}")


def CreateFolders(dir_name: str):
    try:
        os.mkdir(f"{settings.DirPath}.\{settings.DirMeasurementName}")
    except FileExistsError:
        print(f"{settings.DirMeasurementName} folder exists")
        pass
    except Exception as err:
        print(str(err))

    try:
        os.mkdir(f"{settings.DirPath}.{settings.DirMeasurementName}" + dir_name)
        print("Created folder:  " + dir_name)
    except Exception as err:
        print("ERR:" + str(err))
        return


def GetRawChannel(
    oscilloscope: pyvisa.resources.Resource,
    directory: str,
    Channel: int,
    index: int,
    WAV_FORMAT: str,
):
    # RETURN TRUE IF SCALING NEEDED AGAIN
    # save raw data from oscilloscope to file
    oscilloscope.write("*WAI")
    time.sleep(0.05)
    oscilloscope.write(":WAVeform:DATA?")
    data_w_header = oscilloscope.read_raw()
    # TEST THE PREAMBLE FOR DATA RECEIVED
    match WAV_FORMAT:
        case "ASCii":
            print("ASCII FORMAT NOT SUPPORTED")
            exit()
        case "BYTE":
            print("BYTE FORMAT NOT SUPPORTED")
            exit()

        case "WORD":
            print("writing WORD RAW CH:" + str(Channel) + ", index:" + str(index))
            # number to show the samples
            header_byte_size = int(chr(data_w_header[1]))
            # get the sample
            data_wo_header = data_w_header[header_byte_size + 2 : -1]

            data_np = np.frombuffer(data_wo_header, dtype=np.uint16)  # format word
            min_val = np.min(data_np)
            max_val = np.max(data_np)
            RescalingValue(
                oscilloscope, min_val, max_val, Channel
            )  # need to resample the data if settings.Resample_data is true

    with open(
        settings.DirPath
        + settings.DirMeasurementName
        + directory
        + f"/RAW_CH{Channel}"
        + "_"
        + str(index)
        + ".bin",
        "wb",
    ) as binary_file:
        binary_file.write(data_wo_header)


def RescalingValue(
    oscilloscope: pyvisa.resources.Resource,
    min_val: np.uint16,
    max_val: np.uint16,
    Channel: int,
):
    print("Max and MIN ADC values: " + str(max_val) + "," + str(min_val))
    # 65535 full screen, 0.7 about 45k
    if (max_val - min_val) > 60000:
        settings.vertical_div[Channel - 1] = round(
            settings.vertical_div[Channel - 1] * 2, 4
        )
        oscilloscope.write(
            f":CHANnel{Channel}:SCALe {settings.vertical_div[Channel-1]}"
        )
        print(
            f"Setting bigger V/div of CHAN{Channel} to {settings.vertical_div[Channel-1]}"
        )
        settings.Resample_data = True
        return
    if (max_val - min_val) < 20000:
        settings.vertical_div[Channel - 1] = round(
            settings.vertical_div[Channel - 1] / 2, 4
        )
        oscilloscope.write(
            f":CHANnel{Channel}:SCALe {settings.vertical_div[Channel-1]}"
        )
        print(
            f"Setting smaller V/div of CHAN{Channel} to {settings.vertical_div[Channel-1]}"
        )
        settings.Resample_data = True
        return
    settings.Resample_data = False


def SetWAVParams(
    oscilloscope: pyvisa.resources.Resource,
    source_channel: int,
    start_point: int,
    stop_point: int,
):
    oscilloscope.write(":WAVeform:SOURce CHAN" + str(source_channel))
    oscilloscope.write(":WAVeform:STARt " + str(start_point))
    oscilloscope.write(":WAVeform:STOP " + str(stop_point))


def ReceiveParameters(plot_type: str):
    if plot_type == "GAIN_LIST":
        # gain list
        # Parameters about DAC stepping
        try:
            dac_params = f"DAC_START_STEP_STOP,{settings.dac_start},{settings.dac_step},{settings.dac_stop}\n"
            with open(
                settings.DirPath
                + settings.DirMeasurementName
                + settings.SaveDirGain
                + settings.ParameterName,
                "w",
            ) as f:
                f.write(dac_params)
            print("DAC parameters sent")
        except Exception as err:
            print("ERR PRINTING DAC PARAMETERS:" + err)
        # Parameters about input attenuation for MatLab
        if settings.ATTENUATOR_USED:
            try:
                attenuation_params = f"ATTENUATOR_USED_dB,{settings.ATTENUATOR_dB}\n"
                with open(
                    settings.DirPath
                    + settings.DirMeasurementName
                    + settings.SaveDirGain
                    + settings.ParameterName,
                    "a",
                ) as f:
                    f.write(attenuation_params)
                print("Attenuation parameters sent")
            except Exception as err:
                print("ERR PRINTING ATTENUATION PARAMETERS:" + err)

    elif plot_type == "BODE_PLOT":
        # bode plot
        # Frequency list
        try:
            with open(
                settings.DirPath
                + settings.DirMeasurementName
                + settings.SaveDirBode
                + settings.ParameterName,
                "a",
            ) as f:
                f.write("FREQ_LIST")
                for value in settings.FREQUENCY_LIST:
                    f.write("," + str(value))
                f.write("\n")
            print("Frequency list sent")
        except Exception as err:
            print("ERR PRINTING FREQUENCY LIST:" + err)
            # Parameters about input attenuation
        if settings.ATTENUATOR_USED:
            try:
                attenuation_params = f"ATTENUATOR_USED_dB,{settings.ATTENUATOR_dB}\n"
                with open(
                    settings.DirPath
                    + settings.DirMeasurementName
                    + settings.SaveDirBode
                    + settings.ParameterName,
                    "a",
                ) as f:
                    f.write(attenuation_params)
                print("Attenuation parameters sent")
            except Exception as err:
                print("ERR PRINTING ATTENUATION PARAMETERS:" + err)


def ReceivePreamble(
    oscilloscope: pyvisa.resources.Resource, directory: str, channel: int, index: int
):
    # receive oscilloscope preamble for data reconstruction in MatLab
    # set the params to dict

    oscilloscope.write("*WAI")
    time.sleep(0.05)
    Preamble_str = oscilloscope.query(":WAVeform:PREamble?")
    Received_params_list = Preamble_str[0:-1].split(",")  # list of params
    preamble_oscill = dict.fromkeys(
        [
            "points",
            "average",
            "xincrement",
            "xorigin",
            "xreference",
            "yincrement",
            "yorigin",
            "yreference",
        ]
    )
    preamble_oscill["points"] = int(Received_params_list[2])
    preamble_oscill["average"] = int(Received_params_list[3])

    preamble_oscill["xincrement"] = float(Received_params_list[4])
    preamble_oscill["xorigin"] = float(Received_params_list[5])
    preamble_oscill["xreference"] = float(Received_params_list[6])

    preamble_oscill["yincrement"] = float(Received_params_list[7])
    preamble_oscill["yorigin"] = int(Received_params_list[8])
    preamble_oscill["yreference"] = int(Received_params_list[9])

    with open(
        settings.DirPath
        + settings.DirMeasurementName
        + directory
        + f"/PREAMBLE_CH{channel}_"
        + str(index)
        + ".txt",
        "w",
    ) as f:
        f.write(Preamble_str)


def SetupOscTrigger(
    oscilloscope: pyvisa.resources.Resource,
    mode: str,
    coupling: str,
    holdoff: float,
    sweep: str,
):
    oscilloscope.write(f":TRIGger:MODE {mode}")  # EDGE|PULSe|SLOPe
    oscilloscope.write(f":TRIGger:HOLDoff {holdoff}")
    oscilloscope.write(f":TRIGger:COUPling {coupling}")
    oscilloscope.write(f":TRIGger:SWEep {sweep}")  # {AUTO|NORMal|SINGle}
