import psycopg2
import json
import sys
import argparse
import createQueries as cq
import getUpdateQueries as guq

def loadQueries(filename):
	with open(filename, "r") as testFile:
		jsonLines = [line.strip() for line in testFile.readlines()]
		jsonLines = [line for line in jsonLines if line]
		jsonObjects = [json.loads(line) for line in jsonLines]
	return jsonObjects

def connectToDB(dbName, user, password, host='localhost'):
	try:
		con = psycopg2.connect(dbname=dbName, user=user, host=host, password=password)
	except:
		raise 'Could not connect to database'
	return con

def checkPassword(cur, empId, passwd):
	query = """
		SELECT empId FROM employee 
		WHERE empId = {} AND passwd = crypt('{}', passwd)
	""".format(empId, passwd)
	try:
		cur.execute(query)
		qId = cur.fetchone()
		return qId is not None
	except:
		raise 'Error while checking password for {}'.format(empId)

def checkIfEmpExists(cur, empId):
	query = """
		SELECT empId FROM employee
		WHERE empId = {}
	""".format(empId)
	try:
		cur.execute(query)
		qId = cur.fetchone()
		return qId is not None
	except:
		raise 'Could not check if {} exists'.format(empId)

def createStatus(status='OK', data=None, debug=None):
	jsonObj = {
		"status": status
	}
	if data is not None: 
		jsonObj["data"] = data
	if debug is not None:
		jsonObj["debug"] = debug
	json.dump(jsonObj, sys.stdout)
	print('\n')
	
def createErrorStatus(data=None, debug=None):
	createStatus('Error', data, debug)

def createRoot(cur, data):
	try:
		secret = data["secret"]
		password = data["newpassword"]
		rootData = data["data"]
		empId = data["emp"]

		if secret != 'qwerty':
			createErrorStatus(debug='Invalid root secret')
			return

		query = "INSERT INTO employee VALUES({}, crypt('{}', gen_salt('bf')), '{}', NULL)".format(empId, password, rootData)
		cur.execute(query)
		rootPathQuery = "INSERT INTO rootPath VALUES({0}, Array[{0}])".format(empId)
		cur.execute(rootPathQuery)
		subordinateQuery = "INSERT INTO Subordinates VALUES({0}, Array[{0}])".format(empId)
		cur.execute(subordinateQuery)
		createStatus()
		return

	except:
		createErrorStatus(debug='Could not create root user')

def createEmp(cur, data):
	try:
		admin = data["admin"]
		adminPassword = data["passwd"]
		empData = data["data"]
		empPassword = data["newpasswd"]
		empSupervisor = data["emp1"]
		empId = data["emp"]
		if not checkPassword(cur, admin, adminPassword):
			createErrorStatus(debug='Wrong admin id or password')
			return
		supervisorPath = guq.getRootPath(cur, empSupervisor)
		if admin not in supervisorPath:
			createErrorStatus(debug='{} is not allowed to add {} suborinate'.format(admin, empSupervisor))
			return
		if checkIfEmpExists(cur, empId):
			createErrorStatus(debug='{} already exists'.format(empId))
			return
		query = "INSERT INTO employee VALUES({}, crypt('{}', gen_salt('bf')), '{}', {})".format(empId, empPassword, empData, empSupervisor)
		cur.execute(query)
		rootPathQuery = "INSERT INTO rootPath VALUES({}, Array{})".format(empId, supervisorPath+[empId])
		cur.execute(rootPathQuery)
		subordinateQuery = "INSERT INTO Subordinates VALUES({0}, Array[{0}])".format(empId)
		cur.execute(subordinateQuery)
		guq.updateSubordinates(cur, empSupervisor, empId)
		createStatus()
		
	except:
		createErrorStatus(debug='Error while creating user')

def removeEmp(cur, data):
	try:
		admin = data["admin"]
		adminPassword = data["passwd"]
		empId = data["emp"]		
		if not checkPassword(cur, admin, adminPassword):
			createErrorStatus(debug='Wrong admin id or password')
			return
		empRootPath = guq.getRootPath(cur, empId)[:-1]
		if len(empRootPath) == 0 or admin not in empRootPath:
			createErrorStatus(debug='{} is not allowed to remove {}'.format(admin, empId))
			return
		parentId = guq.getParentId(cur, empId)
		guq.removeEmpFromDB(cur, empId)
		guq.deleteFromSubordinates(cur, parentId, empId)
		createStatus()
	except:
		createErrorStatus(debug='Could not remove user')

def getChild(cur, data):
	try:
		admin = data["admin"]
		adminPassword = data["passwd"]
		empId = data["emp"]		
		if not checkPassword(cur, admin, adminPassword):
			createErrorStatus(debug='Wrong admin id or password')
			return
		empSubordinates = guq.getSubordinates(cur, empId)[1:]
		createStatus(data=empSubordinates)
	except:
		createErrorStatus(debug='Could not get children of user')

def getParent(cur, data):
	try:
		admin = data["admin"]
		adminPassword = data["passwd"]
		empId = data["emp"]		
		if not checkPassword(cur, admin, adminPassword):
			createErrorStatus(debug='Wrong admin id or password')
			return
		parentId = guq.getParentId(cur, empId)
		createStatus(data=parentId)
	except:
		createErrorStatus(debug='Could not get parent of user')

def getAncestors(cur, data):
	try:
		admin = data["admin"]
		adminPassword = data["passwd"]
		empId = data["emp"]		
		if not checkPassword(cur, admin, adminPassword):
			createErrorStatus(debug='Wrong admin id or password')
			return
		rootPath = guq.getRootPath(cur, empId)[:-1]
		createStatus(data=rootPath)
	except:
		createErrorStatus(debug='Could not get ancestors of user')

def getDescendants(cur, data):
	descendants = []
	def getSubData(empId):
		try:
			empSubordinates = guq.getSubordinates(cur, empId)[1:]
			for sub in empSubordinates:
				getSubData(sub)
			descendants.extend(empSubordinates)
		except:
			return
	try:
		admin = data["admin"]
		adminPassword = data["passwd"]
		empId = data["emp"]		
		if not checkPassword(cur, admin, adminPassword):
			createErrorStatus(debug='Wrong admin id or password')
			return
		if not checkIfEmpExists(cur, empId):
			createErrorStatus(debug='{} does not exist'.format(empId))
			return
		getSubData(empId)
		descendants.sort()
		createStatus(data=descendants)

	except:
		createErrorStatus(debug='Could not get descendants of user')

def getAncestor(cur, data):
	try:
		admin = data["admin"]
		adminPassword = data["passwd"]
		empId = data["emp1"]
		supervisorId = data["emp2"]		
		if not checkPassword(cur, admin, adminPassword):
			createErrorStatus(debug='Wrong admin id or password')
			return
		if not checkIfEmpExists(cur, supervisorId):
			createErrorStatus(debug='{} does not exist'.format(supervisorId))
			return
		rootPath = guq.getRootPath(cur, empId)[:-1]
		createStatus(data=supervisorId in rootPath)
	except:
		createErrorStatus(debug='Could not check ancestor')

def getData(cur, data):
	try:
		admin = data["admin"]
		adminPassword = data["passwd"]
		empId = data["emp"]		
		if not checkPassword(cur, admin, adminPassword):
			createErrorStatus(debug='Wrong admin id or password')
			return
		empRootPath = guq.getRootPath(cur, empId)
		if admin not in empRootPath:
			createErrorStatus(debug='{} is not allowed to get data of {}'.format(admin, empId))
			return
		data = guq.getEmpData(cur, empId)
		createStatus(data=data)
	except:
		createErrorStatus(debug='Could not get data of user')

def updateData(cur, data):
	try:
		admin = data["admin"]
		adminPassword = data["passwd"]
		empId = data["emp"]		
		newData = data["newdata"]
		if not checkPassword(cur, admin, adminPassword):
			createErrorStatus(debug='Wrong admin id or password')
			return
		empRootPath = guq.getRootPath(cur, empId)
		if admin not in empRootPath:
			createErrorStatus(debug='{} is not allowed to update data of {}'.format(admin, empId))
			return
		guq.updateEmpData(cur, empId, newData)
		createStatus()
	except:
		createErrorStatus(debug='Could not update data of user')

def openDB(openInfo):
	try:
		database = openInfo['database']
		login = openInfo['login']
		password = openInfo['password']
		con = connectToDB(database, login, password)
		cur = con.cursor()
		createStatus()
		return con, cur
	except:
		createErrorStatus(debug='Error while opening database')

def execQuieries(jsonObjects):
	queriesFunctions = {
		'new': createEmp,
		'remove': removeEmp,
		'child': getChild,
		'parent': getParent,
		'ancestors': getAncestors,
		'descendants': getDescendants,
		'ancestor': getAncestor,
		'read': getData,
		'update': updateData,
	}
	try:
		jsonOpen = jsonObjects[0]
		assert set(jsonOpen.keys()) == {'open'}
		con, cur = openDB(jsonOpen['open'])
		for jsonQuery in jsonObjects[1:]:
			query, data = list(jsonQuery.items())[0]
			if query not in queriesFunctions.keys():
				createErrorStatus(debug='Query {} does not exist'.format(query))
				continue
			queriesFunctions[query](cur, data)
		return con, cur
	except:
		createErrorStatus(debug='Error while executing queries')		

def initDB(jsonObjects, dbCreateSQL='createDB.sql'):
	try:
		jsonOpen = jsonObjects[0]
		assert set(jsonOpen.keys()) == {'open'}
		con, cur = openDB(jsonOpen['open'])
		
		query = open(dbCreateSQL, "r").read()
		cur.execute(query)
		#cq.createDB(cur)

		jsonRoot = jsonObjects[1]
		assert set(jsonRoot.keys()) == {'root'}
		createRoot(cur, jsonRoot['root'])
		rootId = jsonRoot['root']['emp']
		for newEmp in jsonObjects[2:]:
			if set(newEmp.keys()) != {'new'} or newEmp['new']['admin'] != rootId:
				createErrorStatus(debug='Only "new" queries with root as admin are allowed during init')
				continue
			createEmp(cur, newEmp['new'])
		return con, cur
	except:
		createErrorStatus(debug='Error while initializng database')

if __name__ == '__main__':
	parser = argparse.ArgumentParser(description='Wojciech Pratkowiecki 281417, Bazy Danych 2017/18')
	parser.add_argument('inputFile', help='Name of the input file with json queries')
	parser.add_argument('--init', action='store_true', help='init database')
	parser.add_argument('--db', help='construct custom database')
	args = parser.parse_args()
	jsonObjects = loadQueries(args.inputFile)

	if args.init:
		con, cur = initDB(jsonObjects) if not args.db else initDB(jsonObjects, args.db)
	else:
		con, cur = execQuieries(jsonObjects)
		
	con.commit()
	cur.close()
	con.close()