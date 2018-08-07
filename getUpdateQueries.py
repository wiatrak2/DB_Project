import psycopg2

def getRootPath(cur, empId):
	query = """
		SELECT pathToRoot FROM rootPath WHERE empId = {}
	""".format(empId)
	try:
		cur.execute(query)
		rootPath = cur.fetchone()
		return rootPath[0]
	except:
		raise 'Error while loading rootPath for employee {}'.format(empId)

def getSubordinates(cur, empId):
	query = """
		SELECT empsubordinates FROM Subordinates WHERE empId = {}
	""".format(empId)
	try:
		cur.execute(query)
		rootPath = cur.fetchone()
		return rootPath[0]
	except:
		raise 'Error while loading subordinates for employee {}'.format(empId)

def getParentId(cur, empId):
	query = """
		SELECT parentId FROM employee WHERE empId = {}
	""".format(empId)
	try:
		cur.execute(query)
		parentId = cur.fetchone()
		return parentId[0]
	except:
		raise 'Error while checking parent of {}'.format(empId)

def getEmpData(cur, empId):
	query = """
		SELECT data FROM employee WHERE empId = {}
	""".format(empId)
	try:
		cur.execute(query)
		data = cur.fetchone()
		return data[0]
	except:
		raise 'Error while checking data of {}'.format(empId)	

def updateSubordinates(cur, supervisorId, empId):
	newTable = getSubordinates(cur, supervisorId) + [empId]
	query = """
		UPDATE Subordinates
		SET empSubordinates = Array{} WHERE empId = {}
	""".format(newTable, supervisorId)
	try:
		cur.execute(query)
	except:
		raise 'Error while updating subordinates for {}'.format(supervisorId)

def deleteFromSubordinates(cur, supervisorId, empId):
	newTable = getSubordinates(cur, supervisorId)
	newTable.remove(empId)
	query = """
		UPDATE Subordinates
		SET empSubordinates = Array{} WHERE empId = {}
	""".format(newTable, supervisorId)
	try:
		cur.execute(query)
	except:
		raise 'Error while updating subordinates for {}'.format(supervisorId)

def updateEmpData(cur, empId, data):
	query = """
		UPDATE employee
		SET data = '{}' WHERE empId = {}
	""".format(data, empId)
	try:
		cur.execute(query)
	except:
		raise 'Error while updating data of {}'.format(empId)

def removeEmpFromDB(cur, empId):
	empSubordinates = getSubordinates(cur, empId)
	for sub in empSubordinates[1:]:
		removeEmpFromDB(cur, sub)
	query = """
		DELETE FROM Subordinates WHERE empId = {0};
		DELETE FROM rootPath WHERE empId = {0};
		DELETE FROM employee WHERE empId = {0};
	""".format(empId)
	try:
		cur.execute(query)
	except:
		raise 'Error while removing {}'.format(empId)