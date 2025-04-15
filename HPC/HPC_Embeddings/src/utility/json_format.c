#include "json_format.h"

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
