#include <stdio.h>
#include <string.h>
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

void processSection(xmlNodePtr section, const char *title) {
    xmlNodePtr curNode = NULL;
    xmlChar *sectionHeading = NULL;
    xmlChar *sectionNumber = NULL;

    for (curNode = section->children; curNode; curNode = curNode->next) {
        if (curNode->type == XML_ELEMENT_NODE) {
            if (!xmlStrcmp(curNode->name, (const xmlChar *)"marginalnote")) {
                sectionHeading = xmlNodeGetContent(curNode);
            } else if (!xmlStrcmp(curNode->name, (const xmlChar *)"num")) {
                sectionNumber = xmlNodeGetContent(curNode);
            }
        }
    }

    if (sectionNumber) {
        printf("Section number is: %s\n", sectionNumber);
    }

    // Process subsections or definitions
    for (curNode = section->children; curNode; curNode = curNode->next) {
        if (curNode->type == XML_ELEMENT_NODE && 
           (!xmlStrcmp(curNode->name, (const xmlChar *)"subsection") ||
            !xmlStrcmp(curNode->name, (const xmlChar *)"definition"))) {
            char *itemText = getNodeContent(curNode);
            if (itemText) {
                printf("Item text: %s\n", itemText);
                // Create chunks and embeddings here
                free(itemText);
            }
        }
    }

    if (sectionHeading) {
        xmlFree(sectionHeading);
    }
    if (sectionNumber) {
        xmlFree(sectionNumber);
    }
}

// Recursive function to find and process all section nodes
void processAllSections(xmlNodePtr node, const char *title) {
    for (xmlNodePtr curNode = node; curNode; curNode = curNode->next) {
        if (curNode->type == XML_ELEMENT_NODE) {
            if (!xmlStrcmp(curNode->name, (const xmlChar *)"section")) {
                processSection(curNode, title);
            }
            processAllSections(curNode->children, title);
        }
    }
}

void extractDataFromMemory(const char *buffer, int size) {
    xmlDocPtr doc;
    xmlNodePtr rootElement, curNode;

    doc = xmlReadMemory(buffer, size, NULL, NULL, 0);
    if (doc == NULL) {
        printf("Failed to parse the XML content from memory\n");
        return;
    }

    rootElement = xmlDocGetRootElement(doc);

    // Get the ACT's title
    xmlNodePtr titleNode = findNodeByNamespace(rootElement, "act", "title");
    if (titleNode) {
        printTitle(titleNode);
    } else {
        xmlFreeDoc(doc);
        return;
    }

    // Process all sections
    processAllSections(rootElement, (const char *)titleNode->name);

    xmlFreeDoc(doc);
}
