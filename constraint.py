# This file will contain the constraint variables and other modules to assist in modeling
# Automated constraint manipulation design framework

class modConstraint:
	def __init__(self):
		self.Amax  = 2000			# mico-meter-square
		self.Pmax  = 0				# micro-Watt
		self.xmaxBuff = 1			# buffer max size
		self.xmax  = 7				# unit less 
		self.xmin  = 1				# unit less
		self.Cload = 10				# femto-farad
		self.ATmax = 630			# pico-second
		self.ATmin = 25				# pico-second
		self.freq  = 1000/float(self.ATmax) 	# giga-hertz
		# design variables
		self.newPmax = 0		# estimate variables: better estimate analysis	
		self.newAmax = 0		# estimate variables: better estimate analysis	
		self.ATpipe = 500		# pico-second # pipleine combinational max delay
		self.ATpipeMin = 20		# pico-second # pipeline combinational min delay
		self.numPipeStage = 2		# number of pipeline stages
		self.maxDelayPad = 15		# pico-second : maximum delay padding
		# correction estimates : must not be touched
		self.delta = 1.1		# delay correction pipeline estimate	
		self.BUMPSIZE = 1.1		# tilos : bump size factor
		self.PERTURB = 1.3		# tilos : perturb sensitivity analysis	
		# operating frequency
		#self.freq  = 1000/float(self.ATmax) 	# giga-hertz
	def __del__(self):	
		pass
	
	def updatePowerConstraint(modifyPower):
		self.newPmax = self.Pmax - modifyPower
		
	def updateAreaConstraint(modifyArea):
		self.newAmax = self.Amax - modifyArea	
		
		
