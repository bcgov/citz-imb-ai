#ifndef TEXT_SPLITTER_H
#define TEXT_SPLITTER_H

#include <immintrin.h>
#include <stdio.h>
#include <string.h>
#include <stdlib.h>
#include <stddef.h>
#include <stdbool.h>

typedef struct {
    char **chunks;
    size_t count;
} SplitChunk_t;

typedef struct {
    size_t chunk_size;
    size_t chunk_overlap;
    size_t (*length_function)(const char *);
    const char **delimeters;
    size_t delimeter_count;
} RecursiveCharacterTextSplitter_t;

void recursive_character_split(const char *text, int start, int end, const RecursiveCharacterTextSplitter_t *splitter, SplitChunk_t *results);
void free_split_result(SplitChunk_t *result);
RecursiveCharacterTextSplitter_t *init_text_splitter_params(const char **separators, size_t separator_count, size_t chunk_size, size_t chunk_overlap);
void* aligned_alloc(size_t size, size_t alignment);
void* numa_aligned_alloc(size_t size, size_t alignment, int node);
void numa_aligned_free(void* ptr);
void prefetch(const char* address, int offset);
bool match_delimiter(const char* text, int position, const char* delimiter);
void append_to_results(SplitChunk_t *results, const char *substring, size_t length);

#endif // TEXT_SPLITTER_H
