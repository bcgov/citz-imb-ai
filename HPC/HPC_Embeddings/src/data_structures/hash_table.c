#include <stdint.h>
#include <stdlib.h>
#include <string.h>
#include <immintrin.h>
#include "data_structures/hash_table.h"

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

// Function to create a hash table with a specified size
HashTable* create_table(size_t size) {
    HashTable *table = malloc(sizeof(HashTable));
    table->size = size;
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

void free_table(HashTable *table) {
    for (size_t i = 0; i < table->size; i++) {
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
    uint32_t slot = hash_function(key) % table->size;
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

char* search22(HashTable *table, const char *key) {
    uint32_t slot = hash_function(key) % table->size;
    Entry *entry = table->entries[slot];
    while (entry != NULL) {
        if (strcmp(entry->key, key) == 0) {
            return entry->value;
        }
        entry = entry->next;
    }
    return NULL;
}


// SIMD-optimized string comparison using AVX-512
static inline int simd_strcmp(const char *s1, const char *s2) {
    size_t len1 = strlen(s1);
    size_t len2 = strlen(s2);

    // Fallback to regular strcmp for short strings
    if (len1 < 64 || len2 < 64) {
        return strcmp(s1, s2);
    }

    while (1) {
        __m512i chunk1 = _mm512_loadu_si512((const __m512i *)s1);
        __m512i chunk2 = _mm512_loadu_si512((const __m512i *)s2);

        __mmask64 cmp_mask = _mm512_cmpeq_epi8_mask(chunk1, chunk2);
        
        if (cmp_mask != 0xFFFFFFFFFFFFFFFF) { // Not all bytes are equal
            int first_diff = __builtin_ctzll(~cmp_mask);
            return (unsigned char)s1[first_diff] - (unsigned char)s2[first_diff];
        }

        // Check if we hit a null character in s1 or s2
        __mmask64 null_mask1 = _mm512_test_epi8_mask(chunk1, _mm512_set1_epi8('\0'));
        __mmask64 null_mask2 = _mm512_test_epi8_mask(chunk2, _mm512_set1_epi8('\0'));
        if (null_mask1 || null_mask2) {
            // If both strings are equal up to their lengths, we consider them equal
            if (len1 == len2) {
                return 0;
            } else {
                return (len1 < len2) ? -1 : 1;
            }
        }

        s1 += 64;
        s2 += 64;
    }
}

char* search(HashTable *table, const char *key) {
    uint32_t slot = hash_function(key) % table->size;
    Entry *entry = table->entries[slot];
    while (entry != NULL) {
        if (simd_strcmp(entry->key, key) == 0) {
            return entry->value;
        }
        entry = entry->next;
    }
    return NULL;
}

void delete(HashTable *table, const char *key) {
    uint32_t slot = hash_function(key) % table->size;
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
