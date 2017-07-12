#!/usr/bin/python

import lxml.html as LH
import re
import json
import sys
import time
import getpass
import os

from robobrowser import RoboBrowser
from requests import Session
from pprint import pprint

class bcolors:
	HEADER = '\033[95m'
	OKBLUE = '\033[94m'
	OKGREEN = '\033[92m'
	WARNING = '\033[93m'
	FAIL = '\033[91m'
	ENDC = '\033[0m'
	BOLD = '\033[1m'
	UNDERLINE = '\033[4m'


print("  \t                      ,.") 
print("  \t                     (\(\)") 
print("  \t     ,_              ;  o >")
print("  \t      {`-.          /  (_)") 
print("  \t      `={\`-._____/`   |")   
print("  \t       `-{ /    -=`\   |")
print("  \t        `={  -= = _/   /")
print("  \t           `\  .-'   /`")
print("  \t            {`-,__.'===,_")
print("  \t            //`        `\\\\")
print("  \t           //")
print("  \t          `\=")
print(" ================================================= ")
print("||            Enumerate Linkedin Users           ||")
print(" ================================================= \n\n")


foundUsers= 0


def main():
	global browser
	try:
		session = Session()
		browser = RoboBrowser(parser='html.parser',session=session,user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10.12; rv:49.0) Gecko/20100101 Firefox/49.0')		
		login()
		company = list_companies()
		enumerate_users(company)
		if os.path.isfile("data.json"):
			os.remove("data.json")
		if os.path.isfile("companiesdata.json"):
			os.remove("companiesdata.json")
			
	except KeyboardInterrupt:
		if os.path.isfile("data.json"):
			os.remove("data.json")
		if os.path.isfile("companiesdata.json"):
			os.remove("companiesdata.json")
		print("")
		print("\t    MM")             
		print("\t   <' \___/|")           
		print("\t     \_  _/ O")   
		print("\t       ][")  
		print("\n  Exiting script. Bye!")
		print("  Found "+str(foundUsers)+" users")
		print("  Results written to out.csv.")
		sys.exit()





# Connect to Linkedin =========================================
# =============================================================

def login():
	user = raw_input('Your Linkedin Account:')
	passw = getpass.getpass('Your Linkedin Password:')
	browser.open('https://www.linkedin.com')

	loggedIn = False
	while (loggedIn == False):
		form = browser.get_form(action="https://www.linkedin.com/uas/login-submit")
		form["session_key"].value = user
		form["session_password"].value = passw 
		browser.submit_form(form)
		if (browser.get_form(action="https://www.linkedin.com/uas/login-submit") is None):
			loggedIn = True
			print "\n"+bcolors.OKGREEN+'  Success - Signed in !'+bcolors.ENDC
		else:
			print "\n"+bcolors.FAIL+'  Login Failure !'+bcolors.ENDC	




# Search for a company profile ================================
# =============================================================

def list_companies():
	search = True
	while search :
		company,search = search_company()
	return company

def search_company():	 
	keyword = raw_input('\nType the name of the target company: ')
	print("Select the ID of the company you are looking for:\n")
	companies = {}
	pageNumber = 1
	foundCompanies=0
	more = True
	while more == True :
		more = False
		browser.open('https://www.linkedin.com/search/results/companies/?keywords='+keyword+'&origin=SWITCH_SEARCH_VERTICAL&page='+str(pageNumber))
		pageNumber+=1
		scrapeCompanies(str(browser.parsed))
		foundCompanies = parseCompanies(companies,foundCompanies)

		# List Companies. Need this to be sorted
		for i in range(0,len(companies)):
			print "#",str(i)+".",companies[i][0]
			print "\tIndustry:",companies[i][2]
			print "\tRegion:",companies[i][3]
			print "\tSize:",companies[i][4]
		print("\n  Press enter for more or type B to search again ...")

		 
		var = raw_input()
		while True:
			try:
				if (var == "b" ) | (var == "B"):
					# Search again
					return None, True
				elif (var == ""):
					# Print more
					more = True
					break 
				elif (var == "exit"):
					sys.exit("Script Stopped. Bye!")
				elif int(var)<foundCompanies:
					c = int(var)
					return companies[c], False
				else:	
					print "Invalid index"
					var = raw_input()
			except ValueError:
				print "Invalid index"
				var = raw_input()



def scrapeCompanies(page):

	root = LH.fromstring(page)
	regex = re.compile("\{\"com.linkedin.voyager.search.VerticalGuide\":\{\"vertical\":\"COMPANIES\"\}\}")
	file = open("companiesdata.json","w") 
	for element in root.xpath('//code/text()'):
		m = regex.search(element)
		if m:
			file.write(element.encode('utf-8'))

	file.close()


		
def parseCompanies(companies,foundCompanies):
	with open('companiesdata.json') as companies_file:    
		    data = json.load(companies_file)
	
	
	for i in data['included']:	
		if (i['$type']==u'com.linkedin.voyager.entities.shared.MiniCompany'):	
			id = i['entityUrn']	
			companies[foundCompanies] = [i['name'],id.split(":")[-1]] 
			foundCompanies+=1

	for i in companies:
		for j in data['included']:
			if('id' in j):	
				if (j['id']==companies[i][1]):
					industry = region = size = "-"
					if('industry' in j):
						industry = j['industry']
					if('region' in j):
						region = j['region']
					if('size' in j):
						size = j['size']
					companies[i].extend([industry,region,size])
	return foundCompanies



		

# List users ==================================================
# =============================================================

def enumerate_users(company):
	print "\n"+bcolors.OKBLUE+'Enumerating employees from '+company[0]+" ..."+bcolors.ENDC+"\n"
	out = open("out.csv","w")
	pageNumber = 1 
	reachedEnd = False
	while (reachedEnd == False):
		reachedEnd = True
		browser.open('https://www.linkedin.com/search/results/people/?facetCurrentCompany=['+company[1]+']&page='+str(pageNumber))
		pageNumber+=1
		scrapeUsers(str(browser.parsed))
		reachedEnd = parseUsers(out)
		time.sleep(2)
	print("Found "+str(foundUsers)+" users")
	out.close()







# Scrape the response for the JSON ==============================
# ===============================================================

def scrapeUsers(page):

	# You can use this  if you download a linkedin search page manually
	#for user in root.xpath('//ul[@class="results-list"]/li/div/div/div[2]/a/h3/span[1]/span[1]/text()'):
	#	print user

	root = LH.fromstring(page)
	regex = re.compile("\{\"com.linkedin.voyager.search.VerticalGuide\":\{\"vertical\":\"PEOPLE\"\}\}")
	file = open("data.json","w") 
	for element in root.xpath('//code/text()'):
		m = regex.search(element)
		if m:
			file.write(element.encode('utf-8'))

	file.close()






# Parse the JSON Response ====================================
# ============================================================

def parseUsers(out):
	global foundUsers 
	reachedEnd = True
	with open('data.json') as data_file:    
	    data = json.load(data_file)

	searchableProfiles = {}

	for i in data['included']:	
		if (i['$type']==u'com.linkedin.voyager.search.SearchProfile'):	
	    		searchableProfiles[i['id']]=1


	for i in data['included']:	
		if (i['$type']==u'com.linkedin.voyager.identity.shared.MiniProfile'):
			reachedEnd = False	
			id = i['entityUrn']	
			if(id.split(":")[-1] in searchableProfiles):
				firstname=lastname=s = ""
				if ('firstName' in i):
					firstName = i['firstName']
					s+=	i['firstName']
				if ('lastName' in i):
					lastName = i['lastName']
					if s=="":
						s+=	i['lastName']
					else : 
						s+=	" "+i['lastName']

				if s != "":
					print('# '+s.ljust(20)+'\t\t'+i['occupation'])
					out.write(firstName.encode('utf-8')+","+lastName.encode('utf-8')+","+i['occupation'].encode('utf-8')+"\n")
					foundUsers+=1

	data_file.close()
	return reachedEnd

if __name__ == '__main__':
    main() 