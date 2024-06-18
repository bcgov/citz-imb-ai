#include <stdio.h>
#include <libxml/parser.h>
#include <libxml/tree.h>

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