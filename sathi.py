# Heuristic Based Design Framework: Sathi 
# Automated Pipeline of Digital CIrcuits : Design Constraints
# Addred buffer based support framework

import os
import sys
import time
from modLib import gpower
from constraint import modConstraint
from random import shuffle
from status import solverStat, insertTimeStamp, insertStatus, reportStatus, lineno
from subsolver import PipeJoint

# file name stored : filename 
filename = os.path.basename(__file__)

# design update framework: prior unit size gate-sizing
def initUpdateDesignframework(dictSathi,stageModule,minNodeIn,minNodeOut):

	sumFanOutCap = 0					# stores the fanout capacitance of a gate
	totalCap = 0						# stores the total capacitance driven by the gate
	totArea = 0
	totDynPower = 0
	totstatPower = 0 
	timeBankMax = []
	timeBankMin = []
	tTime = 0
	maxFanOut = 0
	maxFanIn = 0
	power = gpower()
	modCont = modConstraint()
	print "The stage in the circuit :",len(stageModule)
	print "The number of inputs :",len(minNodeIn),"and outputs :",len(minNodeOut)
	for i in range(len(stageModule)):			# in-out-map
		for j in range(len(stageModule[i].gateList)):
			gateNum = stageModule[i].gateList[j]
			# analyse the maximum fan-out and fan-in for the benchmark circuit design framework
			#print "gate: ",gateNum, "fanout List: ",dictSathi[gateNum].fanOutList
			#print "gate: ",gateNum, "fanIn List: ",dictSathi[gateNum].fanInList
			
			if maxFanOut < len(dictSathi[gateNum].fanOutList):
				maxFanOut = len(dictSathi[gateNum].fanOutList)
			if maxFanIn < len(dictSathi[gateNum].fanInList):
				maxFanIn = len(dictSathi[gateNum].fanInList)
						
			# access each nodes in the list based framework :: Prior initial setup-framework : set all gate size to unity
			if gateNum in minNodeOut:
				sumFanOutCap += modCont.Cload									# output load driven by gate 								
			else:	 
				for k in range(len(dictSathi[gateNum].fanOutList)):
					fanOutGate = dictSathi[gateNum].fanOutList[k] # string type
					dictSathi[fanOutGate].gateSize = 1				
					sumFanOutCap += dictSathi[fanOutGate].unitCapInt * dictSathi[fanOutGate].gateSize	# non-output load driven by gate				
			
			# print sumFanOutCap 
			dictSathi[gateNum].gateSize = 1	
			totalCap = (dictSathi[gateNum].unitCapInt * dictSathi[gateNum].gateSize) + sumFanOutCap			# total capacitance driven by the gate
			
			# timing framework
			for fc in range(len(dictSathi[gateNum].fanInList)):
				gateIn = dictSathi[gateNum].fanInList[fc]		# input gate
				if gateIn  not in minNodeIn:
					timeBankMax.append(dictSathi[gateIn].ATmax)	# append the maximum time stamp
					timeBankMin.append(dictSathi[gateIn].ATmin)	# append the minimum time stamp
			
			# force enter min time for imput nodes 
			if timeBankMin == []:	# input nodes
				 dictSathi[gateNum].ATmin  = power.retAlphaPowerDelayTime(dictSathi[gateNum].unitRes,dictSathi[gateNum].gateSize,totalCap)
				 #dictSathi[gateNum].ATmin  = 0.69 * (dictSathi[gateNum].unitRes / dictSathi[gateNum].gateSize) * totalCap
					

			tTime = power.retAlphaPowerDelayTime(dictSathi[gateNum].unitRes,dictSathi[gateNum].gateSize,totalCap)
			#tTime = 0.69 * (dictSathi[gateNum].unitRes / dictSathi[gateNum].gateSize) * totalCap	# self delay driving the load resistances
			#print "gate:",gateNum,"time:",tTime,"cap:",sumFanOutCap
			
			# check and map time stamp: gate system framework
			if timeBankMax != []:
				dictSathi[gateNum].ATmax = tTime + max(timeBankMax)		# determining maximum time for the node: Dynamic Programming 
			else:
				dictSathi[gateNum].ATmax = tTime
			if timeBankMin != []:		
				dictSathi[gateNum].ATmin = tTime + min(timeBankMin)		# determining minimum time for the node: Dynamic Programming
			else:
				dictSathi[gateNum].ATmin = tTime				
			
			#print "gateMax:",gateNum,dictSathi[gateNum].ATmax	#comment 
			#print "gateMin:",gateNum,dictSathi[gateNum].ATmin	#comment
			
			# reset data
			sumFanOutCap = 0
			timeBankMax = []
			timeBankMin = []
			
			# reset the prior values
			dictSathi[gateNum].gateArea = 0
			dictSathi[gateNum].gateDynPower = 0
			dictSathi[gateNum].gateStatPower = 0
			dictSathi[gateNum].gateTime = 0
			
			# update sensitivity parameters 
			#nowArea  =  dictSathi[gateNum].gateSize * dictSathi[gateNum].unitArea
			#nowPower =  power.retDynamicPower(totalCap) * modCont.freq * dictSathi[gateNum].gateSignalProb + power.retLeakGatePower(dictSathi[gateNum].gateSize ,dictSathi[gateNum].unitIleak)
			#nowTime  =  power.retGateDelayTime(dictSathi[gateNum].unitRes/dictSathi[gateNum].gateSize,totalCap)
			
		
			#print "\nnow: ",nowArea,nowPower,nowTime #comment
			#print "prior: ",dictSathi[gateNum].gateArea,dictSathi[gateNum].gateDynPower + dictSathi[gateNum].gateStatPower,dictSathi[gateNum].gateTime,"\n"  #comment
		
			#deltaArea = abs(nowArea - dictSathi[gateNum].gateArea) 
			#deltaPower = abs(nowPower - dictSathi[gateNum].gateDynPower - dictSathi[gateNum].gateStatPower)
			#deltaTime = abs( nowTime - dictSathi[gateNum].gateTime)
			#dictSathi[gateNum].opSense = deltaTime/float(deltaArea * deltaPower)
			#print 'gate:',gateNum,'opsense: ',dictSathi[gateNum].opSense #comment
			
			
			# updating the operating parameters
			dictSathi[gateNum].gateDynPower = power.retDynamicPower(totalCap) * modCont.freq * dictSathi[gateNum].gateSignalProb
			#print "dyn:power",dictSathi[gateNum].gateDynPower	# comment
			dictSathi[gateNum].gateStatPower  = power.retLeakGatePower(dictSathi[gateNum].gateSize ,dictSathi[gateNum].unitIleak)
			#print "leak:power",dictSathi[gateNum].gateStatPower	# comment	
			dictSathi[gateNum].gateTime = power.retAlphaPowerDelayTime(dictSathi[gateNum].unitRes,dictSathi[gateNum].gateSize,totalCap)				
			#dictSathi[gateNum].gateTime = power.retGateDelayTime(dictSathi[gateNum].unitRes/dictSathi[gateNum].gateSize,totalCap)
			#print "delay",dictSathi[gateNum].gateTime		# comment
			dictSathi[gateNum].gateArea =  dictSathi[gateNum].gateSize * dictSathi[gateNum].unitArea
			#print "area",dictSathi[gateNum].gateArea		# comment


			# update max-delay for gate node in stage
			if stageModule[i].stageTimeMax < dictSathi[gateNum].gateTime:
				stageModule[i].stageTimeMax = dictSathi[gateNum].gateTime				
			else:
				pass
			# update min-delay for gate node in stage	
			if stageModule[i].stageTimeMin > dictSathi[gateNum].gateTime:
				stageModule[i].stageTimeMin = dictSathi[gateNum].gateTime
			else:
				pass	
			# compute total static power in stage
			totstatPower += dictSathi[gateNum].gateStatPower
			# compute total dynamic power in stage
			totDynPower += dictSathi[gateNum].gateDynPower
			# compute total gate area in a stage 	
			totArea += dictSathi[gateNum].gateArea
			
	print "max-FanIn: ",maxFanIn," max-FanOut: ",maxFanOut		
	
	print "\ninit:DynPower:",totDynPower,"StatPower:",totstatPower,"Area:",totArea	
	
	pathDelayMax = 0
	pathDelayMin = sys.maxsize	
	for a in range(len(minNodeOut)):
		pathDelayMax = max(pathDelayMax,dictSathi[minNodeOut[a]].ATmax)
		pathDelayMin = min(pathDelayMin,dictSathi[minNodeOut[a]].ATmin)
	
	print "Max-Delay-Path:",pathDelayMax 
	print "Min-Delay-Path:",pathDelayMin
	
	return totDynPower+totstatPower,totArea,pathDelayMax,pathDelayMin
	
# update and display the parameters of the circuit design
	# STA analysis : single sweep of the entire circit : Called for ever modified node in the circuit
def displayUpdateDesignParam(dictSathi,stageModule,minNodeIn,minNodeOut):
	sumFanOutCap = 0					# stores the fanout capacitance of a gate
	totalCap = 0						# stores the total capacitance driven by the gate
	totArea = 0
	totDynPower = 0
	totstatPower = 0 
	timeBankMax = []
	timeBankMin = []
	tTime = 0
	power = gpower()
	modCont = modConstraint()
	for i in range(len(stageModule)):			# in-out-map
		for j in range(len(stageModule[i].gateList)):
			gateNum = stageModule[i].gateList[j]
			# access each nodes in the list based framework :: Prior initial setup-framework : set all gate size to unity
			if gateNum in minNodeOut:
				sumFanOutCap += modCont.Cload									# output load driven by gate 								
			else:	 
				for k in range(len(dictSathi[gateNum].fanOutList)):
					fanOutGate = dictSathi[gateNum].fanOutList[k] # string type				
					sumFanOutCap += dictSathi[fanOutGate].unitCapInt * dictSathi[fanOutGate].gateSize	# non-output load driven by gate				
			
			# print sumFanOutCap 	
			totalCap = (dictSathi[gateNum].unitCapInt * dictSathi[gateNum].gateSize) + sumFanOutCap			# total capacitance driven by the gate
			
			# timing framework
			for fc in range(len(dictSathi[gateNum].fanInList)):
				gateIn = dictSathi[gateNum].fanInList[fc]		# input gate
				if gateIn  not in minNodeIn:
					timeBankMax.append(dictSathi[gateIn].ATmax)	# append the maximum time stamp
					timeBankMin.append(dictSathi[gateIn].ATmin)	# append the minimum time stamp
			
			# force enter min time for imput nodes 
			if timeBankMin == []:	# input nodes
				 dictSathi[gateNum].ATmin  = power.retAlphaPowerDelayTime(dictSathi[gateNum].unitRes,dictSathi[gateNum].gateSize,totalCap)
				 #dictSathi[gateNum].ATmin  = 0.69 * (dictSathi[gateNum].unitRes / dictSathi[gateNum].gateSize) * totalCap
					

			tTime = power.retAlphaPowerDelayTime(dictSathi[gateNum].unitRes,dictSathi[gateNum].gateSize,totalCap)
			#tTime = 0.69 * (dictSathi[gateNum].unitRes / dictSathi[gateNum].gateSize) * totalCap	# self delay driving the load resistances
			#print "gate:",gateNum,"time:",tTime,"cap:",sumFanOutCap
			
			# check and map time stamp: gate system framework
			if timeBankMax != []:
				dictSathi[gateNum].ATmax = tTime + max(timeBankMax)		# determining maximum time for the node: Dynamic Programming 
			else:
				dictSathi[gateNum].ATmax = tTime
			if timeBankMin != []:		
				dictSathi[gateNum].ATmin = tTime + min(timeBankMin)		# determining minimum time for the node: Dynamic Programming
			else:
				dictSathi[gateNum].ATmin = tTime				
			
			#print "gateMax:",gateNum,dictSathi[gateNum].ATmax	#comment 
			#print "gateMin:",gateNum,dictSathi[gateNum].ATmin	#comment
			
			# reset data
			sumFanOutCap = 0
			timeBankMax = []
			timeBankMin = []
			
			# reset the prior values
			#dictSathi[gateNum].gateArea = 0
			#dictSathi[gateNum].gateDynPower = 0
			#dictSathi[gateNum].gateStatPower = 0
			#dictSathi[gateNum].gateTime = 0
			
			# update sensitivity parameters 
			#nowArea  =  dictSathi[gateNum].gateSize * dictSathi[gateNum].unitArea
			#nowPower =  power.retDynamicPower(totalCap) * modCont.freq * dictSathi[gateNum].gateSignalProb + power.retLeakGatePower(dictSathi[gateNum].gateSize ,dictSathi[gateNum].unitIleak)
			#nowTime  =  power.retGateDelayTime(dictSathi[gateNum].unitRes/dictSathi[gateNum].gateSize,totalCap)
			
		
			#print "\nnow: ",nowArea,nowPower,nowTime #comment
			#print "prior: ",dictSathi[gateNum].gateArea,dictSathi[gateNum].gateDynPower + dictSathi[gateNum].gateStatPower,dictSathi[gateNum].gateTime,"\n"  #comment
		
			#deltaArea = abs(nowArea - dictSathi[gateNum].gateArea) 
			#deltaPower = abs(nowPower - dictSathi[gateNum].gateDynPower - dictSathi[gateNum].gateStatPower)
			#deltaTime = abs( nowTime - dictSathi[gateNum].gateTime)
			#dictSathi[gateNum].opSense = deltaTime/float(deltaArea * deltaPower)
			#print 'gate:',gateNum,'opsense: ',dictSathi[gateNum].opSense #comment
			
			
			# updating the operating parameters
			dictSathi[gateNum].gateDynPower = power.retDynamicPower(totalCap) * modCont.freq * dictSathi[gateNum].gateSignalProb
			#print "dyn:power",dictSathi[gateNum].gateDynPower	# comment
			dictSathi[gateNum].gateStatPower  = power.retLeakGatePower(dictSathi[gateNum].gateSize ,dictSathi[gateNum].unitIleak)
			#print "leak:power",dictSathi[gateNum].gateStatPower	# comment					
			dictSathi[gateNum].gateTime = power.retAlphaPowerDelayTime(dictSathi[gateNum].unitRes,dictSathi[gateNum].gateSize,totalCap)
			#dictSathi[gateNum].gateTime = power.retGateDelayTime(dictSathi[gateNum].unitRes/dictSathi[gateNum].gateSize,totalCap)
			#print "delay",dictSathi[gateNum].gateTime		# comment
			dictSathi[gateNum].gateArea =  dictSathi[gateNum].gateSize * dictSathi[gateNum].unitArea
			#print "area",dictSathi[gateNum].gateArea		# comment


			# update max-delay for gate node in stage
			if stageModule[i].stageTimeMax < dictSathi[gateNum].gateTime:
				stageModule[i].stageTimeMax = dictSathi[gateNum].gateTime				
			else:
				pass
			# update min-delay for gate node in stage	
			if stageModule[i].stageTimeMin > dictSathi[gateNum].gateTime:
				stageModule[i].stageTimeMin = dictSathi[gateNum].gateTime
			else:
				pass	
			# compute total static power in stage
			totstatPower += dictSathi[gateNum].gateStatPower
			# compute total dynamic power in stage
			totDynPower += dictSathi[gateNum].gateDynPower
			# compute total gate area in a stage 	
			totArea += dictSathi[gateNum].gateArea
	
	print "\nDynPower update:",totDynPower,"StatPower:",totstatPower,"Area:",totArea	
	
	pathDelayMax = 0
	pathDelayMin = sys.maxsize	
	for a in range(len(minNodeOut)):
		pathDelayMax = max(pathDelayMax,dictSathi[minNodeOut[a]].ATmax)
		pathDelayMin = min(pathDelayMin,dictSathi[minNodeOut[a]].ATmin)
	
	print "Max-Delay-Path update:",pathDelayMax 
	print "Min-Delay-Path update:",pathDelayMin
	
	return totDynPower+totstatPower,totArea,pathDelayMax,pathDelayMin
	# determine the sensitivity factor of each node in the circuit design framework	
	
# update and display the parameters of the circuit design
	# STA analysis : single sweep of the entire circit : Called for ever modified node in the circuit
def updateDesignParam(dictSathi,stageModule,minNodeIn,minNodeOut):
	sumFanOutCap = 0					# stores the fanout capacitance of a gate
	totalCap = 0						# stores the total capacitance driven by the gate
	totArea = 0
	totDynPower = 0
	totstatPower = 0 
	timeBankMax = []
	timeBankMin = []
	tTime = 0
	power = gpower()
	modCont = modConstraint()
	for i in range(len(stageModule)):			# in-out-map
		for j in range(len(stageModule[i].gateList)):
			gateNum = stageModule[i].gateList[j]
			# access each nodes in the list based framework :: Prior initial setup-framework : set all gate size to unity
			if gateNum in minNodeOut:
				sumFanOutCap += modCont.Cload									# output load driven by gate 								
			else:	 
				for k in range(len(dictSathi[gateNum].fanOutList)):
					fanOutGate = dictSathi[gateNum].fanOutList[k] # string type				
					sumFanOutCap += dictSathi[fanOutGate].unitCapInt * dictSathi[fanOutGate].gateSize	# non-output load driven by gate				
			
			# print sumFanOutCap 	
			totalCap = (dictSathi[gateNum].unitCapInt * dictSathi[gateNum].gateSize) + sumFanOutCap			# total capacitance driven by the gate
			
			# timing framework
			for fc in range(len(dictSathi[gateNum].fanInList)):
				gateIn = dictSathi[gateNum].fanInList[fc]		# input gate
				if gateIn  not in minNodeIn:
					timeBankMax.append(dictSathi[gateIn].ATmax)	# append the maximum time stamp
					timeBankMin.append(dictSathi[gateIn].ATmin)	# append the minimum time stamp
			
			# force enter min time for imput nodes 
			if timeBankMin == []:	# input nodes
				 dictSathi[gateNum].ATmin  = power.retAlphaPowerDelayTime(dictSathi[gateNum].unitRes,dictSathi[gateNum].gateSize,totalCap)
				 #dictSathi[gateNum].ATmin  = 0.69 * (dictSathi[gateNum].unitRes / dictSathi[gateNum].gateSize) * totalCap
					

			tTime = power.retAlphaPowerDelayTime(dictSathi[gateNum].unitRes,dictSathi[gateNum].gateSize,totalCap)
			#tTime = 0.69 * (dictSathi[gateNum].unitRes / dictSathi[gateNum].gateSize) * totalCap	# self delay driving the load resistances
			#print "gate:",gateNum,"time:",tTime,"cap:",sumFanOutCap
			
			# check and map time stamp: gate system framework
			if timeBankMax != []:
				dictSathi[gateNum].ATmax = tTime + max(timeBankMax)		# determining maximum time for the node: Dynamic Programming 
			else:
				dictSathi[gateNum].ATmax = tTime
			if timeBankMin != []:		
				dictSathi[gateNum].ATmin = tTime + min(timeBankMin)		# determining minimum time for the node: Dynamic Programming
			else:
				dictSathi[gateNum].ATmin = tTime				
			
			#print "gateMax:",gateNum,dictSathi[gateNum].ATmax	#comment 
			#print "gateMin:",gateNum,dictSathi[gateNum].ATmin	#comment
			
			# reset data
			sumFanOutCap = 0
			timeBankMax = []
			timeBankMin = []
			
			# reset the prior values
			#dictSathi[gateNum].gateArea = 0
			#dictSathi[gateNum].gateDynPower = 0
			#dictSathi[gateNum].gateStatPower = 0
			#dictSathi[gateNum].gateTime = 0
			
			# update sensitivity parameters 
			#nowArea  =  dictSathi[gateNum].gateSize * dictSathi[gateNum].unitArea
			#nowPower =  power.retDynamicPower(totalCap) * modCont.freq * dictSathi[gateNum].gateSignalProb + power.retLeakGatePower(dictSathi[gateNum].gateSize ,dictSathi[gateNum].unitIleak)
			#nowTime  =  power.retGateDelayTime(dictSathi[gateNum].unitRes/dictSathi[gateNum].gateSize,totalCap)
			
		
			#print "\nnow: ",nowArea,nowPower,nowTime #comment
			#print "prior: ",dictSathi[gateNum].gateArea,dictSathi[gateNum].gateDynPower + dictSathi[gateNum].gateStatPower,dictSathi[gateNum].gateTime,"\n"  #comment
		
			#deltaArea = abs(nowArea - dictSathi[gateNum].gateArea) 
			#deltaPower = abs(nowPower - dictSathi[gateNum].gateDynPower - dictSathi[gateNum].gateStatPower)
			#deltaTime = abs( nowTime - dictSathi[gateNum].gateTime)
			#dictSathi[gateNum].opSense = deltaTime/float(deltaArea * deltaPower)
			#print 'gate:',gateNum,'opsense: ',dictSathi[gateNum].opSense #comment
			
			
			# updating the operating parameters
			dictSathi[gateNum].gateDynPower = power.retDynamicPower(totalCap) * modCont.freq * dictSathi[gateNum].gateSignalProb
			#print "dyn:power",dictSathi[gateNum].gateDynPower	# comment
			dictSathi[gateNum].gateStatPower  = power.retLeakGatePower(dictSathi[gateNum].gateSize ,dictSathi[gateNum].unitIleak)
			#print "leak:power",dictSathi[gateNum].gateStatPower	# comment					
			dictSathi[gateNum].gateTime = power.retAlphaPowerDelayTime(dictSathi[gateNum].unitRes,dictSathi[gateNum].gateSize,totalCap)
			#dictSathi[gateNum].gateTime = power.retGateDelayTime(dictSathi[gateNum].unitRes/dictSathi[gateNum].gateSize,totalCap)
			#print "delay",dictSathi[gateNum].gateTime		# comment
			dictSathi[gateNum].gateArea =  dictSathi[gateNum].gateSize * dictSathi[gateNum].unitArea
			#print "area",dictSathi[gateNum].gateArea		# comment


			# update max-delay for gate node in stage
			if stageModule[i].stageTimeMax < dictSathi[gateNum].gateTime:
				stageModule[i].stageTimeMax = dictSathi[gateNum].gateTime				
			else:
				pass
			# update min-delay for gate node in stage	
			if stageModule[i].stageTimeMin > dictSathi[gateNum].gateTime:
				stageModule[i].stageTimeMin = dictSathi[gateNum].gateTime
			else:
				pass	
			# compute total static power in stage
			totstatPower += dictSathi[gateNum].gateStatPower
			# compute total dynamic power in stage
			totDynPower += dictSathi[gateNum].gateDynPower
			# compute total gate area in a stage 	
			totArea += dictSathi[gateNum].gateArea
	
	#print "\nDynPower update:",totDynPower,"StatPower:",totstatPower,"Area:",totArea	
	
	pathDelayMax = 0
	pathDelayMin = sys.maxsize	
	for a in range(len(minNodeOut)):
		pathDelayMax = max(pathDelayMax,dictSathi[minNodeOut[a]].ATmax)
		pathDelayMin = min(pathDelayMin,dictSathi[minNodeOut[a]].ATmin)
	
	#print "Max-Delay-Path update:",pathDelayMax 
	#print "Min-Delay-Path update:",pathDelayMin
	
	return totDynPower+totstatPower,totArea,pathDelayMax,pathDelayMin
	# determine the sensitivity factor of each node in the circuit design framework
	
	
def extractSensitivityFactorGates(dictSathi,stageModule,minNodeIn,minNodeOut):
	sumFanOutCap = 0
	modConst = modConstraint()
	power = gpower()
	for i in range(len(stageModule)-1,-1,-1):			# out-in map
		for j in range(len(stageModule[i].gateList)):
			gateNum = stageModule[i].gateList[j]	
			# initial state based param map	
			#dictSathi[gateNum].gateSize = 1
			oldPower,oldArea,oldMaxPath,oldMinPath = updateDesignParam(dictSathi,stageModule,minNodeIn,minNodeOut)
			dictSathi[gateNum].gateSize = dictSathi[gateNum].gateSize * modConst.PERTURB
			# perturbed state based param map
			newPower,newArea,newMaxPath,newMinPath = updateDesignParam(dictSathi,stageModule,minNodeIn,minNodeOut)
			# reverting back to normal
			dictSathi[gateNum].gateSize = 1
			
#			deltaArea = abs(newArea - oldArea)
#			deltaTime = abs(newMaxPath - oldMaxPath)
#			deltaPower = abs(newPower - oldPower)	

			deltaArea = newArea - oldArea
			deltaTime = newMaxPath - oldMaxPath
			deltaPower = newPower - oldPower	
			
			if dictSathi[gateNum].gateType == 'BUFF':
				Opsense = 0
			else:
				Opsense = 0 - deltaTime /float(deltaPower * deltaArea)		
			dictSathi[gateNum].opSense = Opsense
			if Opsense > 0:
				print "gate: ",gateNum, " opSense: ",Opsense # comment
				#pass
	

# find the sizing node : BUMP NODE
def findNodeInFilteredCriticalPath(dictSathi,stageModule,minNodeIn,minNodeOut,criticalPath):
	sensitivityList = []
	selHighSense = 0
	#print criticalPath
	designOptPath = criticalPath

	for j in range(len(designOptPath)):
		sensitivityList.append(dictSathi[criticalPath[j]].opSense)
				
	if sensitivityList == []: # no node exists to optimize
		bumpNode = 0	
		return bumpNode
	else:			  # search the best node to optimize	
		# find highest sensitivity factor
		selectHighSensitivity = max(sensitivityList)
		# fine the node  with highest sensitivity
		for k in range(len(sensitivityList)):
			if selectHighSensitivity == sensitivityList[k]:	
				bumpNode = criticalPath[k]
				break
	return bumpNode			
	
	
# finds the critical path based on starting output node : also the opSense > 0, nodes only feasible for sizing to reduce timing 
def findBumpNodeInCriticalPath(selectNode,dictSathi,stageModule,minNodeIn,minNodeOut):
	fanInTime = []
	criticalPath = []
	modConst = modConstraint()
	startNode = selectNode 
	maxTimeNodeIn  = 0
	deleteNodeNum = 0
	while startNode not in minNodeIn:
		# add mode: if node not exceeds  max gate size
		if dictSathi[startNode].gateSize <= modConst.xmax/float(modConst.BUMPSIZE)  and dictSathi[startNode].opSense > 0:
			criticalPath.append(startNode)	
		for i in range(len(dictSathi[startNode].fanInList)):
			nodeSelect = dictSathi[startNode].fanInList[i]
			fanInTime.append(dictSathi[nodeSelect].ATmax)
		maxTimeNodeIn = max(fanInTime)
		for j in range(len(fanInTime)):
			if maxTimeNodeIn == fanInTime[j]:
				selectFanInNode = dictSathi[startNode].fanInList[j]
				break	
		fanInTime = []					
		startNode = selectFanInNode
	#print criticalPath	
	bumpNode = findNodeInFilteredCriticalPath(dictSathi,stageModule,minNodeIn,minNodeOut,criticalPath)
	return bumpNode
	

# tilos module: single gate opt in critical path
#	- - backTraverse and store critical : resize highest sensivity gate in path : single gate opt process				
def CriticalPathAndGateOpt(dictSathi,stageModule,minNodeIn,minNodeOut,maxPath):	
	modConst = modConstraint()
	count = 0
	maxPathEst = maxPath
	designTolerate = 0
	# find the starting output node : for backward path map store
	while True:
		count += 1
		maxOutTime = []
		for i in range(len(minNodeOut)):
			if dictSathi[minNodeOut[i]].ATmax > modConst.ATmax:
				maxOutTime.append(dictSathi[minNodeOut[i]].ATmax)
		#print "maxOutTime: ",maxOutTime		
		# to reduce the delay the transistor sizing must be restricted to the critical path	
		if maxOutTime == []:
			# max delay path has been satified for the entire circuit block
			print 'Optimization Sucess!'			
			return True
		else:		
			# needs to be optimized along the critical path in order to reduce time
			nodeOutMaxTime = max(maxOutTime)
			for k in range(len(minNodeOut)):
				if nodeOutMaxTime == dictSathi[minNodeOut[k]].ATmax:
					selectNode = minNodeOut[k]
					break
			#print "select Node: ",selectNode
			bumpNode = findBumpNodeInCriticalPath(selectNode,dictSathi,stageModule,minNodeIn,minNodeOut)
			if bumpNode == 0: # kill command! viva la revolution!
				print " Optimization Fail! Too tight timing constraints..."
				break
			else:
			
				oldMaxPathDelay = dictSathi[selectNode].ATmax
				# store the twin gate size states
				oldGateSize = dictSathi[bumpNode].gateSize
				newGateSize = dictSathi[bumpNode].gateSize * modConst.BUMPSIZE
				# re-size the bumpNode
				dictSathi[bumpNode].gateSize = newGateSize
				updateDesignParam(dictSathi,stageModule,minNodeIn,minNodeOut)
				newMaxPathDelay = dictSathi[selectNode].ATmax
				if newMaxPathDelay < oldMaxPathDelay: # optimization(time reduction) in progress
					#print "oldtime: ",oldMaxPathDelay , "newtime: ",newMaxPathDelay 
					pass							
				else:   # timing closure detoriated
					#revert back sizing step
					dictSathi[bumpNode].gateSize = oldGateSize
					updateDesignParam(dictSathi,stageModule,minNodeIn,minNodeOut)
					# false triggered sensitivity : tamper the sensitivity value : set to 0
					dictSathi[bumpNode].opSense = 0
			
				# bump the node	and update the param of circuit
				# dictSathi[bumpNode].gateSize = dictSathi[bumpNode].gateSize * modConst.BUMPSIZE
				print "gate:",bumpNode,"resized:",dictSathi[bumpNode].gateSize # comment
				#updateDesignParam(dictSathi,stageModule,minNodeIn,minNodeOut)
				displayUpdateDesignParam(dictSathi,stageModule,minNodeIn,minNodeOut)

# The formulation can be defined as below:
#			minimize Power 
# 			subject t0  SUM alpha_i x_i <= Amax
# 			subject to  Delay <= T_spec
# Returns True on success of optimization and False on failure
def tilosFrameworkComb(dictSathi,stageModule,minNodeIn,minNodeOut):
	startProb = time.time()
	minPath = 0
	maxPath = 0 
	area = 0 
	power = 0 
	modConst = modConstraint()
	extractSensitivityFactorGates(dictSathi,stageModule,minNodeIn,minNodeOut)	
	power,area,maxPath,minPath = initUpdateDesignframework(dictSathi,stageModule,minNodeIn,minNodeOut)	# design update framework: unit gate sizing factor
	if maxPath <= modConst.ATmax:
		return True
	else:
		# optimization initial condition is not feasible
		print "start opt..."
		CriticalPathAndGateOpt(dictSathi,stageModule,minNodeIn,minNodeOut,maxPath)
	endProb = time.time() 
	insertStatus(filename,lineno(),'tilosTime','tilos-time:'+ str(endProb - startProb))
	

# Sequential block optimization : 	
def tilosFrameworkSeq(dictSathi,stageModule,minNodeIn,minNodeOut):	
	modConst = modConstraint()
	# extracting sensitivity once again : 	
	
	
	
# determine gate count:  The total number of gates in the circuit
# abandoned
def determineGateCount(dictSathi,stageModule):
	gateCount = 0
	for i in range(len(stageModule)):
		for j in range(len(stageModule[i].gateList)):
			SelfGate = stageModule[i].gateList[j]
			dictSathi[SelfGate].gateSerNum = gateCount
			# print "gate:",SelfGate ,"serialNo:",gateCount #comment
			gateCount += 1
	return gateCount		
	
# Define the pipeline joints : based on the maximum path delay method:
# 	Here the design can be approached in two ways:
#		- First resize shortest path delays in larger circuit and then estimate pipleline joints:
#		- Second method would be find the pipleline joint estimated and then resize for the sub-combinational blocks to satisfy the shortest path problem
# 	Analyis: Since both cases the pipeline joints are based on the maximum delay path, the pipeline joint estimation mustnt be differnt in ant apporach
#		- However the second approach would result in less computational time complexity : Hence the design of choice
#

# determines the flop joints: for pipelined edge based framework
def determinePipelineJoints(dictSathi,stageModule,minNodeIn,minNodeOut):
	designConst = modConstraint()				# design constraints
	flopCount = 0
	maxStage = 0
	for i in range(len(stageModule)):			# in-out-map
		for j in range(len(stageModule[i].gateList)):
			SelfGate = stageModule[i].gateList[j]
			# estimate pipeline joints
			dictSathi[SelfGate].stageEstimate = int(dictSathi[SelfGate].ATmax/float(designConst.ATpipe)) + 1
			maxStage =  dictSathi[SelfGate].stageEstimate # comment
			
	for i in range(len(stageModule)):			# in-out-map
		for j in range(len(stageModule[i].gateList)):
			SelfGate = stageModule[i].gateList[j]
			for k in range(len(dictSathi[SelfGate].fanOutList)):
				fanOutGate = dictSathi[SelfGate].fanOutList[k]
				if dictSathi[SelfGate].stageEstimate != dictSathi[fanOutGate].stageEstimate:
					dictSathi[SelfGate].pipeJoint  = 1
					print SelfGate,"pipe-stage-block:",dictSathi[SelfGate].stageEstimate,"joint:",fanOutGate,"pipe-stage-block:",dictSathi[fanOutGate].stageEstimate
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
def generateSequentialBlockFramework(dictSathi,stageModule,SeqBlockJoint,maxStage):
	const = modConstraint()
	for i in range(maxStage-1):
		pJoint = PipeJoint()
		SeqBlockJoint.append(pJoint)
		SeqBlockJoint[i].stageNum = i+1


	# insert the pipe joint framework based on the stages encountered:
	for i in range(len(stageModule)):				# in-out-map
		for j in range(len(stageModule[i].gateList)):
			SelfGate = stageModule[i].gateList[j]	
			if dictSathi[SelfGate].pipeJoint  == 1: 	# pipeline joint node	
				selfStage = dictSathi[SelfGate].stageEstimate	
				SeqBlockJoint[selfStage-1].nodeInJoint.append(SelfGate)
				
	pipeDef = len(SeqBlockJoint)		
	# print all the joint based farmework:
	for l in range(pipeDef):
		print "stage:",SeqBlockJoint[l].stageNum,"Joint List:",SeqBlockJoint[l].nodeInJoint
		
	# verify if the pipeline stages exceeded the constraint set 
	if pipeDef < const.numPipeStage - 1: # less pipelined stages than requires
		sline = "tilosFail:less stage pipelined"
		skey = 'tilos-genCut'
		insertStatus(filename,lineno(),skey,sline)	
	elif pipeDef < const.numPipeStage - 1: # more pipelined stages than requires
		sline = "tilosFail:excess stages pipelined"
		skey = 'tilos-genCut'
		insertStatus(filename,lineno(),skey,sline)		
	else:
		sline = "tilosPipeline: Required Stages Achieved"
		skey = 'tilos-genCut'		
		insertStatus(filename,lineno(),skey,sline)


# determine the delay padding that might be required : for functional satisfiability
def determinePadPipeDesignFeasible(dictSathi,stageModule,minNodeIn,minNodeOut,maxStage,flopCount): 
	flopCountExtra = 0
	stageGap = 0
	for i in range(len(stageModule)):			# in-out-map
		for j in range(len(stageModule[i].gateList)):
			SelfGate = stageModule[i].gateList[j]
			if SelfGate in minNodeOut:
				stageGap = maxStage - dictSathi[SelfGate].stageEstimate 
				if stageGap:
					flopCountExtra += 1
			for k in range(len(dictSathi[SelfGate].fanOutList)):
				fanOutGate = dictSathi[SelfGate].fanOutList[k]
				stageGap = dictSathi[fanOutGate].stageEstimate  - dictSathi[SelfGate].stageEstimate
				# if stageGap = 0: lies in same stage: if stageGap =1 : no need to delay pad: if stageGap >= 2 : add flop and delay pad: stageGap-1 
				if stageGap >= 2:
					# insert delay pad : insert a flop
					flopCountExtra += stageGap-1	
			
	print "extra flop: ",flopCountExtra
	print "total flop: ",flopCountExtra + flopCount				


# optimization functions
def optFunctions(dictSathi,stageModule,minNodeIn,minNodeOut,numStage):
	SeqBlockJoint = []	
	tilosFrameworkComb(dictSathi,stageModule,minNodeIn,minNodeOut)
	#flopCount, maxStage = determinePipelineJoints(dictSathi,stageModule,minNodeIn,minNodeOut)
	#generateSequentialBlockFramework(dictSathi,stageModule,SeqBlockJoint,maxStage)
	#determinePadPipeDesignFeasible(dictSathi,stageModule,minNodeIn,minNodeOut,maxStage,flopCount)


# main heuristics: based on a modified tilos solver				
def mainHeuristicandGen(dictSathi,stageModule,minNodeIn,minNodeOut,numStage):
	initUpdateDesignframework(dictSathi,stageModule,minNodeIn,minNodeOut)
	#optFunctions(dictSathi,stageModule,minNodeIn,minNodeOut,numStage)
	#extractSensitivityFactorGates(dictSathi,stageModule,minNodeIn,minNodeOut)
	
		
