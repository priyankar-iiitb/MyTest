# Determines the activity factor of the network module
# Estimate of signal probability in combinational logic networks: Ercolani,Favalli et al. 1989 IEEE
# Abstract: 	Calculation of node signal probabilities in combinational networks that improve
#		the state of the art by providing a better accuracy than existing algorithms and 
#		a deeper insight in the effects of first order correlation due to multiple fanout
#		reconvergencies.
# 		RFON(s) are the reconvergent nodes having fanout > 1 and branches that reconverge within the circuit
#			- the order of RFON considered is of importance: 
# 				-proceed from lower to higher level 
#				-within same level ,from the RFON  whose brances reconverge at lower level	
#
#		The input pins are assigned as nodes for activity analysis of the network	
# Test run: ISCAS-85 benchmark circuits
#

import os
import sys
from status import solverStat, insertStatus, reportStatus, lineno
import time

# file name stored : filename 
filename = os.path.basename(__file__)

# define the digital gate of the circuit
class digitalGate:
	def __init__(self,gateType):
		self.gateType = gateType
		self.inputProb = []
				
	def __del__(self):
		pass	
		
	def GateProb(self):
		probVal = functionProbCompute(self.inputProb,self.gateType)	
		return probVal


# define class structure for the node rfon estimate map
class rfonNode:
	def __init__(self):
		self.startLevel = 0
		self.endLevel = 0
		self.startGate = ''
		self.endGate = ''
	def __del__(self):
		pass			

# define the list for rfon gates: contains all the rfon nodes: unsorted in levels and convergence levels
rfonList = []

# determine the probabilstic effect for the input nodes probability
# 	-estimates based on the digital gate functionality
def functionProbCompute(probInList,gateType):
	if gateType == 'NOT': 	# not gate 
		result = 1 - probInList[0]
		
	elif gateType == 'BUFF': # buffer
		result = probInList[0] 		
	else: 			# other digital gates 
		lenInList = len(probInList)
		result = probInList[0]		
		for i in range(1,lenInList):
			val = probInList[i]
			if gateType == 'AND':
				result  = result*val 
			if gateType == 'NAND':
				result = 1 - (result*val)
			if gateType == "OR":
				result = result + val - (result*val)		
			if gateType == "NOR":
				result = 1 - (result + val - (result*val))							
			if gateType == 'XOR':
				result = (1-result)*val + result*(1-val)
			if gateType == 'XNOR':
				result = result* val + (1-result)*(1-val)	
	return result			


# traverse the graph with a starting node and traverse the entire fanout mapping
# 	- traverse fanout cone to determine the RFON nodes
def traverseGraphfanOutMapRFON(SelfGate,dictNode,stageModule,minNodeIn,minNodeOut):
	memList = []
	opList = []
	opList.append(SelfGate)
	#print SelfGate
	while opList != []:
		for j in range(len(opList)):
			for i in range(len(dictNode[opList[j]].fanOutList)):
				outGate = dictNode[opList[j]].fanOutList[i]
				if outGate not in memList:
					memList.append(outGate)
		opList = memList
		#print opList
		memList = []
		if len(opList) == 1:  # detection of convergence
			rfon = rfonNode()
			rfon.startLevel = dictNode[SelfGate].gateStage
			rfon.endLevel = dictNode[opList[0]].gateStage
			rfon.startGate = SelfGate
			rfon.endGate = opList[0]
			rfonList.append(rfon)
			#print "start:",SelfGate,"end",opList[0]	
			break
	

# arrange the rfon nodes in the circuit
def arrangeRfonNodes(stageModule):
	levelRfonNodes = []
	finRfonList = []
	for i in range(len(stageModule)+1): # including the input node pins
		for j in range(len(rfonList)):	
			if rfonList[j].startLevel == i:
				levelRfonNodes.append(rfonList[j])
		# sort the list : with the attribute end-Level : belongs to same level: starts with zero level
		levelRfonNodes.sort(key =lambda x:x.endLevel)
		# add to the main file :sorted on min reconvergence distance and level
		finRfonList.extend(levelRfonNodes)
		levelRfonNodes = []
		
	# add the number of rfon to status:
	insertStatus(filename,lineno(),'rfonNum','RFON Count:'+str(len(rfonList)))		
	return finRfonList	
			

# determining the order of the RFON determination scheme O(n^2)
#	- the gates are already set in levels from prior design framework
def determineOrderOfRFON(dictNode,stageModule,minNodeIn,minNodeOut):
	# input nodes of the circuit 
	for i in range(len(minNodeIn)):
		SelfGate = minNodeIn[i]
		if len(dictNode[SelfGate].fanOutList) > 1: # suspect for RFON node
			traverseGraphfanOutMapRFON(SelfGate,dictNode,stageModule,minNodeIn,minNodeOut)			
	# intermediate nodes : except the input nodes 
	for i in range(len(stageModule)):			# in-out-map
		for j in range(len(stageModule[i].gateList)):
			SelfGate = stageModule[i].gateList[j]
			if len(dictNode[SelfGate].fanOutList) > 1: # suspect for RFON node
				traverseGraphfanOutMapRFON(SelfGate,dictNode,stageModule,minNodeIn,minNodeOut)
			else:	# not a suspect for RFON node			
				pass	
	return arrangeRfonNodes(stageModule)			


# runs the zero mode analysis on the digital circuit
#  	- perfectly maps the probabilty at node for tree based structure with no RFON(s)
# 	- linear time algorithm : p(j,0)
def runZeroModeModel(dictNode,stageModule,minNodeIn,minNodeOut):
	gateCount = 0
	probInList = []		# stores the input probability mapping
	for i in range(len(stageModule)):			# in-out-map
		for j in range(len(stageModule[i].gateList)):
			SelfGate = stageModule[i].gateList[j]
			gateCount += 1
			for k in range(len(dictNode[SelfGate].fanInList)):
				fanInNode = dictNode[SelfGate].fanInList[k]
				if fanInNode in minNodeIn:
					probInList.append(0.5) 
				else:
					probInList.append(dictNode[fanInNode].gateActivityZero) 
					
			dictNode[SelfGate].gateActivityZero = functionProbCompute(probInList,dictNode[SelfGate].gateType)
			# make copies
			dictNode[SelfGate].gateActivitySetLo = dictNode[SelfGate].gateActivityZero	# copies to initialize the framework
			dictNode[SelfGate].gateActivitySetHi = dictNode[SelfGate].gateActivityZero	# copies to initialize the framework
			dictNode[SelfGate].gateActivity = dictNode[SelfGate].gateActivityZero		# copies to initialize the framework
			dictNode[SelfGate].gateSignalProb = dictNode[SelfGate].gateActivityZero		# copies to initialize the framework
			#print "gate",SelfGate," activity:",dictNode[SelfGate].gateActivityZero # comment
			probInList = []			
	insertStatus(filename,lineno(),'numGates','Tot Gates :'+ str(gateCount))
			

# estimate network activity factor of the framework
#	- uses the rfon assorted nodes : rfonSortedList
def UpdateProbNode(dictNode,outGate,startNode,minNodeIn):
	probInListZero = []
	probInListOne = []
	#print startNode,outGate #comment
	for i in range(len(dictNode[outGate].fanInList)):
		fanInNode = dictNode[outGate].fanInList[i]
		if fanInNode == startNode: # single dependency rfon node
			probInListZero.append(0)
			probInListOne.append(1)
		elif fanInNode in minNodeIn:
			probInListZero.append(0.5)
			probInListOne.append(0.5)
		else:
			probInListZero.append(dictNode[fanInNode].gateActivitySetLo)
			probInListOne.append(dictNode[fanInNode].gateActivitySetHi)	
	
	# update probability map for outGate
	dictNode[outGate].gateActivitySetLo = functionProbCompute(probInListZero,dictNode[outGate].gateType)
	dictNode[outGate].gateActivitySetHi = functionProbCompute(probInListOne,dictNode[outGate].gateType)	

	pstartZero = dictNode[outGate].gateActivitySetLo
	pstartOne =  dictNode[outGate].gateActivitySetHi
	
	if startNode in minNodeIn:
		pZero = 0.5 
		pOne = 0.5
	else:
		pZero = 1 - dictNode[startNode].gateActivity
		pOne = 	dictNode[startNode].gateActivity

	dictNode[outGate].gateActivity = pstartZero * pZero + pstartOne * pOne
	#print " gate:",outGate," prob:",dictNode[outGate].gateActivity," zero:",probInListZero," one:",probInListOne #comment


def UpdateInitNextRfon(dictNode,stageModule,minNodeIn,minNodeOut,startNode):
	for i in range(len(stageModule)):			# in-out-map
		for j in range(len(stageModule[i].gateList)):
			SelfGate = stageModule[i].gateList[j]
			dictNode[SelfGate].gateActivitySetLo = dictNode[SelfGate].gateActivity	# copies to initialize the framework
			dictNode[SelfGate].gateActivitySetHi = dictNode[SelfGate].gateActivity	# copies to initialize the framework
			
			# update the weighting factor
			dictNode[SelfGate].gateWeightFactor = abs(dictNode[SelfGate].gateActivity - dictNode[SelfGate].gateActivityZero)
			#print "gate:",SelfGate," weight:",dictNode[SelfGate].gateWeightFactor # comment
			
			# updating the prev sum rfon weight factor 
			dictNode[SelfGate].sumRfonWeightFactor += dictNode[SelfGate].gateWeightFactor
			#print "sum:",dictNode[SelfGate].sumRfonWeightFactor			
			
			# update probability of previous 			
			dictNode[SelfGate].gateSignalProbHist = dictNode[SelfGate].gateSignalProb		
			
			# compute the signal value 
			gsp = 	dictNode[SelfGate].gateActivity 						# p_f(j)		
			gsph = 	dictNode[SelfGate].gateSignalProbHist 						# p(j,t-1)
			srfwf = dictNode[SelfGate].sumRfonWeightFactor -dictNode[SelfGate].gateWeightFactor	# ws(j,t-1)		
			gwf =   dictNode[SelfGate].gateWeightFactor						# w_f(j)			
			if gwf == 0 and srfwf == 0: # to protect against division by zero
				pass
			else:	
				dictNode[SelfGate].gateSignalProb = (gsph*srfwf+gsp*gwf)/float(srfwf+gwf)	# p(j,t)
				# estimating the switching activity factor
				dictNode[SelfGate].gateSignalProb = dictNode[SelfGate].gateSignalProb * (1-dictNode[SelfGate].gateSignalProb)
			#print "gate:",SelfGate," rfon:",startNode," p_f(j)",gsp," p(j,t-1)",gsph," ws(j,t-1)",srfwf," w_f(j)",gwf," prob:",dictNode[SelfGate].gateSignalProb,"\n" #comment
			

def subDetermineActivityDwaa(dictNode,stageModule,minNodeIn,minNodeOut,rfonSortedList):
	memList = []
	opList = []
	retComputeVal = 0
	for k in range(len(rfonSortedList)):
		startNode = rfonSortedList[k].startGate
		opList.append(startNode)
		while opList != []:
			for j in range(len(opList)):
				for i in range(len(dictNode[opList[j]].fanOutList)):
					outGate = dictNode[opList[j]].fanOutList[i]
					if outGate not in memList:
						# insert function computation here: Sequential push gates driven by startNode
						UpdateProbNode(dictNode,outGate,startNode,minNodeIn)
						memList.append(outGate)
			opList = memList
			memList = []		
		# updating mode for next stage rfon compute:				
		UpdateInitNextRfon(dictNode,stageModule,minNodeIn,minNodeOut,startNode)


# switching activity factor determines the prob that switching occured at a node. Prior designs
# 	were meant to just estimate the probability of state of a node
def updateSwitchingActivityfactor(dictNode,stageModule):
	for i in range(len(stageModule)):			# in-out-map
		for j in range(len(stageModule[i].gateList)):
			SelfGate = stageModule[i].gateList[j]
			dictNode[SelfGate].gateSignalProb = dictNode[SelfGate].gateSignalProb * (1-dictNode[SelfGate].gateSignalProb)

# estimates the activity factor and plugs into the dictionary file of the digitak circuit
#  	- implemented model of the dynamic weighted averaging method model
def determineActivitydwaa(dictNode,stageModule,minNodeIn,minNodeOut):
	startProb = time.time()
	rfonSortedList = []	# sorted rfon nodes based on level and faster convergence
	rfonSortedList = determineOrderOfRFON(dictNode,stageModule,minNodeIn,minNodeOut)
	runZeroModeModel(dictNode,stageModule,minNodeIn,minNodeOut)
	subDetermineActivityDwaa(dictNode,stageModule,minNodeIn,minNodeOut,rfonSortedList)
	#updateSwitchingActivityfactor(dictNode,stageModule)
	endProb = time.time() 
	insertStatus(filename,lineno(),'timeProb','Prob Compute time:'+ str(endProb - startProb))
	

	

	
