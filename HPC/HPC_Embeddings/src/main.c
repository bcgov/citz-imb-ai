#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>
#include <time.h>
#include <omp.h>
#include <mpi.h>
#include "../include/acts.h"
#include "../include/regulations.h"

int main(int argc, char *argv[]) {
    if (argc != 2) {
        printf("Usage: %s <input_file>\n", argv[0]);
        return 1;
    }

    int rank, size;
    MPI_Init(&argc, &argv);
    MPI_Comm_rank(MPI_COMM_WORLD, &rank);
    MPI_Comm_size(MPI_COMM_WORLD, &size);

    if (rank == 0) {
        printf("Hello from rank %d of %d\n", rank, size);
        process_acts(argv[1]);
    } else {
        printf("Hello from rank %d of %d\n", rank, size);
        process_regulations(argv[2]);
    }

    printf("Hello from rank %d of %d\n", rank, size);



    MPI_Finalize();
    return 0;
}
