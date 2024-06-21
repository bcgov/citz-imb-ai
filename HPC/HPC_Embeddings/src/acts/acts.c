#include "../include/acts.h"
#include <sched.h>

void process_acts(char *directory_path) {
    printf("Processing acts from %s\n", directory_path);
    if (!directory_path) {
        printf("No input file provided\n");
        return;
    }

    directory_info_t dir_info;

    init_dram_data(directory_path, &dir_info);
    printf("Directory info initialized. Number of files: %zu\n", dir_info.num_files);

    #pragma omp parallel for schedule(dynamic, 1)
    for (size_t i = 0; i < dir_info.num_files; i++) {
       printf("Thread %d, running on CPU %d\n", omp_get_thread_num(), sched_getcpu());
        printf("Processing file %zu\n", i);

        int num_sections;
        Section *sections = extract_sections_from_memory(dir_info.files[i].buffer, dir_info.files[i].filesize, &num_sections);

        printf("Number of sections: %d\n", num_sections);
        if (sections) {
            printf("File name or act: %s\n", dir_info.files[i].filename); 
//            for (int j = 0; j < num_sections; j++) {
            for (int j = 1; j < 10; j++) {
                if (sections[j].title) {
                    // Process recursive text splitting per section
                    SplitChunk_t results = { .chunks = NULL, .count = 0 };
                    if (sections[j].content) {
                        recursive_character_split(sections[j].content, 0, strlen(sections[j].content), NULL, &results);
                        if (results.chunks) {
                            printf("Number of chunks: %zu\n", results.count);
                            for (size_t k = 0; k < results.count; k++) {
                                printf("Chunk %zu: %s\n", k, results.chunks[k]);
                            }
                            free_split_result(&results);
                        }
                    }
                }
            }
            free_sections(sections, num_sections);
        }
    }

    xmlCleanupParser();
    // Free all the memory
    free_dram_data(&dir_info);
}

