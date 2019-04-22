
# After move, nodes check other node's particle positions within a bound
# of 'radius' length. PARTICLE IN NODE CANNOT INFECT PARTICLE OUT OF NODE

import random
import math as math
from matplotlib import pyplot as plt
from matplotlib import animation 
from mpi4py     import MPI
from functions  import *
from params		import *

# - - - - - - - - - - - - - GLOBAL - - - - - - - - - - - - - - - - - - - - - - - - - - - 

comm = MPI.COMM_WORLD
rank = comm.Get_rank()

#Creates an node matrix, making it easier for me to do stuff.
nodeMatrix = [ [0 for i in range(numNodes)] for j in range(numNodes)]

#rank to be assigned to created nodes
mRank = 0

for i in range(numNodes): 
	for j in range(numNodes):

		mRank += 1

		#Define row position values
		row  = i
		col  = j

		xMin = col/numNodes     * nSide
		xMax = (1+col)/numNodes	* nSide

		yMin = row/numNodes     * nSide
		yMax = (1+row)/numNodes * nSide

		#Initialize node (NodeRep object)
		nodeMatrix[i][j] 		= NodeRep(mRank, numNodes, numParticles, ([row, col]))
		
		#Set node bounds
		nodeMatrix[i][j].xBound = [xMin, xMax]
		nodeMatrix[i][j].yBound = [yMin, yMax]


# - - - - - - - - - - - - - MOTHER - - - - - - - - - - - - - - - - - - - - - - - - - - - 
if rank == 0:

	#The position of the sickBois in particleList
	sickBois = [0, numParticles-1, 3]

	particleList = pListMake(numParticles)
	layout(particleList, nSide)


	for indx, p in enumerate(particleList):
		p.sNode = p.whereAmI(nodeMatrix, nSide, numNodes)

		#Indice is rank - 1
		nodeMatrix[p.sNode[0]][p.sNode[1]].sPList.append(p)
		
		if indx in sickBois:
			p.state = 1


	for i in range(numNodes):
		for j in range(numNodes):
			node = nodeMatrix[i][j]
			tag  = node.tag
			comm.send(node, dest = tag, tag = tag)

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
		
		print("\n\n\n\n {}) POOPBUTT \n\n\n".format(rank))


		#print("pulling recieved data from other nodes")
		#for node in range(numNodes**2):
		#	try:
		#	spEx = comm.recv(source =node, tag=rank)
		#	except():
		#		[PUT SHIT HERE]
			

		particleList = Node.sPList
		pos 		 = Node.pos
		
		healP		 = []
		sick1P		 = []
		sick2P		 = []
		sick3P 		 = []
		sick4P 		 = []
		deadP		 = []

		#Creates type lists, JUST FOR DISEASE PART OF PROGRAM
			
		count = count + 1


		#=======================================================================
		#			Movement and Status Changes (w/ Edge Particles)

		move(particleList, mag, nSide)	

		sNodes	 = sNodeGet(pos, numNodes, nodeMatrix)
		print("{}) sNodes: {}".format(rank, sNodes))
	
		# Creates a list of edge particles for various nodes
		# [[n0], [n1], [n2], [n3], [n4], [5n], [n6], [n7], ...]
		ePartList = ePartGet(particleList, Node.xBound, Node.yBound, radius)

		# Empty list to be filled with outer-node edge particles
		oPartList = [[] for i in range(8)]

		#Sends out edge particles to other Nodes
		for n in range(len(sNodes)):
			comm.send(ePartList[n], dest=sNodes[n])
		print("{}) Done sending edge bois to edge nodes".format(rank))
			
		#Recieves edge partlices from other nodes 
		for n in sNodes:
			nParts = comm.recv(source=n)
			oPartList.append(nParts)

		#comm.Barrier()

		#Does particle disease checks on local and outernode particles
		for i in range(len(particleList)):	
			
			for j in range(i+1, len(particleList)):
				
				if distance(particleList[i], particleList[j], nSide) <= radius:
					
					if particleList[i].state != 0 and particleList[j].state == 0: 
						print('Disease interaction happened')

						if disPass(particleList[j], rProb):
							particleList[j].state = 1
							print("I should become sick")
						else:
							print("no sickness transmitted")
							pass
						
						particleList[i].cTime = particleList[i].cTime + 1
						particleList[j].cTime = particleList[j].cTime + 1
					
					elif particleList[j].state != 0 and particleList[i].state == 0:
						print("Disease interaction happened")

						if disPass(particleList[i], rProb):
							particleList[i].state = 1
							print("I should become sick")
						else:
							print("no sickness transmitted")
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
		#				Moving Main Particles Between Nodes
		
		#different sublists for different node destinations
		#if no particles need to be added to a sublist, add None
		extracts = [[] for i in range(numNodes**2)]      
		
		
		#Checks if each particle needs transfer
		for indx, p in enumerate(particleList):
			loc = p.whereAmI(nodeMatrix, nSide, numNodes) #the tag of the node destination
			newId	 = nodeMatrix[loc[0]][loc[1]].tag

			if newId != rank: #if the node p SHOULD be in is different from its current node
				
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
		
		#Wait for other nodes to finish
		print("{})****Waiting****\n".format(rank))

		print("\n\n\n\n {}) PeePeeBUTT \n\n\n".format(rank))

		#Recieves particle data from each node
		for r in range(numNodes**2):
			extracts = comm.recv(source=(r+1), tag=(r+1))
			print("\n\n\n\n {}) PooPooButt \n\n\n".format(rank))

			#Takes particle from recieved extracts list and adds it to particleList
			for i in range(len(extracts)):
				p = extracts[i]
				particleList.append(p)

		comm.Barrier()
		
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

		# xH, yH = coordExstract(healP)
		# x1, y1 = coordExstract(sick1P)
		# x2, y2 = coordExstract(sick2P)
		# x3, y3 = coordExstract(sick3P)
		# x4, y4 = coordExstract(sick4P)
		# xD, yD = coordExstract(deadP)

		# #--------------------------------------------------------------
		# xB = nodeMatrix[pos[0]][pos[1]].xBound
		# yB = nodeMatrix[pos[0]][pos[1]].yBound
		
		# #if rank == 3 or rank == 4: # just for debugging
		# plt.title("Node {}; xB {} yB {}".format(rank, xB, yB))

		# plt.xlim(0, nSide)
		# plt.ylim(0, nSide)
		
		# plt.scatter(x1, y1, c='#ADE500')
		# plt.scatter(xH, yH, c='#00E500')
		# plt.scatter(x2, y2, c='#E5DF00')
		# plt.scatter(x3, y3, c='#E5B700')
		# plt.scatter(x4, y4, c='#E55D00')
		# plt.scatter(xD, yD, c='#E50018')

		# #Draw outline of domain
		# plt.plot([ xB[0], xB[0] ],[ yB[1], yB[0] ])
		# plt.plot([ xB[1], xB[1] ],[ yB[1], yB[0] ])
		# plt.plot([ xB[0], xB[1] ],[ yB[0], yB[0] ])
		# plt.plot([ xB[0], xB[1] ],[ yB[1], yB[1] ])
		
		# plt.draw()
		# plt.pause(pause)
		# plt.clf()


