import numpy as np
import random
import math
from mpi4py import MPI

# Factors
# 1) Contact time
# 2) Contagiousness
# 3) Incubation period
# 4) Carrier or not

class NodeRep():
	def __init__(self, tag, numNodes, numParticles, pos):
		self.tag	 = tag #Node rank
		self.pos 	 = pos #[i, j] location in matrix
		self.xBound  = []  #[xMin, xMax]
		self.yBound  = []  #[yMin, yMax]
		self.sPList  = []


class Particle():
	def __init__(self, r, state):
		self.r        = r 		 # position as an ndarray
		self.state    = state    # 0 state is healthy, {1, 2, 3, 4} is sick, 5 is dead 
		self.cTime    = 0        # Counts the number of iterations next to another particle
		self.level 	  = 0		 # Severity of disease for individual
		self.carrier  = 0        # Whether or not the individual is a passive carrier (0 is false)
		self.sNode	  = 0		 # The node the particle starts in

	def sicken(self):
		if self.state in [1,2,3,4]:		 #Further sickens (or kills) organism			
				self.state += 1

	
	#Checks which node particle SHOULD be in. Returns rank of node. 
	#INPUT: bounds in nodeBounds looks like [[minX, maxX], [minY, maxY]]
	def whereAmI(self, nodeMatrix, nSide):	
		pos = self.r 
		for indx, node in enumerate(nodeMatrix):
			xBound = node.xBound
			yBound = node.yBound

			if pos[0] >= xBound[0] and pos[1] >= yBound[0]:
				if pos[0] < xBound[1] and pos[1] < yBound[1]:
					return indx + 1
		

def layout(particleList, nSide):			#Lays out the particles from the particleList
	for i in range(len(particleList)):
		particleList[i].r = np.array([i%nSide, np.floor(i/nSide)])

def coordExstract(pList):					#Creates a new coordExtract array with particles' pos
	coordArray = np.array([[None, None]])
	
	for i in range(len(pList)):	
		if type(pList[i]) != type(None):
			coordArray = np.append(coordArray, [pList[i].r], axis=0)
		
	x, y = coordArray.T
	return x, y

def pListMake(numParticles):				#Creates the particle list and initializes the particles
	particleList = []
	for i in range(numParticles):
		particleList.append(Particle([0,0], 0))
		
		if False:   #Add actual thing here when able
			particleList[i].carrier = 1

	return particleList

def move(particleList, mag, nSide):
	pi    = np.pi
	
	for i in range(len(particleList)):
		if type(particleList[i]) == type(None):
			pass
		elif particleList[i].state != 5:

			den = 0
			while den == 0:
				den = np.random.random_sample()

			theta = (2*pi)*den
			
			nX = particleList[i].r[0] + (mag * np.cos(theta))
			nY = particleList[i].r[1] + (mag * np.sin(theta))

			particleList[i].r = np.array([nX%nSide, (nY%nSide)])
	
	return particleList
	
def distance(p1, p2, nSide):	
	dr = p1.r - p2.r 

	dx = dr[0]
	dy = dr[1]

	dxPBC = dx - (np.rint(dx / nSide) * nSide)
	dyPBC = dy - (np.rint(dy / nSide) * nSide)
	
	return (np.sqrt(dxPBC**2 + dyPBC**2))

def disPass(p1, rProb):
	a = np.random.random_sample() + (p1.cTime/10)
	print("a is {}".format(a))
	if rProb >= a and p1.carrier == 0:
		print('Dis')
		return True
	else:
		return False

def extract(indx, *args):
	spEx = []
	for arg in args:
		spEx.append(arg[indx])
		arg.pop(indx)
	return spEx

#takes a list of value list items, and appropriately distributes the values to 
#the node's state lists
def unextract(spEx, *args):				
	if type(spEx) != type(None):
	
		for i in range(len(spEx)):
				try:
					#add correct value to correct list
					args[i].append(spEx[i])
				except:
					print("THE TUPLE IS {}".format(args))
		return True

#Get surrounding nodes
def sNodeGet(rank, numNodes): 
	n0 = ((rank-numNodes)%numNodes) - 1
	n1 = ((rank-numNodes)%numNodes)
	n2 = ((rank-numNodes)%numNodes) + 1
	n3 = (rank-1)%numNodes + (numNodes * math.floor(8/numNodes))
	n4 = (rank+1)%numNodes + (numNodes * math.floor(8/numNodes))
	n5 = ((rank+numNodes)%numNodes) - 1
	n6 = ((rank+numNodes)%numNodes)
	n7 = ((rank+numNodes)%numNodes) + 1 

	return [n0,n1,n2,n3,n4,n5,n6,n7]
	# ________________
	# | n5 | n6  | n7 |
	# |____|_____|____|
	# | n3 |	 | n4 |
	# |____|_____|____|
	# | n0 | n1  | n2 |
	# |____|_____|____|

		
#makes outer particle list
def oPartGet(particleList, xBound, yBound, radius):
	oPartList = [[] for i in range(len(8))]
	for p in particleList:
		corner = [0, 0]      #if corner[0] is 1, p is on the left   - - if corner[0] is 2, p is on the right
							 #if corner[1] is 1, p is on the bottom - - if corner[1] is 2, p is on the top
		r 	   = p.r

		#Checking x values
		if r[0] < xBound[0] + radius:
			oPartList[3].append(p)
			corner[0] = 1
		elif r[0] > xBound[1] - radius:
			oPartList[4].append(p)
			corner[0] = 2
		
		#Checking y values
		if r[1] < yBound[0] + radius:
			oPartList[1].append(p)
			corner[1] = 1
		elif r[1] > yBound[1] - radius:
			oPartList[6].append(p)
			corner[1] = 2

		#Checking the corners
		if corner == [1, 1]:
			oPartList[0].append(p)
		elif corner == [1, 2]:
			oPartList[5].append(p)
		elif corner == [2, 1]:
			oPartList[2].append(p)
		elif corner == [2, 2]:
			oPartList[7].append(p)

	return oPartList

		

		
		

