source ~/Programs/intel/oneapi/setvars.sh --force
mkdir build
cd build
cmake ..
make

#mpirun -genv I_MPI_DEBUG=5  --bind-to socket:2 -np 2 ./HPCChain ../.././../../../XML_Acts/ ../../../../../XML_Regulations/

#mpirun -genv I_MPI_DEBUG=5  --bind-to socket:2 -np 2 ./HPCChain ../fb140275c155a9c7c5a3b3e0e77a9e839594a938    ../.././../../../XML_Acts/ ../../../../../XML_Regulations/


mpirun -genv I_MPI_DEBUG=5  --bind-to socket:2 -np 2 ./HPCChain ../fb140275c155a9c7c5a3b3e0e77a9e839594a938    ../.././../../../XML_Acts/ ../../../../../XML_Regulations/ 1 : python ../mpi_receiver.py


#mpirun -genv I_MPI_DEBUG=5  --bind-to socket:2 -np 2 valgrind --leak-check=full --log-file=valgrind_output_%p.txt  ./HPCChain ../fb140275c155a9c7c5a3b3e0e77a9e839594a938    ../.././../../../XML_Acts/ ../../../../../XML_Regulations/
