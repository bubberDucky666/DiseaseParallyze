
import numpy as np
from matplotlib import pyplot as plt
from matplotlib import animation 
import random


# Factors
# 1) Contact time
# 2) Contagiousness
# 3) Incubation period
# 4) Carrier or not


class Particle():
	def __init__(self, r, state):
		self.r        = r 		 # position as an ndarray
		self.state    = state    # 0 state is healthy, 1 state is sick, 2 state is dead
		self.cTime    = 0        # Counts the number of iterations next to another particle
		self.level 	  = 0		 # Severity of disease for individual
		self.carrier  = 0        # Whether or not the individual is a passive carrier (0 is false)

	def sicken(self):
		if self.state == 1:		 #Further sickens (or kills) organism			
			if self.level <= 5:
				self.level = self.level + 1
			elif self.level > 6:
				self.state = 3

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
		if particleList[i].state != 2:

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

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

#Particle parameters
mag 		  = .1
duration 	  = 10000
nSide 		  = 11
numParticles  = nSide ** 2
radius		  = .1
pause         = .0000000001

#Disease parameters
rProb 	 = 1      
  # 0 is the lowest unit, 1 is the highest unit
devTime  = 60		 # num of frames for disease to worsend in level

#Lists
particleList  = pListMake(numParticles)
healP		  = particleList.copy()
sick1P		  = [None for i in range(len(particleList))]
sick2P		  = [None for i in range(len(particleList))]
sick3P		  = [None for i in range(len(particleList))]
sick4P		  = [None for i in range(len(particleList))]
deadP		  = [None for i in range(len(particleList))]

layout(particleList, nSide)

particleList[0].state = 1
healP[0] = None
sick1P.append(particleList[0])

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
count = 0
fig   = plt.figure()
ax    = plt.axes()
ax.set_xlim(left=0,   right=nSide)
ax.set_ylim(bottom=0, top=nSide)

for i in particleList:
	print(i.carrier)

for frame in range(duration):
	
	count = count + 1
	
	move(particleList, mag)	
	
	for i in range(len(particleList)):	
		
		for j in range(i+1, len(particleList)):
			
			if distance(particleList[i], particleList[j]) <= radius:

				if particleList[i].state == 1 and particleList[j].state == 0: 
					print('Disease interaction happened')

					if disPass(particleList[j], rProb):
						particleList[j].state = 1
						print("I should become sick")
						
						if particleList[j].carrier != 1:
							print("I did become sick")
							healP[j]  = None
							sick1P[j] = particleList[j]
						else:
							pass
					
					particleList[i].cTime = particleList[i].cTime + 1
					particleList[j].cTime = particleList[j].cTime + 1
				
				elif particleList[j].state == 1 and particleList[i].state == 0:
					print("Disease interaction happened")

					if disPass(particleList[i], rProb):
						particleList[i].state = 1
						print("I should become sick")

						if particleList[i].carrier != 1:
							print("I did become sick")
							healP[i]  = None
							sick1P[i] = particleList[i]
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
			
			if part.level == 2:
				sick1P[i] = None
				sick2P[i] = part
			if part.level == 3:
				sick2P[i] = None
				sick3P[i] = part
			if part.level == 4:
				sick3P[i] = None
				sick4P[i] = part
			if part.level == 5:
				sick4P[i]             = None
				particleList[i].state = 2 
				deadP[i]              = part

	xH, yH = coordExstract(healP)
	x1, y1 = coordExstract(sick1P)
	x2, y2 = coordExstract(sick2P)
	x3, y3 = coordExstract(sick3P)
	x4, y4 = coordExstract(sick4P)
	xD, yD = coordExstract(deadP)

	plt.xlim(0, nSide)
	plt.ylim(0, nSide)
	
	plt.scatter(xH, yH, c='#00E500')
	plt.scatter(x1, y1, c='#ADE500')
	plt.scatter(x2, y2, c='#E5DF00')
	plt.scatter(x3, y3, c='#E5B700')
	plt.scatter(x4, y4, c='#E55D00')
	plt.scatter(xD, yD, c='#E50018')

	plt.draw()

	plt.pause(pause)
	plt.clf()


