source ~/Programs/intel/oneapi/setvars.sh --force
mkdir build
cd build
cmake ..
make

mpirun -genv I_MPI_DEBUG=5  --bind-to socket:2 -np 2 ./HPCChain ../.././../../../XML_Acts/ ../../../../../XML_Regulations/
