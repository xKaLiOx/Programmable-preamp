// MCP4725 library header file for STM32 MCU

#ifndef MCP4725_H
#define MCP4725_H

#include "i2c.h"

#define MCP4725_A0_PIN 0 // A0 pin state (0 or 1)

// 0b1100000 A2 A1 hard wired, A0 configurable
#ifdef MCP4725_A0_PIN
#if MCP4725_A0_PIN == 0
#define MCP4725_DEFAULT_ADDRESS (0x60 << 1)
#elif MCP4725_A0_PIN == 1
#define MCP4725_DEFAULT_ADDRESS (0x61 << 1)
#else
#error "Invalid A0 pin state. Must be 0 or 1."
#endif
#endif

typedef enum
{
	MCP4725_FAST_MODE          = 0x00,                              //writes data to DAC register
	MCP4725_REGISTER_MODE      = 0x40,                              //writes data & configuration bits to DAC register
	MCP4725_EEPROM_MODE        = 0x60                               //writes data & configuration bits to DAC register & EEPROM
}
MCP4725_COMMAND_TYPE;

typedef enum
{
	MCP4725_POWER_DOWN_OFF     = 0x00,                              //power down off
	MCP4725_POWER_DOWN_1KOHM   = 0x01,                              //power down on, with 1.0 kOhm to ground
	MCP4725_POWER_DOWN_100KOHM = 0x02,                              //power down on, with 100 kOhm to ground
	MCP4725_POWER_DOWN_500KOHM = 0x03                               //power down on, with 500 kOhm to ground
}
MCP4725_POWER_DOWN_TYPE;

typedef struct
{
	uint16_t DAC_value;
	uint16_t EEPROM_value;
	uint8_t RDY_flag;
	MCP4725_POWER_DOWN_TYPE POWER_DOWN_TYPE;
} MCP4725_READ_REG_DATA;

//ADDRESS IS GENERAL CALL, REGISTER 2ND BYTE
#define MCP4725_GENERAL_CALL_ADDRESS 0x00 // general call address for all devices
#define MCP4725_GENERAL_RESET_COMMAND 0x06 // power on reset command
#define MCP4725_GENERAL_WAKEUP_COMMAND 0x09 // resets power down bits

#define MCP4725_FAST_MODE 0x00 // change without EEPROM write
#define MCP4725_DAC_AND_EEPROM 0x40 // change with EEPROM write

#define MCP4725_I2C_TIMEOUT 30
#define MCP4725_MAX_VALUE 4095

void MCP4725_Init(I2C_HandleTypeDef *hi2c);
void MCP4725_ReadRegister(I2C_HandleTypeDef *hi2c, MCP4725_READ_REG_DATA *registers); // returns the current DAC value (0-4095)
uint8_t MCP4725_CheckConnection(I2C_HandleTypeDef *hi2c); // returns 1 if device is connected, 0 otherwise
HAL_StatusTypeDef MCP4725_SetValue(I2C_HandleTypeDef *hi2c, uint16_t value,
		MCP4725_COMMAND_TYPE mode, MCP4725_POWER_DOWN_TYPE power); // 0 for fast mode, 1 for DAC and EEPROM mode
uint8_t MCP4725_WakeUp(I2C_HandleTypeDef *hi2c);


#endif // MCP4725_H
