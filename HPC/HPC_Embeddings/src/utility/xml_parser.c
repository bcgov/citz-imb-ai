#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <libxml/parser.h>
#include <libxml/tree.h>
#include <ctype.h>
#include <immintrin.h>
#include "../include/xml_parser.h"

// Function to parse XML and print values of a specific tag
void parse_xml(const char *filename, const char *tag) {
    xmlDoc *document = xmlReadFile(filename, NULL, 0);
    if (document == NULL) {
        fprintf(stderr, "Could not parse the XML file: %s\n", filename);
        return;
    }

    xmlNode *root = xmlDocGetRootElement(document);
    xmlNode *currentNode = NULL;

    for (currentNode = root; currentNode; currentNode = currentNode->next) {
        if (currentNode->type == XML_ELEMENT_NODE && xmlStrcmp(currentNode->name, (const xmlChar *)tag) == 0) {
            printf("Tag found: %s\n", tag);
            xmlChar *content = xmlNodeGetContent(currentNode);
            //printf("Content: %s\n", content);
            xmlFree(content);
        }
    }

    xmlFreeDoc(document);
    xmlCleanupParser();
}

// Function to trim and normalize whitespace using AVX-512
char *trim_and_normalize_whitespace(const char *text) {
   if (!text) {
	return NULL;
    }
    size_t len = strlen(text);
    char *normalized_text = malloc(len + 1);
    char *dest = normalized_text;
    int in_whitespace = 0;

    // AVX-512 setup
    const __m512i space_mask = _mm512_set1_epi8(' ');
    const __m512i newline_mask = _mm512_set1_epi8('\n');
    const __m512i tab_mask = _mm512_set1_epi8('\t');
    const __m512i cr_mask = _mm512_set1_epi8('\r');
    const __m512i zero_mask = _mm512_setzero_si512();

    while (len >= 64) {
        // Load 64 bytes into AVX-512 register
        __m512i chunk = _mm512_loadu_si512(text);

        // Compare with whitespace characters
        __mmask64 whitespace_mask = _mm512_cmpeq_epi8_mask(chunk, space_mask) |
                                    _mm512_cmpeq_epi8_mask(chunk, newline_mask) |
                                    _mm512_cmpeq_epi8_mask(chunk, tab_mask) |
                                    _mm512_cmpeq_epi8_mask(chunk, cr_mask);

        // Process each character in the chunk
        for (int i = 0; i < 64; ++i) {
            if (whitespace_mask & (1ULL << i)) {
                if (!in_whitespace) {
                    *dest++ = ' ';
                    in_whitespace = 1;
                }
            } else {
                *dest++ = text[i];
                in_whitespace = 0;
            }
        }

        text += 64;
        len -= 64;
    }

    // Process remaining characters
    while (*text) {
        if (isspace((unsigned char)*text)) {
            if (!in_whitespace) {
                *dest++ = ' ';
                in_whitespace = 1;
            }
        } else {
            *dest++ = *text;
            in_whitespace = 0;
        }
        text++;
    }
    *dest = '\0';

    // Trim leading and trailing spaces
    char *start = normalized_text;
    while (isspace((unsigned char)*start)) start++;
    char *end = normalized_text + strlen(normalized_text) - 1;
    while (end > start && isspace((unsigned char)*end)) end--;
    *(end + 1) = '\0';

    char *final_text = strdup(start);
    free(normalized_text);
    return final_text;
}


void print_readable(const char *text) {
    while (*text) {
        switch (*text) {
            case '\n':
                printf("\\n");
                break;
            case '\t':
                printf("\\t");
                break;
            case '\r':
                printf("\\r");
                break;
            case '\b':
                printf("\\b");
                break;
            case '\f':
                printf("\\f");
                break;
            case '\v':
                printf("\\v");
                break;
            case '\\':
                printf("\\\\");
                break;
            case '\"':
                printf("\\\"");
                break;
            case '\'':
                printf("\\\'");
                break;
            case ' ':
                if (*(text + 1) == ' ') {
                    printf("\\s\\s");
                    text++;  // Skip the next space since it's part of the double space
                } else {
                    printf(" ");
                }
                break;
            default:
                if (isprint((unsigned char)*text)) {
                    printf("%c", *text);
                } else {
                    printf("\\x%02X", (unsigned char)*text);
                }
                break;
        }
        text++;
    }
    printf("\n");
}

// Function to find a node by its name and namespace
xmlNodePtr findNodeByNamespace(xmlNodePtr root, const char *namespace, const char *name) {
    xmlNodePtr curNode = NULL;
    for (curNode = root; curNode; curNode = curNode->next) {
        if (curNode->type == XML_ELEMENT_NODE &&
            !xmlStrcmp(curNode->name, (const xmlChar *)name) &&
            curNode->ns != NULL &&  // Check if ns is not NULL
            !xmlStrcmp(curNode->ns->prefix, (const xmlChar *)namespace)) {
            return curNode;
        }
        xmlNodePtr foundNode = findNodeByNamespace(curNode->children, namespace, name);
        if (foundNode) {
            return foundNode;
        }
    }
    return NULL;
}


void printTitle(xmlNodePtr node) {
    xmlChar *title = xmlNodeGetContent(node);
    if (title) {
        printf("%s\n", title);
        xmlFree(title);
    }
}

char *getNodeContent(xmlNodePtr node) {
    xmlChar *content = xmlNodeGetContent(node);
    if (content) {
        char *result = strdup((char *)content);
        xmlFree(content);
        return result;
    }
    return NULL;
}

Section processSection(xmlNodePtr section, xmlNodePtr titleNode, xmlNodePtr regTitleNode, int print_outputs) {
    xmlNodePtr curNode = NULL;
    xmlChar *sectionHeading = NULL;
    xmlChar *sectionNumber = NULL;
    char *sectionContent = NULL;
    size_t sectionContentLen = 0;

    for (curNode = section->children; curNode; curNode = curNode->next) {
        if (curNode->type == XML_ELEMENT_NODE) {
            if (!xmlStrcmp(curNode->name, (const xmlChar *)"marginalnote")) {
                sectionHeading = xmlNodeGetContent(curNode);
            } else if (!xmlStrcmp(curNode->name, (const xmlChar *)"num")) {
                sectionNumber = xmlNodeGetContent(curNode);
            } else {
                char *itemText = getNodeContent(curNode);
                if (itemText) {
                    size_t itemTextLen = strlen(itemText);
                    size_t newLen = sectionContentLen + itemTextLen + 1;

                    // Reallocate buffer for section content
                    char *newSectionContent = realloc(sectionContent, newLen);
                    if (!newSectionContent) {
                        free(itemText);
                        free(sectionContent);
                        if (sectionHeading) xmlFree(sectionHeading);
                        if (sectionNumber) xmlFree(sectionNumber);
                        return (Section){NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL}; // Allocation failed
                    }

                    sectionContent = newSectionContent;
                    if (sectionContentLen == 0) {
                        sectionContent[0] = '\0'; // Initialize the buffer with an empty string
                    }
                    strcat(sectionContent, itemText);
                    sectionContentLen += itemTextLen;

                    free(itemText);
                }
            }
        }
    }

    if (sectionNumber && print_outputs) {
        printf("Section number is: %s\n", sectionNumber);
    }

    Section newSection;
    newSection.number = sectionNumber ? strdup((char *)sectionNumber) : NULL;
    newSection.content = trim_and_normalize_whitespace(sectionContent);
    free(sectionContent);
    newSection.title = sectionHeading ? strdup((char *)sectionHeading) : NULL;
    newSection.act_title = getNodeContent(titleNode);
    newSection.reg_title = getNodeContent(regTitleNode);
    if (print_outputs) {
	    printf("-----------------------------------\n");
	    printf("-----------------------------------\n");
	    printf("Act title: %s\n", newSection.act_title);
	    printf("Regulation title: %s\n", newSection.reg_title);
	    printf("Section title: %s\n", newSection.title);
	    printf("Section content: %s\n", newSection.content);
	    //print_readable(newSection.content);
	    printf("Section number: %s\n", newSection.number);
	    printf("\n");
	    printf("-----------------------------------\n");
    }	

    if (sectionHeading) {
        xmlFree(sectionHeading);
    }
    if (sectionNumber) {
        xmlFree(sectionNumber);
    }

    return newSection;
}

void processAllSections(xmlNodePtr node, Section **sections, int *num_sections, int *max_sections, xmlNodePtr titleNode, xmlNodePtr regTitleNode, int print_outputs) {
    for (xmlNodePtr curNode = node; curNode; curNode = curNode->next) {
        if (curNode->type == XML_ELEMENT_NODE) {
            if (!xmlStrcmp(curNode->name, (const xmlChar *)"section")) {
                if (*num_sections >= *max_sections) {
                    *max_sections *= 2;
                    Section *newSections = realloc(*sections, sizeof(Section) * (*max_sections));
                    if (!newSections) {
                        fprintf(stderr, "Realloc failed\n");
                        free_sections(*sections, *num_sections);
                        exit(1); // Handle the error as needed
                    }
                    *sections = newSections;
                }
                Section newSection = processSection(curNode, titleNode, regTitleNode, print_outputs);
                (*sections)[*num_sections] = newSection;
                (*num_sections)++;
            }
            processAllSections(curNode->children, sections, num_sections, max_sections, titleNode, regTitleNode, print_outputs);
        }
    }
}

Section *extract_sections_from_memory(const char *buffer, int size, int *num_sections, int print_outputs) {
    xmlDocPtr doc;
    xmlNodePtr rootElement;

    doc = xmlReadMemory(buffer, size, NULL, NULL, 0);
    if (doc == NULL) {
        printf("Failed to parse the XML content from memory\n");
        return NULL;
    }

	xmlNodePtr titleNode = NULL;

	// Get the root element of the document
	rootElement = xmlDocGetRootElement(doc);
	if (!rootElement) {
		return NULL;
	}

	// Try to get the title of the regulation
	xmlNodePtr regTitleNode = findNodeByNamespace(rootElement, "reg", "title");
	if (regTitleNode) {
	        char * reg_title = getNodeContent(regTitleNode);
		printf("reg title Node %s \n", reg_title);
		free(reg_title);
	} else {
		printf("Not a regulation it is an act \n");
	}

	if (regTitleNode) {
	    // Try to get the act title within the regulation title
	    titleNode = findNodeByNamespace(rootElement, "reg", "acttitle");
	} else {
	    // If regulation title is not found, try to get the act's title
	    titleNode = findNodeByNamespace(rootElement, "act", "title");
	}

	// If neither title is found, free the document and return NULL
	if (!titleNode) {
            printf("No title found ");
	    xmlFreeDoc(doc);
	    return NULL;
	}


    // Initialize sections array
    *num_sections = 0;
    int max_sections = 100; // Initial allocation for 100 sections
    Section *sections = malloc(sizeof(Section) * max_sections);
    if (!sections) {
        fprintf(stderr, "Malloc failed\n");
        xmlFreeDoc(doc);
        return NULL;
    }

    // Process all sections
    processAllSections(rootElement, &sections, num_sections, &max_sections, titleNode, regTitleNode, print_outputs);

    xmlFreeDoc(doc);
    return sections;
}

void free_sections(Section *sections, int num_sections) {
    for (int i = 0; i < num_sections; i++) {
        free(sections[i].title);
        free(sections[i].content);
	free(sections[i].number);
	free(sections[i].act_title);
        free(sections[i].reg_title);
    }
    free(sections);
}

