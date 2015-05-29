# Automated Pipelining/Retiming of ditial combinational Circuits  
# This file contains all the solver based formulation and solver outputs 
# imported to ex[num].py. This file is independent of the version upgrades of other files
#
#			Embedded Solver Used: cvx-opt : http://cvxopt.org/
#				Geometric Programming : Non Linear Modeling
#
#
import os
import sys
from gen import genEquation, genEquationSeq
from modLib import gpower, mflop
from constraint import modConstraint
from cvxopt import matrix, log, exp, solvers
from status import solverStat, insertTimeStamp, insertStatus, reportStatus, lineno
from subsolver import levelBasedOptimizationFramework, PipeJoint
import time
solvers.options['show_progress'] = False

# file name stored : filename 
filename = os.path.basename(__file__)

# SOLVER BASED : OPTIMIZATION FRAMEWORK DESIGN:- CONSIDERING THERE ARE NO INTERMEDIATE OUTPUTS

# determines estimated flop inserted count: framework
# 	- determines the estimated flop count based on avg stage node count analysis
def determineEstimatedFlopCount(stageModule):
	modConst = modConstraint()
	estFlopCount = 0
	countStage = 0
	totGates = 0
	for i in range(len(stageModule)):
		countStage += 1
		totGates +=  len(stageModule[i].gateList)
	estFlopCount = totGates/countStage
	print "Estimated Flop:",estFlopCount * modConst.numPipeStage	# comment
	return estFlopCount * modConst.numPipeStage	

# SOLVER MODULE: GENERATION V1.0
# Generate the matrix equivalent for the cvx-opt module v1.0 : first Iteration
# 	The matrix generation is followed according the specified matrix tablulation as mentioned as sample on cvx-opt website
# Wire Modeling feature added: Considering that the interconnect at the input is negligible ,as flops at input are in close promixinity
# 	Rest of the gates have been modeled with their associated wires
def solverOpt(dictNode,stageModule,minNodeIn,minNodeOut,numVar,estFlop):
	#startSol1 = time.time()
	# Note: each monomial is a column of the matrix: F and constant associated in g and posynomial factor in K
	# the generation for each monomial will be based on the number of variables
	# the number of variables is equal to the number of sizing variables and the arrival time: 
	# minimalistic design framework	
	modConst = modConstraint()
	power = gpower()
	flop = mflop()
	# Considering that numVar is the number of nodes, In simplistic model of optimization (AT & x): nVar = 2*numVar
	nVar = numVar * 2	# no.gates & no.arrival times
	# initializing the matrix: Inequality constraints and Objective Constraint Mapping (F)
	mf = matrix((0.0),(nVar,1))
	# initializing the matrix: store the constants associated with monomials (g)	
	mg = matrix((0.0),(1,1))
	#initializing  the List for K 
	mk = []
	# the objective function is added at the start of the matrix formation
	# here the selected objective function is : Power constraints: Min(Power)
	
	# POWER CONSTRAINTS:(Objective Function):
	#fw.write('\n\nPower Constraints: Objective Function\nMin()\n')
	pCount = 0	# count the number of monomials in power equation
	for i in range(0,len(stageModule)):			
		for j in range(len(stageModule[i].gateList)):	
			SelfGate = stageModule[i].gateList[j]
			# monomial: constant
			pcon1 = 0.5 * dictNode[SelfGate].gateSignalProb * modConst.freq * dictNode[SelfGate].unitCapInt * pow(power.v_dd,2)
			# populate for the matrix-cvx(g)
			mb = matrix((0.0),(1,1))			# initialize matrix b of 1x1 set
			mb[0] = pcon1
			#mg = matrix([[mg,mb]])				# g matric : concatenate min-array mb to mg				
			# monomial: inequality map
			ma = matrix((0.0),(nVar,1)) 
			ma[dictNode[SelfGate].gateSerNum] = 1		# set the variable : exponent value
			#mf = matrix([[mf],[ma]])			# F matrix: concatenate min-array ma to mf
			
			if i == 0 and j == 0:
				mf = ma				# F matrix operation
				mg = mb				# g matric operation
			else:	
				mf = matrix([[mf],[ma]])	# F matrix: concatenate min-array ma to mf
				mg = matrix([[mg,mb]])		# g matric : concatenate min-array mb to mg	
			
			pCount += 1						
			#<1> line = '0.5 alpha_' + SelfGate + " freq " + ' Cint_' + SelfGate + ' x_'+ SelfGate +' Vdd^2 + '
			for k in range(len(dictNode[SelfGate].fanOutList)):
				fanOutGate = dictNode[SelfGate].fanOutList[k]
				# monomial: constant
				pcon2 = 0.5 * dictNode[SelfGate].gateSignalProb * modConst.freq * dictNode[fanOutGate].unitCapInt * pow(power.v_dd,2) 
				# populate for the matrix-cvx(g)
				mb = matrix((0.0),(1,1))			# initialize matrix b of 1x1 set
				mb[0] = pcon2				
				mg = matrix([[mg,mb]])				# g matrix : concatenate min-array mb to mg	
				# monomial: inequality map
				ma = matrix((0.0),(nVar,1)) 
				ma[dictNode[fanOutGate].gateSerNum] = 1		# set the variable : exponent value
				mf = matrix([[mf],[ma]])			# F matrix: concatenate min-array ma to mf
				pCount += 1												
				#<2> line += '0.5 alpha_' + SelfGate +" freq "+ ' Cint_' + fanOutGate + ' x_'+ fanOutGate + ' Vdd^2 + '
			if SelfGate in minNodeOut:
				# monomial: constant
				pcon3 = 0.5 * dictNode[SelfGate].gateSignalProb * modConst.freq * modConst.Cload * pow(power.v_dd,2)
				# populate for the matrix-cvx(g)
				mb = matrix((0.0),(1,1))			# initialize matrix b of 1x1 set
				mb[0] = pcon3
				mg = matrix([[mg,mb]])				# g matrix : concatenate min-array mb to mg	
				# monomial: inequality map
				ma = matrix((0.0),(nVar,1)) 					
				#ma[dictNode[SelfGate].gateSerNum] = 1		# set the variable : exponent value	
				mf = matrix([[mf],[ma]])			# F matrix: concatenate min-array ma to mf
				pCount += 1	
				#<3> line += '0.5 alpha_' + SelfGate +" freq "+ ' Cload' + ' Vdd^2 +'
			# monomial: constant
			pcon4 = dictNode[SelfGate].unitIleak * power.v_dd 
			# populate for the matrix-cvx(g)
			mb = matrix((0.0),(1,1))			# initialize matrix b of 1x1 set
			mb[0] = pcon4	
			mg = matrix([[mg,mb]])				# g matrix : concatenate min-array mb to mg	
			# monomial: inequality map
			ma = matrix((0.0),(nVar,1)) 					
			ma[dictNode[SelfGate].gateSerNum] = 1		# set the variable : exponent value	
			mf = matrix([[mf],[ma]])			# F matrix: concatenate min-array ma to mf
			pCount += 1											
			#<4> line += 'Ileak_' + SelfGate + ' x_' + SelfGate + 'Vdd '	
			#line += '+ \n'
	mk.append(pCount)		
	
	# TIMING CONSTRAINTS: (Inequality Constraints):	
	# Note: Considering the input pins has arrival time of 0 units
	for i in range(0,len(stageModule)):			
		for j in range(len(stageModule[i].gateList)):	
			SelfGate = stageModule[i].gateList[j]
			# nodes which have fan-in from input pins completely
			isFlag = 0
			# nodes which have at least a single fan-in from a valid node.
			countMode2 = 0
			for m in range(len(dictNode[SelfGate].fanInList)):
				if dictNode[SelfGate].fanInList[m] not in minNodeIn:
					# print dictNode[SelfGate].fanInList[m] 
					# monomial : constant
					con1 = power.retAlphaPowerDelayTime(dictNode[SelfGate].unitRes,1,dictNode[SelfGate].unitCapInt)
					#con1 = 0.69 * dictNode[SelfGate].unitRes * dictNode[SelfGate].unitCapInt
					countMode2 += 1
					# populate for the matrix-cvx(g)
					mb = matrix((0.0),(1,1))	# initialize matrix b of 1x1 set
					mb[0] = con1			# set the variable const: constant value for the monomial
					mg = matrix([[mg,mb]])		# g matrix : concatenate min-array mb to mg
					# print SelfGate,con1 # comment 
				#<1>	# monomial : __inequality map__
					# populate the matrix-cvx(F)
					ma = matrix((0.0),(nVar,1)) 
					ma[numVar + dictNode[SelfGate].gateSerNum] = -1		# set the variable : exponent value
					mf = matrix([[mf],[ma]])				# F matrix: concatenate min-array ma to mf			
					# line = "0.69R_"+ SelfGate + " ~AT_"+ SelfGate +" Cint_"+ SelfGate 
					for k in range(len(dictNode[SelfGate].fanOutList)):
						FanOutGate = dictNode[stageModule[i].gateList[j]].fanOutList[k]
						# monomial: constant
						con2 = power.retAlphaPowerDelayTime(dictNode[SelfGate].unitRes,1,dictNode[SelfGate].unitCapInt)
						#con2 = 0.69 * dictNode[SelfGate].unitRes * dictNode[FanOutGate].unitCapInt
						countMode2 += 1
						# populate for the matrix-cvx(g)
						mb = matrix((0.0),(1,1))	# initialize matrix b of 1x1 set
						mb[0] = con2			# set the variable const: constant value for the monomial
						mg = matrix([[mg,mb]])		# g matric : concatenate min-array mb to mg
						# print SelfGate,con2 #comment
					#<2>	# monomial : __inequality map__
						# populate the matrix-cvx(F)
						ma = matrix((0.0),(nVar,1)) 
						ma[dictNode[SelfGate].gateSerNum] = -1			# set the variable : exponent value
						ma[dictNode[FanOutGate].gateSerNum] = 1			# set the variable : exponent value
						ma[numVar + dictNode[SelfGate].gateSerNum] = -1	# set the variable : exponent value						
						mf = matrix([[mf],[ma]])				# F matrix: concatenate min-array ma to mf			
						# line += " + " + " 0.69R_" + SelfGate + " ~x_"+ SelfGate + " Cint_"+ FanOutGate + " x_"+ FanOutGate + "~AT_ "+SelfGate
					# modify to model for Cload flops at output
					if not dictNode[SelfGate].fanOutList: 
						# monomial: constant
						con3 = power.retAlphaPowerDelayTime(dictNode[SelfGate].unitRes,1,modConst.Cload)
						#con3 = 0.69 * dictNode[SelfGate].unitRes *  modConst.Cload 
						countMode2 += 1 
						# populate for the matrix-cvx(g)
						mb = matrix((0.0),(1,1))	# initialize matrix b of 1x1 set
						mb[0] = con3			# set the variable const: constant value for the monomial
						mg = matrix([[mg,mb]])		# g matric : concatenate min-array mb to mg
						# print SelfGate,con3 # comment
					#<3>	# monomial: inequality map 
						ma = matrix((0.0),(nVar,1)) 
						ma[dictNode[SelfGate].gateSerNum] = -1			# set the variable : exponent value
						ma[numVar + dictNode[SelfGate].gateSerNum] = -1		# set the variable : exponent value
						mf = matrix([[mf],[ma]])				# F matrix: concatenate min-array ma to mf						
						# line += " + 0.69R_"+ SelfGate + " ~x_" + SelfGate + " Cload" + " ~AT_" + SelfGate 
							
					# monomial: constant
					con4 = 1
					countMode2 += 1
					# populate for the matrix-cvx(g)
					mb = matrix((0.0),(1,1))	# initialize matrix b of 1x1 set
					mb[0] = con4			# set the variable const: constant value for the monomial
					mg = matrix([[mg,mb]])		# g matric : concatenate min-array mb to mg
					# print SelfGate,con4 # comment
				#<4>	# monomial: inequality map
					ma = matrix((0.0),(nVar,1)) 
					ma[numVar + dictNode[dictNode[SelfGate].fanInList[m]].gateSerNum] = 1		# set the variable : exponent value
					ma[numVar + dictNode[SelfGate].gateSerNum] = -1					# set the variable : exponent value
					mf = matrix([[mf],[ma]])							# F matrix: concatenate min-array ma to mf										
					# line += " + AT_"+dictNode[SelfGate].fanInList[m] + "~AT_" + SelfGate 
					mk.append(countMode2)
					countMode2 = 0	# symmetrical repeat nullifier FO gates
					# fw.write(line+" <= 1 \n")
				else:
					isFlag += 1
			# nodes which have fan-in from input pins completely		
			if len(dictNode[SelfGate].fanInList) == isFlag:
				countMode1 = 0
				# monomial: constant
				con5 = power.retAlphaPowerDelayTime(dictNode[SelfGate].unitRes,1,dictNode[SelfGate].unitCapInt)
				#con5 = 0.69 * dictNode[SelfGate].unitRes * dictNode[SelfGate].unitCapInt
				countMode1 += 1
				# populate for the matrix-cvx(g)
				mb = matrix((0.0),(1,1))	# initialize matrix b of 1x1 set
				mb[0] = con5			# set the variable const: constant value for the monomial
				mg = matrix([[mg,mb]])		# g matric : concatenate min-array mb to mg
				# print SelfGate,con5 
			#<5>	# monomial: inequality map
				ma = matrix((0.0),(nVar,1)) 
				ma[numVar + dictNode[SelfGate].gateSerNum] = -1					# set the variable : exponent value
				mf = matrix([[mf],[ma]])							# F matrix: concatenate min-array ma to mf	
				#line = "0.69R_"+ SelfGate + " ~AT_"+ SelfGate +" Cint_"+ SelfGate 
				for z in range(len(dictNode[SelfGate].fanOutList)):
					FanOutGate = dictNode[stageModule[i].gateList[j]].fanOutList[z]
					# monomial: constant
					con6 = power.retAlphaPowerDelayTime(dictNode[SelfGate].unitRes,1,dictNode[SelfGate].unitCapInt)
					#con6 = 0.69 * dictNode[SelfGate].unitRes * dictNode[FanOutGate].unitCapInt
					countMode1 += 1
					# populate for the matrix-cvx(g)
					mb = matrix((0.0),(1,1))	# initialize matrix b of 1x1 set
					mb[0] = con6			# set the variable const: constant value for the monomial
					mg = matrix([[mg,mb]])		# g matric : concatenate min-array mb to mg
					# print SelfGate,con6 # comment
				#<6>	# monomial: inequality map
					ma = matrix((0.0),(nVar,1)) 
					ma[dictNode[SelfGate].gateSerNum] = -1						# set the variable : exponent value
					ma[dictNode[FanOutGate].gateSerNum] = 1						# set the variable : exponent value
					ma[numVar + dictNode[SelfGate].gateSerNum] = -1					# set the variable : exponent value
					mf = matrix([[mf],[ma]])							# F matrix: concatenate min-array ma to mf				
					# line += " + " + " 0.69R_" + SelfGate + " ~x_"+ SelfGate + " Cint_"+ FanOutGate + " x_"+ FanOutGate + "~AT_ "+SelfGate	
				mk.append(countMode1)	# append to mk list
				#fw.write(line+" <= 1 \n")
			# equation for maximum delay path limit for circuit
			if not dictNode[SelfGate].fanOutList: 
				# monomial: constant
				con7 = 1/float(modConst.ATmax)
				# populate for the matrix-cvx(g)
				mb = matrix((0.0),(1,1))	# initialize matrix b of 1x1 set
				mb[0] = con7			# set the variable const: constant value for the monomial
				mg = matrix([[mg,mb]])		# g matric : concatenate min-array mb to mg
				# print SelfGate,con7 # comment
			#<7>	# monomialL: inequality map
				ma = matrix((0.0),(nVar,1)) 
				ma[numVar + dictNode[SelfGate].gateSerNum] = 1					# set the variable : exponent value
				mf = matrix([[mf],[ma]])							# F matrix: concatenate min-array ma to mf					
				mk.append(1)	# append to mk list
				#finline = "(1/AT_max)"+" AT_"+SelfGate +" <= 1\n" 
				

	# AREA  CONSTRAINTS: (Inequality Constraints) 
	for i in range(0,len(stageModule)):			
		for j in range(len(stageModule[i].gateList)):	
			SelfGate = stageModule[i].gateList[j]
			# monomial constant
			ncon1 = (1/float(modConst.Amax-(flop.fArea * estFlop))) * dictNode[SelfGate].unitArea
			# populate for the matrix-cvx(g)
			mb = matrix((0.0),(1,1))		# initialize matrix b of 1x1 set
			mb[0] = ncon1				# set the variable const: constant value for the monomial
			mg = matrix([[mg,mb]])			# g matric : concatenate min-array mb to mg						
			# monomial: Inequality map
			ma = matrix((0.0),(nVar,1)) 
			ma[dictNode[SelfGate].gateSerNum] = 1					# set the variable : exponent value
			mf = matrix([[mf],[ma]])						# F matrix: concatenate min-array ma to mf				
			#lineArea += "(1/Amax)"+" A_"+ SelfGate + " x_"	+ SelfGate +  " + "
	mk.append(numVar)	
					
	# SIZING CONSTRAINTS: (Inequality Constraints) 		
	for i in range(0,len(stageModule)):			
		for j in range(len(stageModule[i].gateList)):	
			SelfGate = stageModule[i].gateList[j]
			if dictNode[SelfGate].gateType == 'BUFF':
				cmax = 1/float(modConst.xmaxBuff)
			else:		
				cmax = 1/float(modConst.xmax)	
			#cmax = 1/float(modConst.xmax)					
			# monomial : constant
			# populate for the matrix-cvx(g)
			mb = matrix((0.0),(1,1))		# initialize matrix b of 1x1 set
			mb[0] = cmax				# set the variable const: constant value for the monomial
			mg = matrix([[mg,mb]])			# g matric : concatenate min-array mb to mg	
			# monomial : Inequality map
			ma = matrix((0.0),(nVar,1)) 
			ma[dictNode[SelfGate].gateSerNum] = 1					# set the variable : exponent value
			mf = matrix([[mf],[ma]])						# F matrix: concatenate min-array ma to mf
			mk.append(1)								# single monomial: Inequality								
			#fw.write("(1/x_max) x_"+SelfGate+" <= 1 \n")
			cmin = float(modConst.xmin)	
			# monomial : constant
			# populate for the matrix-cvx(g)
			mb = matrix((0.0),(1,1))		# initialize matrix b of 1x1 set
			mb[0] = cmin				# set the variable const: constant value for the monomial
			mg = matrix([[mg,mb]])			# g matric : concatenate min-array mb to mg	
			# monomial : Inequality map
			ma = matrix((0.0),(nVar,1)) 
			ma[dictNode[SelfGate].gateSerNum] = -1					# set the variable : exponent value
			mf = matrix([[mf],[ma]])						# F matrix: concatenate min-array ma to mf
			mk.append(1)								# single monomial: Inequality				
			#fw.write("~x_"+SelfGate+" x_min " +" <= 1\n")
	#fw.write(lineArea +" <= 1\n")
	#endSol1 = time.time() 
	#print endSol1 - startSol1	
	
	# Test cases Report
	#getPrintLargeMatrix(mf,mg.trans()) #comment
	#print mk #comment
		
	# SOLVER BASED FRAMEWORK
	# Module block setup framework
	result = []
	g = log(mg)

	startSolve = time.time()
	sol = solvers.gp(mk, mf.trans(), g)
	result = exp(sol['x'])
	endSolve = time.time() 
	insertTimeStamp(filename,lineno(),'solOpt_gp','solverOpt_gp:['+str(endSolve-startSolve)+']')	
	
	if sol['status'] == 'optimal':
		sline = ' module1.0: optimization succes! '
		skey = 'opt1.0 succes'
		insertStatus(filename,lineno(),skey,sline)
		# store the dimension
		dime = mf.size 
		sline = " opt1.0 Mode: variables "+ str(dime[0])+ " monomials "+ str(dime[1])+ " inequalities "+ str(len(mk)) 
		skey = 'opt1.0 successDim'
		insertStatus(filename,lineno(),skey,sline)
	else:
		sline = 'optimization fail : Too tight timing constraints '
		skey = 'opt1.0 fail'
		insertStatus(filename,lineno(),skey,sline)	
	#result = exp(solvers.gp(mk, mf.trans(), g)['x'])		# gp solver : cvx-opt framework
	#print result # comment

	#endSol1 = time.time()	
	#executionTime = endSol1 - startSol1
	#insertTimeStamp(filename,lineno(),'solverOpt','solverOpt:['+str(executionTime)+']')
	# return the gate sizing and arrival timing optimal values
	return result
	

	
# SOLVER MODULE: GENERATION V2.0
# Generate the matrix equivalent for the cvx-opt module v2.0 : second Iteration
# 	The matrix generation is followed according the specified matrix tablulation as mentioned as sample on cvx-opt website		
#	This is a joint sub-combinational modules optimization over area and power
# 	The timing constraints are modified to suit the minimum path: 		
def solverOptSeq(dictNode,stageModule,minNodeIn,minNodeOut,numVar,estFlop,SeqBlockJoint):
	# Note: each monomial is a column of the matrix: F and constant associated in g and posynomial factor in K
	# the generation for each monomial will be based on the number of variables
	# the number of variables is equal to the number of sizing variables and the arrival time: 
	# minimalistic design framework	
	modConst = modConstraint()
	power = gpower()
	flop = mflop()
	# Considering that numVar is the number of nodes, In simplistic model of optimization (AT & x): nVar = 2*numVar
	nVar = numVar * 2	# no.gates & no.arrival times
	# initializing the matrix: Inequality constraints and Objective Constraint Mapping (F)
	mf = matrix((0.0),(nVar,1))
	# initializing the matrix: store the constants associated with monomials (g)	
	mg = matrix((0.0),(1,1))
	#initializing  the List for K 
	mk = []
	# the objective function is added at the start of the matrix formation
	# here the selected objective function is : Power constraints: Min(Power)
	
			
	# POWER CONSTRAINTS:(Objective Function):
	#fw.write('\n\nPower Constraints:Objective Function\nMin()\n')
	pCount = 0	# count the number of monomials in power equation
	for i in range(0,len(stageModule)):			
		for j in range(len(stageModule[i].gateList)):	
			SelfGate = stageModule[i].gateList[j]
			# self gate dynamic power:
			# monomial: constant
			pcon1 = 0.5 * modConst.freq * pow(power.v_dd,2) * dictNode[SelfGate].unitCapInt * dictNode[SelfGate].gateSignalProb
			# populate for the matrix-cvx(g)
			mb = matrix((0.0),(1,1))			# initialize matrix b of 1x1 set
			mb[0] = pcon1
			#mg = matrix([[mg,mb]])				# g matric : concatenate min-array mb to mg				
			# monomial: inequality map
			ma = matrix((0.0),(nVar,1)) 
			ma[dictNode[SelfGate].gateSerNum] = 1		# set the variable : exponent value
			#mf = matrix([[mf],[ma]])			# F matrix: concatenate min-array ma to mf
			
			if i == 0 and j == 0:
				mf = ma				# F matrix operation
				mg = mb				# g matric operation
			else:	
				mf = matrix([[mf],[ma]])	# F matrix: concatenate min-array ma to mf
				mg = matrix([[mg,mb]])		# g matric : concatenate min-array mb to mg	
			
			pCount += 1						
			# <1> linePower = str(0.5) + " alpha_" + SelfGate + " freq "+" Vdd^2 Cint_" + SelfGate +" x_"+SelfGate
			if dictNode[SelfGate].pipeJoint != 1: 
				# non pipe Joint gate
				for k in range(len(dictNode[SelfGate].fanOutList)):
					gateFanOut = dictNode[SelfGate].fanOutList[k]					
					# monomial: constant
					pcon2 = 0.5 * modConst.freq * pow(power.v_dd,2) * dictNode[gateFanOut].unitCapInt * dictNode[SelfGate].gateSignalProb
					# populate for the matrix-cvx(g)
					mb = matrix((0.0),(1,1))			# initialize matrix b of 1x1 set
					mb[0] = pcon2
					mg = matrix([[mg,mb]])			# g matric : concatenate min-array mb to mg						
					# monomial: inequality map
					ma = matrix((0.0),(nVar,1)) 
					ma[dictNode[gateFanOut].gateSerNum] = 1		# set the variable : exponent value
					mf = matrix([[mf],[ma]])			# F matrix: concatenate min-array ma to mf
					pCount += 1							
					#<2> linePower += " + " + str(0.5) + " alpha_"+ gateFanOut + " freq " +" Vdd^2 Cint_" + gateFanOut +" x_"+ gateFanOut
				if dictNode[SelfGate].fanOutList == []:	# output gates nodes
					# monomial: constant
					pcon3 = 0.5 * modConst.freq * pow(power.v_dd,2) * modConst.Cload * dictNode[SelfGate].gateSignalProb
					# populate for the matrix-cvx(g)
					mb = matrix((0.0),(1,1))			# initialize matrix b of 1x1 set
					mb[0] = pcon3
					mg = matrix([[mg,mb]])			# g matric : concatenate min-array mb to mg						
					# monomial: inequality map
					ma = matrix((0.0),(nVar,1)) 
					mf = matrix([[mf],[ma]])			# F matrix: concatenate min-array ma to mf
					pCount += 1	
					#<3> linePower += " + " + str(0.5) + " alpha_"+ SelfGate + " freq " +"Vdd^2 Cload"		
			else:
				# pipeJoint gate
				# monomial: constant
				pcon4 = 0.5 * modConst.freq * pow(power.v_dd,2) * flop.fLoad * dictNode[SelfGate].gateSignalProb
				# populate for the matrix-cvx(g)
				mb = matrix((0.0),(1,1))			# initialize matrix b of 1x1 set
				mb[0] = pcon4
				mg = matrix([[mg,mb]])			# g matric : concatenate min-array mb to mg						
				# monomial: inequality map
				ma = matrix((0.0),(nVar,1)) 
				mf = matrix([[mf],[ma]])			# F matrix: concatenate min-array ma to mf
				pCount += 1		
				#<4>linePower += " + "+ str(0.5) + " alpha_"+ SelfGate + " freq " +" Vdd^2 Cflop"   
			
			# monomial: constant
			pcon5 = power.v_dd * dictNode[SelfGate].unitIleak
			# populate for the matrix-cvx(g)
			mb = matrix((0.0),(1,1))			# initialize matrix b of 1x1 set
			mb[0] = pcon5
			mg = matrix([[mg,mb]])			# g matric : concatenate min-array mb to mg				
			# monomial: inequality map
			ma = matrix((0.0),(nVar,1)) 
			ma[dictNode[SelfGate].gateSerNum] = 1		# set the variable : exponent value
			mf = matrix([[mf],[ma]])			# F matrix: concatenate min-array ma to mf
			pCount += 1	
			#linePower += " + Ileak x_"+ SelfGate + " Vdd"				
			#fw.write(linePower+"\n")					
	mk.append(pCount)


	# TIMING CONSTRAINTS: (Inequality Constraints):	
	# Note: Considering the input pins has arrival time of 0 units
	#fw.write('\n\nTiming Equations: \n')
	tCount = 0	# count the number of monomials in timing equation
	for i in range(0,len(stageModule)):			
		for j in range(len(stageModule[i].gateList)):
			# print "AT_",stageModule[i].gateList[j],"=", dictNode[stageModule[i].gateList[j]].fanOutList #comment
			SelfGate = stageModule[i].gateList[j]
			#SelfGateStage = dictNode[SelfGate].stageEstimate	# stores the self gate stage
			isFlag = 0
			# nodes which have at least a single fan-in from a valid node.
			for m in range(len(dictNode[SelfGate].fanInList)):
				if dictNode[SelfGate].fanInList[m] not in minNodeIn:								
					# print dictNode[SelfGate].fanInList[m] 
					# monomial: constant
					tcon1 = power.retAlphaPowerDelayTime(dictNode[SelfGate].unitRes,1,dictNode[SelfGate].unitCapInt)
					#tcon1 = 0.69 * dictNode[SelfGate].unitRes * dictNode[SelfGate].unitCapInt
					# populate for the matrix-cvx(g)
					mb = matrix((0.0),(1,1))				# initialize matrix b of 1x1 set
					mb[0] = tcon1
					mg = matrix([[mg,mb]])					# g matric : concatenate min-array mb to mg						
					# monomial: inequality map
					ma = matrix((0.0),(nVar,1)) 
					ma[numVar + dictNode[SelfGate].gateSerNum] = -1		# set the variable : exponent value
					mf = matrix([[mf],[ma]])				# F matrix: concatenate min-array ma to mf
					tCount += 1													
					#line = "0.69R_"+ SelfGate + " ~AT_"+ SelfGate +" Cint_"+ SelfGate 
					
					for k in range(len(dictNode[SelfGate].fanOutList)):
						FanOutGate = dictNode[stageModule[i].gateList[j]].fanOutList[k]
						# Assumption : since any single cross stage interface is taken as selfgate pipeJoint, its always ensured that the fan-outs of self gate belong to same stage						
						# monomial: constant
						tcon2 = power.retAlphaPowerDelayTime(dictNode[SelfGate].unitRes,1,dictNode[SelfGate].unitCapInt)
						#tcon2 = 0.69 * dictNode[SelfGate].unitRes *  dictNode[FanOutGate].unitCapInt
						# populate for the matrix-cvx(g)
						mb = matrix((0.0),(1,1))				# initialize matrix b of 1x1 set
						mb[0] = tcon2
						mg = matrix([[mg,mb]])					# g matric : concatenate min-array mb to mg						
						# monomial: inequality map
						ma = matrix((0.0),(nVar,1)) 
						ma[dictNode[SelfGate].gateSerNum] = -1			# set the variable : exponent value
						ma[dictNode[FanOutGate].gateSerNum] =  1		# set the variable : exponent value											
						ma[numVar + dictNode[SelfGate].gateSerNum] = -1		# set the variable : exponent value
						mf = matrix([[mf],[ma]])				# F matrix: concatenate min-array ma to mf
						tCount += 1
						#line += " + " + " 0.69R_" + SelfGate + " ~x_"+ SelfGate + " Cint_"+ FanOutGate + " x_"+ FanOutGate + "~AT_ "+SelfGate
						
					# modify to model for Cload flops at output
					if not dictNode[SelfGate].fanOutList: # for no fanout(s): considerd as output nodes
						# monomial: constant
						tcon3 = power.retAlphaPowerDelayTime(dictNode[SelfGate].unitRes,1,modConst.Cload)
						#tcon3 = 0.69 * dictNode[SelfGate].unitRes * modConst.Cload
						# populate for the matrix-cvx(g)
						mb = matrix((0.0),(1,1))				# initialize matrix b of 1x1 set
						mb[0] = tcon3
						mg = matrix([[mg,mb]])					# g matric : concatenate min-array mb to mg						
						# monomial: inequality map
						ma = matrix((0.0),(nVar,1)) 
						ma[ dictNode[SelfGate].gateSerNum] 	   = -1		# set the variable : exponent value
						ma[numVar + dictNode[SelfGate].gateSerNum] = -1		# set the variable : exponent value						
						mf = matrix([[mf],[ma]])				# F matrix: concatenate min-array ma to mf
						tCount += 1					
						#line += " + 0.69R_"+ SelfGate + " ~x_" + SelfGate + " Cload" + " ~AT_" + SelfGate 
							
					if dictNode[dictNode[SelfGate].fanInList[m]].pipeJoint != 1:
						# monomial: constant
						tcon4 = 1
						# populate for the matrix-cvx(g)
						mb = matrix((0.0),(1,1))				# initialize matrix b of 1x1 set
						mb[0] = tcon4
						mg = matrix([[mg,mb]])					# g matric : concatenate min-array mb to mg						
						# monomial: inequality map
						ma = matrix((0.0),(nVar,1)) 
						ma[numVar + dictNode[dictNode[SelfGate].fanInList[m]].gateSerNum] = 1		# set the variable : exponent value	
						ma[numVar + dictNode[SelfGate].gateSerNum] = -1					# set the variable : exponent value						
						mf = matrix([[mf],[ma]])							# F matrix: concatenate min-array ma to mf					
						tCount += 1
						#line += " + AT_"+dictNode[SelfGate].fanInList[m] + "~AT_" + SelfGate 
					mk.append(tCount)
					tCount = 0	
					#fw.write(line+" <= 1 \n")
				else:
					isFlag += 1
			# nodes which have fan-in from input pins completely		
			if len(dictNode[SelfGate].fanInList) == isFlag:
				# monomial: constant
				tcon5 = power.retAlphaPowerDelayTime(dictNode[SelfGate].unitRes,1,dictNode[SelfGate].unitCapInt)
				#tcon5 = 0.69 * dictNode[SelfGate].unitRes * dictNode[SelfGate].unitCapInt
				# populate for the matrix-cvx(g)
				mb = matrix((0.0),(1,1))				# initialize matrix b of 1x1 set
				mb[0] = tcon5
				mg = matrix([[mg,mb]])					# g matric : concatenate min-array mb to mg						
				# monomial: inequality map
				ma = matrix((0.0),(nVar,1)) 
				ma[numVar + dictNode[SelfGate].gateSerNum] = -1		# set the variable : exponent value						
				mf = matrix([[mf],[ma]])				# F matrix: concatenate min-array ma to mf			
				tCount += 1
				#line = "0.69R_"+ SelfGate + " ~AT_"+ SelfGate +" Cint_"+ SelfGate 
				
				for z in range(len(dictNode[SelfGate].fanOutList)):
					FanOutGate = dictNode[stageModule[i].gateList[j]].fanOutList[z]
					# if SelfGate is a pipeline joint then compute the load gates else flop load 
					if dictNode[SelfGate].pipeJoint != 1:
						# monomial: constant
						tcon6 = power.retAlphaPowerDelayTime(dictNode[SelfGate].unitRes,1,dictNode[SelfGate].unitCapInt)
						#tcon6 = 0.69 * dictNode[SelfGate].unitRes * dictNode[FanOutGate].unitCapInt
						# populate for the matrix-cvx(g)
						mb = matrix((0.0),(1,1))				# initialize matrix b of 1x1 set
						mb[0] = tcon6
						mg = matrix([[mg,mb]])					# g matric : concatenate min-array mb to mg						
						# monomial: inequality map
						ma = matrix((0.0),(nVar,1)) 
						ma[dictNode[SelfGate].gateSerNum] = -1			# set the variable : exponent value	
						ma[dictNode[FanOutGate].gateSerNum] = 1			# set the variable : exponent value
						ma[numVar + dictNode[SelfGate].gateSerNum] = -1		# set the variable : exponent value						
						mf = matrix([[mf],[ma]])				# F matrix: concatenate min-array ma to mf					
						tCount += 1
						#line += " + " + " 0.69R_" + SelfGate + " ~x_"+ SelfGate + " Cint_"+ FanOutGate + " x_"+ FanOutGate + "~AT_ "+SelfGate
							
					else:					
						# monomial: constant
						tcon7 = power.retAlphaPowerDelayTime(dictNode[SelfGate].unitRes,1,flop.fLoad)
						#tcon7 = 0.69 * dictNode[SelfGate].unitRes * flop.fLoad
						# populate for the matrix-cvx(g)
						mb = matrix((0.0),(1,1))				# initialize matrix b of 1x1 set
						mb[0] = tcon7
						mg = matrix([[mg,mb]])					# g matric : concatenate min-array mb to mg						
						# monomial: inequality map
						ma = matrix((0.0),(nVar,1)) 
						ma[dictNode[SelfGate].gateSerNum] = -1			# set the variable : exponent value	
						ma[numVar + dictNode[SelfGate].gateSerNum] = -1		# set the variable : exponent value						
						mf = matrix([[mf],[ma]])				# F matrix: concatenate min-array ma to mf					
						tCount += 1
						#line += " + " + " 0.69R_" + SelfGate + " ~x_"+ SelfGate + " Cflop" + "~AT_ "+ SelfGate						
						break 	# single flop drive multiple FO 
				mk.append(tCount)
				tCount = 0									
				#fw.write(line+" <= 1 \n")
				
			# equation for maximum delay path limit for circuit
			if not dictNode[SelfGate].fanOutList: 
				# monomial: constant
				tcon8 = 1/float(modConst.ATpipe)
				# populate for the matrix-cvx(g)
				mb = matrix((0.0),(1,1))				# initialize matrix b of 1x1 set
				mb[0] = tcon8
				mg = matrix([[mg,mb]])					# g matric : concatenate min-array mb to mg						
				# monomial: inequality map
				ma = matrix((0.0),(nVar,1)) 
				ma[numVar + dictNode[SelfGate].gateSerNum] = 1		# set the variable : exponent value						
				mf = matrix([[mf],[ma]])				# F matrix: concatenate min-array ma to mf	
				mk.append(1)			
				#finline = "AT_"+SelfGate+"~AT_pipe "+" <=1\n"
			# equation for pipeline timing limits
			if dictNode[SelfGate].pipeJoint == 1: 
				# monomial: constant
				tcon8 = 1/float(modConst.ATpipe)
				# populate for the matrix-cvx(g)
				mb = matrix((0.0),(1,1))				# initialize matrix b of 1x1 set
				mb[0] = tcon8
				mg = matrix([[mg,mb]])					# g matric : concatenate min-array mb to mg						
				# monomial: inequality map
				ma = matrix((0.0),(nVar,1)) 
				ma[numVar + dictNode[SelfGate].gateSerNum] = 1		# set the variable : exponent value						
				mf = matrix([[mf],[ma]])				# F matrix: concatenate min-array ma to mf
				mk.append(1)			
				#finline = "AT_"+SelfGate+"~AT_pipe "+" <=1\n"
			#fw.write(finline)
			#finline = ''

				

	# AREA  CONSTRAINTS: (Inequality Constraints) 
	for i in range(0,len(stageModule)):			
		for j in range(len(stageModule[i].gateList)):	
			SelfGate = stageModule[i].gateList[j]
			# monomial constant
			ncon1 = (1/float(modConst.Amax-(flop.fArea * estFlop))) * dictNode[SelfGate].unitArea
			# populate for the matrix-cvx(g)
			mb = matrix((0.0),(1,1))		# initialize matrix b of 1x1 set
			mb[0] = ncon1				# set the variable const: constant value for the monomial
			mg = matrix([[mg,mb]])			# g matric : concatenate min-array mb to mg						
			# monomial: Inequality map
			ma = matrix((0.0),(nVar,1)) 
			ma[dictNode[SelfGate].gateSerNum] = 1					# set the variable : exponent value
			mf = matrix([[mf],[ma]])						# F matrix: concatenate min-array ma to mf				
			#lineArea += "(1/Amax)"+" A_"+ SelfGate + " x_"	+ SelfGate +  " + "
	mk.append(numVar)	
					
	# SIZING CONSTRAINTS: (Inequality Constraints) 		
	for i in range(0,len(stageModule)):			
		for j in range(len(stageModule[i].gateList)):	
			SelfGate = stageModule[i].gateList[j]	
			if dictNode[SelfGate].gateType == 'BUFF':
				cmax = 1/float(modConst.xmaxBuff)
			else:		
				cmax = 1/float(modConst.xmax)			
			#cmax = 1/float(modConst.xmax)	
			# monomial : constant
			# populate for the matrix-cvx(g)
			mb = matrix((0.0),(1,1))		# initialize matrix b of 1x1 set
			mb[0] = cmax				# set the variable const: constant value for the monomial
			mg = matrix([[mg,mb]])			# g matric : concatenate min-array mb to mg	
			# monomial : Inequality map
			ma = matrix((0.0),(nVar,1)) 
			ma[dictNode[SelfGate].gateSerNum] = 1					# set the variable : exponent value
			mf = matrix([[mf],[ma]])						# F matrix: concatenate min-array ma to mf
			mk.append(1)								# single monomial: Inequality								
			#fw.write("(1/x_max) x_"+SelfGate+" <= 1 \n")
			cmin = float(modConst.xmin)	
			# monomial : constant
			# populate for the matrix-cvx(g)
			mb = matrix((0.0),(1,1))		# initialize matrix b of 1x1 set
			mb[0] = cmin				# set the variable const: constant value for the monomial
			mg = matrix([[mg,mb]])			# g matric : concatenate min-array mb to mg	
			# monomial : Inequality map
			ma = matrix((0.0),(nVar,1)) 
			ma[dictNode[SelfGate].gateSerNum] = -1					# set the variable : exponent value
			mf = matrix([[mf],[ma]])						# F matrix: concatenate min-array ma to mf
			mk.append(1)								# single monomial: Inequality				
			#fw.write("~x_"+SelfGate+" x_min " +" <= 1\n")
	#fw.write(lineArea +" <= 1\n")
	
	# Test cases Report
	# getPrintLargeMatrix(mf,mg.trans()) #comment
	# print mk #comment		
		
	# SOLVER BASED FRAMEWORK
	# Module block setup framework
	result = []
	g = log(mg)
	
	sol = solvers.gp(mk, mf.trans(), g)
	result = exp(sol['x'])
	if sol['status'] == 'optimal':
		sline = ' module2: optimization succes! '
		skey = 'opt2succes'
		insertStatus(filename,lineno(),skey,sline)
		# store the dimension
		dime = mf.size 
		sline = " opt2.0 Mode: variables "+ str(dime[0])+ " monomials "+ str(dime[1])+ " inequalities "+ str(len(mk)) 
		skey = 'opt2successDim'
		insertStatus(filename,lineno(),skey,sline)
	else:
		sline = 'optimization fail : Joint optimization failed: Sequential Opt'
		skey = 'opt2fail'
		insertStatus(filename,lineno(),skey,sline)	
	return result


# OTHER MODULE DESIGN: FUNCTIONAL ANALYSIS MODULES
# serialize the gates in the dictionary : simple numerical increment map
def determineGateCount(dictNode,stageModule):
	gateCount = 0
	for i in range(len(stageModule)):
		for j in range(len(stageModule[i].gateList)):
			SelfGate = stageModule[i].gateList[j]
			dictNode[SelfGate].gateSerNum = gateCount
			# print "gate:",SelfGate ,"serialNo:",gateCount #comment
			gateCount += 1
	return gateCount	

def getPrintLargeMatrix(mf,mg_trans):
	# displaying the F matrix in readable format
	dim = mf.size
	rows =  dim[0]
	columns = dim[1]
	listDisp =[]
	line = ''
	for i in range(rows):
		for j in range(columns):
			listDisp.append(mf[i,j]) 
		# print listDisp
		line = "["
		for j in range(len(listDisp)):
			if listDisp[j] < 0:
				line += str(listDisp[j]) + "., "
			else:	
				line += " " + str(listDisp[j]) + "., "
		line += "],"
		print line
		line = ''	
		listDisp = []
	print("\n")	

	# displaying the g matrix in readable format
	gline = ''
	line += "["
	for k in range(len(mg_trans)):
		line +=  str(mg_trans[k]) 
		if k != len(mg_trans)-1:
			line += ", " 
	line += "]"
	print line
	print "\n"	

# plug in the solver based results into the dict table
def populateDictNodeTable(dictNode,stageModule,result,numVar):
	for i in range(0,len(stageModule)):			
		for j in range(len(stageModule[i].gateList)):	
			SelfGate = stageModule[i].gateList[j]
			dictNode[SelfGate].solveGateSize = result[dictNode[SelfGate].gateSerNum]		# store gate-sizing in dict
			dictNode[SelfGate].solveArrivalTime = result[numVar + dictNode[SelfGate].gateSerNum] 	# store arrival time in dict
	
						
# HEURISTIC ANALYSIS : DESIGN AUTOMATION FOR AUTOMATED RETIMING OF COMBINATIONAL CIRCUITS
# displaying the results of the solver 
def displayresultSolver(dictNode,stageModule,minNodeOut):
	totalDynPower = 0
	totalStatPower = 0
	totalArea = 0	
	modConst = modConstraint()
	power = gpower()
	flop = mflop()	
	flopsArea = 0
	flopsPower = 0
	isSequentialMode = False 
	for i in range(0,len(stageModule)):	
		#stage based computation :Initialize 
		stageModule[i].solStageDynPower = 0
		stageModule[i].solStageStatPower  = 0
		stageModule[i].solStageArea = 0		
		for j in range(len(stageModule[i].gateList)):	
			SelfGate = stageModule[i].gateList[j]
			# compute self dyn power
			cap = dictNode[SelfGate].unitCapInt * dictNode[SelfGate].solveGateSize
			if SelfGate in minNodeOut: 	# if the node is a output node 
				# for gates fan-out being the output 
				cap += modConst.Cload
			else:							# if an intermediate node
				# if the node is pipe joint 
				if dictNode[SelfGate].pipeJoint:
					cap += flop.fLoad
					flopsArea += flop.fArea
					flopsPower += flop.fPower
					isSequentialMode = True
				else:	 
					for k in range(len(dictNode[SelfGate].fanOutList)):
						cap += dictNode[dictNode[SelfGate].fanOutList[k]].unitCapInt * dictNode[dictNode[SelfGate].fanOutList[k]].solveGateSize
			
			# dynamic power
			dictNode[SelfGate].gateDynPower = power.retDynamicPower(cap) * modConst.freq * dictNode[SelfGate].gateSignalProb
			# static power
			dictNode[SelfGate].gateStatPower =  dictNode[SelfGate].unitIleak * dictNode[SelfGate].solveGateSize * power.v_dd
			# area 
			dictNode[SelfGate].gateArea = dictNode[SelfGate].unitArea * dictNode[SelfGate].solveGateSize
			# gate delay
			dictNode[SelfGate].gateTime = power.retAlphaPowerDelayTime((dictNode[SelfGate].unitRes * dictNode[SelfGate].solveGateSize),dictNode[SelfGate].solveGateSize,cap)
			#print dictNode[SelfGate].gateTime
			
			#stage based computation
			stageModule[i].solStageDynPower += dictNode[SelfGate].gateDynPower
			stageModule[i].solStageStatPower  += dictNode[SelfGate].gateStatPower
			stageModule[i].solStageArea += dictNode[SelfGate].gateArea
		# total update: param
		totalDynPower += stageModule[i].solStageDynPower
		totalStatPower += stageModule[i].solStageStatPower
		totalArea += stageModule[i].solStageArea
		
	#print "Total Power Consumed:dyn:stat",totalDynPower,totalStatPower
	if isSequentialMode:
		print "Sequential Circuit Block Optimization:" 
		print "flopArea(uM2):",flopsArea," flopPower(uW):",flopsPower
		print "max path delay(ps): ",modConst.ATpipe
	else:	
		print "Combinational Block Optimization :"
	print "DynPower(uW):",totalDynPower+flopsPower,"StatPower(uW):",totalStatPower,"Total Area(uM2):",totalArea +flopsArea


# Shortest Path Analysis: Geometric programming cant model for shortest path:
#	Re-using ATmax and ATmin variable : Used for path analysis:
#		Not to confuse with in Heuristic and both are differnt dictTables
# 	Shortest Path Analysis: Computation based on solver output: gate sizing factor of gates
def updateTimingMapforGateSize(dictNode,stageModule,minNodeIn,minNodeOut):
	sumFanOutCap = 0					# stores the fanout capacitance of a gate
	totalCap = 0						# stores the total capacitance driven by the gate
	totstatPower = 0 
	timeBankMax = []
	timeBankMin = []
	tTime = 0	
	modCont = modConstraint()	
	power = gpower()
	for i in range(len(stageModule)):			# in-out-map
		for j in range(len(stageModule[i].gateList)):
			SelfGate = stageModule[i].gateList[j]
			# access each nodes in the list based framework :: Prior initial setup-framework : set all gate size to unity
			if SelfGate in minNodeOut:
				sumFanOutCap += modCont.Cload									# output load driven by gate 								
			else:	 
				for k in range(len(dictNode[SelfGate].fanOutList)):
					fanOutGate = dictNode[SelfGate].fanOutList[k] # string type				
					sumFanOutCap += dictNode[fanOutGate].unitCapInt * dictNode[fanOutGate].solveGateSize	# non-output load driven by gate				
			# print sumFanOutCap 	
			totalCap = (dictNode[SelfGate].unitCapInt * dictNode[SelfGate].solveGateSize) + sumFanOutCap		# total capacitance driven by the gate		

			# timing framework
			for fc in range(len(dictNode[SelfGate].fanInList)):
				gateIn = dictNode[SelfGate].fanInList[fc]		# input gate
				if gateIn  not in minNodeIn:
					timeBankMax.append(dictNode[gateIn].ATmax)	# append the maximum time stamp
					timeBankMin.append(dictNode[gateIn].ATmin)	# append the minimum time stamp
			
			# force enter min time for input nodes 
			if timeBankMin == []:	# input nodes
				 dictNode[SelfGate].ATmin = power.retAlphaPowerDelayTime(dictNode[SelfGate].unitRes,dictNode[SelfGate].solveGateSize,totalCap)
				 #dictNode[SelfGate].ATmin  = 0.69 * (dictNode[SelfGate].unitRes / dictNode[SelfGate].solveGateSize) * totalCap

			tTime = power.retAlphaPowerDelayTime(dictNode[SelfGate].unitRes,dictNode[SelfGate].solveGateSize,totalCap)
			#tTime = 0.69 * (dictNode[SelfGate].unitRes / dictNode[SelfGate].solveGateSize) * totalCap	# self delay driving the load resistances
			
			#print "gate:",SelfGate,"time:",tTime,"cap:",sumFanOutCap
			
			# check and map time stamp: gate system framework
			if timeBankMax != []:
				dictNode[SelfGate].ATmax = tTime + max(timeBankMax)		# determining maximum time for the node: Dynamic Programming 
			else:
				dictNode[SelfGate].ATmax = tTime
			
			if timeBankMin != []:		
				dictNode[SelfGate].ATmin = tTime + min(timeBankMin)		# determining minimum time for the node: Dynamic Programming
			else:
				dictNode[SelfGate].ATmin = tTime				
			
			#print "gateMax:",SelfGate,dictNode[SelfGate].ATmax	#comment
			#print "gateMin:",SelfGate,dictNode[SelfGate].ATmin	#comment
			
			# reset data
			sumFanOutCap = 0
			timeBankMin = []
			timeBankMax = []	
			
			SelfGate = stageModule[i].gateList[j]
			stageModule[i].solStageTimeMax = max(stageModule[i].solStageTimeMax,dictNode[SelfGate].gateTime)	# extract maximum delay in a stage
			stageModule[i].solStageTimeMin = min(stageModule[i].solStageTimeMin,dictNode[SelfGate].gateTime)	# extract minimum delay in a stage
		# print the max-min values
		#print	"stage",i+1,"max:",stageModule[i].solStageTimeMax
		#print	"stage:",i+1,"min:",stageModule[i].solStageTimeMin						
			
	#pathDelayMax = 0
	pathDelayMin = sys.maxsize	
	for a in range(len(minNodeOut)):
		pathDelayMin = min(pathDelayMin,dictNode[minNodeOut[a]].ATmin)	
	print "Min-Delay-Path(ps):",pathDelayMin,"Max-Delay-Path(ps):",modCont.ATmax



# Define the pipeline joints : based on the maximum path delay method:
# 	Here the design can be approached in two ways:
#		- First resize shortest path delays in larger circuit and then estimate pipleline joints:
#		- Second method would be find the pipleline joint estimated and then resize for the sub-combinational blocks to satisfy the shortest path problem
# 	Analyis: Since both cases the pipeline joints are based on the maximum delay path, the pipeline joint estimation mustnt be differnt in ant apporach
#		- However the second approach would result in less computational time complexity : Hence the design of choice
#

# determines the flop joints: for pipelined edge based framework
def determinePipelineJoints(dictNode,stageModule,minNodeIn,minNodeOut):
	designConst = modConstraint()				# design constraints
	flopCount = 0
	maxStage = 0	
	for i in range(len(stageModule)):			# in-out-map
		for j in range(len(stageModule[i].gateList)):
			SelfGate = stageModule[i].gateList[j]
			# estimate pipeline joints
			dictNode[SelfGate].stageEstimate = int(dictNode[SelfGate].ATmax/float(designConst.ATpipe)) + 1
			maxStage =  dictNode[SelfGate].stageEstimate # comment
			
	for i in range(len(stageModule)):			# in-out-map
		for j in range(len(stageModule[i].gateList)):
			SelfGate = stageModule[i].gateList[j]
			for k in range(len(dictNode[SelfGate].fanOutList)):
				fanOutGate = dictNode[SelfGate].fanOutList[k]
				if dictNode[SelfGate].stageEstimate != dictNode[fanOutGate].stageEstimate:
					dictNode[SelfGate].pipeJoint  = 1
					print SelfGate,"pipe-stage-block:",dictNode[SelfGate].stageEstimate,"joint:",fanOutGate,"pipe-stage-block:",dictNode[fanOutGate].stageEstimate
					flopCount += 1
					break
	# this module ends with just the logging of the stage and the pipeline joint nodes: 
	# An assumption has been made that even if one of the fanouts are on the pipeline joint, the entire gate is considred to be a pipeline joint
	#		- this means that a single flop will be the pipe joint driving multiple fan-outs instead of each interconnect fanout inserted with flop
	# 			- this reduces the number of flop insertion and can be seen as a model for reduced power area and timing	

	# the return variable can be seen as just an estimate to verify : how much it varies from extPipeJoint
	print "flopCount: ",flopCount, "flopStage ", maxStage
	return flopCount, maxStage


# Module framework storing the sequential model : Aids in Timing Equation Generation 
# A framework of only the joints in the sequential circuit : Inserted Flop Mapping
#	- generateAndSolveOptSeq()
#	
def generateSequentialBlockFramework(dictNode,stageModule,SeqBlockJoint,maxStage):
	const = modConstraint()
	for i in range(maxStage-1):
		pJoint = PipeJoint()
		SeqBlockJoint.append(pJoint)
		SeqBlockJoint[i].stageNum = i+1

	# insert the pipe joint framework based on the stages encountered:
	for i in range(len(stageModule)):				# in-out-map
		for j in range(len(stageModule[i].gateList)):
			SelfGate = stageModule[i].gateList[j]	
			if dictNode[SelfGate].pipeJoint  == 1: 	# pipeline joint node	
				selfStage = dictNode[SelfGate].stageEstimate	
				SeqBlockJoint[selfStage-1].nodeInJoint.append(SelfGate)
				
	pipeDef = len(SeqBlockJoint)		
	# print all the joint based farmework:
	for l in range(pipeDef):
		print "stage:",SeqBlockJoint[l].stageNum,"Joint List:",SeqBlockJoint[l].nodeInJoint

 
	if pipeDef < const.numPipeStage - 1: # less pipelined stages than requires
		sline = "Ceems1: Fail:less stage pipelined"
		skey = 'ceemsIgenCut'
		insertStatus(filename,lineno(),skey,sline)	
	elif pipeDef < const.numPipeStage - 1: # more pipelined stages than requires
		sline = "Ceems1: Fail:excess stages pipelined"
		skey = 'ceemsIgenCut'
		insertStatus(filename,lineno(),skey,sline)		
	else:
		sline = "Ceems1: Pipeline: Required Stages Achieved"
		skey = 'ceemsIgenCut'		
		insertStatus(filename,lineno(),skey,sline)

# determine the delay padding that might be required : for functional satisfiability
def determinePadPipeDesignFeasible(dictNode,stageModule,minNodeIn,minNodeOut,maxStage,flopCount): 
	flopCountExtra = 0
	stageGap = 0
	for i in range(len(stageModule)):			# in-out-map
		for j in range(len(stageModule[i].gateList)):
			SelfGate = stageModule[i].gateList[j]
			if SelfGate in minNodeOut:
				stageGap = maxStage - dictNode[SelfGate].stageEstimate 
				if stageGap:
					flopCountExtra += 1
			for k in range(len(dictNode[SelfGate].fanOutList)):
				fanOutGate = dictNode[SelfGate].fanOutList[k]
				stageGap = dictNode[fanOutGate].stageEstimate  - dictNode[SelfGate].stageEstimate
				# if stageGap = 0: lies in same stage: if stageGap =1 : no need to delay pad: if stageGap >= 2 : add flop and delay pad: stageGap-1 
				if stageGap >= 2:
					# insert delay pad : insert a flop
					flopCountExtra += stageGap-1	
			
	print "extra flop: ",flopCountExtra
	print "total flop: ",flopCountExtra + flopCount


# Retiming module for minimal register insertion 
# from section of the thesis:
# Mode A: if the fan-in(s) of a gate is greater than unity then its better to shift the flop to the output of the gate
# Mode B: placing the registers on the interconnects with higher switching activity and high capacitance loads reduces power as well	
#  - module can be reused for both the heuritic and the slver based heuristics cut
def retimingModule(dictNode,stageModule):
	# mode A:
	# mode B: not violating mode A:
	pass
	

# Adjust min delay path constraint: for hold time satisfiability
# 	- compensate for geometric programming modeling limitations
# Method A: Find the shortest path ,start sizing from in-out mode
# Method B: If sizing feasibility doesnt increase the min-delay, insert delay padding element sets
# 
# Conform to min path delay : feasible design framework
def adjustMinPathDelayIterativeSolver(dictNode,stageModule,minNodeIn,minNodeOut):
	modCont = modConstraint()
	for i in range(len(stageModule)):			# in-out-map
		for j in range(len(stageModule[i].gateList)):
			SelfGate = stageModule[i].gateList[j]
			if dictNode[SelfGate].pipeJoint or SelfGate in minNodeOut:
				if dictNode[SelfGate].ATmin < modCont.ATpipeMin:
					# insert delay padding prior to the node:
					delaydiff = modCont.ATpipeMin - dictNode[SelfGate].ATmin
					if delaydiff > modCont.maxDelayPad:	# exceeds delay padding limit	
						sline = "gate:"+ SelfGate +"fails shortest path requirement: Exceeds limit of padding(ps):" + str(modCont.maxDelayPad)
						skey = 'pipefail'+ SelfGate
						insertStatus(filename,lineno(),skey,sline)						
					else:		
						sline = "gate:"+ SelfGate +"fails shortest path requirement: required delay padding(ps):" + str(delaydiff)
						skey = 'pipefail'+ SelfGate
						insertStatus(filename,lineno(),skey,sline)
				else:
					pass
			else:
				pass	


# Sequential : Updates the timing values from the gate sizing provided by the solver 
# Timing path updates as well
def updateSeqTiming(dictNode,stageModule,minNodeIn,minNodeOut):
	sumFanOutCap = 0					# stores the fanout capacitance of a gate
	totalCap = 0						# stores the total capacitance driven by the gate
	totstatPower = 0 
	timeBankMax = []
	timeBankMin = []
	tTime = 0
	isDesignSuccess = True 
	shortPathFailCount = 0
	modCont = modConstraint()	
	flop = mflop()
	power = gpower()
	for i in range(len(stageModule)):			# in-out-map
		for j in range(len(stageModule[i].gateList)):
			SelfGate = stageModule[i].gateList[j]

			if SelfGate in minNodeOut:
				sumFanOutCap += modCont.Cload										# output load driven by gate 								
			else:	
				if dictNode[SelfGate].pipeJoint:
					sumFanOutCap = flop.fLoad
				else:	 
					for k in range(len(dictNode[SelfGate].fanOutList)):
						fanOutGate = dictNode[SelfGate].fanOutList[k] # string type				
						sumFanOutCap += dictNode[fanOutGate].unitCapInt * dictNode[fanOutGate].solveGateSize	# non-output load driven by gate
			totalCap = (dictNode[SelfGate].unitCapInt * dictNode[SelfGate].solveGateSize) + sumFanOutCap			# total capacitance driven by the gate	
			
			# timing framework
			for fc in range(len(dictNode[SelfGate].fanInList)):
				gateIn = dictNode[SelfGate].fanInList[fc]		# input gate
				if gateIn  not in minNodeIn:
					# also check of gate-in is not part of pipeJoint
					if dictNode[gateIn].pipeJoint:
						pass
					else:	 
						timeBankMax.append(dictNode[gateIn].ATmax)	# append the maximum time stamp
						timeBankMin.append(dictNode[gateIn].ATmin)	# append the minimum time stamp

			
			tTime = power.retAlphaPowerDelayTime(dictNode[SelfGate].unitRes,dictNode[SelfGate].solveGateSize,totalCap)
			#tTime = 0.69 * (dictNode[SelfGate].unitRes / dictNode[SelfGate].solveGateSize) * totalCap	# self delay driving the load resistances
			#print "gate:",SelfGate,"time:",tTime,"cap:",sumFanOutCap			
								
			# check and map time stamp: gate system framework
			if timeBankMax != []:
				dictNode[SelfGate].ATmax = tTime + max(timeBankMax)		# determining maximum time for the node: Dynamic Programming 
			else:
				dictNode[SelfGate].ATmax = tTime
			
			if timeBankMin != []:		
				dictNode[SelfGate].ATmin = tTime + min(timeBankMin)		# determining minimum time for the node: Dynamic Programming
			else:
				dictNode[SelfGate].ATmin = tTime

			print "gateMax:",SelfGate,dictNode[SelfGate].ATmax, "gateMin:",SelfGate,dictNode[SelfGate].ATmin	#comment

			if dictNode[SelfGate].pipeJoint or SelfGate in minNodeOut:
				if dictNode[SelfGate].ATmin < modCont.ATpipeMin:
					isDesignSuccess = False
					
			# reset data
			sumFanOutCap = 0
			timeBankMin = []
			timeBankMax = []
			
	return isDesignSuccess		
		

# Generation of extra inequality constraints to validate for max path delay
# The extra matrix generated will be added to the fm  matrix module 
#	- joint optimization of combinational blocks: each individual combinational blocks will be optimized for timing constraints
#						    : joint optimization based on area and power equations : Sequential Circuit
# 								- Load Cap changed and Joint Timing Constraints Modeled
def generateAndSolveOptSeq(dictNode,stageModule,minNodeIn,minNodeOut,numVar,estFlop,SeqBlockJoint):
	# generate for joint combinational block optimization
	result = solverOptSeq(dictNode,stageModule,minNodeIn,minNodeOut,numVar,estFlop,SeqBlockJoint)
	populateDictNodeTable(dictNode,stageModule,result,numVar)						# plug in the solver based results into the dict table	
	displayresultSolver(dictNode,stageModule,minNodeOut)							# update stage based computation: from results:power,area,time
	#adjustMinPathDelayIterativeSolver(dictNode,stageModule,minNodeIn,minNodeOut)
	if updateSeqTiming(dictNode,stageModule,minNodeIn,minNodeOut):						# update the sequential timing framework
		sline = "Pipeline Effective Design Achieved..."
		skey = 'PipeAchieve'
		insertStatus(filename,lineno(),skey,sline)
	else:
		sline = "Pipeline failed due to shortest path.."
		skey = 'PipeFail'
		insertStatus(filename,lineno(),skey,sline)

def nonLevelBasedOptimizationFramework(dictNode,stageModule,minNodeIn,minNodeOut,numVar,estFlop,SeqBlockJoint):	
	result = solverOpt(dictNode,stageModule,minNodeIn,minNodeOut,numVar,estFlop)					# solver based optimization : cvx-opt
	populateDictNodeTable(dictNode,stageModule,result,numVar)							# plug in the solver based results into the dict table
	displayresultSolver(dictNode,stageModule,minNodeOut)								# update stage based computation: from results:power,area,time
	updateTimingMapforGateSize(dictNode,stageModule,minNodeIn,minNodeOut)						# max min path analysis and update based on prior gate sizing by the solver
	# sequential module framework
#	flopCount, maxStage = determinePipelineJoints(dictNode,stageModule,minNodeIn,minNodeOut)			# determine pipeline joints 
#	generateSequentialBlockFramework(dictNode,stageModule,SeqBlockJoint,maxStage)					# generate sequential block framework
#	determinePadPipeDesignFeasible(dictNode,stageModule,minNodeIn,minNodeOut,maxStage,flopCount)	
#	genEquationSeq(dictNode,stageModule,minNodeIn,minNodeOut)							# equation generator : finale version : optimal pipeline 
#	generateAndSolveOptSeq(dictNode,stageModule,minNodeIn,minNodeOut,numVar,estFlop,SeqBlockJoint)			# generate the model based on : Updated Timing model : Sequential Block
#	adjustMinPathDelayIterativeSolver(dictNode,stageModule,minNodeIn,minNodeOut)					# adjust minimum path delay if encountered for a combinational block	


# solver operation : Solve
#    - contains all the routines to edge based framework
def mainSolveandGen(dictNode,stageModule,minNodeIn,minNodeOut,numStage):
	numVar = 0
	estFlop = 0
	SeqBlockJoint = []
	# module 1
	numVar = determineGateCount(dictNode,stageModule)
 	genEquation(dictNode,stageModule,minNodeIn,minNodeOut)								# equation generator : verification module 	
 	estFlop = determineEstimatedFlopCount(stageModule)								# Heuristic Approach : Estimated number of flop inserted	
	
	# Non Level Based Timing Framework : Design
	nonLevelBasedOptimizationFramework(dictNode,stageModule,minNodeIn,minNodeOut,numVar,estFlop,SeqBlockJoint)
		
	# Level Based Timing Framework : Deisgn 
	#levelBasedOptimizationFramework(dictNode,stageModule,minNodeIn,minNodeOut,numVar,estFlop,SeqBlockJoint,numStage)

	
