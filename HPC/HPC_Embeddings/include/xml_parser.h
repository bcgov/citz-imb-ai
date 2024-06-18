#include <stdio.h>
#include <string.h>
#include <libxml/parser.h>
#include <libxml/tree.h>

void parse_xml(const char *filename, const char *tag);
void extractData(const char *filename);
void extractDataFromMemory(const char *buffer, int size);
