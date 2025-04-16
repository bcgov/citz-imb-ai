#include "../../include/thread_buffer.h"

void init_thread_buffer(ThreadBuffer *thread_buffer, int *num_threads) {
    // Determine the number of OpenMP threads and allocate an array of per-thread buffers.
    *num_threads = omp_get_max_threads();
    ThreadBuffer *thread_buffers = malloc(*num_threads * sizeof(ThreadBuffer));
    if (!thread_buffers) {
        fprintf(stderr, "Error: Cannot allocate thread_buffers\n");
        exit(EXIT_FAILURE);
    }
    for (int i = 0; i < *num_threads; i++) {
        thread_buffers[i].data = malloc(INITIAL_BUFFER_SIZE);
        if (!thread_buffers[i].data) {
            fprintf(stderr, "Error: Cannot allocate buffer for thread %d\n", i);
            exit(EXIT_FAILURE);
        }
        thread_buffers[i].used = 0;
        thread_buffers[i].capacity = INITIAL_BUFFER_SIZE;
    }
}

// Ensure the thread buffer has enough space to add additional bytes.
// If not, reallocate (in this example we double the capacity until it fits).
void ensure_capacity(ThreadBuffer *buf, size_t additional) {
    if (buf->used + additional > buf->capacity) {
        while (buf->used + additional > buf->capacity)
            buf->capacity *= 2;
        char *new_data = realloc(buf->data, buf->capacity);
        if (!new_data) {
            fprintf(stderr, "Error: Unable to reallocate thread buffer\n");
            exit(EXIT_FAILURE);
        }
        buf->data = new_data;
    }
}

// Append a block of data to the thread buffer.
void buffer_append(ThreadBuffer *buf, const char *data, size_t len) {
    ensure_capacity(buf, len);
    memcpy(buf->data + buf->used, data, len);
    buf->used += len;
}


void save_thread_buffers_to_folder(ThreadBuffer *thread_buffers, int num_threads, const char *folder_name, int rank) {
    // Create output folder
    mkdir(folder_name, 0777);

    for (int i = 0; i < num_threads; i++) {
        char filepath[512];
        snprintf(filepath, sizeof(filepath), "%s/rank_%d_thread_%d.jsonl", folder_name, rank, i);  // note: .jsonl extension

        FILE *out = fopen(filepath, "w");
        if (!out) {
            fprintf(stderr, "Error: Unable to write to file %s\n", filepath);
            free(thread_buffers[i].data);
            continue;
        }

        // Tokenize the buffer by newline and write each JSON object on its own line
        char *saveptr;
        char *line = strtok_r(thread_buffers[i].data, "\n", &saveptr);
        while (line) {
            fputs(line, out);
            fputc('\n', out);  // Add newline after each JSON object
            line = strtok_r(NULL, "\n", &saveptr);
        }

        fclose(out);
        free(thread_buffers[i].data);
    }
}

// Initialize thread buffer
void init_thread_buffer_v2(ThreadBuffer_v2 *buf, int initial_capacity) {
    buf->chunks = malloc(initial_capacity * sizeof(ChunkData));
    if (!buf->chunks) {
        fprintf(stderr, "Error: Unable to allocate chunk buffer\n");
        exit(EXIT_FAILURE);
    }
    buf->chunk_count = 0;
    buf->chunk_capacity = initial_capacity;
}

// Ensure thread buffer has enough capacity
void ensure_chunk_capacity(ThreadBuffer_v2 *buf, int additional) {
    if (buf->chunk_count + additional > buf->chunk_capacity) {
        int new_capacity = buf->chunk_capacity * 2;
        if (new_capacity < buf->chunk_count + additional)
            new_capacity = buf->chunk_count + additional + 100;
            
        ChunkData *new_chunks = realloc(buf->chunks, new_capacity * sizeof(ChunkData));
        if (!new_chunks) {
            fprintf(stderr, "Error: Unable to reallocate chunk buffer\n");
            exit(EXIT_FAILURE);
        }
        
        buf->chunks = new_chunks;
        buf->chunk_capacity = new_capacity;
    }
}

// Add a chunk to the thread buffer
void buffer_add_chunk(ThreadBuffer_v2 *buf, Section *section, int *tokens, int chunk_seq_id, int rank) {
    ensure_chunk_capacity(buf, 1);
    
    ChunkData *chunk = &buf->chunks[buf->chunk_count];
    
    // Set metadata
    snprintf(chunk->chunk_id, sizeof(chunk->chunk_id), "%s-chunk-%s-%04d",
             section->act_title ? section->act_title : "Unknown",
             section->reg_title ? section->reg_title : "",
             section->title ? section->title : "Unknown",
             chunk_seq_id);
             
    chunk->chunk_seq_id = chunk_seq_id;
    strncpy(chunk->act_id, section->act_title ? section->act_title : "", sizeof(chunk->act_id)-1);
    strncpy(chunk->reg_title, section->reg_title ? section->reg_title : "", sizeof(chunk->reg_title)-1);
    strncpy(chunk->section_number, section->number ? section->number : "", sizeof(chunk->section_number)-1);
    strncpy(chunk->section_title, section->title ? section->title : "", sizeof(chunk->section_title)-1);
    strncpy(chunk->section_url, section->section_url ? section->section_url : "", sizeof(chunk->section_url)-1);
    strncpy(chunk->url, section->url ? section->url : "", sizeof(chunk->url)-1);
    chunk->source_rank = rank;
    
    // Copy tokens
    memcpy(chunk->tokens, tokens, TOKEN_CHUNK_SIZE * sizeof(int));
    
    // Initialize embeddings to zeros
    memset(chunk->embedding, 0, EMBEDDING_SIZE * sizeof(float));
    
    buf->chunk_count++;
}

// Modified save function to store chunk data
void save_openvino_format_to_dram_v2(Section *section, TokenizedData *tokens, int rank, int tid, ThreadBuffer_v2 *thread_buffer)
{
    for (int i = 0; i < tokens->chunk_count; i++)
    {
        buffer_add_chunk(thread_buffer, section, tokens->token_chunks[i], i, rank);
    }
}

// Function to save to JSONL format
void save_thread_buffers_to_folder_v2(ThreadBuffer_v2 *thread_buffers, int num_threads, const char *folder_name, int rank) {
    // Create output folder
    mkdir(folder_name, 0777);
    
    for (int t = 0; t < num_threads; t++) {
        char filepath[512];
        snprintf(filepath, sizeof(filepath), "%s/rank_%d_thread_%d.jsonl", folder_name, rank, t);
        
        FILE *out = fopen(filepath, "w");
        if (!out) {
            fprintf(stderr, "Error: Unable to write to file %s\n", filepath);
            continue;
        }
        
        // Create JSON objects and write them to file
        ThreadBuffer_v2 *buf = &thread_buffers[t];
        for (int i = 0; i < buf->chunk_count; i++) {
            ChunkData *chunk = &buf->chunks[i];
            
            // Create JSON object
            json_object *obj = json_object_new_object();
            
            // Add metadata
            json_object_object_add(obj, "chunk_id", json_object_new_string(chunk->chunk_id));
            json_object_object_add(obj, "chunk_seq_id", json_object_new_int(chunk->chunk_seq_id));
            json_object_object_add(obj, "act_id", json_object_new_string(chunk->act_id));
            json_object_object_add(obj, "reg_title", json_object_new_string(chunk->reg_title));
            json_object_object_add(obj, "section_number", json_object_new_string(chunk->section_number));
            json_object_object_add(obj, "section_title", json_object_new_string(chunk->section_title));
            json_object_object_add(obj, "section_url", json_object_new_string(chunk->section_url));
            json_object_object_add(obj, "url", json_object_new_string(chunk->url));
            json_object_object_add(obj, "source_rank", json_object_new_int(chunk->source_rank));
            
            // Add tokens
            json_object *tokens_array = json_object_new_array();
            for (int j = 0; j < TOKEN_CHUNK_SIZE; j++) {
                json_object_array_add(tokens_array, json_object_new_int(chunk->tokens[j]));
            }
            json_object_object_add(obj, "tokens", tokens_array);
            
            // Add embeddings
            json_object *embedding_array = json_object_new_array();
            for (int j = 0; j < EMBEDDING_SIZE; j++) {
                json_object_array_add(embedding_array, json_object_new_double(chunk->embedding[j]));
            }
            json_object_object_add(obj, "embedding", embedding_array);
            
            // Write to file
            const char *json_str = json_object_to_json_string(obj);
            fprintf(out, "%s\n", json_str);
            
            // Free JSON object
            json_object_put(obj);
        }
        
        fclose(out);
    }
    
    // Free buffers
    for (int t = 0; t < num_threads; t++) {
        free(thread_buffers[t].chunks);
    }
    free(thread_buffers);
}
