#include "MCP4725.h"

void MCP4725_Init(I2C_HandleTypeDef *hi2c) {
	uint8_t call = MCP4725_GENERAL_RESET_COMMAND;
	if (HAL_I2C_IsDeviceReady(hi2c, MCP4725_DEFAULT_ADDRESS, 2,
	MCP4725_I2C_TIMEOUT)) {
		HAL_I2C_Master_Transmit(hi2c, MCP4725_GENERAL_CALL_ADDRESS, &call, 1,
		MCP4725_I2C_TIMEOUT);
	}
}
void MCP4725_ReadRegister(I2C_HandleTypeDef *hi2c, MCP4725_READ_REG_DATA *registers) // returns the current DAC value (0-4095)
{
	uint8_t buffer[5];
	if (HAL_I2C_IsDeviceReady(hi2c, MCP4725_DEFAULT_ADDRESS, 2,
	MCP4725_I2C_TIMEOUT))
	{
		HAL_I2C_Master_Receive(hi2c, MCP4725_DEFAULT_ADDRESS, buffer, 5, MCP4725_I2C_TIMEOUT);

		registers->POWER_DOWN_TYPE = (buffer[0] >> 1) & 0x03;
		registers->RDY_flag = (buffer[0] >> 7) & 0x01;
		registers->DAC_value = ((uint16_t)buffer[1] << 4) | ((uint16_t)buffer[2] >> 4 );
		registers->EEPROM_value = (((uint16_t)buffer[3] & 0xF) << 8) | ((uint8_t)buffer[4]);
	}


}
uint8_t MCP4725_CheckConnection(I2C_HandleTypeDef *hi2c) // returns 1 if device is connected, 0 otherwise
{
	return (HAL_I2C_IsDeviceReady(hi2c, MCP4725_DEFAULT_ADDRESS, 2,
	MCP4725_I2C_TIMEOUT) == HAL_OK);
}

HAL_StatusTypeDef MCP4725_SetValue(I2C_HandleTypeDef *hi2c, uint16_t value,
		MCP4725_COMMAND_TYPE mode, MCP4725_POWER_DOWN_TYPE power)
// 0 for fast mode, 1 for DAC and EEPROM mode
{
	uint8_t buffer[3] = { 0 };

	if (value > 0x0FFF)
		return HAL_ERROR; //wrong set number

	switch (mode) {
	case (MCP4725_FAST_MODE): {
		buffer[0] = (power << 4) | (value >> 8);
		buffer[1] = (value & 0x00FF);

		return HAL_I2C_Master_Transmit(hi2c, MCP4725_DEFAULT_ADDRESS, buffer, 2,
				MCP4725_I2C_TIMEOUT);
	}
	case (MCP4725_REGISTER_MODE):
	case (MCP4725_EEPROM_MODE): {
		buffer[0] = mode | (power << 1);
		value = (value << 4); //12 bits shifted

		buffer[1] = (value >> 8);
		buffer[2] = (value & 0x00F0); // last 4 bits don't care

		return HAL_I2C_Master_Transmit(hi2c, MCP4725_DEFAULT_ADDRESS, buffer, 3,
				MCP4725_I2C_TIMEOUT);
	}
	default:
		return HAL_ERROR;
	}
}
uint8_t MCP4725_WakeUp(I2C_HandleTypeDef *hi2c) {
	uint8_t call = MCP4725_GENERAL_WAKEUP_COMMAND;
	if (HAL_I2C_IsDeviceReady(hi2c, MCP4725_DEFAULT_ADDRESS, 2,
			MCP4725_I2C_TIMEOUT))
	{
		if(HAL_I2C_Master_Transmit(hi2c, MCP4725_GENERAL_CALL_ADDRESS, &call, 1,MCP4725_I2C_TIMEOUT) == HAL_OK)
		{
			return 1;
		}
	}
	return 0;
}
