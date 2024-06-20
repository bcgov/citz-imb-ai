#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <libxml/parser.h>
#include <libxml/tree.h>
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
            printf("Content: %s\n", content);
            xmlFree(content);
        }
    }

    xmlFreeDoc(document);
    xmlCleanupParser();
}

// Function to find a node by its name and namespace
xmlNodePtr findNodeByNamespace(xmlNodePtr root, const char *namespace, const char *name) {
    xmlNodePtr curNode = NULL;
    for (curNode = root; curNode; curNode = curNode->next) {
        if (curNode->type == XML_ELEMENT_NODE && 
            !xmlStrcmp(curNode->name, (const xmlChar *)name) && 
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

Section processSection(xmlNodePtr section) {
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
                        return (Section){NULL, NULL}; // Allocation failed
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

    if (sectionNumber) {
        printf("Section number is: %s\n", sectionNumber);
    }

    Section newSection;
    newSection.title = sectionNumber ? strdup((char *)sectionNumber) : NULL;
    newSection.content = sectionContent;

    if (sectionHeading) {
        xmlFree(sectionHeading);
    }
    if (sectionNumber) {
        xmlFree(sectionNumber);
    }

    return newSection;
}

void processAllSections(xmlNodePtr node, Section **sections, int *num_sections, int *max_sections) {
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
                Section newSection = processSection(curNode);
                (*sections)[*num_sections] = newSection;
                (*num_sections)++;
            }
            processAllSections(curNode->children, sections, num_sections, max_sections);
        }
    }
}

Section *extract_sections_from_memory(const char *buffer, int size, int *num_sections) {
    xmlDocPtr doc;
    xmlNodePtr rootElement;

    doc = xmlReadMemory(buffer, size, NULL, NULL, 0);
    if (doc == NULL) {
        printf("Failed to parse the XML content from memory\n");
        return NULL;
    }

    rootElement = xmlDocGetRootElement(doc);

    // Get the ACT's title
    xmlNodePtr titleNode = findNodeByNamespace(rootElement, "act", "title");
    if (!titleNode) {
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
    processAllSections(rootElement, &sections, num_sections, &max_sections);

    xmlFreeDoc(doc);
    return sections;
}

void free_sections(Section *sections, int num_sections) {
    for (int i = 0; i < num_sections; i++) {
        free(sections[i].title);
        free(sections[i].content);
    }
    free(sections);
}

