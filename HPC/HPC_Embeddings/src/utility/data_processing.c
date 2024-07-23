#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <dirent.h>
#include <sys/types.h>
#include <sys/stat.h>
#include <unistd.h>
#include <fcntl.h>
#include <time.h>
#include "../include/acts_reg.h"

void process_data(char *directory_path, int print_outputs, char *type)
{
    printf("Processing %s from %s\n", type, directory_path);
    if (!directory_path)
    {
        printf("No input file provided\n");
        return;
    }

    directory_info_t dir_info;

    init_dram_data(directory_path, &dir_info);
    printf("Directory info initialized. Number of files: %zu\n", dir_info.num_files);

#pragma omp parallel for schedule(dynamic, 1)
    for (size_t i = 0; i < dir_info.num_files; i++)
    {
        int num_sections;
        Section *sections = extract_sections_from_memory(dir_info.files[i].buffer, dir_info.files[i].filesize, &num_sections, print_outputs);

        printf("File name or act: %s\n", dir_info.files[i].filename);
        if (sections)
        {
            for (int j = 0; j < num_sections; j++)
            {
                if (sections[j].title)
                {
                    // Process recursive text splitting per section
                    if (sections[j].content)
                    {
                        // replace with tokentextsplitter
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
