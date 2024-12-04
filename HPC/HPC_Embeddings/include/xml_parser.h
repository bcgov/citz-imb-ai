#ifndef XML_PARSER
#define XML_PARSER 

#include <stdio.h>
#include <string.h>
#include <libxml/parser.h>
#include <libxml/tree.h>

// Structure to hold the section data
typedef struct {
    char *act_title;
    char *content;
    char *url;
    char *section_name;
    char *section_url;
    char *section_id;
    char *reg_title;
    char *section_type;
    char *number;
    char *title;
} Section;

// Function declarations
void parse_xml(const char *filename, const char *tag);
Section *extract_sections_from_memory(const char *buffer, int size, int *num_sections, int print_outputs);
void free_sections(Section *sections, int num_sections);

#endif
