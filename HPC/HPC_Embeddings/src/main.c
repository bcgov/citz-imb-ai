#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>
#include <time.h>
#include <omp.h>
#include <mpi.h>
#include "../include/acts_reg.h"
#include "../include/memory.h"
#include "memory_pool.h"
#include <json-c/json.h>
#include "thread_buffer.h"
#include <sched.h>
#include "data_structures/hash_table.h"
#include "load_tokens.h"
#include "../include/mpi_def.h"

int main(int argc, char *argv[])
{
    if (argc <= 3 && !(argc == 3 && strcmp(argv[1], "--config") == 0)) {
        printf("Usage: \n");
        printf("  %s <token_file> <act_path_1> <act_path_2> <print_flag>\n", argv[0]);
        printf("  or\n");
        printf("  %s --config <config_file.json>\n", argv[0]);
        return 1;
    }

    int rank, size;
    MPI_Init(&argc, &argv);
    MPI_Comm_rank(MPI_COMM_WORLD, &rank);
    MPI_Comm_size(MPI_COMM_WORLD, &size);
//    omp_set_stacksize(512 * 1024 * 1024); // 512 MB

    // Assume 2 sockets: rank 0 uses socket 0, rank 1 uses socket 1
    int socket = rank % 2;

    // Set CPU affinity and memory policy
    set_affinity_to_socket(socket);
    set_memory_policy_to_socket(socket);

    // Set OpenMP to use all available threads on the current node
    omp_set_num_threads(omp_get_max_threads());

    // Load the file
    char *file_path = argv[1];
    printf("the file path is %s \n", file_path);	
    FILE *file = fopen(file_path, "r");
    if (!file)
    {
        perror("Could not open file");
        return 1;
    } else {
	printf("file is opened properly");
    }
	

    //process the file and load in hash table
    HashTable *table = load_tokens_and_store(file_path);
    if (!table) {
	printf("Hash table is not able to initialzie");
 	fclose(file);
	return 0;
    }

#pragma omp parallel
    {
        printf("Rank %d, Thread %d, running on CPU %d\n", rank, omp_get_thread_num(), sched_getcpu());
    }

    int print_output = 0;
    if (argc > 4)
    {    
        print_output = 1;
    }

    printf("Hello from rank %d of %d\n", rank, size);
    ThreadBuffer *thread_buffers;
    int num_threads;
    
    if (rank == 0)
    {
        init_thread_buffer(thread_buffer, &num_threads);
        process_acts_reg(argv[2], print_output, table,num_threads, thread_buffer, 0);
        free(thread_buffers);

	// Wait for rank 1 completion
        int completion_signal;
        MPI_Recv(&completion_signal, 1, MPI_INT, 1, 98, MPI_COMM_WORLD, MPI_STATUS_IGNORE);
        printf("Rank 0 received completion from rank 1\n");

        // Send termination to Python
 /*       MPI_Datatype section_type;
        create_mpi_section_type(&section_type);
        
        MPISection end_section = {0};
        strcpy(end_section.content, "END_OF_TRANSMISSION");
        MPI_Send(&end_section, 1, section_type, 2, 99, MPI_COMM_WORLD);
        
        MPI_Type_free(&section_type);
*/
    }
    else
    {
        init_thread_buffer(thread_buffer, &num_threads);
        process_acts_reg(argv[3], print_output, table,num_threads, thread_buffer, 1);
        free(thread_buffers);
	// Signal completion to rank 0
        int completion_signal = 1;
        MPI_Send(&completion_signal, 1, MPI_INT, 0, 98, MPI_COMM_WORLD);
    }

    printf("Completed work from rank %d of %d.\n", rank, size);

    MPI_Finalize();
    // Free the hash table
    free_table(table);
    fclose(file);
    return 0;
}
