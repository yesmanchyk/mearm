#ifndef COMMANDS_H
#define COMMANDS_H

typedef struct stm32_api {
	void (*HAL_GPIOC_TogglePin)(uint16_t GPIO_Pin);
	void (*DWT_Delay)(uint32_t us);
} stm32_api_t;

typedef struct stm32_env {
	stm32_api_t api;
	uint16_t gpio[4];
} stm32_env_t;

uint16_t ConvertPinMask(uint16_t* pins, uint8_t mask);
uint16_t RunInstructionSequence(stm32_env_t* env, uint8_t* data, uint32_t retval, uint16_t k);
void RunProgram(stm32_env_t* env, uint8_t* data, uint32_t retval);

#endif