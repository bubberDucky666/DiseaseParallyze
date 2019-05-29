import numpy                as np 
import matplotlib.pyplot    as plt
from matplotlib.animation   import FuncAnimation
from scipy.integrate        import odeint

def m(y, t, b, k):
    dsdx = -b * y[0] * y[1]
    didx = (b * y[0] * y[1]) - (k * y[1])
    drdx = k  * y[1]
    return [dsdx, didx, drdx]


#P is total population
#S0 is initial susceptible
#I0 is initial infected
#R0 is initial recovered

S0   = 5000000
I0   = 1
R0   = S0*.729  
P    = S0 + R0 + I0
S0, I0, R0 = S0/P, I0/P, R0/P

#b is number of indivduals infected per day (particleS per person per day)
#k is recovery time for individual per days (particle  per dayS)
b    = 7/10
k    = 1/8

#t measured in days
days = 365
t    = np.array([i for i in range(days)])

yi   = [S0, I0, R0] #initial values 
args = (b, k)

sols = odeint(m, yi, t, args)
solsT = sols.T

sY = solsT[0]
iY = solsT[1]
rY = solsT[2]


fig     = plt.figure()
x, y    = [], []
xI, yI  = [], []
xR, yR  = [], []
ax      = plt.axes(xlim=(0, days), ylim=(0, 1))

sLine,  = ax.plot([], [], animated =True,  label="Not sick bois")
iLine,  = ax.plot([], [], animated = True, label="Sick bois")
rLine,  = ax.plot([], [], animated = True, label="Recovered bois")


def init():
    sLine.set_data([], [])
    iLine.set_data([], [])
    rLine.set_data([], [])
    return sLine, iLine, rLine

def animate(i):
    global t
    global sY
    global iY
    global rY
   
    x.append(i)
    y.append(sY[i])
    sLine.set_data(x, y)

    xI.append(i)
    yI.append(iY[i])
    iLine.set_data(xI, yI)

    xR.append(i)
    yR.append(rY[i])
    rLine.set_data(xR, yR)
    return sLine, iLine, rLine

anim = FuncAnimation(fig, animate, init_func=init, frames=days, interval=40, blit=True, repeat=False)

plt.legend()
plt.show()