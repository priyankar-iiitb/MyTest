# This file will contain the modules for generating the equations 
# Generated Equations are similar : encoded in  solver.py


# TESTING/VERIFYING MODULES FOR AUTOMATED DESIGN FRAMEWORK : AUTOMATED PIPELINING AND OPTIMIZATION		
# Timing generate Equation : pico second
def stageGenerateEquation(dictNode,stageModule,minNodeIn,minNodeOut):
	finline =''
	lineArea = ''
	eqnCount = 0
	isFlag = 0
	fw = open('eqn.txt','w')
	
	# traverse Out:In mapping for generating dynamic programming based equation formulation:
	fw.write('TESTING/VERIFYING MODULES FOR AUTOMATED DESIGN FRAMEWORK : AUTOMATED PIPELINING AND OPTIMIZATION')
		
	# power constraint : microWatts
	fw.write('\n\nPower Constraints: Objective Function\nMin()\n')
	for i in range(0,len(stageModule)):			
		for j in range(len(stageModule[i].gateList)):	
			SelfGate = stageModule[i].gateList[j]
			line = '0.5 alpha_' + SelfGate + " freq " + ' Cint_' + SelfGate + ' x_'+ SelfGate +' Vdd^2 + '
			for k in range(len(dictNode[SelfGate].fanOutList)):
				fanOutGate = dictNode[SelfGate].fanOutList[k]
				line += '0.5 alpha_' + SelfGate +" freq "+ ' Cint_' + fanOutGate + ' x_'+ fanOutGate + ' Vdd^2 + '
			if SelfGate in minNodeOut:
				line += '0.5 alpha_' + SelfGate +" freq "+ ' Cload' + ' Vdd^2 +'	
			line += 'Ileak_' + SelfGate + ' x_' + SelfGate + 'Vdd '	
			line += '+ \n'
			fw.write(line)	

	

	# Timing: picoSecond
	fw.write('\n\nTiming Equations: \n')
	for i in range(0,len(stageModule)):			
		for j in range(len(stageModule[i].gateList)):
			# print "AT_",stageModule[i].gateList[j],"=", dictNode[stageModule[i].gateList[j]].fanOutList #comment
			SelfGate = stageModule[i].gateList[j]
			# nodes which have fan-in from input pins completely
			isFlag = 0
			# nodes which have at least a single fan-in from a valid node.
			for m in range(len(dictNode[SelfGate].fanInList)):
				if dictNode[SelfGate].fanInList[m] not in minNodeIn:
					# print dictNode[SelfGate].fanInList[m] 			
					line = "0.69R_"+ SelfGate + " ~AT_"+ SelfGate +" Cint_"+ SelfGate 
					for k in range(len(dictNode[SelfGate].fanOutList)):
						FanOutGate = dictNode[stageModule[i].gateList[j]].fanOutList[k]
						line += " + " + " 0.69R_" + SelfGate + " ~x_"+ SelfGate + " Cint_"+ FanOutGate + " x_"+ FanOutGate + "~AT_ "+SelfGate
					# modify to model for Cload flops at output
					if not dictNode[SelfGate].fanOutList: 
						line += " + 0.69R_"+ SelfGate + " ~x_" + SelfGate + " Cload" + " ~AT_" + SelfGate 
							
					line += " + AT_"+dictNode[SelfGate].fanInList[m] + "~AT_" + SelfGate 
					fw.write(line+" <= 1 \n")
				else:
					isFlag += 1
			# nodes which have fan-in from input pins completely		
			if len(dictNode[SelfGate].fanInList) == isFlag:
				line = "0.69R_"+ SelfGate + " ~AT_"+ SelfGate +" Cint_"+ SelfGate 
				for z in range(len(dictNode[SelfGate].fanOutList)):
					FanOutGate = dictNode[stageModule[i].gateList[j]].fanOutList[z]
					line += " + " + " 0.69R_" + SelfGate + " ~x_"+ SelfGate + " Cint_"+ FanOutGate + " x_"+ FanOutGate + "~AT_ "+SelfGate	
				fw.write(line+" <= 1 \n")
			# equation for maximum delay path limit for circuit
			if not dictNode[SelfGate].fanOutList: 
				finline = "(1/AT_max)"+" AT_"+SelfGate +" <= 1\n" 
			# write the final timing constraint bounds	
			fw.write(finline)
		
	# Area  constraints : micro-meter-square
	#fw.write('\n\nIn-eq sizing equations: \n')
	for i in range(0,len(stageModule)):			
		for j in range(len(stageModule[i].gateList)):	
			SelfGate = stageModule[i].gateList[j]
			lineArea += "(1/Amax)"+	" A_"+ SelfGate + " x_"	+ SelfGate +  " + "
			#fw.write("(1/x_max) x_"+SelfGate+" <= 1 \n")
			#fw.write("~x_"+SelfGate+" <= 1\n")
	fw.write('\n\nArea Equations: \n')		
	fw.write(lineArea +" <= 1\n")	

	# sizing constraints : micro-meter-square
	fw.write('\n\nIn-eq sizing equations: \n')
	for i in range(0,len(stageModule)):			
		for j in range(len(stageModule[i].gateList)):	
			SelfGate = stageModule[i].gateList[j]
			#lineArea += "(1/Amax)"+	" A_"+ SelfGate + " x_"	+ SelfGate +  " + "
			if dictNode[SelfGate].gateType == 'BUFF':
				fw.write("(1/x_max_buff) x_"+SelfGate+" <= 1 \n")
			else:	
				fw.write("(1/x_max) x_"+SelfGate+" <= 1 \n")
			fw.write("~x_"+SelfGate+" x_min " +" <= 1\n")
	#fw.write('\n\nArea Equations: \n')		
	#fw.write(lineArea +" <= 1\n")	

	fw.close()

# Level Based Timing Model Framework: 
def stageGenerateEquationLevelBased(dictNode,stageModule,minNodeIn,minNodeOut):
	finline =''
	lineArea = ''
	isFlag = 0
	
	fw = open('eqnLevel.txt','w')
	fw.write('TESTING/VERIFYING MODULES FOR AUTOMATED DESIGN FRAMEWORK : AUTOMATED PIPELINING AND OPTIMIZATION')
	# power constraint : microWatts
	fw.write('\n\nPower Constraints: Objective Function\nMin()\n')
	for i in range(0,len(stageModule)):			
		for j in range(len(stageModule[i].gateList)):	
			SelfGate = stageModule[i].gateList[j]
			line = '0.5 alpha_' + SelfGate + " freq " + ' Cint_' + SelfGate + ' x_'+ SelfGate +' Vdd^2 + '
			for k in range(len(dictNode[SelfGate].fanOutList)):
				fanOutGate = dictNode[SelfGate].fanOutList[k]
				line += '0.5 alpha_' + SelfGate +" freq "+ ' Cint_' + fanOutGate + ' x_'+ fanOutGate + ' Vdd^2 + '
			if SelfGate in minNodeOut:
				line += '0.5 alpha_' + SelfGate +" freq "+ ' Cload' + ' Vdd^2 +'	
			line += 'Ileak_' + SelfGate + ' x_' + SelfGate + 'Vdd '	
			line += '+ \n'
			fw.write(line)	
	
	
	# Timing: picoSecond : gateStage
	fw.write('\n\nTiming Equations: \n')
	for i in range(0,len(stageModule)):			
		for j in range(len(stageModule[i].gateList)):
			# print "AT_",stageModule[i].gateList[j],"=", dictNode[stageModule[i].gateList[j]].fanOutList #comment
			SelfGate = stageModule[i].gateList[j]
			# nodes which have fan-in from input pins completely
			isFlag = 0
			# nodes which have at least a single fan-in from a valid node.
			for m in range(len(dictNode[SelfGate].fanInList)):
				if dictNode[SelfGate].fanInList[m] not in minNodeIn:
					inNode = dictNode[SelfGate].fanInList[m] 			
					line = "0.69R_"+ SelfGate + " ~AT_"+ str(dictNode[SelfGate].gateStage) +" Cint_"+ SelfGate 
					for k in range(len(dictNode[SelfGate].fanOutList)):
						FanOutGate = dictNode[stageModule[i].gateList[j]].fanOutList[k]
						line += " + " + " 0.69R_" + SelfGate + " ~x_"+ SelfGate + " Cint_"+ FanOutGate + " x_"+ FanOutGate + "~AT_ "+ str(dictNode[SelfGate].gateStage) 
					# modify to model for Cload flops at output
					if not dictNode[SelfGate].fanOutList: 
						line += " + 0.69R_"+ SelfGate + " ~x_" + SelfGate + " Cload" + " ~AT_" + str(dictNode[SelfGate].gateStage)  
							
					line += " + AT_"+ str(dictNode[inNode].gateStage)  + "~AT_" + str(dictNode[SelfGate].gateStage) 
					fw.write(line+" <= 1 \n")
				else:
					isFlag += 1
			# nodes which have fan-in from input pins completely		
			if len(dictNode[SelfGate].fanInList) == isFlag:
				line = "0.69R_"+ SelfGate + " ~AT_"+ str(dictNode[SelfGate].gateStage) +" Cint_"+ SelfGate 
				for z in range(len(dictNode[SelfGate].fanOutList)):
					FanOutGate = dictNode[stageModule[i].gateList[j]].fanOutList[z]
					line += " + " + " 0.69R_" + SelfGate + " ~x_"+ SelfGate + " Cint_"+ FanOutGate + " x_"+ FanOutGate + "~AT_ "+ str(dictNode[SelfGate].gateStage)	
				fw.write(line+" <= 1 \n")
			# equation for maximum delay path limit for circuit
			if not dictNode[SelfGate].fanOutList: 
				finline = "(1/AT_max)"+" AT_"+ str(dictNode[SelfGate].gateStage) +" <= 1\n" 
			# write the final timing constraint bounds	
			fw.write(finline)

	# Area  constraints : micro-meter-square
	#fw.write('\n\nIn-eq sizing equations: \n')
	for i in range(0,len(stageModule)):			
		for j in range(len(stageModule[i].gateList)):	
			SelfGate = stageModule[i].gateList[j]
			lineArea += "(1/Amax)"+	" A_"+ SelfGate + " x_"	+ SelfGate +  " + "
			#fw.write("(1/x_max) x_"+SelfGate+" <= 1 \n")
			#fw.write("~x_"+SelfGate+" <= 1\n")
	fw.write('\n\nArea Equations: \n')		
	fw.write(lineArea +" <= 1\n")	

	# sizing constraints : micro-meter-square
	fw.write('\n\nIn-eq sizing equations: \n')
	for i in range(0,len(stageModule)):			
		for j in range(len(stageModule[i].gateList)):	
			SelfGate = stageModule[i].gateList[j]
			#lineArea += "(1/Amax)"+	" A_"+ SelfGate + " x_"	+ SelfGate +  " + "
			if dictNode[SelfGate].gateType == 'BUFF':
				fw.write("(1/x_max_buff) x_"+SelfGate+" <= 1 \n")
			else:	
				fw.write("(1/x_max) x_"+SelfGate+" <= 1 \n")
			fw.write("~x_"+SelfGate+" x_min " +" <= 1\n")
	#fw.write('\n\nArea Equations: \n')		
	#fw.write(lineArea +" <= 1\n")		
	fw.close()



def stageGenerateEquationSeq(dictNode,stageModule,minNodeIn,minNodeOut):
	finline =''
	lineArea = ''
	linePower = ''
	linePowerLoad = ''
	eqnCount = 0
	isFlag = 0
	fw = open('finEqn.txt','w')
	
	# traverse Out:In mapping for generating dynamic programming based equation formulation:
	fw.write('TESTING/VERIFYING MODULES FOR AUTOMATED DESIGN FRAMEWORK : AUTOMATED PIPELINING AND OPTIMIZATION: SEQUENTIAL OPT')		
	
	# power constraints : microWatts
	fw.write('\n\nPower Constraints:Objective Function\nMin()\n')
	for i in range(0,len(stageModule)):			
		for j in range(len(stageModule[i].gateList)):	
			SelfGate = stageModule[i].gateList[j]
			# self gate dyn power
			linePower = str(0.5) + " alpha_" + SelfGate + " freq "+" Vdd^2 Cint_" + SelfGate +" x_"+SelfGate
			if dictNode[SelfGate].pipeJoint != 1: 
				# non pipe Joint gate
				for k in range(len(dictNode[SelfGate].fanOutList)):
					gateFanOut = dictNode[SelfGate].fanOutList[k]
					linePower += " + " + str(0.5) + " alpha_"+ gateFanOut + " freq " +" Vdd^2 Cint_" + gateFanOut +" x_"+ gateFanOut
				if dictNode[SelfGate].fanOutList == []:	# output gates nodes
					linePower += " + " + str(0.5) + " alpha_"+ SelfGate + " freq " +"Vdd^2 Cload"	
			else:
				# pipeJoint gate
				linePower += " + "+ str(0.5) + " alpha_"+ SelfGate + " freq " +" Vdd^2 Cflop"  
			linePower += " + Ileak x_"+ SelfGate + " Vdd"				
			fw.write(linePower+"\n")	
	

	# Timing: picoSecond
	fw.write('\n\nTiming Equations: \n')
	for i in range(0,len(stageModule)):			
		for j in range(len(stageModule[i].gateList)):
			# print "AT_",stageModule[i].gateList[j],"=", dictNode[stageModule[i].gateList[j]].fanOutList #comment
			SelfGate = stageModule[i].gateList[j]
			SelfGateStage = dictNode[SelfGate].stageEstimate	# stores the self gate stage
			isFlag = 0
			# nodes which have at least a single fan-in from a valid node.
			for m in range(len(dictNode[SelfGate].fanInList)):
				if dictNode[SelfGate].fanInList[m] not in minNodeIn:
					# print dictNode[SelfGate].fanInList[m] 			
					line = "0.69R_"+ SelfGate + " ~AT_"+ SelfGate +" Cint_"+ SelfGate 
					for k in range(len(dictNode[SelfGate].fanOutList)):
						FanOutGate = dictNode[stageModule[i].gateList[j]].fanOutList[k]
						# Assumption : since any single cross stage interface is taken as selfgate pipeJoint, its always ensured that the fan-outs of self gate belong to same stage
						line += " + " + " 0.69R_" + SelfGate + " ~x_"+ SelfGate + " Cint_"+ FanOutGate + " x_"+ FanOutGate + "~AT_ "+SelfGate
					# modify to model for Cload flops at output
					if not dictNode[SelfGate].fanOutList: # for no fanout(s): considerd as output nodes
						line += " + 0.69R_"+ SelfGate + " ~x_" + SelfGate + " Cload" + " ~AT_" + SelfGate 
							
					if dictNode[dictNode[SelfGate].fanInList[m]].pipeJoint != 1:
						line += " + AT_"+dictNode[SelfGate].fanInList[m] + "~AT_" + SelfGate 
					fw.write(line+" <= 1 \n")
				else:
					isFlag += 1
			# nodes which have fan-in from input pins completely		
			if len(dictNode[SelfGate].fanInList) == isFlag:
				line = "0.69R_"+ SelfGate + " ~AT_"+ SelfGate +" Cint_"+ SelfGate 
				for z in range(len(dictNode[SelfGate].fanOutList)):
					FanOutGate = dictNode[stageModule[i].gateList[j]].fanOutList[z]
					# if SelfGate is a pipeline joint then compute the load gates else flop load 
					if dictNode[SelfGate].pipeJoint != 1:
						line += " + " + " 0.69R_" + SelfGate + " ~x_"+ SelfGate + " Cint_"+ FanOutGate + " x_"+ FanOutGate + "~AT_ "+SelfGate	
					else:
						line += " + " + " 0.69R_" + SelfGate + " ~x_"+ SelfGate + " Cflop" + "~AT_ "+ SelfGate
						break 	# single flop drive multiple FO 		
				fw.write(line+" <= 1 \n")
				
			# equation for maximum delay path limit for circuit
			if not dictNode[SelfGate].fanOutList: 
				finline = "AT_"+SelfGate+"~AT_pipe "+" <=1\n"					
			# equation for pipeline timing limits
			if dictNode[SelfGate].pipeJoint == 1: 
				finline = "AT_"+SelfGate+"~AT_pipe "+" <=1\n"
			fw.write(finline)
			finline = ''
	
		
	# Area  constraints : micro-meter-square
	#fw.write('\n\nIn-eq sizing equations: \n')
	for i in range(0,len(stageModule)):			
		for j in range(len(stageModule[i].gateList)):	
			SelfGate = stageModule[i].gateList[j]
			lineArea += "(1/Amax)"+	" A_"+ SelfGate + " x_"	+ SelfGate +  " + "
			#fw.write("(1/x_max) x_"+SelfGate+" <= 1 \n")
			#fw.write("~x_"+SelfGate+" <= 1\n")
	fw.write('\n\nArea Equations: \n')		
	fw.write(lineArea +" <= 1\n")	

	# sizing constraints : micro-meter-square
	fw.write('\n\nIn-eq sizing equations: \n')
	for i in range(0,len(stageModule)):			
		for j in range(len(stageModule[i].gateList)):	
			SelfGate = stageModule[i].gateList[j]
			#lineArea += "(1/Amax)"+	" A_"+ SelfGate + " x_"	+ SelfGate +  " + "
			if dictNode[SelfGate].gateType == 'BUFF':
				fw.write("(1/x_max_buff) x_"+SelfGate+" <= 1 \n")
			else:	
				fw.write("(1/x_max) x_"+SelfGate+" <= 1 \n")
			fw.write("~x_"+SelfGate+" x_min " +" <= 1\n")
	#fw.write('\n\nArea Equations: \n')		
	#fw.write(lineArea +" <= 1\n")	

	fw.close()


# level based timing formulation : Sequential Equation Generator
def stageGenerateEquationSeqLevelBased(dictNode,stageModule,minNodeIn,minNodeOut):
	finline =''
	lineArea = ''
	linePower = ''
	linePowerLoad = ''
	eqnCount = 0
	isFlag = 0
	fw = open('eqnLevelFin.txt','w')
	
	# traverse Out:In mapping for generating dynamic programming based equation formulation:
	fw.write('TESTING/VERIFYING MODULES FOR AUTOMATED DESIGN FRAMEWORK : AUTOMATED PIPELINING AND OPTIMIZATION: SEQUENTIAL OPT')		
	
	# power constraints : microWatts
	fw.write('\n\nPower Constraints:Objective Function\nMin()\n')
	for i in range(0,len(stageModule)):			
		for j in range(len(stageModule[i].gateList)):	
			SelfGate = stageModule[i].gateList[j]
			# self gate dyn power
			linePower = str(0.5) + " alpha_" + SelfGate + " freq "+" Vdd^2 Cint_" + SelfGate +" x_"+SelfGate
			if dictNode[SelfGate].pipeJoint != 1: 
				# non pipe Joint gate
				for k in range(len(dictNode[SelfGate].fanOutList)):
					gateFanOut = dictNode[SelfGate].fanOutList[k]
					linePower += " + " + str(0.5) + " alpha_"+ gateFanOut + " freq " +" Vdd^2 Cint_" + gateFanOut +" x_"+ gateFanOut
				if dictNode[SelfGate].fanOutList == []:	# output gates nodes
					linePower += " + " + str(0.5) + " alpha_"+ SelfGate + " freq " +"Vdd^2 Cload"	
			else:
				# pipeJoint gate
				linePower += " + "+ str(0.5) + " alpha_"+ SelfGate + " freq " +" Vdd^2 Cflop"  
			linePower += " + Ileak x_"+ SelfGate + " Vdd"				
			fw.write(linePower+"\n")	
	

	# Timing: picoSecond
	fw.write('\n\nTiming Equations: \n')
	for i in range(0,len(stageModule)):			
		for j in range(len(stageModule[i].gateList)):
			SelfGate = stageModule[i].gateList[j]
			SelfGateStage = dictNode[SelfGate].stageEstimate	# stores the self gate stage
			isFlag = 0
			# nodes which have at least a single fan-in from a valid node.
			for m in range(len(dictNode[SelfGate].fanInList)):
				if dictNode[SelfGate].fanInList[m] not in minNodeIn:
					inNode = dictNode[SelfGate].fanInList[m] 			
					line = "0.69R_"+ SelfGate + " ~AT_"+ str(dictNode[SelfGate].gateStage)	+" Cint_"+ SelfGate 
					for k in range(len(dictNode[SelfGate].fanOutList)):
						FanOutGate = dictNode[stageModule[i].gateList[j]].fanOutList[k]
						# Assumption : since any single cross stage interface is taken as selfgate pipeJoint, its always ensured that the fan-outs of self gate belong to same stage
						line += " + " + " 0.69R_" + SelfGate + " ~x_"+ SelfGate + " Cint_"+ FanOutGate + " x_"+ FanOutGate + "~AT_ "+ str(dictNode[SelfGate].gateStage)	
					# modify to model for Cload flops at output
					if not dictNode[SelfGate].fanOutList: # for no fanout(s): considerd as output nodes
						line += " + 0.69R_"+ SelfGate + " ~x_" + SelfGate + " Cload" + " ~AT_" + str(dictNode[SelfGate].gateStage)	 
							
					if dictNode[dictNode[SelfGate].fanInList[m]].pipeJoint != 1:
						line += " + AT_"+str(dictNode[inNode].gateStage) + "~AT_" + str(dictNode[SelfGate].gateStage)	
					fw.write(line+" <= 1 \n")
				else:
					isFlag += 1
			# nodes which have fan-in from input pins completely		
			if len(dictNode[SelfGate].fanInList) == isFlag:
				line = "0.69R_"+ SelfGate + " ~AT_"+ str(dictNode[SelfGate].gateStage) +" Cint_"+ SelfGate 
				for z in range(len(dictNode[SelfGate].fanOutList)):
					FanOutGate = dictNode[stageModule[i].gateList[j]].fanOutList[z]
					# if SelfGate is a pipeline joint then compute the load gates else flop load 
					if dictNode[SelfGate].pipeJoint != 1:
						line += " + " + " 0.69R_" + SelfGate + " ~x_"+ SelfGate + " Cint_"+ FanOutGate + " x_"+ FanOutGate + "~AT_ "+ str(dictNode[SelfGate].gateStage)		
					else:
						line += " + " + " 0.69R_" + SelfGate + " ~x_"+ SelfGate + " Cflop" + "~AT_ "+ str(dictNode[SelfGate].gateStage)	
						break 	# single flop drive multiple FO 		
				fw.write(line+" <= 1 \n")
				
			# equation for maximum delay path limit for circuit
			if not dictNode[SelfGate].fanOutList: 
				finline = "AT_"+ str(dictNode[SelfGate].gateStage) +"~AT_pipe "+" <=1\n"					
			# equation for pipeline timing limits
			if dictNode[SelfGate].pipeJoint == 1: 
				finline = "AT_"+ str(dictNode[SelfGate].gateStage) +"~AT_pipe "+" <=1\n"
			fw.write(finline)
			finline = ''
	
		
	# Area  constraints : micro-meter-square
	#fw.write('\n\nIn-eq sizing equations: \n')
	for i in range(0,len(stageModule)):			
		for j in range(len(stageModule[i].gateList)):	
			SelfGate = stageModule[i].gateList[j]
			lineArea += "(1/Amax)"+	" A_"+ SelfGate + " x_"	+ SelfGate +  " + "
			#fw.write("(1/x_max) x_"+SelfGate+" <= 1 \n")
			#fw.write("~x_"+SelfGate+" <= 1\n")
	fw.write('\n\nArea Equations: \n')		
	fw.write(lineArea +" <= 1\n")	

	# sizing constraints : micro-meter-square
	fw.write('\n\nIn-eq sizing equations: \n')
	for i in range(0,len(stageModule)):			
		for j in range(len(stageModule[i].gateList)):	
			SelfGate = stageModule[i].gateList[j]
			#lineArea += "(1/Amax)"+	" A_"+ SelfGate + " x_"	+ SelfGate +  " + "
			if dictNode[SelfGate].gateType == 'BUFF':
				fw.write("(1/x_max_buff) x_"+SelfGate+" <= 1 \n")
			else:	
				fw.write("(1/x_max) x_"+SelfGate+" <= 1 \n")
			fw.write("~x_"+SelfGate+" x_min " +" <= 1\n")
	#fw.write('\n\nArea Equations: \n')		
	#fw.write(lineArea +" <= 1\n")	

	fw.close()

# Equation Generator for solver call V1.0
def genEquation(dictNode,stageModule,minNodeIn,minNodeOut):
	stageGenerateEquation(dictNode,stageModule,minNodeIn,minNodeOut)
	stageGenerateEquationLevelBased(dictNode,stageModule,minNodeIn,minNodeOut)	# level based timing framework

# Equation Generator for solver call V2.0
def genEquationSeq(dictNode,stageModule,minNodeIn,minNodeOut):
	stageGenerateEquationSeq(dictNode,stageModule,minNodeIn,minNodeOut)	
	stageGenerateEquationSeqLevelBased(dictNode,stageModule,minNodeIn,minNodeOut)
	

