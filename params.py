from mpi4py import MPI

# - - - - - - - - - - - - - User Defined Constants - - - - - - - - - - - - - - - - - - - - - - - - -

# Particle parameters
mag 		  = .1
duration 	  = 10000
nSide 		  = 10
numParticles  = nSide ** 2
radius		  = .1
pause         = .0000000001
comm 		  = MPI.COMM_WORLD
rank		  = comm.Get_rank()

# Disease parameters
rProb 	 = 1         # 0 is the lowest unit, 1 is the highest unit
devTime  = 60		 # num of frames for disease to worsend in level

# Node Parameters [minX, maxX] [minY, maxY]
numNodes = 2  #SQUARE ROOT
