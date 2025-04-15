#include <json-c/json.h>
#include <mpi.h>
#include <string.h>
#include <stdlib.h>
#include "thread_buffer.h"
#include "xml_parser.h"
#include "token_text_splitter.h"

// Helper macro for safely adding JSON strings
#define ADD_JSON_STRING(obj, key, value) \
    json_object_object_add(obj, key, json_object_new_string((value) ? value : ""))

json_object *build_section_json(Section *section, TokenizedData *tokens, int rank);

void save_section_as_json_to_dram(Section *section, TokenizedData *tokens, int rank, int tid, ThreadBuffer *thread_buffers);

void save_openvino_format_to_dram(Section *section, TokenizedData *tokens, int rank, int tid, ThreadBuffer *openvino_buffers);

