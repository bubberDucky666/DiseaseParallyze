
# SOME PARTICLES ARE STILL SLIPPING THROUGH
# MAKE SURE MPI WHEREAMI CHECKS PBC CONDITIONS

import numpy as np
from matplotlib import pyplot as plt
from matplotlib import animation 
import random
from mpi4py     import MPI
from functions  import *


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
	nodeMatrix[i] 		 = NodeRep(i+1, numNodes, numParticles, ([row, col]))
	
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


#=======================================================================
		move(particleList, mag, nSide)	
		for i in range(len(particleList)):	
			for j in range(i+1, len(particleList)):
				if distance(particleList[i], particleList[j], nSide) <= radius:
					
					if particleList[i].state == 1 and particleList[j].state == 0: 
						print('Disease interaction happened')

						if disPass(particleList[j], rProb):
							particleList[j].state = 1
							print("I should become sick")
						else:
							pass
						
						particleList[i].cTime = particleList[i].cTime + 1
						particleList[j].cTime = particleList[j].cTime + 1
					
					elif particleList[j].state == 1 and particleList[i].state == 0:
						print("Disease interaction happened")

						if disPass(particleList[i], rProb):
							particleList[i].state = 1
							print("I should become sick")
						else:
							pass
	
						particleList[j].cTime = particleList[i].cTime + 1
						particleList[i].cTime = particleList[j].cTime + 1
				
				else:
					particleList[i].cTime = 0
					particleList[j].cTime = 0
					
		if count % devTime == 0:
			for i in range(len(particleList)):
				part = particleList[i]
				part.sicken()
			
#========================================================================
		
		
		
		#different sublists for different node destinations
		#if no particles need to be added to a sublist, add None
		extracts = [[] for i in range(numNodes**2)]      
		
		
		#Checks if each particle needs transfer
		for indx, p in enumerate(particleList):
			newId = p.whereAmI(nodeMatrix, nSide) #the tag of the node destination
		
			if newId != rank: #if the node p SHOULD be in is different from its current node
				print("{}) I should be in node {}".format(rank, newId))
				
				#puts particle in proper sublist for desination (slist indice is node rank - 1)
				extracts[newId-1].append(p)

				#gets rid of particle from node particle list
				particleList.pop(indx)


		print("{}) sending spEx to other nodes".format(rank))
		
		for i in range(len(extracts)):
			dest = i+1
			
			#sends out extracts to proper nodes with own rank as a tag
			print("{}) sending to {}".format(rank, dest))	
			comm.send(extracts[i], dest=dest, tag=rank) 
		
		print("{}) Extracts sent out".format(rank))

		#Wait for other nodes to finish
		print("{})****Waiting****\n".format(rank))
		comm.Barrier()
				
		#Recieves particle data from each node
		for r in range(numNodes**2):
			extracts = comm.recv(source=(r+1), tag=(r+1))
			print('cow')
		
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
		
		if rank == 3 or rank == 4: # just for debugging
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


