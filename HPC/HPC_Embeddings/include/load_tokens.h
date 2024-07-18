#include "data_structures/hash_table.h"

size_t count_lines(const char *filename);
void load_tokens(HashTable *table, const char *filename);
HashTable *load_tokens_and_store(const char *file);
