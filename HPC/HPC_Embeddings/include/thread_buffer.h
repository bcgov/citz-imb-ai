#include <string.h>
#include <stdlib.h>
#include <stdio.h>
#include <sys/stat.h>  // For mkdir
#include <sys/types.h> // For mode_t used by mkdir
#include "xml_parser.h"
#include "token_text_splitter.h"
#include <json-c/json.h>

// Define initial per-thread buffer size (here 100MB)
#define INITIAL_BUFFER_SIZE (100 * 1024 * 1024)

typedef struct {
    char *data;        // Pointer to the allocated buffer
    size_t used;       // Bytes used so far
    size_t capacity;   // Total capacity of this buffer
} ThreadBuffer;


// Define our token chunk size
#define TOKEN_CHUNK_SIZE 255
#define EMBEDDING_SIZE 384

// Custom chunk data structure
typedef struct {
    char chunk_id[512];
    int chunk_seq_id;
    char act_id[256];
    char reg_title[256];
    char section_number[64];
    char section_title[256];
    char section_url[256];
    char url[512];
    int source_rank;
    int tokens[TOKEN_CHUNK_SIZE];
    float embedding[EMBEDDING_SIZE];
} ChunkData;

// Modified thread buffer to store ChunkData structures
typedef struct {
    ChunkData *chunks;       // Array of chunk data
    int chunk_count;         // Number of chunks stored
    int chunk_capacity;      // Capacity of chunk array
} ThreadBuffer_v2;

void init_thread_buffer(ThreadBuffer *thread_buffer);

void ensure_capacity(ThreadBuffer *buf, size_t additional);

// Append a block of data to the thread buffer.
void buffer_append(ThreadBuffer *buf, const char *data, size_t len);

void save_thread_buffers_to_folder(ThreadBuffer *thread_buffers, int num_threads, const char *folder_name, int rank);

// Initialize thread buffer
void init_thread_buffer(ThreadBuffer_v2 *buf, int initial_capacity);

// Ensure thread buffer has enough capacity
void ensure_chunk_capacity(ThreadBuffer_v2 *buf, int additional);

// Add a chunk to the thread buffer
void buffer_add_chunk(ThreadBuffer_v2 *buf, Section *section, int *tokens, int chunk_seq_id, int rank);

// Modified save function to store chunk data
void save_openvino_format_to_dram_v2(Section *section, TokenizedData *tokens, int rank, int tid, ThreadBuffer_v2 *thread_buffer);

void save_thread_buffers_to_folder_v2(ThreadBuffer_v2 *thread_buffers, int num_threads, const char *folder_name, int rank);
