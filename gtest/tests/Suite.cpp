#include <gtest/gtest.h>
#include <gmock/gmock.h>

#include "../Commands.h"

TEST(TestSuite, Equality) {
    SCOPED_TRACE("eq");
    uint16_t a = 1;
    uint16_t b = 2;
    EXPECT_EQ(a, --b);
}

TEST(TestSuite, Inequality) {
    EXPECT_NE(3, 1);
}

uint16_t pins[] = { 0x0200, 0x0100, 0x0080, 0x0040 };

TEST(ConvertPinMask, HappyPath) {
    SCOPED_TRACE("ConvertPinMask");
    uint16_t gpio = ConvertPinMask(pins, 0x0d);
    EXPECT_EQ(gpio, 0x02c0);
}

TEST(ConvertPinMask, One) {
    SCOPED_TRACE("ConvertPinMask_One");
    uint16_t gpio = ConvertPinMask(pins, 1);
    EXPECT_EQ(gpio, 0x0200);
}

uint32_t args[256];
uint32_t argc = 0;

void HAL_GPIOC_TogglePin(uint16_t GPIO_Pin) {
    args[argc] = GPIO_Pin;
    ++argc;
}

void DWT_Delay(uint32_t us) {
    args[argc] = us;
    ++argc;
}

stm32_env_t env;

void init() {
    int i;
    for (i = 0; i < 4; ++i) env.gpio[i] = pins[i];
    env.api.DWT_Delay= &DWT_Delay;
    env.api.HAL_GPIOC_TogglePin = &HAL_GPIOC_TogglePin;
    for (i = 0; i < sizeof(args) / sizeof(*args); ++i) args[i] = 0;
    argc = 0;
}

TEST(RunInstructionSequence, HappyPath) {
    SCOPED_TRACE("RunInstructionSequence");
    init();
    uint8_t i, data[] = {17, 50, 13, 90, 4, 30, 8, 35, 1, 0};
    RunInstructionSequence(&env, data, 10, 0);
    EXPECT_EQ(argc, 8);
    EXPECT_EQ(args[0], 0x02c0);
    EXPECT_EQ(args[1], 900);
    EXPECT_EQ(args[2], 0x0080);
    EXPECT_EQ(args[3], 300);
    EXPECT_EQ(args[4], 0x0040);
    EXPECT_EQ(args[5], 350);
    EXPECT_EQ(args[6], 0x0200);
    EXPECT_EQ(args[7], 20000 - 1550);
}


TEST(RunProgram, HappyPath) {
    SCOPED_TRACE("RunProgram");
    init();
    uint8_t i, data[] = {17, 20, 13, 120, 13, 0,   17, 25, 1, 155, 1, 0};
    RunProgram(&env, data, 12);
    EXPECT_EQ(argc, 4 * 20 + 4 * 25);
    EXPECT_EQ(args[0], 0x02c0);
    EXPECT_EQ(args[1], 1200);
    EXPECT_EQ(args[4 * 20], 0x0200);
    EXPECT_EQ(args[4 * 20 + 1], 1550);
    EXPECT_EQ(args[4 * 20 + 4 * 25 - 2], 0x0200);
    EXPECT_EQ(args[4 * 20 + 4 * 25 - 1], 20000 - 1550);
}