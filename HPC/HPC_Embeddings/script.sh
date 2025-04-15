source ~/Programs/intel/oneapi/setvars.sh --force
mkdir build
cd build
cmake ..
make

#mpirun -genv I_MPI_DEBUG=5  --bind-to socket:2 -np 2 ./HPCChain ../.././../../../XML_Acts/ ../../../../../XML_Regulations/

#mpirun -genv I_MPI_DEBUG=5  --bind-to socket:2 -np 2 ./HPCChain ../fb140275c155a9c7c5a3b3e0e77a9e839594a938    ../.././../../../XML_Acts/ ../../../../../XML_Regulations/


mpirun -genv I_MPI_DEBUG=5  --bind-to socket:2 -np 2 ./HPCChain ../fb140275c155a9c7c5a3b3e0e77a9e839594a938    ../.././../../../XML_Acts/ ../../../../../XML_Regulations/ 1 : python ../mpi_receiver.py


mpirun -genv I_MPI_DEBUG=5  --bind-to socket:2 -np 2 ./HPCChain ../fb140275c155a9c7c5a3b3e0e77a9e839594a938    ../../../data/bclaws/Consolidations/Acts/Consol\ 14\ -\ February\ 13\,\ 2006/ ../../../data/bclaws/Consolidations/Acts/Consol\ 15\ -\ July\ 11\,\ 2006/  1 : python ../mpi_receiver.py



#mpirun -genv I_MPI_DEBUG=5  --bind-to socket:2 -np 2 valgrind --leak-check=full --log-file=valgrind_output_%p.txt  ./HPCChain ../fb140275c155a9c7c5a3b3e0e77a9e839594a938    ../.././../../../XML_Acts/ ../../../../../XML_Regulations/

# Process all acts and regulations using all 16 cores
python BCLawsCopyFiles.py --source "../../data/bclaws/Consolidations" --destination BCLaws_Output

# Only process acts
python BCLawsCopyFiles.py --source "../../data/bclaws/Consolidations" --destination BCLaws_Output --acts-only

# Only process a specific consolidation
python BCLawsCopyFiles.py --source "../../data/bclaws/Consolidations" --destination BCLaws_Output --consolidation "Consol 14 - February 13, 2006"

# Use a specific number of worker processes
python BCLawsCopyFiles.py --source "../../data/bclaws/Consolidations" --destination BCLaws_Output --workers 12


mpirun -genv I_MPI_DEBUG=5  --bind-to socket:2 -np 2 ./HPCChain ../fb140275c155a9c7c5a3b3e0e77a9e839594a938    ../BCLaws_Output/act_flat/Consol_43___October_15_2024 ../BCLaws_Output/act_flat/Consol_42___March_11_2024 1 : python ../mpi_receiver.py
