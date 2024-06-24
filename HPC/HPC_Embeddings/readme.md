# High Performance Computing to generate embeddings

## Introduction
When generating embeddings for large datasets like B.C acts and regulations, running the embeddings on a Core-i7, on a docker container on a laptop is not feasible. The whole process can take upto 10 days rendering the laptop unusable for any other tasks. 

Using the cloud compute resources avaiable in B.C Gov, by using some of the open source frameworks we can generate the embeddings in a fraction of the time. But it still takes a few hours to generate the embeddings.

This brings us to writing custom code to take advantage of the hardware to generate the embeddings faster.

Using and writing a custom C code that is designed with HPC in mind we may be able to generate the embeddings in a fraction of the time it takes to generate the embeddings using the open source frameworks.   

The optimizations and architecture details to enable HPC are as follows:
1. Before processing the data, we need to move the data into DRAM on the respective NUMA node. This is done to reduce the latency and increase the throughput of the data transfer during processing.
2. The Acts data will be processing on one MPI node and the regulations data will be processed on another MPI node. This is done to take advantage of the distributed processing capabilities of MPI which is avaible on the B.C Gov cloud.

In each of the node, the following steps are taken to generate the embeddings:
1. The data is first parsed using libxml to divide the data into sections. This allows for better modularizty and retrieval of the data. After the parsing, the next step is to create the embeddings by spllting them into 256 token chunks. 
2. During the text splitting and tokenization, we take avantage of the SIMD isntructions for recursive text splitting. By using intrinsics, we can take advantage of the AVX-512 instructions to speed up the process.
3. By using OpenMP, we can parallelize the tokenization process to take advantage of the multi-core architecture of the CPU.
4. The embeddings are generated using ONNX Runtime which is optimized for the hardware. The embeddings are generated in parallel using OpenMP to take advantage of the multi-core architecture of the CPU.
5. The embeddings are then stored in NEO4J.
6. The same process will be repeated for other datasets that can take advantage of using MPI for distributed processing.