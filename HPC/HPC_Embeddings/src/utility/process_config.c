#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <json-c/json.h>
#include "process_config.h"

void process_config_file(const char *config_path, process_files *config) {
    FILE *file = fopen(config_path, "r");
    if (!file) {
        fprintf(stderr, "Error: Could not open config file: %s\n", config_path);
        exit(EXIT_FAILURE);
    }

    fseek(file, 0, SEEK_END);
    long file_size = ftell(file);
    rewind(file);

    char *buffer = malloc(file_size + 1);
    if (!buffer) {
        fclose(file);
        fprintf(stderr, "Error: Memory allocation failed for config buffer\n");
        exit(EXIT_FAILURE);
    }

    fread(buffer, 1, file_size, file);
    buffer[file_size] = '\0';
    fclose(file);

    struct json_object *root = json_tokener_parse(buffer);
    free(buffer);

    if (!root) {
        fprintf(stderr, "Error: Failed to parse JSON config\n");
        exit(EXIT_FAILURE);
    }

    // Parse token_file
    struct json_object *processing_options;
    if (!json_object_object_get_ex(root, "processing_options", &processing_options)) {
        fprintf(stderr, "Error: Missing 'processing_options' section\n");
        json_object_put(root);
        exit(EXIT_FAILURE);
    }

    struct json_object *token_file_obj;
    if (!json_object_object_get_ex(processing_options, "token_file", &token_file_obj)) {
        fprintf(stderr, "Error: Missing 'token_file' in processing_options\n");
        json_object_put(root);
        exit(EXIT_FAILURE);
    }

    const char *token_file = json_object_get_string(token_file_obj);
    config->token_file_path = strdup(token_file);  // caller must free

    // Parse acts array
    struct json_object *acts_array;
    if (!json_object_object_get_ex(root, "acts", &acts_array)) {
        fprintf(stderr, "Error: Missing 'acts' array in config\n");
        json_object_put(root);
        exit(EXIT_FAILURE);
    }

    int num_acts = json_object_array_length(acts_array);
    config->num_of_files = num_acts;
    config->properties = malloc(sizeof(legislation *) * num_acts);
    if (!config->properties) {
        fprintf(stderr, "Error: Failed to allocate properties array\n");
        json_object_put(root);
        exit(EXIT_FAILURE);
    }

    for (int i = 0; i < num_acts; i++) {
        struct json_object *act_obj = json_object_array_get_idx(acts_array, i);

        legislation *entry = malloc(sizeof(legislation));
        memset(entry, 0, sizeof(legislation));  // safety

        struct json_object *val;

        if (json_object_object_get_ex(act_obj, "date", &val)) {
            entry->date = strdup(json_object_get_string(val));
        }
        if (json_object_object_get_ex(act_obj, "source_path", &val)) {
            entry->source_path = strdup(json_object_get_string(val));
        }
        if (json_object_object_get_ex(act_obj, "destination_path", &val)) {
            entry->destination_path = strdup(json_object_get_string(val));
        }
        if (json_object_object_get_ex(act_obj, "base_url", &val)) {
            entry->base_url = strdup(json_object_get_string(val));
        }

        // Optional: if you want to support regulations too
        entry->type = 'A';  // Default to Act
        if (json_object_object_get_ex(act_obj, "type", &val)) {
            const char *type_str = json_object_get_string(val);
            if (type_str && strcmp(type_str, "regulation") == 0) {
                entry->type = 'R';
            }
        }

        config->properties[i] = entry;
    }

    json_object_put(root);
}

void free_process_files(process_files *config) {
    for (int i = 0; i < config->num_of_files; i++) {
        legislation *entry = config->properties[i];
        free(entry->date);
        free(entry->source_path);
        free(entry->destination_path);
        free(entry->base_url);
        free(entry);
    }
    free(config->properties);
    free(config->token_file_path);
}
