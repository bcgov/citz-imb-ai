#include <mpi.h>
#include <string.h>
#include <stddef.h>
#include "xml_parser.h"

// In a header file (e.g., section_types.h)
#define MAX_STRING_LENGTH 2048
#define MAX_URL_LENGTH 512
#define MAX_ID_LENGTH 128

typedef struct {
    char act_title[MAX_STRING_LENGTH];
    char reg_title[MAX_STRING_LENGTH];
    char section_title[MAX_STRING_LENGTH];
    char content[MAX_STRING_LENGTH * 4];  // Larger for content
    char url[MAX_URL_LENGTH];
    char section_id[MAX_ID_LENGTH];
    char section_number[MAX_ID_LENGTH];
    int source_rank;
} MPISection;

void create_mpi_section_type(MPI_Datatype* section_type);