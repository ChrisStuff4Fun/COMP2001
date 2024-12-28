# people.py

from datetime import datetime
from flask import abort, make_response
import pyodbc
import json




# SQL Login stuffs
SERVER   = "DIST-6-505.uopnet.plymouth.ac.uk"
DATABASE = "COMP2001_CCatlin"
USERNAME = "CCatlin"
PASSWORD = "HmqA769+"
TRUSTSERVERCERTIFICATE = "yes" # Needed for connections to Uni DB Server

# Create string
connectionString = f'DRIVER={{ODBC Driver 18 for SQL Server}};SERVER={SERVER};DATABASE={DATABASE};UID={USERNAME};PWD={PASSWORD};TRUSTSERVERCERTIFICATE={TRUSTSERVERCERTIFICATE}'
# Start connection
conn = pyodbc.connect(connectionString) 
# Open new cursor (no point in creating inside a function, since this file only opens on an api request)



def getAllUsers():
    cursor = conn.cursor() 

    SQLQuery = "SELECT * FROM [CW2].[Users] ORDER BY UserID ASC;"
    cursor.execute(SQLQuery)

    records = cursor.fetchall()

    userData = []    # Create dict obj and populate
    for row in records:
        userData.append({
            'UserID': row.UserId,
            'Email': row.Email,
            'Role': row.Role
        })

    # Convert to JSON obj
    jsonArray = json.dumps(userData, indent=4)

    cursor.close()

    return jsonArray


def createNewUser(userJSON):

    if not userJSON:
        print("JSON Object not parsed, stopping.")
        return

    userEmail = userJSON.get("email")
    userRole  = userJSON.get("role")

    # Check for nulls
    if ( (userRole == None or "") or (userEmail == None or "") ):
        print("JSON field(s) empty, stopping.")
        return 

    # If we get here, data has been given correctly

    try:
        cursor = conn.cursor() 

        SQLQuery1 = "INSERT INTO [CW2].[Users] ([Email], [Role]) VALUES (LOWER(?), LOWER(?))"  # Build query and exec
        cursor.execute(SQLQuery1, userEmail, userRole)
        conn.commit() # Commit changes

        if (cursor.rowcount > 0):  # If rows exist with email...
            #Row added successfully
            print("Row added successfully")
        else:
            # No rows added
            print("Failed to add row")

        cursor.close()

    except pyodbc.Error as e:
        print("pyodbc Error:", e)




def updateUserById(userJSON):
    
    if not userJSON:
        print("JSON Object not parsed, stopping.")
        return

    userId    = userJSON.get("id")
    userEmail = userJSON.get("email")
    userRole  = userJSON.get("role")

    try:
        cursor = conn.cursor()

        #Check for nulls
        if ( ( (userRole == None or "") and (userEmail == None or "") ) or (userId == None or "") ):
            # User ID CANNOT be empty, however, ONE of userRole or userEmail can be
            print("JSON field(s) empty, stopping.")
            return 
        
        elif (userRole == None or ""):
            # Only update email
            SQLQuery = "UPDATE [CW2].[Users] SET [Email] = LOWER(?) WHERE [UserId] = ?"
            cursor.execute(SQLQuery, userEmail, userId)

        elif (userEmail == None or ""):
            # Only update role
            SQLQuery = "UPDATE [CW2].[Users] SET [Role] = LOWER(?) WHERE [UserId] = ?"
            cursor.execute(SQLQuery, userRole, userId)

        else:
            # Update both
            SQLQuery = "UPDATE [CW2].[Users] SET [Role] = LOWER(?) , SET [Email] = LOWER(?) WHERE [UserId] = ?"
            cursor.execute(SQLQuery, userRole, userEmail, userId)

        if (cursor.rowcount > 0):
            #Row added successfully
            print("Row updated successfully")
        else:
            # No rows added
            print("Failed to update row")

        cursor.close()

    except pyodbc.Error as e:
        print("pyodbc Error:", e)

    



def deleteUserById(userId):

    if not userId:
        print("No user provided")
        return
    
    try:
        cursor = conn.cursor()

        # Delete the user by UserID
        SQLQuery = "DELETE FROM [CW2].[Users] WHERE [UserID] = ?"
        cursor.execute(SQLQuery, userId)
        conn.commit()  # Commit changes 

        if cursor.rowcount > 0:  # rowcount gives the number of rows affected
            print("User deleted successfully.")
        else:
            print("No user found")

    except pyodbc.Error as e:
        print("pyodbc Error:", e)




def getUserById(userId):
    if not userId:
        print("No user provided")
        return
    
    try:
        cursor = conn.cursor()

        SQLQuery = "SELECT * FROM [CW2].[Users] WHERE [UserId] = ?"
        cursor.execute(SQLQuery, userId)
 
        row = cursor.fetchone()

        columns = [column[0] for column in cursor.description]
        userDict = dict(zip(columns, row))

        JSONReturn = json.dumps(userDict, indent=4) # Convert py dictionary to JSON

        if row: 
            print("User: ", JSONReturn)
            return JSONReturn
        else:
            print("No user found")

    except pyodbc.Error as e:
        print("pyodbc Error:", e)

 

if conn is None:
    print("Connection failed.")
else:
    print("Connected to DB.")
    getAllUsers()

def get_timestamp():
    return datetime.now().strftime(("%Y-%m-%d %H:%M:%S"))

PEOPLE = {
    "Hopper": {
        "fname": "Grace",
        "lname": "Hopper",
        "timestamp": get_timestamp(),
    },
    "BernersLee": {
        "fname": "Tim",
        "lname": "Berners-Lee",
        "timestamp": get_timestamp(),
    },
    "Lovelace": {
        "fname": "Ada",
        "lname": "Lovelace",
        "timestamp": get_timestamp(),
    }
}

def read_all():
    return list(PEOPLE.values())

def create(person):
    lname = person.get("lname")
    fname = person.get("fname", "")

    if lname and lname not in PEOPLE:
        PEOPLE[lname] = {
            "lname": lname,
            "fname": fname,
            "timestamp": get_timestamp(),
        }
        return PEOPLE[lname], 201
    else:
        abort(
            406,
            f"Person with last name {lname} already exists",
        )

def read_one(lname):
    if lname in PEOPLE:
        return PEOPLE[lname]
    else:
        abort(
            404, f"Person with last name {lname} not found"
        )

def update(lname, person):
    if lname in PEOPLE:
        PEOPLE[lname]["fname"] = person.get("fname", PEOPLE[lname]["fname"])
        PEOPLE[lname]["timestamp"] = get_timestamp()
        return PEOPLE[lname]
    else:
        abort(
            404,
            f"Person with last name {lname} not found"
        )

def delete(lname):
    if lname in PEOPLE:
        del PEOPLE[lname]
        return make_response(
            f"{lname} successfully deleted", 200
        )
    else:
        abort(
            404,
            f"Person with last name {lname} not found"
        )