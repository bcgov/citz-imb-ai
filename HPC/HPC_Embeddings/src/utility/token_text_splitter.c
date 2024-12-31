#include <stdint.h>
#include <stdlib.h>
#include <string.h>
#include <stdio.h>
#include <ctype.h>
#include "token_text_splitter.h"
#include "memory_pool.h"
#include <immintrin.h>
#include <stdbool.h>

void removeWhitespace(char *input)
{
    char *output = input;
    char *temp = input;

    while (*temp != '\0')
    {
        if (!isspace((unsigned char)*temp))
        {
            *output = *temp;
            output++;
        }
        temp++;
    }
    *output = '\0';
}

// Function to check if a substring exists in the hash table
char *check_substring(HashTable *table, const char *substring)
{
    char *result;
    removeWhitespace(substring);
    // printf("The sub_string is %s\n", substring);
    result = search(table, substring);
    // printf("The result is %s\n", result);
    return result;
}

// Convert a string to lowercase
void to_lowercase(char *str)
{
    for (; *str; ++str)
    {
        *str = tolower((unsigned char)*str);
    }
}

/**
 * Converts all uppercase characters in the input string to lowercase using AVX-512 instructions.
 * The function processes the input string in chunks of 64 bytes for efficient SIMD operations.
 *
 * @param str The input string to be converted to lowercase.
 * @return The input string with all uppercase characters converted to lowercase.
 */
char *to_lowercase_avx512(char *str, size_t len)
{
    // size_t len = strlen(str); // Get the length of the input string
    size_t i = 0; // Initialize index to traverse the string

    // Create a 512-bit mask with each byte set to 0x20 (32 in decimal)
    // This is used to convert uppercase letters to lowercase by adding 32 to their ASCII values
    __m512i mask_uppercase = _mm512_set1_epi8(0x20);

    // Create 512-bit vectors with each byte set to 'A' (65) and 'Z' (90) respectively
    // These are used to identify uppercase letters within the range 'A' to 'Z'
    __m512i lower_limit = _mm512_set1_epi8('A');
    __m512i upper_limit = _mm512_set1_epi8('Z');

    // Process the string in chunks of 64 bytes
    while (i + 64 <= len)
    {
        // Load 64 bytes of the string into an AVX-512 register
        __m512i chunk = _mm512_loadu_si512((__m512i *)(str + i));

        // Create a mask where each bit is set if the corresponding byte is less than or equal to 'Z'
        __mmask64 mask = _mm512_cmple_epu8_mask(chunk, upper_limit);

        // Update the mask to only include bytes that are greater than or equal to 'A'
        mask &= _mm512_cmpge_epu8_mask(chunk, lower_limit);

        // Conditionally add 32 to bytes that are uppercase letters to convert them to lowercase
        __m512i result = _mm512_mask_add_epi8(chunk, mask, chunk, mask_uppercase);

        // Store the result back into the string
        _mm512_storeu_si512((__m512i *)(str + i), result);

        // Move to the next 64-byte chunk
        i += 64;
    }

    // Handle any remaining characters that were not processed in the 64-byte chunks
    for (; i < len; i++)
    {
        // Convert individual uppercase characters to lowercase
        if (str[i] >= 'A' && str[i] <= 'Z')
        {
            str[i] = str[i] + 32;
        }
    }

    // Return the modified string
    return str;
}

// Create a lookup table for punctuation characters
const char punctuation_lookup[256] = {
    ['!'] = 1,
    ['"'] = 1,
    ['#'] = 1,
    ['$'] = 1,
    ['%'] = 1,
    ['&'] = 1,
    ['\''] = 1,
    ['('] = 1,
    [')'] = 1,
    ['*'] = 1,
    ['+'] = 1,
    [','] = 1,
    ['-'] = 1,
    ['.'] = 1,
    ['/'] = 1,
    [':'] = 1,
    [';'] = 1,
    ['<'] = 1,
    ['='] = 1,
    ['>'] = 1,
    ['?'] = 1,
    ['@'] = 1,
    ['['] = 1,
    ['\\'] = 1,
    [']'] = 1,
    ['^'] = 1,
    ['_'] = 1,
    ['`'] = 1,
    ['{'] = 1,
    ['|'] = 1,
    ['}'] = 1,
    ['~'] = 1,
};

// Helper function to identify punctuation using SIMD
void mark_punctuation_avx512(const char *str, size_t len, char *punctuation_mask)
{
    // Process the string in chunks of 64 bytes
    size_t i = 0;
    while (i + 64 <= len)
    {
        // Load 64 bytes of the input string into an AVX-512 register
        __m512i chunk = _mm512_loadu_si512((__m512i *)(str + i));

        // Initialize a mask to store the result of punctuation checking
        __mmask64 is_punct = 0;

        // Check each byte in the chunk to see if it is a punctuation character
        for (int j = 0; j < 64; j++)
        {
            char c = ((char *)&chunk)[j];
            if (punctuation_lookup[(unsigned char)c])
            {
                is_punct |= (1ULL << j); // Set the corresponding bit in the mask
            }
        }

        // Store 1s in punctuation_mask where is_punct is true (indicating punctuation)
        _mm512_mask_storeu_epi8(punctuation_mask + i, is_punct, _mm512_set1_epi8(1));

        // Store 0s in punctuation_mask where is_punct is false (indicating non-punctuation)
        _mm512_mask_storeu_epi8(punctuation_mask + i, ~is_punct, _mm512_set1_epi8(0));

        // Move to the next 64-byte chunk
        i += 64;
    }

    // Handle any remaining characters that were not processed in the 64-byte chunks
    for (; i < len; i++)
    {
        punctuation_mask[i] = ispunct(str[i]) ? 1 : 0;
    }
}

// Function to split punctuations and convert to lowercase
char *split_punctuations_and_to_lowercase(const char *str)
{
    size_t len = strlen(str);

    // Allocate memory for the mutable copy of the input string
    char *lower_str = (char *)malloc(len + 1);
    if (!lower_str)
    {
        return NULL; // Memory allocation failed
    }
    strcpy(lower_str, str);

    // Convert to lowercase
    to_lowercase_avx512(lower_str, len);

    // Allocate memory for the punctuation mask
    char *punctuation_mask = (char *)malloc(len);
    if (!punctuation_mask)
    {
        free(lower_str);
        return NULL; // Memory allocation failed
    }

    // Mark punctuation positions
    mark_punctuation_avx512(lower_str, len, punctuation_mask);

    // Calculate the new length of the string considering added spaces
    size_t new_len = len;
    for (size_t i = 0; i < len; i++)
    {
        if (punctuation_mask[i])
        {
            new_len += 2; // Add space before and after punctuation
        }
    }
    printf("word is %s, total len is %d \n", lower_str, new_len);

    // Allocate memory for the new string
    char *result = (char *)malloc(new_len + 1);
    if (!result)
    {
        free(lower_str);
        free(punctuation_mask);
        return NULL; // Memory allocation failed
    }

    // Build the new string
    size_t i = 0, j = 0;
    while (i < len)
    {
        char ch = lower_str[i];
        if (punctuation_mask[i])
        {
            result[j++] = ' ';
            result[j++] = ch;
            result[j++] = ' ';
        }
        else
        {
            result[j++] = ch;
        }
        i++;
    }

    result[new_len] = '\0'; // Null-terminate the new string

    // Free allocated memory
    free(lower_str);
    free(punctuation_mask);

    return result;
}

tokens_t get_token(HashTable *table, const char *text)
{
    size_t len = strlen(text);
    char *buffer = malloc(len + 1);
    char *prefix_buffer = malloc(len + 3);
    tokens_t token_result;
    token_result.token_values = malloc((len + 1) * sizeof(int));
    token_result.word = strdup(text);
    token_result.token_count = 0;

    if (buffer == NULL || prefix_buffer == NULL || token_result.token_values == NULL || token_result.word == NULL)
    {
        perror("Failed to allocate memory");
        free(buffer);
        free(prefix_buffer);
        free(token_result.token_values);
        free(token_result.word);
        exit(EXIT_FAILURE);
    }
    // printf("The word is %s \n", text);
    bool prefix = false;
    for (size_t i = 0; i < len;)
    {
        int found = 0;
        for (size_t j = len - i; j > 0; j--)
        {
            strncpy(buffer, text + i, j);
            buffer[j] = '\0';

            if (isdigit((unsigned char)*buffer) || !prefix)
            {
                snprintf(prefix_buffer, j + 1, "%s", buffer);
            }
            else
            {
                snprintf(prefix_buffer, j + 3, "##%s", buffer);
            }

            char *key_found = check_substring(table, prefix_buffer);

            if (key_found)
            {
                token_result.token_values[token_result.token_count++] = atoi(key_found);
                prefix = !isdigit((unsigned char)*buffer); // Reset prefix for numbers
                i += j;
                found = true;
                break;
            }
        }
        if (!found)
        {
            printf("Unrecognized token part: %c\n", text[i]);
            i++;
            prefix = false;
        }
    }

    free(buffer);
    free(prefix_buffer);

    return token_result;
}

// handle remaining characters
void less_than_64_bytes_extract_words(size_t len, char *text_copy, char *token_start, int *count, char **result, MemoryPool *pool)
{
    for (size_t i = 0; i < len; i++)
    {
        if (text_copy[i] == ' ')
        {
            text_copy[i] = '\0';
            char **temp = realloc(result, sizeof(char *) * (*count + 1));
            if (temp == NULL)
            {
                perror("Failed to reallocate memory");
                exit(EXIT_FAILURE);
            }
            result = temp;
            result[*count] = pool_strdup(pool, token_start);
            if (result[*count] == NULL)
            {
                perror("Failed to duplicate token");
                exit(EXIT_FAILURE);
            }
            *count++;
            token_start = text_copy + i + 1;
        }
    }
    // Add the last token if there's any remaining text
    if (*token_start != '\0')
    {
        char **temp = realloc(result, sizeof(char *) * (*count + 1));
        if (temp == NULL)
        {
            perror("Failed to reallocate memory");
            exit(EXIT_FAILURE);
        }
        result = temp;
        result[*count] = pool_strdup(pool, token_start);
        if (result[*count] == NULL)
        {
            perror("Failed to duplicate token");
            exit(EXIT_FAILURE);
        }
        *count++;
    }
}

void split_text_to_words(const char *text, char ***words, int *word_count, MemoryPool *pool)
{
    size_t len = strlen(text);
    char *text_copy = pool_strdup(pool, text);
    if (text_copy == NULL)
    {
        perror("Failed to duplicate text");
        exit(EXIT_FAILURE);
    }

    char *token_start = text_copy;
    int count = 0;
    char **result = NULL;

    // Handle case where text length is less than 64 bytes
    if (len < 64)
    {
        // less_than_64_bytes_extract_words(len, text_copy, token_start, &count, result, pool);
        for (size_t i = 0; i < len; i++)
        {
            if (text_copy[i] == ' ')
            {
                text_copy[i] = '\0';
                char **temp = realloc(result, sizeof(char *) * (count + 1));
                if (temp == NULL)
                {
                    perror("Failed to reallocate memory");
                    exit(EXIT_FAILURE);
                }
                result = temp;
                result[count] = pool_strdup(pool, token_start);
                if (result[count] == NULL)
                {
                    perror("Failed to duplicate token");
                    exit(EXIT_FAILURE);
                }
                count++;
                token_start = text_copy + i + 1;
            }
        }
        // Add the last token if there's any remaining text
        if (*token_start != '\0')
        {
            char **temp = realloc(result, sizeof(char *) * (count + 1));
            if (temp == NULL)
            {
                perror("Failed to reallocate memory");
                exit(EXIT_FAILURE);
            }
            result = temp;
            result[count] = pool_strdup(pool, token_start);
            if (result[count] == NULL)
            {
                perror("Failed to duplicate token");
                exit(EXIT_FAILURE);
            }
            count++;
        }
    }
    else
    {
        size_t i;
        for (i = 0; i + 64 <= len; i += 64)
        {
            __m512i chunk = _mm512_loadu_si512((const __m512i *)(text_copy + i));
            __mmask64 space_mask = _mm512_cmpeq_epi8_mask(chunk, _mm512_set1_epi8(' '));

            while (space_mask)
            {
                int space_idx = __builtin_ctzll(space_mask);
                space_mask &= space_mask - 1;

                text_copy[i + space_idx] = '\0';
                char **temp = realloc(result, sizeof(char *) * (count + 1));
                if (temp == NULL)
                {
                    perror("Failed to reallocate memory");
                    exit(EXIT_FAILURE);
                }
                result = temp;
                result[count] = pool_strdup(pool, token_start);
                if (result[count] == NULL)
                {
                    perror("Failed to duplicate token");
                    exit(EXIT_FAILURE);
                }
                count++;
                token_start = text_copy + i + space_idx + 1;
            }
        }

        // Handle remaining characters
        for (; i < len; i++)
        {
            if (text_copy[i] == ' ')
            {
                text_copy[i] = '\0';
                char **temp = realloc(result, sizeof(char *) * (count + 1));
                if (temp == NULL)
                {
                    perror("Failed to reallocate memory");
                    exit(EXIT_FAILURE);
                }
                result = temp;
                result[count] = pool_strdup(pool, token_start);
                if (result[count] == NULL)
                {
                    perror("Failed to duplicate token");
                    exit(EXIT_FAILURE);
                }
                count++;
                token_start = text_copy + i + 1;
            }
        }

        // Add the last token if there's any remaining text
        if (*token_start != '\0')
        {
            char **temp = realloc(result, sizeof(char *) * (count + 1));
            if (temp == NULL)
            {
                perror("Failed to reallocate memory");
                exit(EXIT_FAILURE);
            }
            result = temp;
            result[count] = pool_strdup(pool, token_start);
            if (result[count] == NULL)
            {
                perror("Failed to duplicate token");
                exit(EXIT_FAILURE);
            }
            count++;
        }
    }

    *words = result;
    *word_count = count;
}

// Function to split text into tokens and return them
TokenizedData token_text_splitter(HashTable *table, const char *text, MemoryPool *pool)
{
    TokenizedData result;
    result.words = NULL;
    result.token_values = NULL;
    result.token_counts = NULL;
    result.word_count = 0;

    char **words;
    int word_count;

    char *processed_buffer = split_punctuations_and_to_lowercase(text);
    split_text_to_words(processed_buffer, &words, &word_count, pool);

    // Allocate memory for the tokenized data
    result.words = (char **)malloc(word_count * sizeof(char *));
    result.token_values = (int **)malloc(word_count * sizeof(int *));
    result.token_counts = (int *)malloc(word_count * sizeof(int));
    result.word_count = word_count;

    for (int i = 0; i < word_count; i++)
    {
        tokens_t token = get_token(table, words[i]);

        // Store the word and its tokens
        result.words[i] = strdup(words[i]); // Copy the word
        result.token_counts[i] = token.token_count;

        // Allocate memory for token values and copy them
        result.token_values[i] = (int *)malloc(token.token_count * sizeof(int));
        for (int j = 0; j < token.token_count; j++)
        {
            result.token_values[i][j] = token.token_values[j];
        }

        // Free memory allocated in get_token
        free(token.token_values);
        free(token.word);
    }

    // Free intermediate buffers
    free(words);
    free(processed_buffer);

    return result;
}
