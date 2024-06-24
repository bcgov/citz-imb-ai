#include "../include/text_splitter.h"
#include <stdlib.h>
#include <stdio.h>
#include <string.h>
#include <stdbool.h>
#include <immintrin.h>

// Function to initialize the text splitter parameters
RecursiveCharacterTextSplitter_t *init_text_splitter_params(const char **separators, size_t separator_count, size_t chunk_size, size_t chunk_overlap)
{
    RecursiveCharacterTextSplitter_t *splitter = malloc(sizeof(RecursiveCharacterTextSplitter_t));
    splitter->delimeters = separators;
    splitter->delimeter_count = separator_count;
    splitter->chunk_size = chunk_size;
    splitter->chunk_overlap = chunk_overlap;
    return splitter;
}

// Constants
#define SIMD_WIDTH 64 // 512-bit AVX-512 registers (64 bytes)
#define PREFETCH_DISTANCE 2 * SIMD_WIDTH

// Iterative function to split text using character delimiters
void recursive_character_split(const char *text, int start, int end, const RecursiveCharacterTextSplitter_t *splitter, SplitChunk_t *results)
{
    // Stack structure to hold function call parameters
    typedef struct {
        int start;
        int end;
    } StackFrame;

    // Allocate the stack
    StackFrame *stack = malloc((end - start + 1) * sizeof(StackFrame));
    if (!stack) {
        fprintf(stderr, "Memory allocation failed\n");
        exit(EXIT_FAILURE);
    }

    int top = -1;
    stack[++top] = (StackFrame){start, end};

    // Initialize results if necessary
    if (results->chunks == NULL) {
        results->chunks = NULL;
        results->count = 0;
    }

    // Loop until stack is empty
    while (top >= 0) {
        StackFrame frame = stack[top--];
        start = frame.start;
        end = frame.end;

        if (start >= end)
            continue;

        RecursiveCharacterTextSplitter_t *default_splitter = NULL;
        if (!splitter) {
            // Create a default splitter
            default_splitter = init_text_splitter_params((const char *[]){"\n\n", "\n", "\t", ". "}, 3, 1024, 128);
            splitter = default_splitter;
        }

        // Loop through the text using AVX-512 for faster processing using SIMD
        int i = start;
        while (i <= (end - SIMD_WIDTH)) {
            _mm_prefetch(&text[i + PREFETCH_DISTANCE], _MM_HINT_T0); // Prefetch the next SIMD_WIDTH bytes

            // Load the SIMD_WIDTH bytes into a 512-bit register
            __m512i textVector = _mm512_loadu_si512(&text[i]);

            // Loop through the delimiters to check if the current character is a delimiter
            for (int d = 0; d < splitter->delimeter_count; d++) {
                const char *delimiter = splitter->delimeters[d];
                int delimiterLength = strlen(delimiter);

                // Create a vector with the delimiter character in all positions
                __m512i delimiterVector = _mm512_set1_epi8(delimiter[0]);

                // Compare the textVector with the delimiterVector
                __mmask64 comparisonMask = _mm512_cmpeq_epi8_mask(textVector, delimiterVector);

                // Check if any of the characters in the textVector match the first character of the delimiter
                if (comparisonMask != 0) {
                    for (int k = 0; k < SIMD_WIDTH; k++) {
                        if (comparisonMask & (1ULL << k)) {
                            // Verify the entire delimiter matches
                            if (match_delimiter(text, i + k, delimiter)) {
                                // Extract the substring up to the delimiter
                                int chunkEnd = (i + k + delimiterLength < end) ? i + k + delimiterLength : end;
                                size_t length = chunkEnd - start;
                                append_to_results(results, &text[start], length);

                                // Push the remaining text after the delimiter onto the stack
                                stack[++top] = (StackFrame){chunkEnd, end};
                                i = chunkEnd; // Update i to avoid infinite loop
                                goto next_iteration;
                            }
                        }
                    }
                }
            }

            // Move to the next block of text, considering chunk overlap
            i += splitter->chunk_size - splitter->chunk_overlap;
        }

        // Process any remaining characters that were not handled by AVX-512
        for (int j = i; j < end; j++) {
            for (int d = 0; d < splitter->delimeter_count; d++) {
                const char *delimiter = splitter->delimeters[d];
                if (match_delimiter(text, j, delimiter)) {
                    // Extract the substring up to the delimiter
                    int chunkEnd = (j + strlen(delimiter) < end) ? j + strlen(delimiter) : end;
                    size_t length = chunkEnd - start;
                    append_to_results(results, &text[start], length);

                    // Push the remaining text after the delimiter onto the stack
                    stack[++top] = (StackFrame){chunkEnd, end};
                    j = chunkEnd; // Update j to avoid infinite loop
                    goto next_iteration;
                }
            }
        }

    next_iteration:
        // Continue with the next stack frame
        if (splitter == default_splitter) {
            free(default_splitter);
            splitter = NULL;
        }
    }

    free(stack);
}

// Free the split result
void free_split_result(SplitChunk_t *result)
{
    if (result->chunks) {
        for (size_t i = 0; i < result->count; i++) {
            free(result->chunks[i]);
        }
        free(result->chunks);
    }
}

// Helper function to match a delimiter
bool match_delimiter(const char *text, int position, const char *delimiter)
{
    int len = strlen(delimiter);
    for (int i = 0; i < len; i++) {
        if (text[position + i] != delimiter[i]) {
            return false;
        }
    }
    return true;
}

// Helper function to append a substring to results array
void append_to_results(SplitChunk_t *results, const char *substring, size_t length)
{
    // Allocate memory for the new substring, adding 1 for the null terminator
    char *new_substring = malloc(length + 1);
    if (!new_substring) {
        // Handle memory allocation failure
        fprintf(stderr, "Memory allocation failed\n");
        exit(EXIT_FAILURE);
    }

    // Copy the substring and add the null terminator
    strncpy(new_substring, substring, length);
    new_substring[length] = '\0';

    // Reallocate memory for the results array to hold the new substring
    results->chunks = realloc(results->chunks, (results->count + 1) * sizeof(char *));
    if (!results->chunks) {
        // Handle memory allocation failure
        fprintf(stderr, "Memory allocation failed\n");
        exit(EXIT_FAILURE);
    }

    // Add the new substring to the results array
    results->chunks[results->count] = new_substring;
    results->count++;
}

