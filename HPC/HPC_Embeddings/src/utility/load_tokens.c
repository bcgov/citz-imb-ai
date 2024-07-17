#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "data_structures/hash_table.h"

size_t count_lines(const char *filename) {
    FILE *file = fopen(filename, "r");
    if (!file) {
        perror("Could not open file");
        exit(EXIT_FAILURE);
    }

    size_t lines = 0;
    char ch;
    while ((ch = fgetc(file)) != EOF) {
        if (ch == '\n') {
            lines++;
        }
    }

    fclose(file);
    return lines;
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

// Function to load tokens from a text file
void load_tokens(HashTable *table, const char *filename) {
    FILE *file = fopen(filename, "r");
    if (!file) {
        perror("Could not open file");
        exit(EXIT_FAILURE);
    }

    char line[256];
    while (fgets(line, sizeof(line), file)) {
        char *token = strtok(line, " \t\n");
        if (!token) continue;

        char *key = strdup(token);
        token = strtok(NULL, " \t\n");
        if (!token) continue;

        char *value = strdup(token);
        insert(table, key, value);

        free(key);
        free(value);
    }

    fclose(file);
}

HashTable *load_tokens_and_store(const char *filename) {
    // Count the number of lines in the token file
    size_t line_count = count_lines(filename);

    // Create a hash table with a size based on the line count
    HashTable *table = create_table(line_count);

    // Load the tokens into the hash table
    load_tokens(table, filename);

    // Print the contents of the hash table
    for (size_t i = 0; i < table->size; i++) {
        Entry *entry = table->entries[i];
        while (entry != NULL) {
            printf("%s: %s\n", entry->key, entry->value);
            entry = entry->next;
        }
    }

    return table;
}