#include "../include/acts_reg.h"
#include "token_text_splitter.h"
#include "../include/json_format.h"
#include <sched.h>
#include "memory_pool.h"
#include <json-c/json.h>
#include <mpi.h>
#include <string.h>

#include <fcntl.h>
#include <unistd.h>

#define DEST_RANK 2
#define TAG_LENGTH 0
#define TAG_DATA 1

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

void process_acts_reg(legislation *item, int print_output, HashTable *table, int num_threads, ThreadBuffer *thread_buffers, MemoryPool *pool)
{
    //printf("Processing %s from %s\n", (act_reg) ? "Regulation" : "Acts", directory_path);
    // Initialize streaming context
    const char *directory_path = item->source_path;
    const char *dest_path = item->destination_path;

    if (!directory_path) {
        fprintf(stderr, "Error: No input file (source_path) provided in legislation struct\n");
        return;
    }

    if (!directory_path)
    {
        printf("No input file provided\n");
        return;
    }
    printf("calling json");
    directory_info_t dir_info;

    init_dram_data(directory_path, &dir_info);
    printf("Directory info initialized. Number of files: %zu\n", dir_info.num_files);

    int rank;
    MPI_Comm_rank(MPI_COMM_WORLD, &rank);

    int total_sections = 0;

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
    
    save_thread_buffers_to_folder(thread_buffers, num_threads, dest_path, rank);
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

    // At program end
    xmlCleanupParser();
    xmlMemoryDump();
    // Free all the memory
    free_dram_data(&dir_info);
}