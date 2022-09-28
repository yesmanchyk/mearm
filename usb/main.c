/**
 * Copyright (c) 2015, Lukasz Marcin Podkalicki <lpodkalicki@gmail.com>
 */

#include "stm32f4xx_hal.h"
#include "config.h"
#include "led.h"
#include "log.h"
#include "usbd_cdc.h"
#include "usbd_desc.h"
#include "usbd_cdc_if.h"
#include "dwt_delay.h"


extern void error_handler(void);

/* Variables used for USB */
extern USBD_HandleTypeDef  hUSBDDevice;

void HAL_GPIOC_TogglePin(uint16_t GPIO_Pin) {
	HAL_GPIO_TogglePin(GPIOC, GPIO_Pin);
}

// Commands.cpp

typedef struct stm32_api {
	void (*HAL_GPIOC_TogglePin)(uint16_t GPIO_Pin);
	void (*DWT_Delay)(uint32_t us);
} stm32_api_t;

typedef struct stm32_env {
	stm32_api_t api;
	uint16_t gpio[4];
} stm32_env_t;

uint16_t ConvertPinMask(uint16_t* pins, uint8_t mask)
{
    int j;
    uint16_t gpios = 0;
    for (j = 0; mask > 0 && j < 4; ++j) {
        if (mask & 1) gpios |= pins[j];
        mask >>= 1;
    }
    return gpios;
}

uint16_t RunInstructionSequence(stm32_env_t* env, uint8_t* data, uint32_t retval, uint16_t k)
{
    uint16_t i, sum, delay, gpios;
    stm32_api_t* api = &env->api;
    i = k + 2;
    gpios = sum = 0;
    while (i + 1 < retval) {
        gpios = ConvertPinMask(env->gpio, data[i]);
        delay = data[i + 1];
        i += 2;
        if (delay == 0) break;
        api->HAL_GPIOC_TogglePin(gpios);
        api->DWT_Delay(delay * 10);
        sum += delay;
    }
    api->HAL_GPIOC_TogglePin(gpios);
    api->DWT_Delay(20000 - sum * 10);
    return i;
}

#define PROGRAM_VERSION (16 + 1)

void RunProgram(stm32_env_t* env, uint8_t* data, uint32_t retval)
{
    uint16_t i, j, k, n;
    if (retval > 2 && data[0] == PROGRAM_VERSION) {
        data[retval] = 0;
        // log_info("data(%u)=%s", retval, data);
        // CDC_IntfTransmit(data, retval);
        /* [ 0: { iterations: i16, actions: [{pins,delay}, ...] }, 1: {...}, ...] */
        for (i = k = 0; k + 1 < retval; k = i) {
            n = data[k + 1];
            //led_toggle(LED_RED);        
            for (j = 0; j < n; ++j) {
                i = RunInstructionSequence(env, data, retval, k);
                // uint16_t gpios = 0;
                // i = k + 2;
                // sum = 0;
                // while (i + 1 < retval && data[i + 1] > 0) {
                // 	gpios = ConvertPinMask(pins, data[i]);
                // 	delay = data[i + 1];
                // 	api.HAL_GPIOC_TogglePin(gpios);
                // 	api.DWT_Delay(delay * 10);
                // 	sum += delay;
                // 	i += 2;
                // }
                // api.HAL_GPIOC_TogglePin(gpios);
                // api.DWT_Delay(20000 - sum * 10);
            }
        }
        /*
        n = retval < 4 ? retval : 4;
        for (pin = 0; pin < n; ++pin) {
            d = data[pin];
            led = LED_BLUE;
            if (d > 80) led = LED_GREEN;
            if (d > 160) led = LED_ORANGE;
            led_toggle(led);
            for (i = 0; i < 10; ++i) {
                HAL_GPIO_TogglePin(GPIOC, pins[pin]);
                // HAL_Delay(d/ 100);
                DWT_Delay(d * 10);
                HAL_GPIO_TogglePin(GPIOC, pins[pin]);
                // HAL_Delay(20 - d / 100);
                DWT_Delay(20000 - d * 10);
            }
            led_toggle(led);
        }
        */
        // retval = 0;
    }
}

// End of Commands.cpp	

int ReadProgram(int n, uint8_t *data, int avail) {
    int sent, retval;
    while (n < 2) {
        do {
            retval = CDC_IntfReceive(data + n, avail - n - 1);
            HAL_Delay(10);
        } while(retval < 1);
    }
    sent = data[1];
    while(n < sent + 2) {
        do {
            retval = CDC_IntfReceive(data + n, avail - n - 1);
            HAL_Delay(10);
        } while(retval < 1);
        n += retval;
    }
    return sent;
}

int psize = 60; // mouse
    // 704; // wave
uint8_t data[1024] =
    // mouse:
    { 17, 250, 15, 60, 8, 80, 4, 17, 1, 18, 2, 0, 17, 250, 15, 60, 8, 80, 4, 17, 1, 3, 2, 0, 17, 250, 15, 60, 8, 80, 4, 5, 2, 12, 1, 0, 17, 250, 15, 60, 8, 80, 4, 17, 1, 3, 2, 0, 17, 250, 15, 60, 8, 80, 4, 17, 1, 3, 2, 0 };
    /* wave:* { 17, 25, 15, 140, 2, 10, 4, 10, 9, 0, 17, 25, 15, 140, 2, 10, 4, 10, 9, 0, 17, 25, 15, 149, 6, 9, 8, 2, 1, 0, 17, 25,
 15, 148, 4, 4, 8, 5, 2, 3, 1, 0, 17, 25, 15, 148, 4, 4, 8, 5, 2, 3, 1, 0, 17, 25, 15, 143, 8, 2, 4, 15, 1, 4, 2, 0, 17,
25, 15, 132, 8, 11, 4, 17, 1, 8, 2, 0, 17, 25, 15, 132, 8, 11, 4, 17, 1, 8, 2, 0, 17, 25, 15, 120, 8, 20, 4, 20, 1, 10, 2
, 0, 17, 25, 15, 108, 8, 29, 4, 23, 1, 8, 2, 0, 17, 25, 15, 108, 8, 29, 4, 23, 1, 8, 2, 0, 17, 25, 15, 97, 8, 38, 4, 25,
1, 4, 2, 0, 17, 25, 15, 88, 8, 44, 4, 25, 2, 3, 1, 0, 17, 25, 15, 88, 8, 44, 4, 25, 2, 3, 1, 0, 17, 25, 15, 82, 8, 49, 4,
 18, 2, 11, 1, 0, 17, 25, 15, 80, 8, 50, 4, 10, 2, 20, 1, 0, 17, 25, 15, 80, 8, 50, 4, 10, 2, 20, 1, 0, 17, 25, 15, 82, 8
, 49, 6, 29, 1, 0, 17, 25, 15, 88, 8, 35, 2, 9, 4, 28, 1, 0, 17, 25, 15, 88, 8, 35, 2, 9, 4, 28, 1, 0, 17, 25, 15, 97, 8,
 19, 2, 19, 4, 25, 1, 0, 17, 25, 15, 108, 8, 4, 2, 25, 4, 23, 1, 0, 17, 25, 15, 108, 8, 4, 2, 25, 4, 23, 1, 0, 17, 25, 15
, 110, 2, 10, 8, 20, 4, 20, 1, 0, 17, 25, 15, 112, 2, 20, 8, 11, 4, 17, 1, 0, 17, 25, 15, 112, 2, 20, 8, 11, 4, 17, 1, 0,
 17, 25, 15, 116, 2, 27, 8, 2, 4, 15, 1, 0, 17, 25, 15, 123, 2, 25, 4, 4, 8, 8, 1, 0, 17, 25, 15, 123, 2, 25, 4, 4, 8, 8,
 1, 0, 17, 25, 15, 131, 2, 18, 4, 9, 8, 2, 1, 0, 17, 25, 15, 140, 2, 10, 4, 10, 9, 0, 17, 25, 15, 140, 2, 10, 4, 10, 9,
 0, 17, 25, 15, 149, 6, 9, 8, 2, 1, 0, 17, 25, 15, 148, 4, 4, 8, 5, 2, 3, 1, 0, 17, 25, 15, 148, 4, 4, 8, 5, 2, 3, 1, 0, 17,
25, 15, 143, 8, 2, 4, 15, 1, 4, 2, 0, 17, 25, 15, 132, 8, 11, 4, 17, 1, 8, 2, 0, 17, 25, 15, 132, 8, 11, 4, 17, 1, 8, 2,
0, 17, 25, 15, 120, 8, 20, 4, 20, 1, 10, 2, 0, 17, 25, 15, 108, 8, 29, 4, 23, 1, 8, 2, 0, 17, 25, 15, 108, 8, 29, 4, 23
, 1, 8, 2, 0, 17, 25, 15, 97, 8, 38, 4, 25, 1, 4, 2, 0, 17, 25, 15, 88, 8, 44, 4, 25, 2, 3, 1, 0, 17, 25, 15, 88, 8, 44,
4, 25, 2, 3, 1, 0, 17, 25, 15, 82, 8, 49, 4, 18, 2, 11, 1, 0, 17, 25, 15, 80, 8, 50, 4, 10, 2, 20, 1, 0, 17, 25, 15, 80,
8, 50, 4, 10, 2, 20, 1, 0, 17, 25, 15, 82, 8, 49, 6, 29, 1, 0, 17, 25, 15, 88, 8, 35, 2, 9, 4, 28, 1, 0, 17, 25, 15, 88,
8, 35, 2, 9, 4, 28, 1, 0, 17, 25, 15, 97, 8, 19, 2, 19, 4, 25, 1, 0, 17, 25, 15, 108, 8, 4, 2, 25, 4, 23, 1, 0, 17, 25, 15,
108, 8, 4, 2, 25, 4, 23, 1, 0, 17, 25, 15, 110, 2, 10, 8, 20, 4, 20, 1, 0, 17, 25, 15, 112, 2, 20, 8, 11, 4, 17, 1, 0,
 17, 25, 15, 112, 2, 20, 8, 11, 4, 17, 1, 0, 17, 25, 15, 116, 2, 27, 8, 2, 4, 15, 1, 0, 17, 25, 15, 123, 2, 25, 4, 4, 8,
8, 1, 0, 17, 25, 15, 123, 2, 25, 4, 4, 8, 8, 1, 0, 17, 25, 15, 131, 2, 18, 4, 9, 8, 2, 1, 0 };
/**/

int
main(void)
{
	int retval, state;
	
	HAL_Init();
    SystemClock_Config();
    RCC_Config();
    GPIO_Config();
	USART_Config();
    DWT_Init();

    if (SysTick_Config(SystemCoreClock / 1000)) {
            error_handler();
    }
    
    log_init(LOGLEVEL_INFO);
    log_info("PROJECT STARTED");

        
        /* Init Device Library */
	USBD_Init(&hUSBDDevice, &CDC_Desc, 0);
	
	/* Add Supported Class */
	USBD_RegisterClass(&hUSBDDevice, USBD_CDC_CLASS);
	USBD_CDC_RegisterInterface(&hUSBDDevice, &USBD_CDC_fops);
	
	/* Start Device Process */
	USBD_Start(&hUSBDDevice);
	
	stm32_env_t env;
	// uint16_t pins[] = { GPIO_PIN_6, GPIO_PIN_7, GPIO_PIN_8, GPIO_PIN_9 };
	uint16_t i, pins[] = { GPIO_PIN_9, GPIO_PIN_8, GPIO_PIN_7, GPIO_PIN_6 };
    for (i = 0; i < 4; ++i) env.gpio[i] = pins[i];
	env.api.HAL_GPIOC_TogglePin = &HAL_GPIOC_TogglePin;
	env.api.DWT_Delay = &DWT_Delay;

    state = 0;
    led_on(LED_RED);
    while (state == 0) {
        GPIO_PinState button_pin_state = HAL_GPIO_ReadPin(GPIOA, GPIO_PIN_0);
        if (button_pin_state == GPIO_PIN_SET) {
            state = (state + 1) % 2;
        }
        RunProgram(&env, data, psize);
        led_toggle(LED_RED);
    }

    led_off(LED_RED);
    do {
        retval = CDC_IntfReceive(data, sizeof(data) - 1);
        // retval = CDC_IntfReceive(&sent, 1);
        HAL_Delay(10);
    } while(retval < 1);
    if (data[0] == PROGRAM_VERSION + 1) {
        psize = ReadProgram(retval, data, sizeof(data) - 1);
        led_toggle(LED_RED);
        while (1) {			
            led_toggle(LED_BLUE);
            RunProgram(&env, data + 2, psize);
            led_toggle(LED_BLUE);
        }
    } else {
        led_t led = LED_GREEN;
        led_toggle(led);
        RunProgram(&env, data, retval);
        led_toggle(led);
        HAL_Delay(10);
        while (1) {
            led_toggle(led);
            while((retval = CDC_IntfReceive(data, sizeof(data) - 1)) > 0) {
                RunProgram(&env, data, retval);
            }
            HAL_Delay(10);
            led_toggle(led);
            led = led == LED_GREEN ? LED_ORANGE : LED_GREEN;
		}
    }

}

