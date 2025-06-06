cmake_minimum_required(VERSION 3.10)

# Find and set the compiler to icx if available, otherwise fall back to gcc
find_program(ICX_EXECUTABLE NAMES icx)
if(ICX_EXECUTABLE)
    set(CMAKE_C_COMPILER ${ICX_EXECUTABLE} CACHE STRING "C compiler" FORCE)
    set(CMAKE_CXX_COMPILER ${ICX_EXECUTABLE} CACHE STRING "CXX compiler" FORCE)
    message(STATUS "Found ICX compiler: ${ICX_EXECUTABLE}")
else()
    set(CMAKE_C_COMPILER gcc CACHE STRING "C compiler" FORCE)
    set(CMAKE_CXX_COMPILER g++ CACHE STRING "CXX compiler" FORCE)
    message(WARNING "ICX compiler not found, falling back to GCC")
endif()

project(HPC_Embeddings C)

set(CMAKE_C_STANDARD 99)
add_definitions(-D_GNU_SOURCE)

# Print the compiler ID
message(STATUS "CMake is using the ${CMAKE_C_COMPILER_ID} compiler.")

# Find MPI package
find_package(MPI REQUIRED)
if (MPI_FOUND)
    include_directories(SYSTEM ${MPI_INCLUDE_PATH})
else()
    message(FATAL_ERROR "MPI not found")
endif()

# Find libxml2 package
find_package(LibXml2 REQUIRED)
if (LIBXML2_FOUND)
    include_directories(${LIBXML2_INCLUDE_DIR})
else()
    message(FATAL_ERROR "libxml2 not found")
endif()

# Find NUMA package
find_library(NUMA_LIBRARIES numa REQUIRED)
if (NUMA_LIBRARIES)
    message(STATUS "NUMA library found: ${NUMA_LIBRARIES}")
else()
    message(FATAL_ERROR "NUMA library not found")
endif()

# Find OpenMP package
find_package(OpenMP REQUIRED)
if(OpenMP_FOUND)
    if(CMAKE_C_COMPILER_ID MATCHES "Intel")
        set(CMAKE_C_FLAGS "${CMAKE_C_FLAGS} ${OpenMP_C_FLAGS} -qopenmp")
    else()
        set(CMAKE_C_FLAGS "${CMAKE_C_FLAGS} ${OpenMP_C_FLAGS} -fopenmp")
    endif()
endif()

# Find Kafka package
find_library(KAFKA_LIBRARIES rdkafka REQUIRED)
if (KAFKA_LIBRARIES)
    message(STATUS "Kafka library found: ${KAFKA_LIBRARIES}")
else()
    message(FATAL_ERROR "Kafka library not found")
endif()

# Find C-JSON package
find_library(JSON_LIBRARIES json-c REQUIRED)
if (JSON_LIBRARIES)
    message(STATUS "JSON-C library found: ${JSON_LIBRARIES}")
else()
    message(FATAL_ERROR "JSON-C library not found")
endif()

# OpenVINO configuration
set(OPENVINO_DIR "/opt/app-root/src/Programs/openvino_toolkit_rhel8_2025.1.0.18503.6fec06580ab_x86_64")
set(OPENVINO_INCLUDE_DIR "${OPENVINO_DIR}/runtime/include")
set(OPENVINO_LIB_DIR "${OPENVINO_DIR}/runtime/lib/intel64")

# Check if OpenVINO is available
if(EXISTS "${OPENVINO_INCLUDE_DIR}" AND EXISTS "${OPENVINO_LIB_DIR}")
    include_directories(${OPENVINO_INCLUDE_DIR})
    link_directories(${OPENVINO_LIB_DIR})
    set(OPENVINO_LIBRARIES openvino_c openvino)
    add_definitions(-DUSE_OPENVINO)
    message(STATUS "OpenVINO found at: ${OPENVINO_DIR}")
else()
    message(WARNING "OpenVINO not found at: ${OPENVINO_DIR}. Building without OpenVINO support.")
    set(OPENVINO_LIBRARIES "")
endif()


# Include directories
include_directories(include)

# Add source directories
add_subdirectory(src/process_acts_reg)
add_subdirectory(src/utility)
add_subdirectory(src/data_structures)

# Collect all source files from subdirectories
set(SOURCES ${ACTS_SOURCES} ${REGULATIONS_SOURCES} ${UTILITY_SOURCES} ${DATA_STRUCTURE_SOURCES})

# Add the main source file
list(APPEND SOURCES src/main.c)

# Add the executable
add_executable(HPCChain ${SOURCES})

# Link MPI, libxml2, NUMA, and OpenMP libraries
target_link_libraries(HPCChain MPI::MPI_C ${LIBXML2_LIBRARIES} ${NUMA_LIBRARIES} OpenMP::OpenMP_C ${JSON_LIBRARIES} ${OPENVINO_LIBRARIES})

set(CMAKE_BUILD_TYPE Debug)

# Set compiler flags
if(CMAKE_C_COMPILER_ID MATCHES "Intel")
    set(CMAKE_C_FLAGS "${CMAKE_C_FLAGS} -qopenmp -O3 -mavx512f -mavx -msse3 -mavx512bw -mtune=generic -march=x86-64 -Wall -Wextra")
else()
    set(CMAKE_C_FLAGS "${CMAKE_C_FLAGS} -fopenmp -O3 -mavx512f -mavx -msse3 -mavx512bw -mtune=generic -march=x86-64 -Wall -Wextra")
endif()

# Add AddressSanitizer flags for GCC, Clang, and ICX
if(CMAKE_C_COMPILER_ID STREQUAL "GNU" OR CMAKE_C_COMPILER_ID MATCHES "Clang" OR CMAKE_C_COMPILER_ID MATCHES "Intel")
    target_compile_options(HPCChain PRIVATE -fsanitize=address -g)
    target_link_options(HPCChain PRIVATE -fsanitize=address -g)
endif()

# Print final status
message(STATUS "Configuration done. Ready to build.")

