#include "../include/acts.h"

void process_regulations(char *directory_path, int print_outputs) {
    printf("Processing regulations from %s\n", directory_path);
    if (!directory_path) {
        printf("No input file provided\n");
        return;
    }

    directory_info_t dir_info;
    file_info_t *files;
    init_dram_data(directory_path, &dir_info);

    #pragma omp parallel for schedule(dynamic, 1)
    for (size_t i = 0; i < dir_info.num_files; i++) {
//       printf("Thread %d, running on CPU %d\n", omp_get_thread_num(), sched_getcpu());
//        printf("Processing file %zu\n", i);
        printf("File name or act: %s\n", dir_info.files[i].filename); 

        int num_sections;
        Section *sections = extract_sections_from_memory(dir_info.files[i].buffer, dir_info.files[i].filesize, &num_sections, print_outputs);

//        printf("Number of sections: %d\n", num_sections);
        if (sections) {
//           printf("--------------- processing SEctions --------------- \n ");
            for (int j = 0; j < num_sections; j++) {
                if (sections[j].title) {
                    // Process recursive text splitting per section
                    if (sections[j].content) {
                        // replace with tokentextsplitter 
                    }
                }
            }
            free_sections(sections, num_sections);
//            printf("--------------- End of processing sections --------------------- \n ");
//            printf("------------------------------------------------------------------ \n\n");
        }
    }

    xmlCleanupParser();
    // Free all the memory
    free_dram_data(&dir_info);

}
