CREATE TABLE employee (
	empId INTEGER PRIMARY KEY,
	passwd TEXT NOT NULL,
	data varchar(100),
	parentId INTEGER
);

CREATE TABLE rootPath (
	empId INTEGER REFERENCES employee(empId),
	pathToRoot int[]
);

CREATE TABLE Subordinates (
	empId INTEGER REFERENCES employee(empId),
	empSubordinates int[]
);

CREATE USER app with ENCRYPTED PASSWORD 'qwerty';
ALTER USER init WITH SUPERUSER;
GRANT ALL ON employee TO app;
GRANT ALL ON rootPath TO app;
GRANT ALL ON Subordinates TO app;
