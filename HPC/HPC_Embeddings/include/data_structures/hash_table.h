#define TABLE_SIZE 10000 // Adjust the table size as needed

typedef struct Entry {
    char *key;
    char *value;
    struct Entry *next;
} Entry;

typedef struct HashTable {
    Entry **entries;
} HashTable;