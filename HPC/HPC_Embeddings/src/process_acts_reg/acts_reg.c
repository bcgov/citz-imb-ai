#include "../include/acts_reg.h"
#include <sched.h>
#include "token_text_splitter.h"
#include "memory_pool.h"
#include <json-c/json.h>
#include <mpi.h>
#include <string.h>

#include <fcntl.h>
#include <unistd.h>

#define DEST_RANK 2
#define TAG_LENGTH 0
#define TAG_DATA 1

// Helper macro for safely adding JSON strings
#define ADD_JSON_STRING(obj, key, value) \
    json_object_object_add(obj, key, json_object_new_string((value) ? value : ""))

json_object *build_section_json(Section *section, TokenizedData *tokens, int rank)
{
    if (!section)
    {
        fprintf(stderr, "Error: Section pointer is NULL\n");
        return NULL;
    }

    json_object *json_section = json_object_new_object();
    if (!json_section)
    {
        fprintf(stderr, "Error: Failed to create JSON object\n");
        return NULL;
    }

    // Add section fields to JSON object
    ADD_JSON_STRING(json_section, "act_title", section->act_title);
    ADD_JSON_STRING(json_section, "reg_title", section->reg_title);
    ADD_JSON_STRING(json_section, "title", section->title);
    ADD_JSON_STRING(json_section, "content", section->content);
    ADD_JSON_STRING(json_section, "url", section->url);
    ADD_JSON_STRING(json_section, "section_url", section->section_url);
    ADD_JSON_STRING(json_section, "section_number", section->number);
    json_object_object_add(json_section, "source_rank", json_object_new_int(rank));

    // Add tokens to JSON object
    json_object *json_tokens = json_object_new_array();
    for (int i = 0; i < tokens->word_count; i++)
    {
        json_object *json_token = json_object_new_object();
        json_object_object_add(json_token, "word", json_object_new_string(tokens->words[i]));

        json_object *json_values = json_object_new_array();
        for (int j = 0; j < tokens->token_counts[i]; j++)
        {
            json_object_array_add(json_values, json_object_new_int(tokens->token_values[i][j]));
        }
        json_object_object_add(json_token, "token_values", json_values);
        json_object_array_add(json_tokens, json_token);
    }
    json_object_object_add(json_section, "tokens", json_tokens);

    // Add 255-token chunks to JSON object
    json_object *json_chunks = json_object_new_array();
    for (int i = 0; i < tokens->chunk_count; i++)
    {
        json_object *json_chunk = json_object_new_array();
        for (int j = 0; j < 255; j++)
        {
            json_object_array_add(json_chunk, json_object_new_int(tokens->token_chunks[i][j]));
        }
        json_object_array_add(json_chunks, json_chunk);
    }
    json_object_object_add(json_section, "token_chunks", json_chunks);

    return json_section;
}


// Define initial per-thread buffer size (here 100MB)
#define INITIAL_BUFFER_SIZE (100 * 1024 * 1024)

typedef struct {
    char *data;        // Pointer to the allocated buffer
    size_t used;       // Bytes used so far
    size_t capacity;   // Total capacity of this buffer
} ThreadBuffer;

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

void save_section_as_json_to_dram(Section *section, TokenizedData *tokens, int rank, int tid, ThreadBuffer *thread_buffers)
{
    printf("This is thread %d\n", tid);

    json_object *json_section = build_section_json(section, tokens, rank);
    if (!json_section)
        return;

    // Convert to string and store or print
    const char *json_str = json_object_to_json_string(json_section);
    size_t json_str_len = strlen(json_str);

    // Example: Print or save to file
    //printf("Thread %d JSON: %s\n", tid, json_str);
    buffer_append(thread_buffers, json_str, json_str_len);
    buffer_append(thread_buffers, "\n", 1);

    // Cleanup
    json_object_put(json_section);
}

void save_openvino_format_to_dram(Section *section, TokenizedData *tokens, int rank, int tid, ThreadBuffer *openvino_buffers)
{
    for (int i = 0; i < tokens->chunk_count; i++)
    {
        json_object *chunk_obj = json_object_new_object();
        
        // Create a unique chunk_id
        char chunk_id[512];
        snprintf(chunk_id, sizeof(chunk_id), "%s-chunk-%s-%04d", 
                 section->act_title ? section->act_title : "Unknown",
                 section->reg_title ? section->reg_title : "",
                 section->title ? section->title : "Unknown", 
                 i);
        
        // Add all metadata
        json_object_object_add(chunk_obj, "chunk_id", json_object_new_string(chunk_id));
        json_object_object_add(chunk_obj, "chunk_seq_id", json_object_new_int(i));
        json_object_object_add(chunk_obj, "act_id", json_object_new_string(section->act_title ? section->act_title : ""));
        json_object_object_add(chunk_obj, "reg_title", json_object_new_string(section->reg_title ? section->reg_title : ""));
        //json_object_object_add(chunk_obj, "section_id", json_object_new_string(section->section_id ? section->section_id : ""));
        json_object_object_add(chunk_obj, "section_number", json_object_new_string(section->number ? section->number : ""));
        json_object_object_add(chunk_obj, "section_title", json_object_new_string(section->title ? section->title : ""));
        json_object_object_add(chunk_obj, "section_url", json_object_new_string(section->section_url ? section->section_url : ""));
        json_object_object_add(chunk_obj, "url", json_object_new_string(section->url ? section->url : ""));
        json_object_object_add(chunk_obj, "source_rank", json_object_new_int(rank));
        
        // Add tokens array
        json_object *tokens_array = json_object_new_array();
        for (int j = 0; j < 255; j++) {
            json_object_array_add(tokens_array, json_object_new_int(tokens->token_chunks[i][j]));
        }
        json_object_object_add(chunk_obj, "tokens", tokens_array);
        
        // Convert to string and append to buffer
        const char *json_str = json_object_to_json_string(chunk_obj);
        size_t json_str_len = strlen(json_str);
        buffer_append(openvino_buffers, json_str, json_str_len);
        buffer_append(openvino_buffers, "\n", 1);
        
        // Free the JSON object
        json_object_put(chunk_obj);
    }
}


void send_section_as_json(Section *section, TokenizedData *tokens, int rank)
{
    json_object *json_section = build_section_json(section, tokens, rank);
    if (!json_section)
        return;

    const char *json_str = json_object_to_json_string(json_section);
    int str_len = strlen(json_str);

    int mpi_err = MPI_Send(&str_len, 1, MPI_INT, DEST_RANK, TAG_LENGTH, MPI_COMM_WORLD);
    if (mpi_err != MPI_SUCCESS)
    {
        fprintf(stderr, "Error: Failed to send JSON string length (MPI_Send)\n");
        json_object_put(json_section);
        return;
    }

    mpi_err = MPI_Send(json_str, str_len, MPI_CHAR, DEST_RANK, TAG_DATA, MPI_COMM_WORLD);
    if (mpi_err != MPI_SUCCESS)
    {
        fprintf(stderr, "Error: Failed to send JSON string (MPI_Send)\n");
    }

    json_object_put(json_section);
}

void send_thread_buffers_as_json(ThreadBuffer *thread_buffers, int num_threads, int rank) {
    size_t total_len = 2; // [ and ]
    for (int i = 0; i < num_threads; i++) {
        total_len += thread_buffers[i].used + 2; // comma + newline safety
    }

    char *json_array = malloc(total_len + 1);
    if (!json_array) {
        fprintf(stderr, "Memory allocation failed\n");
        return;
    }

    strcpy(json_array, "[\n");

    for (int i = 0; i < num_threads; i++) {
        if (i > 0) strcat(json_array, ",\n");
        strncat(json_array, thread_buffers[i].data, thread_buffers[i].used);
        free(thread_buffers[i].data);
    }

    strcat(json_array, "\n]");

    int json_len = strlen(json_array);
    int mpi_err;

    mpi_err = MPI_Send(&json_len, 1, MPI_INT, DEST_RANK, TAG_LENGTH, MPI_COMM_WORLD);
    if (mpi_err != MPI_SUCCESS) {
        fprintf(stderr, "Error sending length\n");
        free(json_array);
        return;
    }

    mpi_err = MPI_Send(json_array, json_len, MPI_CHAR, DEST_RANK, TAG_DATA, MPI_COMM_WORLD);
    if (mpi_err != MPI_SUCCESS) {
        fprintf(stderr, "Error sending JSON data\n");
    }

    free(json_array);
    free(thread_buffers);
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

    free(thread_buffers);
}

void process_acts_reg(char *directory_path, int print_outputs, HashTable *table, bool act_reg)
{
    printf("Processing %s from %s\n", (act_reg) ? "Regulation" : "Acts", directory_path);
    // Initialize streaming context

    if (!directory_path)
    {
        printf("No input file provided\n");
        return;
    }
    printf("calling json");
    directory_info_t dir_info;

    init_dram_data(directory_path, &dir_info);
    printf("Directory info initialized. Number of files: %zu\n", dir_info.num_files);
    MemoryPool *pool = create_pool(POOL_SIZE);

    int rank;
    MPI_Comm_rank(MPI_COMM_WORLD, &rank);

    int total_sections = 0;

    // Determine the number of OpenMP threads and allocate an array of per-thread buffers.
    int num_threads = omp_get_max_threads();
    ThreadBuffer *thread_buffers = malloc(num_threads * sizeof(ThreadBuffer));
    if (!thread_buffers) {
        fprintf(stderr, "Error: Cannot allocate thread_buffers\n");
        exit(EXIT_FAILURE);
    }
    for (int i = 0; i < num_threads; i++) {
        thread_buffers[i].data = malloc(INITIAL_BUFFER_SIZE);
        if (!thread_buffers[i].data) {
            fprintf(stderr, "Error: Cannot allocate buffer for thread %d\n", i);
            exit(EXIT_FAILURE);
        }
        thread_buffers[i].used = 0;
        thread_buffers[i].capacity = INITIAL_BUFFER_SIZE;
    }

#pragma omp parallel for schedule(dynamic, 1)
    for (size_t i = 0; i < dir_info.num_files; i++)
    {
        printf("File name or act: %s\n", dir_info.files[i].filename);

        int num_sections;
        Section *sections = extract_sections_from_memory(dir_info.files[i].buffer, dir_info.files[i].filesize, &num_sections, print_outputs);

        if (sections)
        {
            for (int j = 0; j < num_sections; j++)
            {
                if (sections[j].title && sections[j].content)
                {
                    total_sections += 1;
                    // token_text_splitter(table, sections[j].content, pool);

                    TokenizedData tokens = token_text_splitter(table, sections[j].content, pool);

                    // Retrieve the thread's buffer and append JSON data.
                    int tid = omp_get_thread_num();
                    //save_section_as_json_to_dram(&sections[j], &tokens, rank, tid, &thread_buffers[tid]);
                    save_openvino_format_to_dram(&sections[j], &tokens, rank, tid, &thread_buffers[tid]);
                    
                    #pragma omp critical
                    {
                        // printf("Rank %d sending section with title: %s\n", rank, mpi_section.section_title);
                        //send_section_as_json(&sections[j], &tokens, rank);
                    }

                    // Free tokens memory
                    for (int i = 0; i < tokens.word_count; i++)
                    {
                        free(tokens.words[i]);
                        free(tokens.token_values[i]);
                    }
                    free(tokens.words);
                    free(tokens.token_values);
                    free(tokens.token_counts);
                    // Free flattened_tokens
                    if (tokens.flattened_tokens)
                    {
                        free(tokens.flattened_tokens);
                    }

                    // Free token_chunks
                    if (tokens.token_chunks)
                    {
                        for (int i = 0; i < tokens.chunk_count; i++)
                        {
                            free(tokens.token_chunks[i]);
                        }
                        free(tokens.token_chunks);
                    }
                }
            }
            free_sections(sections, num_sections);
        }
    }
    printf("total sections is %d \n", total_sections);
    
    save_thread_buffers_to_folder(thread_buffers, num_threads, "consol_42", rank);
    //send_thread_buffers_as_json(thread_buffers, num_threads,rank);

    // Merge the per-thread buffers by writing them to a single output file.
    /*
    FILE *out = fopen("output.json", "w");
    if (out) {
        for (int i = 0; i < num_threads; i++) {
            fwrite(thread_buffers[i].data, 1, thread_buffers[i].used, out);
            free(thread_buffers[i].data);
        }
        fclose(out);
    } else {
        fprintf(stderr, "Error: Unable to open output file\n");
    }
    free(thread_buffers);
    */

    destroy_pool(pool);
    // At program end
    xmlCleanupParser();
    xmlMemoryDump();
    // Free all the memory
    free_dram_data(&dir_info);
}