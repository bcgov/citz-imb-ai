#include "../include/acts.h"

void process_acts(char *directory_path) {
    printf("Processing acts from %s\n", directory_path);
    if (!directory_path) {
        printf("No input file provided\n");
        return;
    }

    directory_info_t dir_info;

    init_dram_data(directory_path, &dir_info);
    printf("dir info is and num files are %zu \n", dir_info.num_files);


    #pragma omp parallel for dynamic schedule(guided)
    
    for (size_t i = 0; i < dir_info.num_files; i++) {

	printf("processing file %zu \n", i);

	int num_sections;
	Section *sections =  extract_sections_from_memory(dir_info.files[i].buffer, dir_info.files[i].filesize , &num_sections);


	printf("num of sections is:::  %d \n", num_sections);
	if (sections) {
		for (int j=0; j < num_sections; j++) {
			///recur
			if (sections[j].title) {
				printf("Title is %s \n", sections[j].title);
				printf("data is %s \n", sections[j].content);
                // process recursive text splitting per section
                SplitChunk_t *chunks = recursive_character_split(sections[j].content, 0, strlen(sections[j].content), NULL);
                if (chunks) {
                    for (int k = 0; k < chunks->num_count; k++) {
                        printf("Chunk %d: %s\n", k, chunks->chunks[k]);
                    }
                    free_split_chunks(chunks);
                }
			}
		}
		free_sections(sections, num_sections);
	}

    }

    xmlCleanupParser();
    // free all the memory
    free_dram_data(&dir_info);
}

