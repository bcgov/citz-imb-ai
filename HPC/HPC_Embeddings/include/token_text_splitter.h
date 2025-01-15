#include "data_structures/hash_table.h"
#include "memory_pool.h"

typedef struct tokens {
    int *token_values;
    char *word;
    int token_count;
} tokens_t;

// In token_text_splitter.h
typedef struct {
    int* values;
    int count;
} TokenArray;

typedef struct {
    TokenArray* arrays;
    int num_arrays;
    int total_tokens;
    int capacity;  // Track capacity separately
} TokenCollection;

typedef struct {
    char **words;
    int **token_values;  // 2D array for token values
    int *token_counts;   // Array to store the number of tokens per word
    int word_count;

    int *flattened_tokens; // Flattened array of all tokens
    int flattened_count;   // Total number of tokens in the flattened array

    int **token_chunks;    // E.g Array of 255-token chunks
    int chunk_count;       // Number of chunks
} TokenizedData;

//void token_text_splitter(HashTable *table, const char *text, MemoryPool *pool);

TokenizedData token_text_splitter(HashTable *table, const char *text, MemoryPool *pool);

// Function to create and initialize a TokenCollection
TokenCollection* create_token_collection(int initial_capacity);

// Function to add a token array to the collection
void add_token_array(TokenCollection* collection, int* values, int count);

// Function to free a TokenCollection
void free_token_collection(TokenCollection* collection);

