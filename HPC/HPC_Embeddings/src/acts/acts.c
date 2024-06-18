#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>
#include <time.h>
#include <omp.h>
#include <mpi.h>
#include "../include/acts.h"
#include "../include/file_dram.h"
#include "../include/xml_parser.h"

void process_acts(char *directory_path) {
    printf("Processing acts from %s\n", directory_path);
    if (!directory_path) {
        printf("No input file provided\n");
        return;
    }

    directory_info_t dir_info;
    file_info_t *files;
    init_dram_data(directory_path, &dir_info);
    parse_xml(dir_info.files[0].buffer, "act");
    // free all the memory
    free_dram_data(&dir_info);
}

