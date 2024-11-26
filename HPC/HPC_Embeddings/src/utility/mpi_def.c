#include "../include/mpi_def.h"

void create_mpi_section_type(MPI_Datatype* section_type) {
    MPISection section;
    
    // Define the structure layout
    int block_lengths[] = {
        MAX_STRING_LENGTH,    // act_title
        MAX_STRING_LENGTH,    // reg_title
        MAX_STRING_LENGTH,    // section_title
        MAX_STRING_LENGTH * 4,// content
        MAX_URL_LENGTH,       // url
        MAX_ID_LENGTH,        // section_id
        MAX_ID_LENGTH,        // section_number
        1                     // source_rank
    };
    
    MPI_Datatype types[] = {
        MPI_CHAR, MPI_CHAR, MPI_CHAR, MPI_CHAR,
        MPI_CHAR, MPI_CHAR, MPI_CHAR, MPI_INT
    };
    
    MPI_Aint offsets[8];
    offsets[0] = offsetof(MPISection, act_title);
    offsets[1] = offsetof(MPISection, reg_title);
    offsets[2] = offsetof(MPISection, section_title);
    offsets[3] = offsetof(MPISection, content);
    offsets[4] = offsetof(MPISection, url);
    offsets[5] = offsetof(MPISection, section_id);
    offsets[6] = offsetof(MPISection, section_number);
    offsets[7] = offsetof(MPISection, source_rank);
    
    MPI_Type_create_struct(8, block_lengths, offsets, types, section_type);
    MPI_Type_commit(section_type);
}
