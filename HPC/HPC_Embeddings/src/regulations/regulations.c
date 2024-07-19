#include "../include/acts.h"
#include "../include/token_text_splitter.h"
#include "../include/memory_pool.h"

void process_regulations(char *directory_path, int print_outputs, HashTable *table)
{
    printf("Processing regulations from %s\n", directory_path);
    if (!directory_path)
    {
        printf("No input file provided\n");
        return;
    }

    directory_info_t dir_info;
    file_info_t *files;
    init_dram_data(directory_path, &dir_info);
    printf("Directory info initialized. Number of files: %zu\n", dir_info.num_files);

    MemoryPool *pool = create_pool(POOL_SIZE);
//#pragma omp parallel for schedule(dynamic, 1)
    for (size_t i = 0; i < dir_info.num_files; i++)
    {
        printf("File name or act: %s\n", dir_info.files[i].filename);

        int num_sections;
        Section *sections = extract_sections_from_memory(dir_info.files[i].buffer, dir_info.files[i].filesize, &num_sections, print_outputs);

        if (sections)
        {
            for (int j = 0; j < num_sections; j++)
            {
                if (sections[j].title && sections[j].content)
                {
                        token_text_splitter(table, sections[j].content, pool);
			// replace with tokentextsplitter
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
