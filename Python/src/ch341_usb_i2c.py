import struct
import usb.core
import usb.util

import numpy as np
import time

STM32_ADDR = 0x25

ERASE_ALL=0x00
FLASHING_DAC=0x01
SEND_TO_DAC=0x02
RETRIEVE_FROM_FLASH=0x03
FLASHING_MAGIC_NUMBER=0x04

"""
@brief USB Control Commands
"""
class CtrlCmd():
    READ = 0xc0
    WRITE = 0x40

"""
@brief CH341 USB Commands

Used for general functionality of the CH341. Not fully tested.
"""
class VendorCmd():
    READ_REG = 0x95
    WRITE_REG = 0x9a
    SERIAL = 0xa1
    PRINT = 0xa3
    MODEM = 0xa4
    MEMW = 0xa6 # aka mCH341_PARA_CMD_W0
    MEMR = 0xac # aka mCH341_PARA_CMD_R0
    SPI = 0xa8
    SIO = 0xa9
    I2C = 0xaa
    UIO = 0xab
    I2C_STATUS = 0x52
    I2C_COMMAND = 0x53
    VERSION = 0x5f # at least in serial mode?

class I2CCmd():
    STA = 0x74
    STO = 0x75
    OUT = 0x80
    IN = 0xc0
    MAX = 32 # Vendor code (seems like the wrong place for this): min(0x3f, 32)
    SET = 0x60 # Bit 7 apparently SPI bit order, Bit 2 SPI single vs SPI double
    US = 0x40 # Vendor code uses a few of these in 20khz mode...
    MS = 0x50
    DLY = 0x0f
    END = 0x00 # Finish commands with this. Is this really necessary?


"""
@brief CH341 Class for detection, reading, writing, etc.

Attempts to behave like python smbus for compatiblilty.
"""
class CH341():
    # USB Endpoints for interacting with CH341
    EP_OUT = 0x02
    EP_IN = 0x82

    """
    @brief Construct a new CH341 object.
    
    By default, use the VID and PID assigned by the vendor for I2C mode.
    """
    def __init__(self, vid=0x1a86, pid=0x5512):
        dev = usb.core.find(idVendor=vid, idProduct=pid)

        if dev is None:
            raise ConnectionError("Device not found (%x:%x)" % (vid, pid))

        print(f'Found CH341 device ({vid:x}:{pid:x})')

        # These devices only have one that I know of...
        if (dev.bNumConfigurations != 1):
            raise ConnectionError("Device configuration error")
        dev.set_configuration()
        self.dev = dev
        # print("Device USB Protocol: %d", dev.bDeviceProtocol)


    """
    @brief Set the desired I2C speed 

    @param speed [in] clock frequency in KHz - will round down to 20, 100, 400, 750

    @return: None
    """
    def set_speed(self, speed=100):
        if speed < 100:
            sbit = 0
        elif speed < 400:
            sbit = 1
        elif speed < 750:
            sbit = 2
        else:
            sbit = 3

        cmd = [VendorCmd.I2C, I2CCmd.SET | sbit, I2CCmd.END]
        cnt = self.dev.write(self.EP_OUT, cmd)
        if (cnt != len(cmd)):
            raise ConnectionError("Failed to issue I2C Set Speed Command")
        print("Speed set to "+ str(speed))


    """
    @brief Set I2C START Condition

    @return None
    """
    def __start(self):
        cmd = [VendorCmd.I2C, I2CCmd.STA, I2CCmd.END]
        cnt = self.dev.write(self.EP_OUT, cmd)
        if (cnt != len(cmd)):
            raise ConnectionError("Failed to issue I2C START Command")


    """
    @brief Set I2C STOP Condition

    @return None
    """
    def __stop(self):
        cmd = [VendorCmd.I2C, I2CCmd.STO, I2CCmd.END]
        cnt = self.dev.write(self.EP_OUT, cmd)
        if (cnt != len(cmd)):
            raise ConnectionError("Failed to issue I2C STOP Command")


    """
    @brief Check if a byte sent on the I2C bus has been acknowledged
    
    @return bool: True for ACK, False for NAK
    """
    def __check_ack(self):
        rval = self.dev.read(self.EP_IN, I2CCmd.MAX)
        if ((len(rval) != 1 ) or (rval[0] & 0x80)):
            return False
        else:
            return True


    """
    @brief Write one or more bytes to I2C bus
    
    @param data [in] bytes to write (<=32)

    @return None
    """
    def __write_bytes(self, data):
        cmd = [VendorCmd.I2C, I2CCmd.OUT]
        if type(data) is list:
            print(data)
            for point in data:
                cmd.append(point)
        else:
            cmd.append(data)
        cmd.append(I2CCmd.END)
        cnt = self.dev.write(self.EP_OUT, cmd)
        if (cnt != len(cmd)):
            raise ConnectionError("Failed to issue I2C Send Command")
        if not (self.__check_ack()):
            raise ConnectionError("I2C ACK not received")


    """
    @brief Read one or more bytes from I2C bus

    @param length [in] number of bytes to read (<=32)

    @return array: data read from bus
    """
    def __read_bytes(self, length=1):
        cmd = [VendorCmd.I2C, I2CCmd.IN | length, I2CCmd.END]
        cnt = self.dev.write(self.EP_OUT, cmd)
        if (cnt != len(cmd)):
            raise ConnectionError("Failed to issue I2C Receive Command")

        rval = self.dev.read(self.EP_IN, length, 100) # (const, len, timeout ms)
        if len(rval) != length:
            raise ConnectionError("I2C Received an incorrect number of bytes")
        return rval


    """
    @brief Check if an address is connected to the I2C bus.
            Confirm ACK bit is set by slave.

    @param addr [in] I2C Slave address to check for
    
    @return bool: True if connected, False if not
    """
    def detect(self, addr):
        """
        Improved detect that bundles Start, Address, and Stop into one 
        USB packet to ensure SCL is released even on NAK.
        """
        # 1. Create a single command stream
        # [Start] -> [Write Address] -> [Stop]
        cmd = [
            VendorCmd.I2C, 
            I2CCmd.STA,               # Start Condition
            I2CCmd.OUT, (addr << 1),  # Send Address + Write Bit
            I2CCmd.STO,               # Stop Condition (Crucial!)
            I2CCmd.END                # End of commands
        ]
        
        try:
            # 2. Send everything in ONE USB write
            self.dev.write(self.EP_OUT, cmd)
            
            # 3. Read the status byte back from the CH341
            # The CH341 returns status for each OUT operation.
            # We sent one 'OUT' command (the address), so we expect 1 byte back.
            res = self.dev.read(self.EP_IN, 1, 100)
        
            is_ack = (res[0] & 0x80) == 0
            return is_ack

        except Exception as e:
            # In case of a USB timeout or hardware error
            print(f"USB Error during scan: {e}")
            return False


    """
    @brief Write one byte to an I2C device

    @param addr [in] I2C address to write to
    @param off [in] register to start wrtiting to
    @param byte [in] data to write

    @return None
    """
    def write_byte_data(self, addr, off, byte):
        try:
            self.__start()
            self.__write_bytes(addr << 1)
            if off is not None:
                self.__write_bytes(off)
            self.__write_bytes(byte)
            self.__stop()
        except ConnectionError as err:
            print(err)


    """
    @brief Read one byte from an I2C device
    
    @param addr [in] I2C address to read from
    @param off [in] register to start reading from

    @return byte: data read from the I2C device
    """
    def read_byte_data(self, addr, off):
        rval = None
        try:
            self.__start()
            self.__write_bytes(addr << 1)
            self.__write_bytes(off)
            self.__stop()
            self.__start()
            self.__write_bytes((addr << 1) | 1)
            rval = self.__read_bytes()
            rval = rval[0]
            self.__stop()
        except ConnectionError as err:
            print(err)
        return rval
    
    def stm32_read_byte(self, addr):
        # 0xAA = Vendor I2C
        # 0x74 = START
        # 0x81 = Write 1 byte (the address)
        # 0xC1 = Read 1 byte
        # 0x75 = STOP
        cmd = [
            0xAA,                 
            0x74,                 
            0x81,                 # Header to send the address
            (addr << 1) | 0x01,   # Address + READ bit
            0xC1,                 # Read 1 byte from bus
            0x75,                 
            0x00                  
        ]

        try:
            # 1. Clear buffer
            try: self.dev.read(self.EP_IN, 64, 2)
            except: pass

            # 2. Send command
            self.dev.write(self.EP_OUT, cmd)

            # 3. Read back from CH341
            # We expect 2 bytes: [Address_Status, Data_Byte]
            # We read 5 bytes just to be safe and clear the pipe
            res = self.dev.read(self.EP_IN, 5, timeout=100)

            if len(res) < 2:
                print("Read failed: No data returned from CH341")
                return None
                
            address_status = res[0]
            actual_data = res[1]

            if address_status & 0x80:
                print(f"Device 0x{addr:02x} NAKed the read request")
                return None

            return actual_data

        except usb.core.USBError as e:
            print(f"USB Error: {e}")
            return None
    
    def stm32_send_frame(self, addr, command,index, data):
        if not isinstance(data, (list, bytes)):
            data = [data]

        # total_len = Address (1) + Command Byte (1) + Data (N)
        total_len =  1+ 1 + 1 + len(data)
        
        if total_len > 32:
            raise ValueError("CH341 cannot send more than 32 bytes in one packet")

        cmd = [
            0xAA,               # Vendor I2C Command
            0x74,               # START
            0x80 | total_len,   # WRITE header (Must match the bytes below!)
            (addr << 1) & 0xFE, # Byte 1: Address
            command & 0xFF,      # Byte 2: Command
            index & 0xFF,       # Byte 3: Index
        ]

        # Bytes 4 to N: Data
        for b in data:
            cmd.append(b & 0xFF)
            
        cmd.append(0x75)        # STOP
        cmd.append(0x00)        # END

        try:
            # 1. Clear USB pipe
            try: self.dev.read(self.EP_IN, 64, 2)
            except: pass

            # 2. Write the frame
            self.dev.write(self.EP_OUT, cmd)
            
        except usb.core.USBError as e:
            print(f"USB Error: {e}")
            return False


    def bus_reset(self):
        """Forces a Stop condition and clears buffers to rescue a stuck SCL line."""
        try:
            # Send a burst of Stops and an End
            cmd = [VendorCmd.I2C, I2CCmd.STO, I2CCmd.STO, I2CCmd.END]
            self.dev.write(self.EP_OUT, cmd)
            # Flush any pending data in the chip
            self.dev.read(self.EP_IN, 64, 50)
        except:
            pass
    def full_reset(self):
        try:
            self.dev.reset()
            
            self.dev.set_configuration()
            self.dev.control_write(0x40, 0x51, 0, 0)
            self.set_speed(20)
            
            for _ in range(3):
                cmd = [0xAA, 0x74, 0x75, 0x00] # I2C + START + STOP + END
                self.dev.write(self.EP_OUT, cmd)
                
            try: self.dev.read(self.EP_IN, 64, 10)
            except: pass
            
        except Exception as e:
            print(f"Nuclear Reset Failed: {e}")
            return False



"""
@brief Perform a simple scan for devices attached to the I2C bus.

@param i2c [in] CH341 device to use for I2C scanning

@return None
"""
def scan(i2c):
    results = []
    for i in range(128):
        r = i2c.detect(i)
        if r: results += [i]
    print("Responses from i2c devices at: ", [hex(a) for a in results])

if __name__ == "__main__":
    try:
        i2c = CH341()
        print("CH341 I2C Device Initialized")
        i2c.set_speed(20) # 20 khz slow i2c
        
        #packet of stm32 flash is 64 bits, 16 bits for one DAC_index, 4, so it is 16 bit values clear
        # ERASE_ALL=0x00
        # FLASHING_DAC=0x01
        # SEND_TO_DAC=0x02
        # RETRIEVE_FROM_FLASH=0x03
        # FLASHING_MAGIC_NUMBER=0x04
        data = [1,2,4,8,16,32,64,128]
        # i2c.stm32_send_frame(STM32_ADDR,FLASHING_DAC,0x01,data)
        
        # dac_value = [4052, 210, 1234, 531, 1456, 3214, 123] #12 bit dac value  
        # dac_value_np = np.uint16(dac_value) #12 bit dac value
        # dac_value_converted = np.uint16(dac_value).tobytes() # Convert to 2 bytes
        
    except ConnectionError as err:
        print(err)
