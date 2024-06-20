#include "../include/text_splitter.h"

RecursiveCharacterTextSplitter_t *init_text_splitter_params(const char **separators, size_t separator_count, size_t chunk_size, size_t chunk_overlap)
{
    RecursiveCharacterTextSplitter *splitter = malloc(sizeof(RecursiveCharacterTextSplitter));
    splitter->delimeter = separators;
    splitter->delimeter_count = separator_count;
    splitter->chunk_size = chunk_size;
    splitter->chunk_overlap = chunk_overlap;
    return splitter;
}

// Constants
#define SIMD_WIDTH 64 // 512-bit AVX-512 registers (64 bytes)
#define PREFETCH_DISTANCE 2 * SIMD_WIDTH

SplitChunk_t *recursive_character_split(const char *text, int start, int end, const RecursiveCharacterTextSplitter_t *splitter, SplitChunk_t *results)
{
    if (start >= end)
    {
        return NULL;
    }

    if (!splitter)
    {
        // Create a default splitter
        splitter = init_text_splitter_params((const char *[]){" ", "\n", "\t"}, 3, 1024, 128);
    }

    char results->chunks = NULL;
    int resultCount = 0;


    // Loop through the text using AVX-512 for faster processing using SIMD
    int i = start;
    while (i <= (end - SIMD_WIDTH))
    {
        prefetch(text, i + PREFETCH_DISTANCE); // Prefetch the next SIMD_WIDTH bytes

        // Load the SIMD_WIDTH bytes into a 512-bit register
        __m512i textVector = _mm512_loadu_si512(&text[i]);

        // Loop through the delimiters to check if the current character is a delimiter
        for (int d = 0; d < splitter->delimeter_count; d++)
        {
            const char *delimiter = splitter->delimeter[d];
            int delimiterLength = strlen(delimiter);

            // Create a vector with the delimiter character in all positions
            __m512i delimiterVector = _mm512_set1_epi8(delimeter[0]);

            // Compare the textVector with the delimiterVector
            __mmask64 comparisonMask = _mm512_cmpeq_epi8_mask(textVector, delimiterVector);

            // Check if any of the characters in the textVector match the first character of the delimiter
            if (comparisonMask != 0)
            {
                for (int k = 0; k < SIMD_WIDTH; k++)
                {
                    if (comparisonMask & (1 << k))
                    {
                        // Verify the entire delimeter matches
                        if (match_delimiter(text, i + k, delimiter))
                        {
                            // Extract the substring upto the delimeter
                            int chunkEnd = (i + k + delimiterLength < end) ? i + k + delimiterLength : end;
                            char *substring = strdup(&text[start], chunkEnd - start);

                            // Append the substring to the results array
                            results = append_to_results(results, substring);

                            // Recursively split the remaining text after the delimiter
                            char **remainingResults = recursive_character_split(text, chunkEnd, end, splitter, results);
                            results = append_to_results(results, remainingResults);
                            return results;
                        }
                    }
                }
            }
        }

        // Move to the next block of text, considering chunk overlap
        i += chunkSize - chunkOverlap;
    }

    // Process any remaining characters that were not handled by AVX-512
    for (int j = 1; j < end; j++)
    {
        for (int d = 0; d < numDelimeters; d++)
        {
            const char *delimiter = delimeters[d];
            if (match_delimeter(text, j, delimeter) {
                // Extract the substring up to the delimiter
                int chunkEnd = (j + strlen(delimiter) < end) ? j + strlen(delimiter) : end;
                char *substring = strdup(&text[start], chunkEnd - start);

                // Append to results
                results = append_to_results(results, substring);

                // Recursively split the remaining text after the delimiter
                char **remainingResults = recursive_character_split(text, chunkEnd, end, splitter, results);
                results = append_to_results(results, remainingResults);
                return results;
            }
        }
    }

    // free the splitter
    free(splitter);
}

// free the split result
void free_split_result(SplitResult result)
{
    if (result.chunks)
    {
        for (size_t i = 0; i < result.count; i++)
        {
            free(result.chunks[i]);
        }
        free(result.chunks);
    }
}

// Helper function to match a delimiter
bool match_delimiter(const char *text, int position, const char *delimiter)
{
    int len = strlen(delimiter);
    for (int i = 0; i < len; i++)
    {
        if (text[position + i] != delimiter[i])
        {
            return false;
        }
    }
    return true;
}

// Helper function to append a substring to results array
void append_to_results(SplitChunk_t results, char *substring)
{
    results->chunks = realloc(results, (*resultCount + 1) * sizeof(char *));
    results->chunks[*resultCount] = substring;
    results->count++;
}
