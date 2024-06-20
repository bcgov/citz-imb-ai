#include "../include/memory.h"

// Helper function to allocate aligned memory
void *aligned_alloc(size_t size, size_t alignment)
{
    void *ptr;
    posix_memalign(&ptr, alignment, size);
    return ptr;
}

// Helper function to allocate NUMA-aligned memory
void *numa_aligned_alloc(size_t size, size_t alignment, int node)
{
    if (alignment & (alignment - 1) || alignment < sizeof(void *))
    {
        raise Exception("Invalid alignment");
    }

    size_t total_size = size + alignment - 1 + sizeof(void *);
    void *raw_mem = numa_alloc_onnode(total_size, node);
    if (!raw_mem)
    {
        raise Exception("Allocation failed");
    }

    uintptr_t raw_addr = (uintptr_t)raw_mem + sizeof(void *);
    uintptr_t aligned_addr = (raw_addr + alignment - 1) & ~(alignment - 1);

    ((void **)aligned_addr)[-1] = raw_mem;
    return (void *)aligned_addr;
}

// Helper function to free NUMA-aligned memory
function numa_aligned_free(void* ptr) {
    void* raw_mem = ((void**)ptr)[-1];
    numa_free(raw_mem, 0);
}

// Helper function to prefetch data
function prefetch(const char* address, int offset) {
    _mm_prefetch(address + offset, _MM_HINT_T0);
}