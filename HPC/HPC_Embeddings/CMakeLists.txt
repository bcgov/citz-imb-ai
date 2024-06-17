cmake_minimum_required(VERSION 3.10)

project(HPC_Embeddings C)  # Ensure the project name is valid for CMake

# Set the compiler to icx if available, otherwise fall back to gcc
find_program(MPICC_EXECUTABLE NAMES mpicc)
if(MPICC_EXECUTABLE)
    set(CMAKE_C_COMPILER ${MPICC_EXECUTABLE})
else()
    set(CMAKE_C_COMPILER gcc)
endif()

# Find MPI package
find_package(MPI REQUIRED)
if (MPI_FOUND)
    include_directories(SYSTEM ${MPI_INCLUDE_PATH})
    set(CMAKE_C_COMPILER ${MPI_C_COMPILER})
endif()

# Find libxml2 package
find_package(LibXml2 REQUIRED)
if (LIBXML2_FOUND)
    include_directories(${LIBXML2_INCLUDE_DIR})
endif()

# Include directories
include_directories(include)

# Add source directories
add_subdirectory(src/acts)
add_subdirectory(src/regulations)
add_subdirectory(src/utility)

# Collect all source files from subdirectories
set(SOURCES ${ACTS_SOURCES} ${REGULATIONS_SOURCES} ${UTILITY_SOURCES})

# Add the main source file
list(APPEND SOURCES src/main.c)

# Add the executable
add_executable(HPCChain ${SOURCES})
