#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>
#include <time.h>
#include <omp.h>
#include <mpi.h>
#include "../include/acts.h"
#include "../include/file_dram.h"


void process_acts(char *directory_path) {
    printf("Processing acts from %s\n", directory_path);
    if (!directory_path) {
        printf("No input file provided\n");
        return;
    }
    directory_info_t dir_info;
    get_directory_info(directory_path, &dir_info);
    printf("Number of files: %zu\n", dir_info.num_files);

    load_file_to_memory(directory_path);


    return EXIT_SUCCESS;
}