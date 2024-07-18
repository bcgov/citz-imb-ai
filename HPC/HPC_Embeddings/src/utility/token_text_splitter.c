#include <stdint.h>
#include <stdlib.h>
#include <string.h>
#include <stdio.h>
#include <ctype.h>
#include "token_text_splitter.h"

// Function to check if a substring exists in the hash table
char *check_substring(HashTable *table, const char *substring) {
    char *result;
    #pragma omp critical
    {
        result =  search(table, substring);
    }

    return result;
}

// Convert a string to lowercase
void to_lowercase(char *str) {
    for (; *str; ++str) {
        *str = tolower((unsigned char)*str);
    }
}

tokens_t get_token(HashTable *table, const char *text) {
    size_t len = strlen(text);
    char *buffer = malloc(len + 1);
    char *prefix_buffer = malloc(len + 3); // Additional space for "##"
    tokens_t token_result;
    token_result.token_values = malloc((len + 1) * sizeof(int));
    token_result.word = strdup(text); // Copy the original word
    token_result.token_count = 0;

    if (buffer == NULL || prefix_buffer == NULL || token_result.token_values == NULL || token_result.word == NULL) {
        perror("Failed to allocate memory");
        exit(EXIT_FAILURE);
    }

    for (size_t i = 0; i < len;) {
        int found = 0;
        // Try to find the longest token
        for (size_t j = len - i; j > 0; j--) {
            strncpy(buffer, text + i, j);
            buffer[j] = '\0';
            to_lowercase(buffer);

            char *key_found = check_substring(table, buffer);
            if (key_found) {
                token_result.token_values[token_result.token_count++] = atoi(key_found);
                i += j;
                found = 1;

                // Check if there's remaining text to be matched as a subword
                if (i < len && text[i] != ' ') {
                    size_t remaining_len = len - i;
                    for (size_t k = remaining_len; k > 0; k--) {
                        strncpy(buffer, text + i, k);
                        buffer[k] = '\0';
                        to_lowercase(buffer);

                        snprintf(prefix_buffer, k + 3, "##%s", buffer);

                        key_found = check_substring(table, prefix_buffer);
                        if (key_found) {
                            token_result.token_values[token_result.token_count++] = atoi(key_found);
                            i += k;
                            break;
                        }
                    }
                }

                break;
            }
        }

        if (!found) {
            printf("Unrecognized token part: %c\n", text[i]);
            i++;
        }
    }

    free(buffer);
    free(prefix_buffer);

    return token_result;
}

// Function to split text into words
void split_text_to_words(const char *text, char ***words, int *word_count) {
    char *text_copy = strdup(text);
    if (text_copy == NULL) {
        perror("Failed to duplicate text");
        exit(EXIT_FAILURE);
    }
    char *token = strtok(text_copy, " ");
    int count = 0;
    char **result = NULL;

    while (token) {
        char **temp = realloc(result, sizeof(char *) * (count + 1));
        if (temp == NULL) {
            // Handle memory allocation failure
            for (int i = 0; i < count; i++) {
                free(result[i]);
            }
            free(result);
            free(text_copy);
            *words = NULL;
            *word_count = 0;
            perror("Failed to reallocate memory");
            exit(EXIT_FAILURE);
        }
        result = temp;
        result[count] = strdup(token);
        if (result[count] == NULL) {
            perror("Failed to duplicate token");
            exit(EXIT_FAILURE);
        }
        count++;
        token = strtok(NULL, " ");
    }

    *words = result;
    *word_count = count;

    free(text_copy);
}

// Function to split text into tokens and process them
void token_text_splitter(HashTable *table, const char *text) {
    char **words;
    int word_count;

    split_text_to_words(text, &words, &word_count);

    for (int i = 0; i < word_count; i++) {
        tokens_t token = get_token(table, words[i]);
        printf("Original word: %s\n", token.word);
        printf("Token count: %d\n", token.token_count);
        printf("Token values: ");
        for (int j = 0; j < token.token_count; j++) {
            printf("%d ", token.token_values[j]);
        }
        printf("\n");

        free(token.token_values);
        free(token.word);
    }

    for (int i = 0; i < word_count; i++) {
        free(words[i]);
    }
    free(words);
}
