# The constants and other considerations for process extracts 
# are listed down here for approximate : 130nm model library :

# Consists of the supply voltage: threhsold: leakage constants	
class gpower:
	def __init__(self):
		self.v_dd = 1.2						# supply -voltage
		self.v_th = 0.3782					# threshold- voltage		
		self.v_dd_ref = 1.2					# supply -voltage: volt default: 1.2 volt
		self.v_th_ref = 0.3782					# threshold- voltage: volt : default: 0.3782 volt		
		self.leak_m = 1.02 					# variable for excess fan-in(s)	
		self.alpha = 1.4					# constant
		
	def __del__(self):
		pass	
		
	def retLeakConst(self,):					# returns the leakage constant
		leak_e = 2.718281					# constant : e 	
		leak_var_o = (self.v_th -(0.06* self.v_dd))/0.04	# variable : power term
		leak_var = pow(leak_e,-leak_var_o)			# variable : power term
		return leak_var
		
	def retLeakGatePower(self,gateSize,unitLeak):			# computes leakage power: 
		leakGatePower =  unitLeak * self.v_dd * gateSize
		return leakGatePower
		
	def retDynamicPower(self,Tcap):				# computes dynamic power:
		dynConst = 0.5 * pow(self.v_dd,2)*Tcap			
		return dynConst
	
	# the total cap must be computed and then passed into the function 	
	def retGateDelayTime(self,res,TCap):				# computes gate delay:
		return 0.69 * res*TCap	
		
	def retAlphaPowerDelayTime(self,res,size,TCap):		# computes alpha power gate delay:
		alphaBuf = (self.v_dd - self.v_th)/float(self.v_dd_ref - self.v_th_ref)
		alphaVar = 1/float(pow(alphaBuf,self.alpha))  
		alphaDelay = alphaVar * 0.69 * (res/float(size)) * TCap
		return alphaDelay
		
	def computeGateSize(self,time,unitRes,unitSelfCap,LoadCap):	# computes the gate size 
		alphaBuf = (self.v_dd - self.v_th)/float(self.v_dd_ref - self.v_th_ref)
		alphaVar = pow(alphaBuf,self.alpha)
		gateSize = LoadCap / float( time/float(alphaVar * 0.69 * unitRes) - unitSelfCap)	
		return gateSize		

# flop model 
class mflop:
	def __init__(self):
		self.fLoad =  9			# femto-farad
		self.fArea =  2			# micro-meter-square
		self.fPower = 0.8		# micro-watt
	def __del__(self):
		pass		

# Consists of the wire parameters	
class gwire:
	# estimates: width=0.20um space=0.20um thickness=0.45um height=0.45um Kild=3.2 
	def __init__(self):
		self.w_res  = 0.01		# unit length : kilo-ohm
		self.w_cap  = 0.002		# unit length : femto-farad
		self.wc_res = 0.005		# unit fanout : constant (add)
		#self.wc_cap = 2		# unit fanout : constant (mul)	
		self.w_width = .20		# micrometer	
		self.rConst = 6			# constant 
	def __del__(self):
		pass	
	
	def wireAreaCompute(self,fanOutCount,constGateArea): # compute the partial wire area: 
		# wire_length = ~R_ri * A^0.5 * M  : need to multiply x^0.5 for equations 
		constWireArea = self.rConst * pow(constGateArea,0.5) * fanOutCount
		return constWireArea
		
	def  wireCapCompute(self,fanOutCount,unitGateArea):	# multiple return: unit wire-cap: wire cap
		# wire_cap = w_cap * M * ~R_ri * A^0.5 
		wire_cap = self.w_cap * fanOutCount * self.rConst * pow(unitGateArea,0.5)
		return wire_cap
			
		
# Consist of the buffer parameters 
# 	Refer trick mode in Rough Copy for modeling as a node gate		
class gbuff:
	def __init__(self):	
		self.lo_buff = 6		# unit leakage: micro-unit
		self.co_buff = 3		# femto-farad
		self.ro_buff = 0.05		# assuming no delay model
		self.ao_buff = 5		# micro-meter-square 
	def __del__(self):
		pass

	
# gate model for and gate 		
class gand:	
	def __init__(self):
		self.lo_and = 6			# unit leakage  :mico-unit
		self.co_and = 3.6 		# unit intrinsic capacitance: femto-farad
		self.ro_and = 5.2		# unit resistance: kilo-ohm
		self.ao_and = 5.15 		# unit-area: micro-meter-square
		self.ac_and = 1.25 		# constant(x)
		self.ak_and = 1.2 		# constant (in)		
	def __del__(self):
		pass	
		
# gate model for nand gate 		
class gnand:	
	def __init__(self):
		self.lo_nand = 7.125		# unit leakage  :mico-unit
		self.co_nand = 4.8 		# unit intrinsic capacitance: femto-farad
		self.ro_nand = 5.2		# unit resistance: kilo-ohm
		self.ao_nand = 3.4 		# unit-area: micro-meter-square
		self.ac_nand = 1.5 		# constant (x)	
		self.ak_nand = 1.3		# constant (in)
	def __del__(self):
		pass
		
# gate model for the inverter model
class ginv:
	def __init__(self):
		self.lo_inv = 5.383		# unit leakage  : mico-unit 
		self.co_inv = 4.9 		# unit intrinsic capacitance: femto-farad
		self.ro_inv = 3.4		# unit resistance: kilo-ohm
		self.ao_inv = 2.27		# unit area: micro-meter-square
		self.ac_inv = 0.226		# constant (x)
		self.ac_inv = 0 		# constant (in)
	def __del__(self):
		pass

# gate model for the nor gate 
class gnor:
	def __init__(self):
		self.lo_nor = 5.383		# unit leakage : mico-unit 
		self.co_nor = 4.9 		# unit intrinsic capacitance: femto-farad
		self.ro_nor = 4.1		# unit resistance: kilo-ohm
		self.ao_nor = 3.4 		# unit-area: micro-meter-square
		self.ac_nor = 1.5 		# constant (x)
		self.ak_nor = 1.3               # constant (in)	
	def __del__(self):
		pass

# gate model for the or gate
class gor:
	def __init__(self):
		self.lo_or = 5			# unit leakage : mico-unit
		self.co_or = 3.7 		# unit intrinsic capacitance: femto-farad
		self.ro_or = 5.2		# unit resistance: kilo-ohm
		self.ao_or = 5.15		# unit-area: micro-meter-square
		self.ac_or = 1.25		# constant
		self.ak_or = 1.2		# constant	
	def __del__(self):
		pass
		
# gate model for the xor gate 
class gxor:
	def __init__(self):
		self.lo_xor = 21.4		# unit leakage : mico-unit 
		self.co_xor = 5.3 		# unit intrinsic capacitance: femto-farad
		self.ro_xor = 4.2		# unit resistance: kilo-ohm
		self.ao_xor = 6.83		# unit-area: micro-meter-square
		self.ac_xor = 1.5 		# constant
		self.ak_xor = 1.3		# constant	
	def __del__(self):
		pass		

# gate model for the xnor gate 
class gxnor:
	def __init__(self):
		self.lo_xnor = 23.32		# unit leakage : mico-unit 
		self.co_xnor = 5.4 		# unit intrinsic capacitance: femto-farad
		self.ro_xnor = 4.3		# unit resistance: kilo-ohm
		self.ao_xnor = 6.85		# unit-area: micro-meter-square
		self.ac_xnor = 1.5 		# constant
		self.ak_xnor = 1.3		# constant
	def __del__(self):
		pass		


