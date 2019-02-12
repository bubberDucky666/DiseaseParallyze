
from mpi4py import MPI

comm = MPI.COMM_WORLD
rank = comm.Get_rank()
num  = 10**7

def act():
    if rank != 0:
        fracNum = int(num/5)
        nums    = [i for i in range((rank-1)*fracNum, rank*fracNum)]
        val     = sum(nums)
        print(val)
        mess    = comm.send(val, dest=0, tag=rank)
    elif rank == 0:
        val1 = comm.recv(source=1, tag=1)
        val2 = comm.recv(source=2, tag=2)
        val3 = comm.recv(source=3, tag=3)
        val4 = comm.recv(source=4, tag=4)
        val5 = comm.recv(source=5, tag=5)
        valList = [val1, val2, val3, val4, val5]
        print("The sum is {}".format(sum(valList)))

act()
