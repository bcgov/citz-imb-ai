#include "data_structures/hash_table.h"
#include "memory_pool.h"

typedef struct tokens {
    int *token_values;
    char *word;
    int token_count;
} tokens_t;

void token_text_splitter(HashTable *table, const char *text, MemoryPool *pool);
