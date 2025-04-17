#include <json-c/json.h>

/*
      "date": "October 15, 2024",
      "source_path": "BCLaws_Output/act_flat/Consol_43___October_15_2024",
      "destination_path": "Processed/consol_43/",
      "base_url": "https://www.bclaws.gov.bc.ca/civix/document/id/consol43/consol43/",
      "time_enforced": "October 15, 2024",
      "token_file": "../fb140275c155a9c7c5a3b3e0e77a9e839594a938",    
*/

typedef struct {
    char *date;
    char *source_path;
    char *base_url;
    char *destination_path;
    char type;  // 'A' for Act, 'R' for Regulation
} legislation;

typedef struct {
    char *token_file_path;
    int num_of_files;
    legislation **properties;  // array of pointers to legislation
} process_files;

void process_config_file(const char *config_path, process_files *config);
void free_process_files(process_files *config);