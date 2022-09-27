#include <bits/stdint-uintn.h>
#include "Commands.h"

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

void RunProgram(stm32_env_t* env, uint8_t* data, uint32_t retval)
{
    uint16_t i, j, k, n;
    if (retval > 2 && data[0] == 16 + 1) {
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