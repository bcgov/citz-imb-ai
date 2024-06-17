#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>
#include <time.h>
#include <omp.h>
#include <mpi.h>
#include "../include/acts.h"
#include "../include/file_dram.h"


void process_regulations(char *directory_path) {
    printf("Processing regulations from %s\n", input_file);
    if (!input_file) {
        printf("No input file provided\n");
        return;
    }

    load_file_to_memory(directory_path);


    return EXIT_SUCCESS;
}