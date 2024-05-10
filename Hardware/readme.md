# Hardware
----------

This folder has all the hardware details for the CITZ IMB AI project. When dealing with A.I., making it work better, faster, and cheaper is important. Making the algorithms work as best as they can on the hardware is crucial for this project. This folder has info about different ways the hardware can help with deep learning and teaches us more about how the hardware works.

## B.C Gov Openshift Hardware Details
Openshift clusters in B.C gov are equipped with these processors:


| CPU | Cores | Threads | Base Frequencey | Instruction Set Extensions | Generation | Link |
| --- | --- | --- | --- | --- | --- | --- |
Intel Xeon Gold 6134 | 8 | 16 | 3.2 GHz | AVX-512 | Skylake 1st Gen | [Intel Xeon Gold 6134](https://www.intel.com/content/www/us/en/products/sku/120493/intel-xeon-gold-6134-processor-24-75m-cache-3-20-ghz/specifications.html) 
Intel Xeon Gold 6234 | 8 | 16 | 2.4 GHz | AVX-512 (VNNI) | Cascade Lake 2nd Gen | [Intel Xeon Gold 6234](https://www.intel.com/content/www/us/en/products/sku/193954/intel-xeon-gold-6234-processor-24-75m-cache-3-30-ghz/specifications.html)
Intel Xeon Gold 6244 | 8 | 16 | 3.6 GHz | AVX-512 (VNNI) | Cascade Lake 2nd Gen | [Intel Xeon Gold 6244](https://ark.intel.com/content/www/us/en/ark/products/192442/intel-xeon-gold-6244-processor-24-75m-cache-3-60-ghz.html)
Intel Xeon Platinum 8168 | 24 | 48 | 2.7 GHz | AVX-512 (VNNI) | Cascade Lake 1st Gen | [Intel Xeon Platinum 8168](https://www.intel.com/content/www/us/en/products/sku/120504/intel-xeon-platinum-8168-processor-33m-cache-2-70-ghz/specifications.html)
Intel Xeon Platinum 8268 | 24 | 48 | 2.9 GHz | AVX-512 | Cascade Lake 2nd Gen | [Intel Xeon Platinum 8268](https://www.intel.com/content/www/us/en/products/sku/192481/intel-xeon-platinum-8268-processor-35-75m-cache-2-90-ghz/specifications.html)
Intel Xeon Gold 6342 | 24 |48 | 2.8 GHz | AVX-512 (VNNI) (BF16) | Ice Lake 3rd Gen | [Intel Xeon Gold 6342](https://www.intel.com/content/www/us/en/products/sku/215276/intel-xeon-gold-6342-processor-36m-cache-2-80-ghz/specifications.html)

For more detailed information which AVX instructions are supported by which processor, please refer to the [Intel AVX](https://www.intel.com/content/www/us/en/support/articles/000058341/processors/intel-xeon-processors.html) page.

### Intel Xeon Advanced Vector Extensions 512 (AVX-512)
Advanced vector extension is a type of instruction set that can be used to perform multiple operations on a single instruction. When performing deep learning operations, AVX-512 can be used to perform multiple operations on a single instruction. This can help speed up the process of training and inference.

As an example of how AVX-512 can be used to speed up deep learning operations, consider the following please refer to this example [avxtest.c](intelHW/avxtest.c) file. This file contains a simple example of how AVX-512 can be used to perform multiple operations on a single instruction and shows the speed differnece between AVX-512 and non AVX-512 operations.


For more info on AVX please refer to Intels documentation on [AVX](https://www.intel.com/content/www/us/en/developer/articles/guide/deep-learning-with-avx512-and-dl-boost.html) 

## Pulbic Cloud Hardware Details
To increase the speed of training and inference, the CITZ IMB AI project uses public cloud services. We will be using AWS. 




 