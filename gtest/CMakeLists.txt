cmake_minimum_required(VERSION 3.10)
project(ci)

add_library(Commands Commands.cpp)

add_subdirectory(googletest)
add_executable(tests tests/Suite.cpp Commands.cpp)

target_include_directories(tests PUBLIC "${PROJECT_SOURCE_DIR}/googletest")
target_include_directories(tests PUBLIC "${PROJECT_SOURCE_DIR}/googletest/googlemock/include")
target_link_libraries(tests gtest gtest_main)
