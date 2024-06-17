#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <dirent.h>
#include <sys/types.h>
#include <sys/stat.h>
#include <unistd.h>
#include <fcntl.h>
#include <time.h>

// Function to get the size of a file
off_t get_file_size(const char *filename) {
    struct stat st;
    if (stat(filename, &st) != 0) {
        return -1;
    }
    return st.st_size;
}

// Function to read a file into memory and return the time taken
double read_file_to_memory(const char *filepath) {
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

    char *buffer = malloc(filesize);
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

    clock_gettime(CLOCK_MONOTONIC, &end);

    free(buffer);
    close(fd);

    double elapsed = (end.tv_sec - start.tv_sec) + (end.tv_nsec - start.tv_nsec) / 1e9;
    return elapsed;
}

// Recursive function to traverse directory and read files
double traverse_directory(const char *dirpath) {
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
                //snprintf(path, sizeof(path), "%s/%s", dirpath, entry->d_name);
                total_time += traverse_directory(path);
            }
        } else {
            char filepath[1024];
            snprintf(filepath, sizeof(filepath), "%s/%s", dirpath, entry->d_name);
            double time_taken = read_file_to_memory(filepath);
            if (time_taken != -1) {
                //printf("Loaded %s in %.6f seconds\n", filepath, time_taken);
                total_time += time_taken;
            }
        }
    }

    closedir(dp);
    return total_time;
}

void load_file_to_memory(char *directory_path) {
    struct timespec start, end;
    clock_gettime(CLOCK_MONOTONIC, &start);

    double total_time = traverse_directory(directory_path);

    clock_gettime(CLOCK_MONOTONIC, &end);

    double elapsed = (end.tv_sec - start.tv_sec) + (end.tv_nsec - start.tv_nsec) / 1e9;
    
    printf("Total time to load all files: %.6f seconds\n", total_time);
    printf("Total execution time: %.6f seconds\n", elapsed);
}