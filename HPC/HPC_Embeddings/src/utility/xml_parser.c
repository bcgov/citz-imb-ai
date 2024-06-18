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

void printTitle(xmlDocPtr doc, xmlNodePtr node) {
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

void processSection(xmlDocPtr doc, xmlNodePtr section, const char *title) {
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

void extractData(const char *filename) {
    xmlDocPtr doc;
    xmlNodePtr rootElement, curNode;

    doc = xmlReadFile(filename, NULL, 0);
    if (doc == NULL) {
        printf("Failed to parse %s\n", filename);
        return;
    }

    rootElement = xmlDocGetRootElement(doc);

    // Get the ACT's title
    xmlNodePtr titleNode = xmlFindNodeByPath(rootElement, (xmlChar *)"act:title");
    if (titleNode) {
        printTitle(doc, titleNode);
    } else {
        xmlFreeDoc(doc);
        return;
    }

    // Get all sections
    for (curNode = rootElement->children; curNode; curNode = curNode->next) {
        if (curNode->type == XML_ELEMENT_NODE && !xmlStrcmp(curNode->name, (const xmlChar *)"section")) {
            processSection(doc, curNode, (const char *)titleNode->name);
        }
    }

    xmlFreeDoc(doc);
}
