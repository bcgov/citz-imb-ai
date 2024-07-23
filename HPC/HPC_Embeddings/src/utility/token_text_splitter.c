#include <stdint.h>
#include <stdlib.h>
#include <string.h>
#include <stdio.h>
#include <ctype.h>
#include "token_text_splitter.h"
#include "memory_pool.h"
#include <immintrin.h>

// Function to check if a substring exists in the hash table
char *check_substring(HashTable *table, const char *substring) {
    char *result;
    result =  search(table, substring);

    return result;
}

// Convert a string to lowercase
void to_lowercase(char *str) {
    for (; *str; ++str) {
        *str = tolower((unsigned char)*str);
    }
}

char *to_lowercase_avx512(char *str) {
    size_t len = strlen(str);
    size_t i = 0;
    __m512i mask_uppercase = _mm512_set1_epi8(0x20); // Mask to convert uppercase to lowercase
    __m512i lower_limit = _mm512_set1_epi8('A');
    __m512i upper_limit = _mm512_set1_epi8('Z');

    while (i + 64 <= len) {
        __m512i chunk = _mm512_loadu_si512((__m512i *)(str + i));
        __mmask64 mask = _mm512_cmplt_epu8_mask(chunk, upper_limit);
        mask &= _mm512_cmpge_epu8_mask(chunk, lower_limit);
        __m512i result = _mm512_mask_add_epi8(chunk, mask, chunk, mask_uppercase);
        _mm512_storeu_si512((__m512i *)(str + i), result);
        i += 64;
    }

    // Handle remaining characters
    for (; i < len; i++) {
        if (str[i] >= 'A' && str[i] <= 'Z') {
            str[i] = str[i] + 32;
        }
    }

    return str;
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
            to_lowercase_avx512(buffer);

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
                        to_lowercase_avx512(buffer);

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
void split_text_to_words2(const char *text, char ***words, int *word_count, MemoryPool *pool) {
     //printf("%s ", text);
    //return;
	char *text_copy;
	text_copy = pool_strdup(pool, text);
    if (text_copy == NULL) {
        perror("Failed to duplicate text");
        exit(EXIT_FAILURE);
    }
    char *token = strtok(text_copy, " ");
    int count = 0;
    char **result = NULL;

    while (token) {
	char **temp;
	temp = realloc(result, sizeof(char *) * (count + 1));
        if (temp == NULL) {
            // Handle memory allocation failure
            for (int i = 0; i < count; i++) {
                free(result[i]);
            }
            free(result);
            //free(text_copy);
            *words = NULL;
            *word_count = 0;
            perror("Failed to reallocate memory");
            exit(EXIT_FAILURE);
        }
        result = temp;
	result[count] = pool_strdup(pool, token);
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


// handle remaining characters
void less_than_64_bytes_extract_words(size_t len, char *text_copy, char *token_start, int *count,  char **result, MemoryPool *pool) {
        for (size_t i = 0; i < len; i++) {
            if (text_copy[i] == ' ') {
                text_copy[i] = '\0';
                char **temp = realloc(result, sizeof(char *) * (*count + 1));
                if (temp == NULL) {
                    perror("Failed to reallocate memory");
                    exit(EXIT_FAILURE);
                }
                result = temp;
                result[*count] = pool_strdup(pool, token_start);
                if (result[*count] == NULL) {
                    perror("Failed to duplicate token");
                    exit(EXIT_FAILURE);
                }
                *count++;
                token_start = text_copy + i + 1;
            }
        }
        // Add the last token if there's any remaining text
        if (*token_start != '\0') {
            char **temp = realloc(result, sizeof(char *) * (*count + 1));
            if (temp == NULL) {
                perror("Failed to reallocate memory");
                exit(EXIT_FAILURE);
            }
            result = temp;
            result[*count] = pool_strdup(pool, token_start);
            if (result[*count] == NULL) {
                perror("Failed to duplicate token");
                exit(EXIT_FAILURE);
            }
            *count++;
        }
}

void split_text_to_words(const char *text, char ***words, int *word_count, MemoryPool *pool) {
    size_t len = strlen(text);
    char *text_copy = pool_strdup(pool, text);
    if (text_copy == NULL) {
        perror("Failed to duplicate text");
        exit(EXIT_FAILURE);
    }

    char *token_start = text_copy;
    int count = 0;
    char **result = NULL;

    // Handle case where text length is less than 64 bytes
    if (len < 64) {
	//less_than_64_bytes_extract_words(len, text_copy, token_start, &count, result, pool);
        for (size_t i = 0; i < len; i++) {
            if (text_copy[i] == ' ') {
                text_copy[i] = '\0';
                char **temp = realloc(result, sizeof(char *) * (count + 1));
                if (temp == NULL) {
                    perror("Failed to reallocate memory");
                    exit(EXIT_FAILURE);
                }
                result = temp;
                result[count] = pool_strdup(pool, token_start);
                if (result[count] == NULL) {
                    perror("Failed to duplicate token");
                    exit(EXIT_FAILURE);
                }
                count++;
                token_start = text_copy + i + 1;
            }
        }
        // Add the last token if there's any remaining text
        if (*token_start != '\0') {
            char **temp = realloc(result, sizeof(char *) * (count + 1));
            if (temp == NULL) {
                perror("Failed to reallocate memory");
                exit(EXIT_FAILURE);
            }
            result = temp;
            result[count] = pool_strdup(pool, token_start);
            if (result[count] == NULL) {
                perror("Failed to duplicate token");
                exit(EXIT_FAILURE);
            }
            count++;
        }
    } else {
	    size_t i;
	    for (i = 0; i + 64 <= len; i += 64) {
		__m512i chunk = _mm512_loadu_si512((const __m512i *)(text_copy + i));
		__mmask64 space_mask = _mm512_cmpeq_epi8_mask(chunk, _mm512_set1_epi8(' '));

		while (space_mask) {
		    int space_idx = __builtin_ctzll(space_mask);
		    space_mask &= space_mask - 1;

		    text_copy[i + space_idx] = '\0';
		    char **temp = realloc(result, sizeof(char *) * (count + 1));
		    if (temp == NULL) {
			perror("Failed to reallocate memory");
			exit(EXIT_FAILURE);
		    }
		    result = temp;
		    result[count] = pool_strdup(pool, token_start);
		    if (result[count] == NULL) {
			perror("Failed to duplicate token");
			exit(EXIT_FAILURE);
		    }
		    count++;
		    token_start = text_copy + i + space_idx + 1;
		}
	    }

	    // Handle remaining characters
	    for (; i < len; i++) {
		if (text_copy[i] == ' ') {
		    text_copy[i] = '\0';
		    char **temp = realloc(result, sizeof(char *) * (count + 1));
		    if (temp == NULL) {
			perror("Failed to reallocate memory");
			exit(EXIT_FAILURE);
		    }
		    result = temp;
		    result[count] = pool_strdup(pool, token_start);
		    if (result[count] == NULL) {
			perror("Failed to duplicate token");
			exit(EXIT_FAILURE);
		    }
		    count++;
		    token_start = text_copy + i + 1;
		}
	    }

	    // Add the last token if there's any remaining text
	    if (*token_start != '\0') {
		char **temp = realloc(result, sizeof(char *) * (count + 1));
		if (temp == NULL) {
		    perror("Failed to reallocate memory");
		    exit(EXIT_FAILURE);
		}
		result = temp;
		result[count] = pool_strdup(pool, token_start);
		if (result[count] == NULL) {
		    perror("Failed to duplicate token");
		    exit(EXIT_FAILURE);
		}
		count++;
	    }
    }

    *words = result;
    *word_count = count;
}


// Function to split text into tokens and process them
void token_text_splitter(HashTable *table, const char *text, MemoryPool *pool) {
    char **words;
    int word_count;
    //printf("%s \n", text);
    split_text_to_words(text, &words, &word_count, pool);
    for (int i = 0; i < word_count; i++) {
        tokens_t token = get_token(table, words[i]);
        //printf("Original word: %s\n", token.word);
        //printf("Token count: %d\n", token.token_count);
        //printf("Token values: ");
        //for (int j = 0; j < token.token_count; j++) {
        //    printf("%d ", token.token_values[j]);
        //}
        //printf("\n");

        free(token.token_values);
        free(token.word);
    }

    //for (int i = 0; i < word_count; i++) {
    //    free(words[i]);
   // }
    free(words);
}
