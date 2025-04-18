#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>
#include <time.h>
#include <omp.h>
#include <mpi.h>
#include "file_dram.h"
#include "xml_parser.h"
#include "text_splitter.h"
#include "memory.h"
#include "thread_buffer.h"
#include "data_structures/hash_table.h"
#include "process_config.h"

void process_acts_reg(legislation *item, int print_output, HashTable *table, int num_threads, ThreadBuffer *thread_buffers, MemoryPool *pool);
