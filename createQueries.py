import psycopg2

def createEmployeeTable(cur):
	query = """
		CREATE TABLE employee (
			empId INTEGER PRIMARY KEY,
			passwd TEXT NOT NULL,
			data varchar(100),
			parentId INTEGER
		)
	"""
	try:
		cur.execute(query)
	except:
		raise 'Error while creating EMPLOYEE table'

def createRootPathTable(cur):
	query = """
		CREATE TABLE rootPath (
			empId INTEGER REFERENCES employee(empId),
			pathToRoot int[]
		)
	"""
	try:
		cur.execute(query)
	except:
		raise 'Error while creating rootPath table'

def createSubordinatesTable(cur):
	query = """
		CREATE TABLE Subordinates (
			empId INTEGER REFERENCES employee(empId),
			empSubordinates int[]
		)
	"""
	try:
		cur.execute(query)
	except:
		raise 'Error while creating rootPath table'

def createAppUser(cur):
	query = """
		CREATE USER app with ENCRYPTED PASSWORD 'qwerty';
		ALTER USER init WITH SUPERUSER;
		GRANT ALL ON employee TO app;
		GRANT ALL ON rootPath TO app;
		GRANT ALL ON Subordinates TO app;
	"""
	try: 
		cur.execute(query)
	except:
		raise 'Error while creating app user'

def createDB(cur):
	createEmployeeTable(cur)
	createRootPathTable(cur)
	createSubordinatesTable(cur)
	createAppUser(cur)
