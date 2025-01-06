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

void send_section_as_json(Section *section, TokenizedData *tokens, int rank)
{
    if (!section)
    {
        fprintf(stderr, "Error: Section pointer is NULL\n");
        return;
    }

    json_object *json_section = json_object_new_object();
    if (!json_section)
    {
        fprintf(stderr, "Error: Failed to create JSON object\n");
        return;
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

        // Add word
        json_object_object_add(json_token, "word", json_object_new_string(tokens->words[i]));

        // Add token values as an array
        json_object *json_values = json_object_new_array();
        for (int j = 0; j < tokens->token_counts[i]; j++)
        {
            json_object_array_add(json_values, json_object_new_int(tokens->token_values[i][j]));
        }
        json_object_object_add(json_token, "token_values", json_values);

        // Add the token object to the tokens array
        json_object_array_add(json_tokens, json_token);
    }

    // Add the tokens array to the main JSON object
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

    // Add the chunks array to the main JSON object
    json_object_object_add(json_section, "token_chunks", json_chunks);

    // Convert to string and send via MPI
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

    // Clean up
    json_object_put(json_section);
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
#pragma omp critical
                    {
                        // printf("Rank %d sending section with title: %s\n", rank, mpi_section.section_title);
                        send_section_as_json(&sections[j], &tokens, rank);
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
    destroy_pool(pool);
    // At program end
    xmlCleanupParser();
    xmlMemoryDump();
    // Free all the memory
    free_dram_data(&dir_info);
}
