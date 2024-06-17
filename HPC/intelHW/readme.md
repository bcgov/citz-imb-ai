# Intel Hardware Test
This folder contains test to understand the performance of certain instruction sets.

To compile the avxtest.c file, use the following command:

```bash
make avxtest
./avxtest
```
Running the above command on an intel Xeon 4th gen processor Intel(R) Xeon(R) Platinum 8480+ with 224 cores, the following results were obtained for the avxtest.c file:

Memory allocation is for 1000000000 elements
`
#define ARRAY_SIZE 1000000000
`

```bash
u9f7c442b99c9169c85adc884bb78c10@idc-beta-batch-pvc-node-05:~$ ./testavx 

Time taken with AVX2 0.949827 - cell 15 result is 225.000000

Time taken with AVX2-512f 0.937135 - cell 15 result is 225.000000

Time taken without AVX 2.230493 - cell 15 result is 225.000000
```
AVX2 and AVX512 compute at similar speed a little less than 1 sec, but without AVX, it takes more than 2 sec to compute the same result.