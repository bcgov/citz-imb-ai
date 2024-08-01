#include "../include/acts_reg.h"
#include <sched.h>
#include "token_text_splitter.h"
#include "memory_pool.h"
#include <json-c/json.h>

int call_json(Section *section) {
	    // Create a root JSON object
    json_object *root = json_object_new_object();

    // Add a string item
    json_object_object_add(root, "act title", json_object_new_string(section->act_title));
    if (section->reg_title) {
	    json_object_object_add(root, "reg title", json_object_new_string(section->reg_title));
	}
    json_object_object_add(root, "sec title", json_object_new_string(section->title));
    json_object_object_add(root, "sec title", json_object_new_string(section->content));

    // Add a number item
    //json_object_object_add(root, "age", json_object_new_int(30));

    // Add a boolean item
    //json_object_object_add(root, "is_student", json_object_new_boolean(0));

    // Add an array
    //json_object *hobbies = json_object_new_array();
    //json_object_array_add(hobbies, json_object_new_string("reading"));
    //json_object_array_add(hobbies, json_object_new_string("swimming"));
    //json_object_array_add(hobbies, json_object_new_string("coding"));
    //json_object_object_add(root, "hobbies", hobbies);

    // Add an object
    //json_object *address = json_object_new_object();
    //json_object_object_add(address, "street", json_object_new_string("123 Main St"));
    //json_object_object_add(address, "city", json_object_new_string("Anytown"));
    //json_object_object_add(address, "zip", json_object_new_string("12345"));
    //json_object_object_add(root, "address", address);

    // Serialize JSON to string
    const char *json_str = json_object_to_json_string(root);

    // Print the JSON string (for debugging purposes)
    printf("Generated JSON:\n%s\n", json_str);

    // Write JSON string to file
    FILE *file = fopen("data.json", "w");
    if (file == NULL) {
        fprintf(stderr, "Could not open file for writing\n");
        return 1;
    }
    fprintf(file, "%s\n", json_str);
    fclose(file);

    // Clean up
    json_object_put(root);

	return 1;
}



void process_acts_reg(char *directory_path, int print_outputs, HashTable *table, bool act_reg)
{
    printf("Processing %s from %s\n", (act_reg) ? "Regulation" : "Acts"  , directory_path);
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
    //char *test_str ="section (1),";
    //token_text_splitter(table, test_str, pool);
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
                // Process recursive text splitting per section
		//call_json(sections);		
                if (sections[j].title && sections[j].content)
                {
                    token_text_splitter(table, sections[j].content, pool);
                }
            }
            free_sections(sections, num_sections);
        }
    }
    destroy_pool(pool);
    xmlCleanupParser();
    // Free all the memory
    free_dram_data(&dir_info);
}
