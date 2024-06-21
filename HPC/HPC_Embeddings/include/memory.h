#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>
#include <numa.h>
#include <numaif.h>
#include <sched.h>
#include <immintrin.h>  // For AVX-512 intrinsics


void * aligned_alloc(size_t size, size_t alignment);
void* numa_aligned_alloc(size_t size, size_t alignment, int node);
void numa_aligned_free(void* ptr);
void prefetch(const char* address, int offset);

void set_affinity_to_socket(int socket);
void set_memory_policy_to_socket(int socket); 
