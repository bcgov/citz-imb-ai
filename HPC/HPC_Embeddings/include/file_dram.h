#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <dirent.h>
#include <sys/types.h>
#include <sys/stat.h>
#include <unistd.h>
#include <fcntl.h>
#include <time.h>

typedef struct {
    char *filename;
    off_t filesize;
    char *buffer;
} file_info_t;

typedef struct {
    file_info_t *files;
    size_t num_files;
    size_t total_size;
} directory_info_t;

off_t get_file_size(const char *filename);
double read_file_to_memory(const char *filepath);
double traverse_directory(const char *dirpath, file_info_t *files);
void get_directory_info(const char *dirpath, directory_info_t *dir_info);
void load_file_to_memory(char *directory_path, file_info_t *files);