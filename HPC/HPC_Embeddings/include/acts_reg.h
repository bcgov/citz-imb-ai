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
#include "data_structures/hash_table.h"

void process_acts_reg(char *directory_path, int print_outputs, HashTable *table, bool act_reg);
