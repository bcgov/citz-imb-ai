#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "data_structures/hash_table.h"
#include <immintrin.h>

// Function to count the number of lines in a file using AVX-512 intrinsics
size_t count_lines(const char *filename) {
    FILE *file = fopen(filename, "r");
    if (!file) {
        perror("Could not open file");
        exit(EXIT_FAILURE);
    }
    printf("counting lines \n");
    size_t lines = 0;
    const size_t buffer_size = 1024;
    char buffer[buffer_size];

    __m512i newline = _mm512_set1_epi8('\n');
    while (!feof(file)) {
        size_t bytes_read = fread(buffer, 1, buffer_size, file);
        if (bytes_read == 0) {
            break;
        }

        size_t i = 0;
        for (; i + 63 < bytes_read; i += 64) {
            __m512i data = _mm512_loadu_si512((__m512i*)(buffer + i));
            __mmask64 cmp_mask = _mm512_cmpeq_epu8_mask(data, newline);
            lines += _mm_popcnt_u64(cmp_mask);
        }

        // Handle the remaining bytes
        for (; i < bytes_read; i++) {
            if (buffer[i] == '\n') {
                lines++;
            }
        }
    }

    fclose(file);
    return lines;
}

// Function to load tokens from a text file
void load_tokens(HashTable *table, const char *filename) {
    FILE *file = fopen(filename, "r");
    if (!file) {
        perror("Could not open file");
        exit(EXIT_FAILURE);
    }

    char line[256];
    size_t line_number = 0;
    while (fgets(line, sizeof(line), file)) {
        // Remove trailing newline or carriage return characters
        line[strcspn(line, "\r\n")] = 0;

        if (line[0] == '\0') {
            fprintf(stderr, "Error: Empty line at line number %zu\n", line_number);
            line_number++;
            continue;
        }

        char *key = strdup(line);
        if (!key) {
            fprintf(stderr, "Error: Memory allocation failed for line number %zu\n", line_number);
            line_number++;
            continue;
        }

        // Convert line number to string
        char value[20];
        snprintf(value, sizeof(key), "%zu", line_number);

        insert(table, key, value);
	free(key);
	key = NULL;
        line_number++;
    }

    fclose(file);
}

HashTable *load_tokens_and_store(const char *filename) {
    // Count the number of lines in the token file
    size_t line_count = count_lines(filename);
    printf("The line count is %zu \n", line_count);

    // Create a hash table with a size based on the line count
    HashTable *table = create_table(line_count);

    // Load the tokens into the hash table
    load_tokens(table, filename);

    // Print the contents of the hash table
    /*
    for (size_t i = 0; i < table->size; i++) {
        Entry *entry = table->entries[i];
        while (entry != NULL) {
            printf("%s: %s\n", entry->key, entry->value);
            entry = entry->next;
        }
    }
    */
    // search table
    /*
     char *test = "hello";
     char *data = search(table, test);
     if (data) {
	printf("The key is %s \n", data);
     } else {
        printf("hash did not find any data %s \n", test);
    }
    */
    //free to debug the hash table
    printf("Free the hash table \n");
    return table;
}
