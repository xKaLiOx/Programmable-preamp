# #python -m fx2.fx2tool load src/i2c-tiny-usb.ihex

# import usb.core
# import usb.util
# import libusb_package

# def i2c_scan():
#     print("Scanning I2C bus...")
#     found_any = False
    
#     # Standard I2C addresses are 0x08 to 0x77
#     for addr in range(0x00, 0x80):
#         try:
#             # bmRequestType: 0xC0 (Device-to-Host, Vendor, Interface)
#             # bRequest: 0xA2 (The FX2 standard I2C transfer command)
#             # wValue: The I2C address
#             # wIndex: 0 (Internal register to read)
#             # Length: 1 (Just try to read 1 byte)
#             dev.ctrl_transfer(0xC0, 0xA2, addr, 0, 1)
#             print(f"  -> Found device at address: {hex(addr)}")
#             found_any = True
#         except usb.core.USBError:
#             # Most addresses will fail/timeout, which is normal
#             continue
            
#     if not found_any:
#         print("No I2C devices responded. Check your wiring and pull-up resistors.")
        
        
# # Standard CY7C68013A VID/PID
# VID = 0x04b4 
# PID = 0x8613

# print("Searching for device...")

# backend = libusb_package.get_libusb1_backend()
# dev = usb.core.find(idVendor=VID, idProduct=PID, backend=backend)


# if dev is None:
#     print(f"Error: Device {hex(VID)}:{hex(PID)} not found.")
# else:
#     print(f"Success! Found device: {dev.idVendor:04x}:{dev.idProduct:04x}")
    
#     # 3. Set configuration (mandatory for Windows/WinUSB)
#     try:
#         dev.set_configuration()
#         print("Configuration set. The device is ready.")
#     except usb.core.USBError as e:
#         print(f"Found device, but could not set configuration: {e}")

# i2c_scan()

import usb.core
import usb.util
import libusb_package  # Add this import
import sys

# i2c-tiny-usb standard IDs
ID_VENDOR = 0x0403
ID_PRODUCT = 0xC631

# Protocol Command
CMD_I2C_IO = 1

class I2CAdapter:
    def __init__(self):
        # Find the backend provided by libusb-package
        backend = libusb_package.get_libusb1_backend()
        
        # Find the device using that backend
        self.dev = usb.core.find(idVendor=ID_VENDOR, idProduct=ID_PRODUCT, backend=backend)
        
        if self.dev is None:
            print("Error: i2c-tiny-usb device not found!")
            print("Check: Is the device plugged in and does Zadig show 'WinUSB' for it?")
            sys.exit(1)
        
        # Standard USB initialization
        self.dev.set_configuration()

    def read_registers(self, addr, length):
        try:
            # 0xC0: Device-to-Host, Vendor Request
            data = self.dev.ctrl_transfer(0xC0, CMD_I2C_IO, addr, 0, length)
            return data
        except Exception as e:
            return f"Read failed: {e}"

# --- MAIN SCRIPT ---
try:
    adapter = I2CAdapter()
    target_address = 0x70 
    num_bytes = 16

    print(f"Reading {num_bytes} bytes from I2C address 0x{target_address:02x}...")
    data = adapter.read_registers(target_address, num_bytes)

    if isinstance(data, str):
        print(data)
    else:
        print("     0  1  2  3  4  5  6  7  8  9  a  b  c  d  e  f")
        print("00: ", end="")
        for byte in data:
            print(f"{byte:02x} ", end="")
        print()
except Exception as e:
    print(f"An error occurred: {e}")