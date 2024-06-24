#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>
#include <time.h>
#include <omp.h>
#include <mpi.h>
#include "../include/acts.h"
#include "../include/regulations.h"
#include "../include/memory.h"
#include <sched.h>


int main(int argc, char *argv[]) {
    if (argc <= 2) {
        printf("Usage: %s <input_file>\n", argv[0]);
        return 1;
    }

    int rank, size;
    MPI_Init(&argc, &argv);
    MPI_Comm_rank(MPI_COMM_WORLD, &rank);
    MPI_Comm_size(MPI_COMM_WORLD, &size);

    // Assume 2 sockets: rank 0 uses socket 0, rank 1 uses socket 1
    int socket = rank % 2;

    // Set CPU affinity and memory policy
    set_affinity_to_socket(socket);
    set_memory_policy_to_socket(socket);

    // Set OpenMP to use all available threads on the current node
    omp_set_num_threads(omp_get_max_threads());

    #pragma omp parallel
    {
        printf("Rank %d, Thread %d, running on CPU %d\n", rank, omp_get_thread_num(), sched_getcpu());
    }
	
    int print_output = 0;
    if (argc > 3) {
	print_output = 1;
    }

    if (rank == 0) {
        printf("Hello from rank %d of %d\n", rank, size);
        process_acts(argv[1], print_output);
    } else {
        printf("Hello from rank %d of %d\n", rank, size);
        process_regulations(argv[2], print_output);
    }

    printf("Hello from rank %d of %d\n", rank, size);



    MPI_Finalize();
    return 0;
}
