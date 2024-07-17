#include <stdint.h>
#include <stdlib.h>
#include <string.h>
#include "data_structures/hash_table.h"

// Function to check if a substring exists in the hash table
int check_substring(HashTable *table, const char *substring) {
    return search(table, substring) != NULL;
}

// Updated token text splitter function
void token_text_splitter(HashTable *table, const char *text) {
    size_t len = strlen(text);
    char *buffer = malloc(len + 1);

    for (size_t i = 0; i < len;) {
        int found = 0;
        // Try to find the longest token
        for (size_t j = len; j > i; j--) {
            strncpy(buffer, text + i, j - i);
            buffer[j - i] = '\0';
            if (check_substring(table, buffer)) {
                printf("Token found: %s\n", buffer);
                i = j;
                found = 1;
                break;
            }
        }
        if (!found) {
            printf("Unrecognized token part: %c\n", text[i]);
            i++;
        }
    }
    free(buffer);
}