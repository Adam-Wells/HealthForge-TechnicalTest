# -*- coding: utf-8 -*-
"""
Created on Thu Jun 15 15:37:09 2017

@author: pyaww
"""

import json
from collections import OrderedDict


class Patient:
	"""Details regarding the patient"""
	def __init__(self, ID='', firstName='', lastName='', DOB='', lab_results=None):
		self.ID=ID
		self.firstName=firstName
		self.lastName=lastName
		self.DOB=DOB
		if lab_results is None: self.lab_results=[]
		else: self.lab_results=lab_results
	def JSONform(self):
		"""Converts the data in this class to an ordered dictionary for the purpose of creating a JSON format"""
		return OrderedDict([("id",self.ID), ("firstName",self.firstName), ("lastName",self.lastName), ("dob",self.DOB), ("lab_results",[x.JSONform() for x in self.lab_results])])

class Result:
	"""Details regarding test samples, separated by instances of testing"""
	def __init__(self,sampleID='',timestamp='',profile_name='',profile_code='',panel=None):
		self.sampleID=sampleID
		self.timestamp=timestamp
		self.profile_name=profile_name
		self.profile_code=profile_code
		if panel==None: self.panel=[]
		else: self.panel=panel
	def JSONform(self):
		return OrderedDict([("timestamp",self.timestamp), ("profile",OrderedDict([("name",self.profile_name), ("code",self.profile_code)])), ("panel",[x.JSONform() for x in self.panel])])

class Panel:
	"""Details of each panel"""
	def __init__(self,code='',label='',value='',unit='',lower=None,upper=None):
		self.code=code
		self.label=label
		self.value=value
		self.unit=unit
		self.lower=lower
		self.upper=upper
	def JSONform(self):
		return OrderedDict([("code",self.code), ("label",self.label), ("value",self.value), ("unit",self.unit), ("lower",self.lower), ("upper",self.upper)])


#Data holders
codeMap={}
patient_details={}
patients={}


def ReadMap(inputFile='M:\san\data\labresults-codes.csv'):
	"""Reads the codes file and stores it in a dictionary of tuples"""
	with open(inputFile,'r') as f:
		for line in f:
			if '"' in line:
				sL=line.split('"')
				codeMap[sL[0].split(',')[0]]=(sL[0].split(',')[1],sL[1])
			else:
				sLine=line.split(',')
				codeMap[sLine[0]]=(sLine[1],sLine[2].split('\n')[0])

def ReadPatientDetails(inputFile='M:\san\data\patients.json'):
	"""Reads and returns patient details from json file"""
	with open(inputFile,'r') as f:
		patient_details=json.load(f)
	return patient_details

def ConvertTime(timestamp):
	"""Converts and returns timestamp in ISO 8601 format"""
	sTime=timestamp.split('/')
	return sTime[2]+'-'+sTime[1]+'-'+sTime[0]

def ReadCSV(inputFile='M:\san\data\labresults.csv'):
	"""Reads the data file and stores it in a database, compiling results for like patients and samples"""
	with open(inputFile,'r') as f:
		patient=''#stores last known patient ID to push the completed result to
		result=None #lab result to be built up until all panels are complete
		for line in f: #cycles through lines in the CSV file
			sLine=line.split('\n')[0].split(',')
			if sLine[0]=='HospID': continue #Skips header line
			if 'IMMUNOGLOBULINS (G' in sLine[3]: sLine=sLine[0:3]+["IMMUNOGLOBULINS (G,A"]+sLine[5:] #deals with use of comma in profile name
			try:
				patients[sLine[0]] #checks for patient instance
			except(KeyError): #If not in existance, finds the correct details and creates one
				for dets in patient_details:
					if sLine[0] in dets['identifiers']:
						details=dets
						break
				else:
					details={'dateOfBirth':'0000-00-00T00:00:00.000Z','firstName':'','id':'','lastName':''}
				patients[sLine[0]]=Patient(ID=details['id'],firstName=details['firstName'],lastName=details['lastName'],DOB=details['dateOfBirth'])
			
			if result==None: #Creates a result if none yet made
				result=Result(sampleID=sLine[1],timestamp=ConvertTime(sLine[2]),profile_name=sLine[3],profile_code=sLine[4])
			elif result.sampleID!=sLine[1] or codeMap[sLine[30]][0] in [x.code for x in result.panel]: #If a new sample code is detected, or a new batch of tests has started, pushes result onto the patient and makes a new one
				patients[patient].lab_results.append(result)
				result=Result(sampleID=sLine[1],timestamp=ConvertTime(sLine[2]),profile_name=sLine[3],profile_code=sLine[4])
			
			val=''
			for res in sLine[5:29]:
				if sLine[30] in res:
					val=res.split('~')[1] #Finds the value for the specific panel
	
			try: up,low=float(sLine[33]),float(sLine[32])
			except(ValueError):up,low=sLine[33],sLine[32] #handles cases where reference values exist
			result.panel.append(Panel(code=codeMap[sLine[30]][0],label=codeMap[sLine[30]][1],value=val,unit=sLine[31],lower=low,upper=up))
			patient=sLine[0] #updates the last known patient ID

		patients[patient].lab_results.append(result)



def CreateJSON(outputFile='M:\san\data\output.json'):
	"""Creates a JSON file from the patients data structure"""
	with open(outputFile,'w') as f:
		json.dump({'patients':[y.JSONform() for x,y in patients.iteritems()]},f,indent=4, separators=(',', ': '))

#Read in details
ReadMap()
patient_details=ReadPatientDetails()
ReadCSV()
#Write JSON file
CreateJSON()