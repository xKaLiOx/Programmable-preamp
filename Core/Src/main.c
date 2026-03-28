/* USER CODE BEGIN Header */
/**
 ******************************************************************************
 * @file           : main.c
 * @brief          : Main program body
 ******************************************************************************
 * @attention
 *
 * Copyright (c) 2026 STMicroelectronics.
 * All rights reserved.
 *
 * This software is licensed under terms that can be found in the LICENSE file
 * in the root directory of this software component.
 * If no LICENSE file comes with this software, it is provided AS-IS.
 *
 ******************************************************************************
 */
/* USER CODE END Header */
/* Includes ------------------------------------------------------------------*/
#include "main.h"
#include "i2c.h"
#include "spi.h"
#include "tim.h"
#include "gpio.h"

/* Private includes ----------------------------------------------------------*/
/* USER CODE BEGIN Includes */
#include "MCP4725.h"
#include "EPD_1in02d.h"
#include <string.h>
#include "GUI_Paint.h"
#include "i2c_slave.h"

/* USER CODE END Includes */

/* Private typedef -----------------------------------------------------------*/
/* USER CODE BEGIN PTD */
/* USER CODE END PTD */

/* Private define ------------------------------------------------------------*/
/* USER CODE BEGIN PD */
#define Imagesize ((EPD_1IN02_WIDTH / 8) * EPD_1IN02_HEIGHT)

#define ADDR_FLASH_PAGE_31    ((uint32_t)0x0800F800) /* Base @ of Page 31, 2 Kbytes */
#define FLASH_USER_START_ADDR   ADDR_FLASH_PAGE_31   /* Start @ of user Flash area */
#define FLASH_USER_END_ADDR     ADDR_FLASH_PAGE_31 + FLASH_PAGE_SIZE - 1   /* End @ of user Flash area */
#define FLASH_PAGE_NOT_EMPTY 0x1324576886754231 //magic number
/* USER CODE END PD */

/* Private macro -------------------------------------------------------------*/
/* USER CODE BEGIN PM */

/* USER CODE END PM */

/* Private variables ---------------------------------------------------------*/

/* USER CODE BEGIN PV */
FSM_MCU MCU_STATE = RUNNING; // default MCU state is normal
MCU_MODE MCU_STATUS = AWAKE;
uint8_t E_BUSY = 1;

uint8_t IS_EXTERNAL_I2C_SHORT = 0; //disable if 1

char text[12] = "\0";

CONFIGURATION_BYTE CONFIG_SETTING;
uint8_t DAC_RDY_FLAG;
uint8_t I2C_CMD_REQUEST;
uint8_t HAS_CALIBRATION_VALUES = 0;
/*
 * −4.5 dB to +43.5 dB in LO gain and +7.5 dB to +55.5 dB in HI gain mode.
 */

DAC_FLASH_DATA DAC_CALIBRATION_DATA;
uint8_t DAC_INDEX = 0; //from i2c write the chunk to
DAC_FLASH_DWORD DAC_DATA;

uint8_t I2C_RESET;
/* USER CODE END PV */

/* Private function prototypes -----------------------------------------------*/
void SystemClock_Config(void);
/* USER CODE BEGIN PFP */
void ReadI2CLine(); //test I2C line for test line
uint8_t EpaperGetPixelCenter(char *string, sFONT *font);

void FlashProgramLocation(DAC_FLASH_DWORD *DAC_STRUCT, uint8_t index,
		uint8_t MAGIC_NUMBER);
void EraseLastPage();
/* USER CODE END PFP */

/* Private user code ---------------------------------------------------------*/
/* USER CODE BEGIN 0 */
uint8_t E_paper_middle_pixel;
/* USER CODE END 0 */

/**
  * @brief  The application entry point.
  * @retval int
  */
int main(void)
{

  /* USER CODE BEGIN 1 */
	static UBYTE CurrentImage[Imagesize];
	static UBYTE OldImage[Imagesize];
  /* USER CODE END 1 */

  /* MCU Configuration--------------------------------------------------------*/

  /* Reset of all peripherals, Initializes the Flash interface and the Systick. */
  HAL_Init();

  /* USER CODE BEGIN Init */
  /* USER CODE END Init */

  /* Configure the system clock */
  SystemClock_Config();

  /* USER CODE BEGIN SysInit */

	//read i2c3 pins before configuring
  /* USER CODE END SysInit */

  /* Initialize all configured peripherals */
  MX_GPIO_Init();
  MX_I2C1_Init();
  MX_SPI1_Init();
  MX_TIM16_Init();
  /* USER CODE BEGIN 2 */

	HAL_GPIO_TogglePin(MCU_SLEEP_GPIO_Port, MCU_SLEEP_Pin);
	HAL_GPIO_TogglePin(DEBUG_LED1_GPIO_Port, DEBUG_LED1_Pin);
	HAL_GPIO_TogglePin(DEBUG_LED2_GPIO_Port, DEBUG_LED2_Pin);
	HAL_Delay(100);
	HAL_GPIO_TogglePin(MCU_SLEEP_GPIO_Port, MCU_SLEEP_Pin);
	HAL_GPIO_TogglePin(DEBUG_LED1_GPIO_Port, DEBUG_LED1_Pin);
	HAL_GPIO_TogglePin(DEBUG_LED2_GPIO_Port, DEBUG_LED2_Pin);

	ReadI2CLine();

	//INIT e-paper
	//dont turnoff e-paper as it sits at 2V and is screaming (higher current draw as well)

	HAL_GPIO_WritePin(E_PWR_EN_GPIO_Port, E_PWR_EN_Pin, GPIO_PIN_RESET); //turn on power for E-paper (open drain setup, RESET pulls low to GND)

	EPD_1IN02_Init();
	EPD_1IN02_Clear();
	DEV_Delay_ms(100);

	Paint_NewImage(CurrentImage, EPD_1IN02_WIDTH, EPD_1IN02_HEIGHT, 270, WHITE);
	Paint_NewImage(OldImage, EPD_1IN02_WIDTH, EPD_1IN02_HEIGHT, 270, WHITE);
	Paint_SelectImage(OldImage);
	Paint_Clear(WHITE);
	Paint_SelectImage(CurrentImage);
	Paint_Clear(WHITE);
	//copy calibration data to struct if it exists in flash
	DAC_FLASH_DATA *flash_ptr = (DAC_FLASH_DATA*) FLASH_USER_START_ADDR;
	if (flash_ptr->MAGIC_NUMBER == FLASH_PAGE_NOT_EMPTY) {
		//calibration data is flashed, copy to struct
		HAS_CALIBRATION_VALUES = 1;
		DAC_CALIBRATION_DATA = *flash_ptr;
	}
	//
	if (!IS_EXTERNAL_I2C_SHORT) {
		printf("\nCALIBRATION PROCEDURE\n");
		MX_I2C3_Init();
		MCU_STATE = CALIBRATION;

		strcpy(text, "MODE");
		E_paper_middle_pixel = EpaperGetPixelCenter(text, &Font24_Terminus);
		Paint_DrawString_EN(E_paper_middle_pixel, 0, text, &Font24_Terminus,
		BLACK, WHITE);

		strcpy(text, "CALIBRATE");
		E_paper_middle_pixel = EpaperGetPixelCenter(text,
				&Font16_Terminus_normal);
		Paint_DrawString_EN(E_paper_middle_pixel, 30, text,
				&Font16_Terminus_normal, BLACK, WHITE);

		//start I2C listening
		printf("Started listening\n");
		if (HAL_I2C_EnableListen_IT(&hi2c3) != HAL_OK) {
			Error_Handler();
		}
	} else {
		printf("I2C IS SHORTED/ NORMAL PROCEDURE\n");

		strcpy(text, "MODE");
		E_paper_middle_pixel = EpaperGetPixelCenter(text, &Font24_Terminus);
		Paint_DrawString_EN(E_paper_middle_pixel, 0, text, &Font24_Terminus,
		BLACK, WHITE);
		strcpy(text, "NORMAL");
		E_paper_middle_pixel = EpaperGetPixelCenter(text, &Font24_Terminus);
		Paint_DrawString_EN(E_paper_middle_pixel, 30, text,
				&Font16_Terminus_normal, BLACK, WHITE);
	}

	//turn off e-paper power after init
	EPD_1IN02_Display(CurrentImage);
	EPD_1IN02_Sleep();
	//partial init time update

//	EPD_1IN02_Part_Init();
//	Paint_SelectImage(OldImage);
//	Paint_Clear(WHITE);
//	Paint_SelectImage(CurrentImage);
//	Paint_Clear(WHITE);
//    EPD_1IN02_Clear();

  /* USER CODE END 2 */

  /* Infinite loop */
  /* USER CODE BEGIN WHILE */
	while (1) {
		if (I2C_CMD_REQUEST) {
			switch (CONFIG_SETTING) {

			case (FLASHING_MAGIC_NUMBER): {
				for (uint8_t i = 0; i < 4; i++) {
					DAC_DATA.DAC_VALUES[i] = (uint16_t) (FLASH_PAGE_NOT_EMPTY
							>> (16 * (i - 1)));
				}
				FlashProgramLocation(&DAC_DATA, DAC_INDEX, 1);
				printf("MAGIC NUMBER INSERTED\n");
				break;
			}
			case (RETRIEVE_FROM_FLASH): {
				//problem with ch341a
				printf("RETRIEVE FLASH\n");
				break;
			}
			case (FLASHING_DAC): {
				printf("FLASHING DWORD\n");
				FlashProgramLocation(&DAC_DATA, DAC_INDEX, 0);
				break;
			}
			case (SEND_TO_DAC): { //sending commands directly to DAC
				if (DAC_DATA.DAC_VALUES[0] < 4096) {
					//wakeup

					//send
					//HAL_I2C_Master_Transmit(hi2c, DevAddress, pData, Size, Timeout);

					//standby
				}
				printf("DAC SEND\n");

				break;
			}
			case (ERASE_ALL): {
				EraseLastPage();
				printf("Page 31 erased\n");
				break;
			}
			}
			I2C_CMD_REQUEST = 0; // completed a request, flag down
		}


//		sprintf(text, "%d", counter);
//		E_paper_middle_pixel = EpaperGetPixelCenter(text, &Font24_Terminus);
//		Paint_ClearWindows(E_paper_middle_pixel, 50,
//				E_paper_middle_pixel + strlen(text) * Font24_Terminus.Width,
//				50 + Font24_Terminus.Height, WHITE);
//
//		Paint_DrawNum(E_paper_middle_pixel, 50, counter, &Font24_Terminus,
//		WHITE, BLACK);
//		EPD_1IN02_DisplayPartial(OldImage, CurrentImage);
//		memcpy(OldImage, CurrentImage, Imagesize);
    /* USER CODE END WHILE */

    /* USER CODE BEGIN 3 */
	}
  /* USER CODE END 3 */
}

/**
  * @brief System Clock Configuration
  * @retval None
  */
void SystemClock_Config(void)
{
  RCC_OscInitTypeDef RCC_OscInitStruct = {0};
  RCC_ClkInitTypeDef RCC_ClkInitStruct = {0};

  /** Configure the main internal regulator output voltage
  */
  if (HAL_PWREx_ControlVoltageScaling(PWR_REGULATOR_VOLTAGE_SCALE1) != HAL_OK)
  {
    Error_Handler();
  }

  /** Initializes the RCC Oscillators according to the specified parameters
  * in the RCC_OscInitTypeDef structure.
  */
  RCC_OscInitStruct.OscillatorType = RCC_OSCILLATORTYPE_HSI;
  RCC_OscInitStruct.HSIState = RCC_HSI_ON;
  RCC_OscInitStruct.HSICalibrationValue = RCC_HSICALIBRATION_DEFAULT;
  RCC_OscInitStruct.PLL.PLLState = RCC_PLL_ON;
  RCC_OscInitStruct.PLL.PLLSource = RCC_PLLSOURCE_HSI;
  RCC_OscInitStruct.PLL.PLLM = 2;
  RCC_OscInitStruct.PLL.PLLN = 8;
  RCC_OscInitStruct.PLL.PLLQ = RCC_PLLQ_DIV2;
  RCC_OscInitStruct.PLL.PLLR = RCC_PLLR_DIV8;
  if (HAL_RCC_OscConfig(&RCC_OscInitStruct) != HAL_OK)
  {
    Error_Handler();
  }

  /** Initializes the CPU, AHB and APB buses clocks
  */
  RCC_ClkInitStruct.ClockType = RCC_CLOCKTYPE_HCLK|RCC_CLOCKTYPE_SYSCLK
                              |RCC_CLOCKTYPE_PCLK1|RCC_CLOCKTYPE_PCLK2;
  RCC_ClkInitStruct.SYSCLKSource = RCC_SYSCLKSOURCE_PLLCLK;
  RCC_ClkInitStruct.AHBCLKDivider = RCC_SYSCLK_DIV2;
  RCC_ClkInitStruct.APB1CLKDivider = RCC_HCLK_DIV1;
  RCC_ClkInitStruct.APB2CLKDivider = RCC_HCLK_DIV1;

  if (HAL_RCC_ClockConfig(&RCC_ClkInitStruct, FLASH_LATENCY_0) != HAL_OK)
  {
    Error_Handler();
  }
}

/* USER CODE BEGIN 4 */
int _write(int file, char *ptr, int len) {
	for (int i = 0; i < len; i++) {
		ITM_SendChar((*ptr++));
	}
	return len;
}

void FlashProgramLocation(DAC_FLASH_DWORD *DAC_STRUCT, uint8_t index,
		uint8_t MAGIC_NUMBER) {

	DAC_FLASH_DATA *Struct_p = (DAC_FLASH_DATA*) FLASH_USER_START_ADDR;
	uint32_t addr_index;
	uint64_t data;
	if (MAGIC_NUMBER) {
		addr_index = (uint32_t) (&(Struct_p->MAGIC_NUMBER));
		data = FLASH_PAGE_NOT_EMPTY;
	} else {
		addr_index = (uint32_t) (&(Struct_p->CALIBRATION_DATA[index * 4]));
		data = *(uint64_t*) (DAC_STRUCT->DAC_VALUES);
	}

	if (index > (DAC_FLASH_MAX_SIZE >> 2)) {//division by 4, because indexing is by 64 bits (4 16 bits)
		printf("INDEX TOO HIGH\n");
		return;
	}

	__HAL_FLASH_CLEAR_FLAG(FLASH_FLAG_OPTVERR | FLASH_FLAG_ALL_ERRORS);

	HAL_FLASH_Unlock();
	if (HAL_FLASH_Program(FLASH_TYPEPROGRAM_DOUBLEWORD, addr_index, data)
			!= HAL_OK) {
		uint32_t err = HAL_FLASH_GetError();
		printf("FLASH ERROR: %lu\n", err);
		//PARODYTI PER E-PAPER
	} else {
		printf("FLASHED AT %d index\n", index);
	}

	HAL_FLASH_Lock();
}

void HAL_GPIO_EXTI_Callback(uint16_t GPIO_Pin) {
	if (GPIO_Pin == BTN_ADD_Pin) //subtract pressed
	{
		printf("ADD \r\n");
	} else if (GPIO_Pin == BTN_SUB_Pin) //subtract
	{
		printf("SUB \r\n");
	} else {
		printf("other exti\r\n");
	}
}

void EraseLastPage() {
	uint32_t PAGEError = 0;
	static FLASH_EraseInitTypeDef EraseInitStruct;
	EraseInitStruct.TypeErase = FLASH_TYPEERASE_PAGES;
	EraseInitStruct.Banks = FLASH_BANK_1;
	EraseInitStruct.Page = 31;
	EraseInitStruct.NbPages = 1;

	HAL_FLASH_Unlock();

	if (HAL_FLASHEx_Erase(&EraseInitStruct, &PAGEError) != HAL_OK) {
		printf("PAGE:%lu, ERR:%lu", PAGEError, HAL_FLASH_GetError());
	}
	HAL_FLASH_Lock();
}

uint8_t EpaperGetPixelCenter(char *string, sFONT *font) {
	uint8_t len = strlen(string);
	if (len % 2 == 0) {
		return (EPD_1IN02_HEIGHT / 2) - ((len / 2) * font->Width);
	} else {
		return (((EPD_1IN02_HEIGHT / 2) - ((len / 2) * font->Width))
				- (font->Width / 2));
	}
}

void ReadI2CLine() {
	HAL_Delay(10);

	GPIO_InitTypeDef GPIO_InitStruct = { 0 };

	GPIO_InitStruct.Pin = GPIO_PIN_7;
	GPIO_InitStruct.Mode = GPIO_MODE_AF_OD;
	GPIO_InitStruct.Pull = GPIO_NOPULL;
	GPIO_InitStruct.Speed = GPIO_SPEED_FREQ_VERY_HIGH;
	GPIO_InitStruct.Alternate = GPIO_AF4_I2C3;
	HAL_GPIO_Init(GPIOA, &GPIO_InitStruct);

	GPIO_InitStruct.Pin = GPIO_PIN_4;
	GPIO_InitStruct.Mode = GPIO_MODE_AF_OD;
	GPIO_InitStruct.Pull = GPIO_NOPULL;
	GPIO_InitStruct.Speed = GPIO_SPEED_FREQ_VERY_HIGH;
	GPIO_InitStruct.Alternate = GPIO_AF4_I2C3;
	HAL_GPIO_Init(GPIOB, &GPIO_InitStruct);

	uint8_t counter = 0;
	//measuring short line for a second
	volatile uint8_t line_shorts = 0;
	while (counter < 10) {
		if ((HAL_GPIO_ReadPin(GPIOA, GPIO_PIN_7) == GPIO_PIN_RESET)
				|| (HAL_GPIO_ReadPin(GPIOB, GPIO_PIN_4) == GPIO_PIN_RESET)) {
			line_shorts += 1;
			printf("SHORT FOUND\n");
		}
		HAL_Delay(50);
		counter += 1;
	}

	if (line_shorts >= 6) {
		printf("I2C line is DOWN, DEINIT GPIO\r\n");
		IS_EXTERNAL_I2C_SHORT = 1;
		HAL_GPIO_DeInit(GPIOC, GPIO_PIN_0);
		HAL_GPIO_DeInit(GPIOC, GPIO_PIN_1);
	}
}
/* USER CODE END 4 */

/**
  * @brief  This function is executed in case of error occurrence.
  * @retval None
  */
void Error_Handler(void)
{
  /* USER CODE BEGIN Error_Handler_Debug */
	/* User can add his own implementation to report the HAL error return state */
	__disable_irq();
	while (1) {
	}
  /* USER CODE END Error_Handler_Debug */
}
#ifdef USE_FULL_ASSERT
/**
  * @brief  Reports the name of the source file and the source line number
  *         where the assert_param error has occurred.
  * @param  file: pointer to the source file name
  * @param  line: assert_param error line source number
  * @retval None
  */
void assert_failed(uint8_t *file, uint32_t line)
{
  /* USER CODE BEGIN 6 */
  /* User can add his own implementation to report the file name and line number,
     ex: printf("Wrong parameters value: file %s on line %d\r\n", file, line) */
  /* USER CODE END 6 */
}
#endif /* USE_FULL_ASSERT */
