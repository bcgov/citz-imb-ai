#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <dirent.h>
#include <sys/types.h>
#include <sys/stat.h>
#include <unistd.h>
#include <fcntl.h>
#include <time.h>
#include "../include/file_dram.h"

// Function to get the size of a file
off_t get_file_size(const char *filename) {
    struct stat st;
    if (stat(filename, &st) != 0) {
        return -1;
    }
    return st.st_size;
}

// Function to read a file into memory and return the time taken
double read_file_to_memory(const char *filepath, file_info_t *file) {
    int fd = open(filepath, O_RDONLY);
    if (fd == -1) {
        perror("open");
        return -1;
    }

    off_t filesize = get_file_size(filepath);
    if (filesize == -1) {
        perror("get_file_size");
        close(fd);
        return -1;
    }

    char *buffer = malloc(filesize + 1); // Allocate extra byte for null terminator
    file->buffer = buffer;
    if (!buffer) {
        perror("malloc");
        close(fd);
        return -1;
    }

    struct timespec start, end;
    clock_gettime(CLOCK_MONOTONIC, &start);

    ssize_t read_bytes = read(fd, buffer, filesize);
    if (read_bytes == -1) {
        perror("read");
        free(buffer);
        close(fd);
        return -1;
    }

    buffer[filesize] = '\0'; // Null-terminate the buffer

    clock_gettime(CLOCK_MONOTONIC, &end);

    close(fd);

    double elapsed = (end.tv_sec - start.tv_sec) + (end.tv_nsec - start.tv_nsec) / 1e9;
    file->filesize = filesize;
    return elapsed;
}


// Recursive function to traverse directory and read files
double traverse_directory(const char *dirpath, file_info_t *files, size_t *file_index) {
    struct dirent *entry;
    DIR *dp = opendir(dirpath);
    double total_time = 0;

    if (dp == NULL) {
        perror("opendir");
        return 0;
    }

    while ((entry = readdir(dp))) {
        if (entry->d_type == DT_DIR) {
            if (strcmp(entry->d_name, ".") != 0 && strcmp(entry->d_name, "..") != 0) {
                char path[1024];
                snprintf(path, sizeof(path), "%s/%s", dirpath, entry->d_name);
                total_time += traverse_directory(path, files, file_index);
            }
        } else {
            char filepath[1024];
            snprintf(filepath, sizeof(filepath), "%s/%s", dirpath, entry->d_name);
            double time_taken = read_file_to_memory(filepath, &files[*file_index]);
            if (time_taken != -1) {
                printf("Loaded %s in %.6f seconds\n", filepath, time_taken);
                total_time += time_taken;
                (*file_index)++;
            }
        }
    }

    closedir(dp);
    return total_time;
}

// Get total files and total size of files in a directory
void get_directory_info(const char *dirpath, directory_info_t *dir_info) {
    struct dirent *entry;
    DIR *dp = opendir(dirpath);

    if (dp == NULL) {
        perror("opendir");
        return;
    }

    dir_info->total_size = 0;
    while ((entry = readdir(dp))) {
        if (entry->d_type == DT_REG) {
            char filepath[1024];
            snprintf(filepath, sizeof(filepath), "%s/%s", dirpath, entry->d_name);
            off_t filesize = get_file_size(filepath);
            if (filesize != -1) {
                dir_info->total_size += filesize;
                dir_info->num_files++;
            }
        }
    }

    closedir(dp);
}

void load_file_to_memory(char *directory_path, file_info_t *files) {
    struct timespec start, end;
    clock_gettime(CLOCK_MONOTONIC, &start);

    size_t file_index = 0;
    double total_time = traverse_directory(directory_path, files, &file_index);

    clock_gettime(CLOCK_MONOTONIC, &end);

    double elapsed = (end.tv_sec - start.tv_sec) + (end.tv_nsec - start.tv_nsec) / 1e9;

    printf("Total time to load all files: %.6f seconds\n", total_time);
    printf("Total execution time: %.6f seconds\n", elapsed);
}

void init_dram_data(char *directory_path, directory_info_t *dir_info) {
    printf("Initializing file_dram\n");
    get_directory_info(directory_path, dir_info);
    printf("Number of files: %zu\n", dir_info->num_files);
    printf("Total size: %zu\n", dir_info->total_size);

    /* allocate memory */
    dir_info->files = (file_info_t *)malloc(dir_info->num_files * sizeof(file_info_t));
    if (!dir_info->files) {
        perror("malloc");
        return;
    }

    load_file_to_memory(directory_path, dir_info->files);
}

void free_dram_data(directory_info_t *dir_info) {
    printf("Freeing dram data %zu\n", dir_info->num_files);
    for (size_t i = 0; i < dir_info->num_files; i++) {
        if (dir_info->files[i].buffer)
            free(dir_info->files[i].buffer);
    }
    free(dir_info->files);
}
