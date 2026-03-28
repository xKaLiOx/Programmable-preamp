/*
 * i2c_slave.c
 *
 *  Created on: 5 Mar 2026
 *      Author: Linas
 */

#include "main.h"
#include "i2c_slave.h"
#include <stdio.h>

extern I2C_HandleTypeDef hi2c3;
extern uint8_t DAC_INDEX;
extern DAC_FLASH_DWORD DAC_DATA;
uint8_t count = 0;
uint8_t RxData[RxSize];
uint8_t TxData[TxSize];

void HAL_I2C_ListenCpltCallback(I2C_HandleTypeDef *hi2c) {
	//wait for MCU to listen again
    __HAL_I2C_CLEAR_FLAG(hi2c, I2C_FLAG_STOPF);

    // Also clear OVR if set
    if (__HAL_I2C_GET_FLAG(hi2c, I2C_FLAG_OVR)) {
        __HAL_I2C_CLEAR_FLAG(hi2c, I2C_FLAG_OVR);
    }

	HAL_I2C_EnableListen_IT(hi2c);
}

void HAL_I2C_AddrCallback(I2C_HandleTypeDef *hi2c, uint8_t TransferDirection,
		uint16_t AddrMatchCode) {
	if (TransferDirection == I2C_DIRECTION_TRANSMIT) {
		HAL_I2C_Slave_Seq_Receive_IT(hi2c, RxData, RxSize,
		I2C_FIRST_AND_LAST_FRAME);
	} else {
		//format the data to send
		HAL_I2C_Slave_Seq_Transmit_IT(hi2c, &DAC_RDY_FLAG, 1,
				I2C_FIRST_AND_LAST_FRAME);
	}
}

void HAL_I2C_SlaveRxCpltCallback(I2C_HandleTypeDef *hi2c) {
	if (hi2c->Instance == I2C3) {
		I2C_CMD_REQUEST = 1;
		CONFIG_SETTING = (CONFIGURATION_BYTE) RxData[0];
		if (RxData[1] >= 1) {
			DAC_INDEX = RxData[1];
		}

		//copy data to the block
		//0th configuration, 1st index, 2-10 chunk data
		for (uint8_t i = 2, x = 0; i < 10; i = i + 2, x++) {
			DAC_DATA.DAC_VALUES[x] = (RxData[i + 1] << 8) | RxData[i];
		}

	}
}

void HAL_I2C_SlaveTxCpltCallback(I2C_HandleTypeDef *hi2c) {
	//finished sending/RDY FLAG

}

void HAL_I2C_ErrorCallback(I2C_HandleTypeDef *hi2c) {
	if (hi2c->Instance == I2C3) {
		uint32_t error = HAL_I2C_GetError(hi2c);

		if (error == HAL_I2C_ERROR_AF) {
			// Normal: master NACKed to end a read — not a real error
			// HAL already stopped TX, just re-arm
			HAL_I2C_EnableListen_IT(hi2c);
			return;
		}
		if (error == HAL_I2C_ERROR_OVR) {
		    __HAL_I2C_CLEAR_FLAG(hi2c, I2C_FLAG_OVR);
		    __HAL_I2C_CLEAR_FLAG(hi2c, I2C_FLAG_STOPF);
			__HAL_I2C_DISABLE(hi2c);
			__HAL_I2C_ENABLE(hi2c);
		}

		//other hard errors — full re-arm
		HAL_I2C_EnableListen_IT(hi2c);
	}
}
