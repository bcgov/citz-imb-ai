#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <dirent.h>
#include <sys/types.h>
#include <sys/stat.h>
#include <unistd.h>
#include <fcntl.h>
#include <time.h>

off_t get_file_size(const char *filename);
double read_file_to_memory(const char *filepath);
double traverse_directory(const char *dirpath);
void load_file_to_memory(char *directory_path);