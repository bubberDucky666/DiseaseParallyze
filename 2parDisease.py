
# SOME PARTICLES ARE STILL SLIPPING THROUGH
# MAKE SURE MPI WHEREAMI CHECKS PBC CONDITIONS

import numpy as np
from matplotlib import pyplot as plt
from matplotlib import animation 
import random
from mpi4py     import MPI


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
		if self.state == 1:		 #Further sickens (or kills) organism			
			if self.level <= 5:
				self.level = self.level + 1
			elif self.level > 6:
				self.state = 3
	
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

def move(particleList, mag):
	pi    = np.pi
	
	for i in range(len(particleList)):
		if type(particleList[i]) == type(None):
			pass
		elif particleList[i].state != 2:

			den = 0
			while den == 0:
				den = np.random.random_sample()

			theta = (2*pi)*den
			
			nX = particleList[i].r[0] + (mag * np.cos(theta))
			nY = particleList[i].r[1] + (mag * np.sin(theta))

			particleList[i].r = np.array([nX%nSide, (nY%nSide)])
	
	return particleList
	
def distance(p1, p2):	
	dr = p1.r - p2.r 

	dx = dr[0]
	dy = dr[1]

	dxPBC = dx - (np.rint(dx / nSide) * nSide)
	dyPBC = dy - (np.rint(dy / nSide) * nSide)
	
	return (np.sqrt(dxPBC**2 + dyPBC**2))

def disPass(p1, rProb):
	a = np.random.random_sample() + (p1.cTime/10)
	print("a is {}".format(a))
	if rProb >= a:
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
# - - - - - - - - - - - - - User Defined Constants - - - - - - - - - - - - - - - - - - - - - - - - -

# Particle parameters
mag 		  = .1
duration 	  = 10000
nSide 		  = 30
numParticles  = nSide ** 2
radius		  = .1
pause         = .0000000001
comm 		  = MPI.COMM_WORLD
rank		  = comm.Get_rank()

# Disease parameters
rProb 	 = 1         # 0 is the lowest unit, 1 is the highest unit
devTime  = 60		 # num of frames for disease to worsend in level

# Node Parameters [minX, maxX] [minY, maxY]
numNodes = 6  #SQUARE ROOT

# - - - - - - - - - - - - - GLOBAL - - - - - - - - - - - - - - - - - - - - - - - - - - - 

#Creates an node matrix, making it easier for me to do stuff.
nodeMatrix = [0 for i in range(numNodes**2)]


for i in range(numNodes**2): 

	#Define row position values
	row  = int(np.floor(i/numNodes))
	col  = i % numNodes

	xMin = col/numNodes     * nSide
	xMax = (1+col)/numNodes	* nSide

	yMin = row/numNodes     * nSide
	yMax = (1+row)/numNodes * nSide

	#Initialize node (NodeRep object)
	nodeMatrix[i] 		= NodeRep(i+1, numNodes, numParticles, ([row, col]))
	
	#Set node bounds
	nodeMatrix[i].xBound = [xMin, xMax]
	nodeMatrix[i].yBound = [yMin, yMax]


# - - - - - - - - - - - - - MOTHER - - - - - - - - - - - - - - - - - - - - - - - - - - - 
if rank == 0:

	#The position of the sickBois in particleList
	sickBois = [0]

	particleList = pListMake(numParticles)
	layout(particleList, nSide)


	for indx, p in enumerate(particleList):
		p.sNode = p.whereAmI(nodeMatrix, nSide)

		#Indice is rank - 1
		nodeMatrix[(p.sNode - 1)].sPList.append(p)
		
		if indx in sickBois:
			p.state = 1


	for i in range(numNodes**2):
		#row  = int(np.floor(i/numNodes))
		#col  = int(i % numNodes)
		comm.send(nodeMatrix[i], dest = i+1, tag = i+1)

	for frame in range(duration):
		comm.Barrier()
	print("Done")
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

# - - - - - - - - - - - - - NODE - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

# RECIEVE SICKBOI AND PARTICLE LIST FROM THE MOTHER
# MINS AND MAX VALUES NEED TO BE
else:    							

	Node = comm.recv(source=0, tag=rank)    #recieve initial information from node object

	print("{}) recieved info\n".format(rank))

	count = 0

	for frame in range(duration):
		
		#print("pulling recieved data from other nodes")
		#for node in range(numNodes**2):
		#	try:
		#	spEx = comm.recv(source =node, tag=rank)
		#	except():
		#		[PUT SHIT HERE]
			

		particleList = Node.sPList
		
		healP		 = []
		sick1P		 = []
		sick2P		 = []
		sick3P 		 = []
		sick4P 		 = []
		deadP		 = []

		#Creates type lists, JUST FOR DISEASE PART OF PROGRAM
			
		count = count + 1

		move(particleList, mag)	
		 
		#different sublists for different node destinations
		#if no particles need to be added to a sublist, add None
		exctracts = [[] for i in range(numNodes**2)]      
		
		
		#Checks if each particle needs transfer
		for indx, p in enumerate(particleList):
			newId 	  = p.whereAmI(nodeMatrix, nSide) #the tag of the node destination
		
			if newId != rank: #if the node p SHOULD be in is different from its current node
				print("There should be movement")
				
				#puts particle in proper sublist for desination (slist indice is node rank - 1)
				exctracts[newId-1].append(p)

				#gets rid of particle from node particle list
				particleList.pop(indx)
		
			#Purely for debugging
			else:
				print("{}) I should be in node {}".format(rank, newId))


		print("{}) sending spEx to other nodes".format(rank))
		
		for i in range(len(exctracts)):
			dest = i+1
			
			#sends out extracts to proper nodes with own rank as a tag
			print("sending to {}".format(i+1))	
			comm.send(exctracts[i], dest=dest, tag=rank) 
		
		print("{}) Extracts sent out".format(rank))

		#Wait for other nodes to finish
		print("{})\n****Waiting****\n".format(rank))
		comm.Barrier()
				
		#Recieves particle data from each node
		for r in range(numNodes**2):
			extracts = comm.recv(source=(r+1), tag=(r+1))
		
			#Takes particle from recieved extracts list and adds it to particleList
			for i in range(len(extracts)):
				p = extracts[i]
				particleList.append(p)
				
		
		#Sets particle state lists for graphing 
		particleList = Node.sPList
		
		for p in particleList:
			if p.state   == 0: healP.append(p)
			elif p.state == 1: sick1P.append(p)
			elif p.state == 2: sick2P.append(p)
			elif p.state == 3: sick3P.append(p)
			elif p.state == 4: sick4P.append(p)
			elif p.state == 5: deadP.append(p)
			else: print("PARTICLE STATE ERROR")
		
		print("{}) All extracts properly recieved and sorted".format(rank))



		# for i in range(len(particleList)):	
			
		# 	for j in range(i+1, len(particleList)):
				
		# 		if distance(particleList[i], particleList[j]) <= radius:

		# 			if particleList[i].state == 1 and particleList[j].state == 0: 
		# 				print('Disease interaction happened')

		# 				if disPass(particleList[j], rProb):
		# 					particleList[j].state = 1
		# 					print("I should become sick")
							
		# 					if particleList[j].carrier != 1:
		# 						print("I dtagbecome sick")
		# 						healP[j]  = None
		# 						sick1P[j] = particleList[j]
		# 					else:
		# 						pass
						
		# 				particleList[i].cTime = particleList[i].cTime + 1
		# 				particleList[j].cTime = particleList[j].cTime + 1
					
		# 			elif particleList[j].state == 1 and particleList[i].state == 0:
		# 				print("Disease interaction happened")

		# 				if disPass(particleList[i], rProb):
		# 					particleList[i].state = 1
		# 					print("I should become sick")

		# 					if particleList[i].carrier != 1:
		# 						print("I dtagbecome sick")
		# 						healP[i]  = None
		# 						sick1P[i] = particleList[i]
		# 					else:
		# 						pass

						
		# 				particleList[j].cTime = particleList[i].cTime + 1
		# 				particleList[i].cTime = particleList[j].cTime + 1
				
		# 		else:
		# 			particleList[i].cTime = 0
		# 			particleList[j].cTime = 0
					
		# if count % devTime == 0:
		# 	for i in range(len(particleList)):
		# 		part = particleList[i]
		# 		part.sicken()
				
		# 		if part.level == 2:
		# 			sick1P[i] = None
		# 			sick2P[i] = part
		# 		if part.level == 3:
		# 			sick2P[i] = None
		# 			sick3P[i] = part
		# 		if part.level == 4:
		# 			sick3P[i] = None
		# 			sick4P[i] = part
		# 		if part.level == 5:
		# 			sick4P[i]             = None
		# 			particleList[i].state = 2 
		# 			deadP[i]              = part
		pass

		xH, yH = coordExstract(healP)
		x1, y1 = coordExstract(sick1P)
		x2, y2 = coordExstract(sick2P)
		x3, y3 = coordExstract(sick3P)
		x4, y4 = coordExstract(sick4P)
		xD, yD = coordExstract(deadP)

		#--------------------------------------------------------------
		xB = nodeMatrix[rank-1].xBound
		yB = nodeMatrix[rank-1].yBound
		
		if rank == 3 or rank == 6: # just for debugging
			plt.title("Node {}; xB {} yB {}".format(rank, xB, yB))

			plt.xlim(0, nSide)
			plt.ylim(0, nSide)
			
			plt.scatter(x1, y1, c='#ADE500')
			plt.scatter(xH, yH, c='#00E500')
			plt.scatter(x2, y2, c='#E5DF00')
			plt.scatter(x3, y3, c='#E5B700')
			plt.scatter(x4, y4, c='#E55D00')
			plt.scatter(xD, yD, c='#E50018')

			#Draw outline of domain
			plt.plot([ xB[0], xB[0] ],[ yB[1], yB[0] ])
			plt.plot([ xB[1], xB[1] ],[ yB[1], yB[0] ])
			plt.plot([ xB[0], xB[1] ],[ yB[0], yB[0] ])
			plt.plot([ xB[0], xB[1] ],[ yB[1], yB[1] ])
			
			plt.draw()
			plt.pause(pause)
			plt.clf()


