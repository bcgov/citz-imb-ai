#include <stdint.h>
#include <stdlib.h>
#include <string.h>
#include "datastructures/hash_table.h"

uint32_t MurmurHash3(const char* key, uint32_t len, uint32_t seed) {
    const uint32_t c1 = 0xcc9e2d51;
    const uint32_t c2 = 0x1b873593;
    const uint32_t r1 = 15;
    const uint32_t r2 = 13;
    const uint32_t m = 5;
    const uint32_t n = 0xe6546b64;

    uint32_t hash = seed;

    const int nblocks = len / 4;
    const uint32_t *blocks = (const uint32_t *)(key);
    int i;
    for (i = 0; i < nblocks; i++) {
        uint32_t k = blocks[i];

        k *= c1;
        k = (k << r1) | (k >> (32 - r1));
        k *= c2;

        hash ^= k;
        hash = (hash << r2) | (hash >> (32 - r2));
        hash = hash * m + n;
    }

    const uint8_t *tail = (const uint8_t *)(key + nblocks * 4);
    uint32_t k1 = 0;

    switch (len & 3) {
        case 3:
            k1 ^= tail[2] << 16;
        case 2:
            k1 ^= tail[1] << 8;
        case 1:
            k1 ^= tail[0];
            k1 *= c1;
            k1 = (k1 << r1) | (k1 >> (32 - r1));
            k1 *= c2;
            hash ^= k1;
    }

    hash ^= len;
    hash ^= hash >> 16;
    hash *= 0x85ebca6b;
    hash ^= hash >> 13;
    hash *= 0xc2b2ae35;
    hash ^= hash >> 16;

    return hash;
}




HashTable* create_table(size_t size) {
    HashTable *table = malloc(sizeof(HashTable));
    table->entries = malloc(sizeof(Entry*) * size);
    for (size_t i = 0; i < size; i++) {
        table->entries[i] = NULL;
    }
    return table;
}

Entry* create_entry(const char *key, const char *value) {
    Entry *entry = malloc(sizeof(Entry));
    entry->key = strdup(key);
    entry->value = strdup(value);
    entry->next = NULL;
    return entry;
}

void free_entry(Entry *entry) {
    free(entry->key);
    free(entry->value);
    free(entry);
}

void free_table(HashTable *table, size_t size) {
    for (size_t i = 0; i < size; i++) {
        Entry *entry = table->entries[i];
        while (entry != NULL) {
            Entry *temp = entry;
            entry = entry->next;
            free_entry(temp);
        }
    }
    free(table->entries);
    free(table);
}

uint32_t hash_function(const char *key) {
    return MurmurHash3(key, strlen(key), 0x9747b28c);
}

void insert(HashTable *table, const char *key, const char *value) {
    uint32_t slot = hash_function(key) % TABLE_SIZE;
    Entry *entry = table->entries[slot];
    if (entry == NULL) {
        table->entries[slot] = create_entry(key, value);
    } else {
        Entry *prev = NULL;
        while (entry != NULL) {
            if (strcmp(entry->key, key) == 0) {
                free(entry->value);
                entry->value = strdup(value);
                return;
            }
            prev = entry;
            entry = entry->next;
        }
        prev->next = create_entry(key, value);
    }
}

char* search(HashTable *table, const char *key) {
    uint32_t slot = hash_function(key) % TABLE_SIZE;
    Entry *entry = table->entries[slot];
    while (entry != NULL) {
        if (strcmp(entry->key, key) == 0) {
            return entry->value;
        }
        entry = entry->next;
    }
    return NULL;
}

void delete(HashTable *table, const char *key) {
    uint32_t slot = hash_function(key) % TABLE_SIZE;
    Entry *entry = table->entries[slot];
    Entry *prev = NULL;
    while (entry != NULL) {
        if (strcmp(entry->key, key) == 0) {
            if (prev == NULL) {
                table->entries[slot] = entry->next;
            } else {
                prev->next = entry->next;
            }
            free_entry(entry);
            return;
        }
        prev = entry;
        entry = entry->next;
    }
}
