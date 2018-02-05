#we use Gauge Invariance to assume that t=0 at the time of the crash.
#(this allows us to work with U(y,x) rather than U(y,x,t) )
#it is a bit of a hack.
#U_time is the positive value of 1 second (saved) in dollars.
#U_crash is negtive value of crashing.
#/2 occurs where we assume a player is moving at speed 2 and convert time=distance/speed.
#20180202: change so that python indices really are y and x
#use fanta's scheme so crashes are at 0,0 and 1,1 only.
#and assign (0,.5*U_d*x/2) , (.5*U_d*y/2, 0) to outer 2 rows and 2 cols. (using gauge invar)

import numpy as np
from pylab import *
import nash
import pdb
import random
SEED=13

def sim(S, ystart, xstart, seed=0):  #S=strategy matrix; y,x start locations
	random.seed(seed)
	y=ystart
	x=xstart
	ypos=[y]
	xpos=[x]
	done=False
	while not done:
		p_yield_y = S[y,x,0]	
		p_yield_x = S[y,x,1]
		r1=random.random()
		r2=random.random()
		if r1 < p_yield_y:
			ay=1
		else:
			ay=2
		if r2 < p_yield_x:
			ax=1
		else:
			ax=2
		y-=ay
		x-=ax
		ypos.append(y)
		xpos.append(x)
		if y<2 or x<2:
			done=True
	clf()
	plot( range(0, len(ypos)), ypos, 'k');
	plot( range(0, len(xpos)), xpos, 'k--');
	plot( [0, len(ypos)] , [0,0], 'k')
	legend(['y, Y position / meters', 'x, X position / meters'])
	xlabel('time')
	ylabel('vehicle location')
	title('Simulated trajectories')
	return (ypos, xpos)

def computeStateProbs(S, y_init, x_init): #compute prob that a state is ever visited in a run
        P=np.zeros((S.shape[0], S.shape[1]))
        P[y_init, x_init] = 1.  #start state
        y=y_init
        while(y>1):
                x=x_init
                while(x>1):
                        p_y_1 = S[y,x,0]
                        p_y_2 = 1 - p_y_1
                        p_x_1 = S[y,x,1]
                        p_x_2 = 1 - p_x_1
                        P[y-1, x-1] += P[y,x]*p_y_1*p_x_1
                        P[y-1, x-2] += P[y,x]*p_y_1*p_x_2
                        P[y-2, x-1] += P[y,x]*p_y_2*p_x_1
                        P[y-2, x-2] += P[y,x]*p_y_2*p_x_2
                        x-=1
                y-=1
        p_crash = P[0,0] + P[1,1]   #total prob of a crash occuring
        return (P,p_crash)

def solveGame(U_crash_y=-100, U_crash_x=-100, U_time=1., NY=20, NX=20):
	V = np.zeros((NY,NX,2))   #vals as pairs in 3rd dim
	S = np.zeros((NY,NX,2))   #strategies at each point, as yield probs

	#successful passing end states  [y,x,player_to_reward Y=0]
	Y=0 ; X=1
	for x in range(1,NX):    #Y has won
	    V[0,x,Y] = 0.    	    
	    V[0,x,X] = -U_time*(x/2)  
	for x in range(2,NX):
	    V[1,x,Y] = 0.            
	    V[1,x,X] = -U_time*((x-1)/2)
	for y in range(1,NY):    #X has won
	    V[y,0,X] = 0. 
	    V[y,0,Y] = -U_time*(y/2)  
	for y in range(2,NY):
	    V[y,1,X] = 0.     	    
	    V[y,1,Y] = -U_time*((y-1)/2)
	#crash end states -- overwrite
	V[0,0,Y] = U_crash_y
	V[0,0,X] = U_crash_x
	V[1,1,Y] = U_crash_y
	V[1,1,X] = U_crash_x

	#recursively compute optimal strategies and game values
	for x in range(2,NX):
		for y in range(2,NY):
			print("--"+str(y)+"_"+str(x))
			Y=[[0,0],[0,0]]
			X=[[0,0],[0,0]]

			#make subgame payoff matrix.  Actions: move-1, move-2
			for ay in [1,2]:        #action me, action u
				for ax in [1,2]:
					y_next = y-ay
					x_next = x-ax
					val_y  = V[y_next, x_next, 0]
					val_x  = V[y_next, x_next, 1]
					Y[ay-1][ax-1] = val_y-1     #each tick pays 1 second
					X[ay-1][ax-1] = val_x-1
#			print(Y)
#			print(X)
#			if y==2 \u-nd x==7:
#				pdb.set_trace()

			#compute the nashes - pynash
			G = nash.Game(Y, X)
			eqs = G.support_enumeration()
			eq_best = 0 
			vY_best = -999 #vals of both players at single best known equilibrium
			vX_best = -999
			for eq in eqs:
				b_sym = (eq[0][0]==eq[1][0])            #symetric (NB the game is not sym though)
				(vY,vX) = G[eq[0], eq[1]]         #values to players
				b_dom = ( vY<vY_best and vX < vX_best )    #is it dominated?

				if (eq_best==0) or (not b_dom and not b_sym):   #ignore dominated and non-symetric nashes (TODO Think about sym?)
					eq_best = eq     #TODO what if multiple non-dominateds? -- then do CF iteration basin thing!
					vY_best=vY
					vX_best=vX

			print("best", eq_best)
			#log results
			S[y,x,0] = eq[0][0]  #yield probs -> strategy  
			S[y,x,1] = eq[1][0]
			V[y,x,0] = vY_best
			V[y,x,1] = vX_best
	return (V,S)


if __name__ == "__main__":
	(V,S) = solveGame(U_crash_y=-20, U_crash_x=-20, U_time=1, NY=20, NX=20)

	if 1:
		print(V[:,:,0])
		print(V[:,:,1])
		print("S")
		print(S[:,:,0])
		print(S[:,:,1])

	if 1:
		figure(1)
		clf()
		imshow(V[:,:,0], interpolation='none', cmap='gray')
		xlabel("x, player X location / meters")
		ylabel("y, player Y location / meters")
		title("Player Y Values, both to play")
		colorbar();
		savefig('V.png', bbox_inches='tight')

	if 1:
		figure(5)
		clf()
		imshow(V[:,:,1], interpolation='none', cmap='gray')
		xlabel("x, player X location / meters")
		ylabel("y, player Y location / meters")
		title("Player X Values, both to play")
		colorbar();
		#savefig('VX.png', bbox_inches='tight')

	if 1:
		mstart=12
		ustart=12
		figure(2)
		clf()
		sim(S, mstart, ustart, SEED)
		savefig('sim.png', bbox_inches='tight')

	if 1:
		(P, p_crash) = computeStateProbs(S, mstart, ustart)
		figure(4)
		clf()
		imshow(P, interpolation='none', cmap='gray'); 
		colorbar();
		s='State probabilities (P_crash=%0.4f)'%p_crash
		title(s)
		xlabel("x, player X location / meters")
		ylabel("y, player Y location / meters")
		savefig('P.png', bbox_inches='tight')

	if 1:
		figure(7)
		clf()
		imshow(S[:,:,0], interpolation='none', cmap='gray')
		xlabel("x, player X location / meters")
		ylabel("y, player Y location / meters")
		title('Player Y strategy, P(yield|y,x)')
		colorbar()
		savefig('S.png', bbox_inches='tight')

	if 1:
		figure(6)
		clf()
		imshow(S[:,:,1], interpolation='none', cmap='gray')
		xlabel("x, player X location / meters")
		ylabel("y, player Y location / meters")
		title('Player X strategy, P(yield|y,x)')
		colorbar()
		#savefig('SU.png', bbox_inches='tight')

	show()
