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
#include "process_config.h"

int main(int argc, char *argv[])
{
    if (argc <= 3 && !(argc == 3 && strcmp(argv[1], "--config") == 0))
    {
        printf("Usage: \n");
        printf("  %s <token_file> <act_path_1> <act_path_2> <print_flag>\n", argv[0]);
        printf("  or\n");
        printf("  %s --config <config_file.json>\n", argv[0]);
        return 1;
    }

    // Check if we're using config mode
    int using_config = 0;
    char *config_file = NULL;

    if (argc > 2 && strcmp(argv[1], "--config") == 0)
    {
        using_config = 1;
        config_file = argv[2];
    }

    process_files config;
    memset(&config, 0, sizeof(process_files));  // initialize to zero

    if (using_config)
    {
        using_config = 1;
        config_file = argv[2];
        process_config_file(config_file, &config);
    }
    else
    {
        // Legacy command mode:
        // argv[1] = token_file
        // argv[2] = rank 0 source path
        // argv[3] = rank 1 source path (optional)

        if (argc < 3)
        {
            fprintf(stderr, "Usage: %s <token_file> <act_path_rank0> [<act_path_rank1>]\n", argv[0]);
            exit(1);
        }

        config.token_file_path = strdup(argv[1]);
        config.num_of_files = (argc >= 4) ? 2 : 1;
        config.properties = malloc(sizeof(legislation *) * config.num_of_files);

        // Rank 0
        legislation *leg0 = malloc(sizeof(legislation));
        memset(leg0, 0, sizeof(legislation));
        leg0->source_path = strdup(argv[2]);
        leg0->type = 'A'; // Default to Act
        config.properties[0] = leg0;

        // Rank 1 (if provided)
        if (argc >= 4)
        {
            legislation *leg1 = malloc(sizeof(legislation));
            memset(leg1, 0, sizeof(legislation));
            leg1->source_path = strdup(argv[3]);
            leg1->type = 'A';
            config.properties[1] = leg1;
        }
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
    }
    else
    {
        printf("file is opened properly");
    }

    // process the file and load in hash table
    HashTable *table = load_tokens_and_store(file_path);
    if (!table)
    {
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
    ThreadBuffer *thread_buffers = NULL;
    int num_threads;
    MemoryPool *pool = create_pool(POOL_SIZE);
    init_thread_buffer(&thread_buffers, &num_threads);
    printf("Rank %d: Number of threads %d \n", rank, num_threads);

    int start = (rank * config.num_of_files) / size;
    int end = ((rank + 1) * config.num_of_files) / size;

    for (int i = start; i < end; i++) {
        legislation *item = config.properties[i];

        reset_thread_buffers(thread_buffers, num_threads);
        reset_pool(pool);

        if (!item->destination_path) {
            asprintf(&item->destination_path, "output/rank_%d_%d", rank, i);  // or fallback default
        }

        if (!item->base_url) {
            item->base_url = strdup("https://default.url/");
        }

        printf("Rank %d processing: %s\n", rank, item->source_path);
        //process_acts_reg(item->source_path, print_output, table, num_threads, thread_buffers, pool, (item->type == 'R'));
        process_acts_reg(item, print_output, table, num_threads, thread_buffers, pool);

    }


    if (rank == 0)
    {
    //    for (i =0; i< config.num_files/2; i++) {
    //        process_acts_reg(config.properties[i]->source_path, print_output, table, num_threads, thread_buffers, pool, 0);
    //    }

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
    //    for (i = (config.num_files/2) + 1; i< config.num_files; i++) {
    //        process_acts_reg(config.properties[i]->source_path, print_output, table, num_threads, thread_buffers, pool, 1);
    //    }

        // Signal completion to rank 0
        int completion_signal = 1;
        MPI_Send(&completion_signal, 1, MPI_INT, 0, 98, MPI_COMM_WORLD);
    }

    /* Free all memory */
    free_process_files(&config);
    free_thread_buffers(thread_buffers, num_threads);
    destroy_pool(pool);

    printf("Completed work from rank %d of %d.\n", rank, size);

    MPI_Finalize();
    // Free the hash table
    free_table(table);
    fclose(file);
    return 0;
}
