#include <stdio.h>
#include <string.h>
#include <libxml/parser.h>
#include <libxml/tree.h>

// Structure to hold the section data
typedef struct {
    char *title;
    char *content;
} Section;

// Function declarations
void parse_xml(const char *filename, const char *tag);
Section *extract_sections_from_memory(const char *buffer, int size, int *num_sections);
void free_sections(Section *sections, int num_sections);
