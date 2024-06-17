cmake_minimum_required(VERSION 3.10)

project(HPC Embeddings C)

# Set the compiler to ICC if available, otherwise fall back to GCC
find_program(ICC_EXECUTABLE NAMES icc)
if(ICC_EXECUTABLE)
    set(CMAKE_C_COMPILER ${ICC_EXECUTABLE})
else()
    set(CMAKE_C_COMPILER gcc)
endif()

# Include directories
include_directories(include)

# Add source directories
add_subdirectory(src/acts)
add_subdirectory(src/regulations)
add_subdirectory(src/utility)

# Collect all source files
file(GLOB_RECURSE ACTS_SOURCES src/acts/*.c)
file(GLOB_RECURSE REGULATIONS_SOURCES src/regulations/*.c)
file(GLOB_RECURSE UTILITY_SOURCES src/utility/*.c)

# Combine all source files
set(SOURCES ${ACTS_SOURCES} ${REGULATIONS_SOURCES} ${UTILITY_SOURCES})

# Add the executable
add_executable(HPCChain ${SOURCES})