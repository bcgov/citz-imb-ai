#ifndef HASH_TABLE
#define HASH_TABLE

#define TABLE_SIZE 10000 // Adjust the table size as needed

typedef struct Entry {
    char *key;
    char *value;
    struct Entry *next;
} Entry;

typedef struct HashTable {
    Entry **entries;
    size_t size;
} HashTable;

HashTable* create_table(size_t size);
void insert(HashTable *table, const char *key, const char *value);
char* search(HashTable *table, const char *key);
void delete(HashTable *table, const char *key);
void free_table(HashTable *table);
#endif
