/*
 * This program demonstrates the use of AVX2 and AVX-512F and non AVX instructions to multiply two arrays of floats.
 * The program calculates the time taken to multiply the two arrays to demonstrate the performance improvement of 
 * AVX2 and AVX-512F instructions.
 */

#include <immintrin.h>
#include <stdio.h>
#include <time.h>

#define ARRAY_SIZE 1000000000

int main()
{
        float *arr_1 = malloc(sizeof(float) * ARRAY_SIZE);
        float *arr_2 = malloc(sizeof(float) * ARRAY_SIZE);
        for (int i = 0; i < ARRAY_SIZE; i++)
        {
                arr_1[i] = i;
                arr_2[i] = i;
        }
        float result256[ARRAY_SIZE];
        float result512[ARRAY_SIZE];
        float result[ARRAY_SIZE];

        clock_t t = clock();
        for (int i = 0; i < ARRAY_SIZE; i += 8)
        {
                __m256 a = _mm256_loadu_ps(&arr_1[i]);
                __m256 b = _mm256_loadu_ps(&arr_2[i]);
                __m256 c = _mm256_mul_ps(a, b);
                _mm256_storeu_ps(&result256[i], c);
        }
        t = clock() - t;
        printf("\nTime taken with AVX2 %f - cell 15 result is %f\n", ((double)t) / CLOCKS_PER_SEC, result256[15]);

        t = clock();
        for (int i = 0; i < ARRAY_SIZE; i += 16)
        {
                __m512 a = _mm512_loadu_ps(&arr_1[i]);
                __m512 b = _mm512_loadu_ps(&arr_2[i]);
                __m512 c = _mm512_mul_ps(a, b);
                _mm512_storeu_ps(&result512[i], c);
        }
        t = clock() - t;
        printf("\nTime taken with AVX2-512f %f - cell 15 result is %f\n", ((double)t) / CLOCKS_PER_SEC, result512[15]);

        t = clock();
        for (int i = 0; i < ARRAY_SIZE; i++)
        {
                result[i] = arr_1[i] * arr_2[i];
        }
        t = clock() - t;
        printf("\nTime taken without AVX %f - cell 15 result is %f\n", ((double)t) / CLOCKS_PER_SEC, result[15]);

        return 0;
}