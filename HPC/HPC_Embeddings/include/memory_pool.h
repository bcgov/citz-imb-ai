#ifndef MEMORY_POOL
#define MEMORY_POOL

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <pthread.h>
#include <omp.h>

#define POOL_SIZE 1024 * 1024 * 1024 // 1 MB memory pool

typedef struct MemoryPool {
    char *pool;
    size_t size;
    size_t used;
    pthread_mutex_t lock;
} MemoryPool;

void *pool_alloc(MemoryPool *pool, size_t size);
MemoryPool *create_pool(size_t size);
void destroy_pool(MemoryPool *pool);
char *pool_strdup(MemoryPool *pool, const char *source);

#endif
