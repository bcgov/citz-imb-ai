cmake_minimum_required(VERSION 3.10)

project(HPC_Embeddings C)

# Set the compiler to icx if available, otherwise fall back to gcc
find_program(ICX_EXECUTABLE NAMES icx)
if(ICX_EXECUTABLE)
    set(CMAKE_C_COMPILER ${ICX_EXECUTABLE})
    message(STATUS "Found ICX compiler: ${ICX_EXECUTABLE}")
else()
    set(CMAKE_C_COMPILER gcc)
    message(WARNING "ICX compiler not found, falling back to GCC")
endif()

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

# Link MPI and libxml2 libraries
target_link_libraries(HPCChain MPI::MPI_C ${LIBXML2_LIBRARIES})

# Add AddressSanitizer flags for GCC, Clang, and ICX
if(CMAKE_C_COMPILER_ID STREQUAL "GNU" OR CMAKE_C_COMPILER_ID MATCHES "Clang" OR CMAKE_C_COMPILER_ID STREQUAL "IntelLLVM")
    target_compile_options(HPCChain PRIVATE -fsanitize=address -g)
    target_link_options(HPCChain PRIVATE -fsanitize=address)
endif()

# Print final status
message(STATUS "Configuration done. Ready to build.")

