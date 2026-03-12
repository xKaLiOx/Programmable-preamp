import pyvisa
#yra dar
import pyvisa_py



rm = pyvisa.ResourceManager()
print(rm.list_resources())
print(rm) #visa shared lib
generator = rm.open_resource('USB0::0xF4EC::0x1101::SDG6XEBX4R0162::INSTR')
oscilloscope = rm.open_resource('USB0::0x1AB1::0x0610::HDO4A244801408::INSTR')


print(generator.query('*IDN?'))
print(oscilloscope.query('*IDN?'))

oscilloscope.write(':STOP')