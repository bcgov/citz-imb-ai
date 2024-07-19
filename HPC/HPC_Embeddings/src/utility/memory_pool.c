#include "memory_pool.h"

MemoryPool *create_pool(size_t size) {
    MemoryPool *pool = (MemoryPool *)malloc(sizeof(MemoryPool));
    pool->pool = (char *)malloc(size);
    pool->size = size;
    pool->used = 0;
    pthread_mutex_init(&pool->lock, NULL);
    return pool;
}

void *pool_alloc(MemoryPool *pool, size_t size) {
    pthread_mutex_lock(&pool->lock);
    if (pool->used + size > pool->size) {
        pthread_mutex_unlock(&pool->lock);
        return NULL; // Not enough space
    }
    void *ptr = pool->pool + pool->used;
    pool->used += size;
    pthread_mutex_unlock(&pool->lock);
    return ptr;
}

void destroy_pool(MemoryPool *pool) {
    pthread_mutex_destroy(&pool->lock);
    free(pool->pool);
    free(pool);
}

// Utility function to duplicate a string using a memory pool
char *pool_strdup(MemoryPool *pool, const char *source) {
    size_t length = strlen(source) + 1;
    char *copy = (char *)pool_alloc(pool, length);
    if (copy == NULL) {
        perror("Failed to allocate memory from pool");
        exit(EXIT_FAILURE);
    }
    memcpy(copy, source, length);
    return copy;
}
