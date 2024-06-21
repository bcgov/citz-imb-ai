#include "../include/acts.h"

void process_regulations(char *directory_path) {
    printf("Processing regulations from %s\n", directory_path);
    if (!directory_path) {
        printf("No input file provided\n");
        return;
    }

    directory_info_t dir_info;
    file_info_t *files;
    init_dram_data(directory_path, &dir_info);

/*
    #pragma omp parallel for dynamic schedule(guided)
    for (size_t i = 0; i < dir_info.num_files; i++) {
        //parse_xml(dir_info.files[i].buffer, "act");
        //extractData(dir_info.files[i].buffer);
        //extractDataFromMemory(dir_info.files[i].buffer, dir_info.files[i].filesize);
    }

    xmlCleanupParser();
*/
    // free all the memory
    free_dram_data(&dir_info);

}
