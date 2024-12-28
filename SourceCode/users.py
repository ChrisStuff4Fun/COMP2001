# users.py

from datetime import datetime
from flask import abort, make_response, jsonify
import pyodbc


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

####    ####    ####    ####    ####    ####    ####    ####    ####    ####    ####    ####    
# Returns all records in [CW2].[Users] as a JSON array
def getAllUsers():
    cursor = conn.cursor() 

    SQLQuery = "SELECT * FROM [CW2].[Users] ORDER BY UserID ASC;"

    try:
        cursor.execute(SQLQuery)

        records = cursor.fetchall()

        if(records == None):
            return None

        userData = []    # Create dict obj and populate
        for row in records:
            userData.append({
                'UserID': row.UserId,
                'Email': row.Email,
                'Role': row.Role
            })

        # Convert to JSON obj
        cursor.close()
        return make_response(jsonify(userData), 200)

    except pyodbc.Error as e:
        print("pyodbc Error:", e)
        abort(500, f"Server encountered an error: {e}")

####    ####    ####    ####    ####    ####    ####    ####    ####    ####    ####    ####    
# Create new row in user table with format {"Email": email, "Role": role}
def createNewUser(userJSON):

    if not userJSON:
        print("JSON Object not parsed, stopping.")
        abort(400, "No user provided")
        return

    userEmail = userJSON.get("Email")
    userRole  = userJSON.get("Role")

    # Check for nulls
    if ( (userRole == None or "") or (userEmail == None or "") ):
        print("JSON field(s) empty, stopping.")
        abort(400, "Provided JSON field(s) empty")
        return 

    # If we get here, data has been given correctly

    try:
        cursor = conn.cursor() 

        SQLQuery1 = "INSERT INTO [CW2].[Users] ([Email], [Role]) VALUES (LOWER(?), LOWER(?))"  # Build query and exec
        cursor.execute(SQLQuery1, userEmail, userRole)
        conn.commit() # Commit changes

        if (cursor.rowcount > 0):  
            #Row added successfully
            print("Row added successfully")
            return make_response(201, "Row added successfully")
        else:
            # No rows added
            print("Failed to add row")
            abort(400, "Failed to add row")

        cursor.close()

    except pyodbc.Error as e:
        print("pyodbc Error:", e)
        abort(500, f"Server encountered an error: {e}")

####    ####    ####    ####    ####    ####    ####    ####    ####    ####    ####    ####    
# Updates one or both email and role with format {"UserId" : userId, "Email": email, "Role": role}
def updateUserById(userJSON):
    
    if not userJSON:
        print("JSON Object not parsed, stopping.")
        abort(400, "No user provided")
        return

    userId    = userJSON.get("id")
    userEmail = userJSON.get("email")
    userRole  = userJSON.get("role")

    try:
        cursor = conn.cursor()

        #Check for nulls
        if ( ( (userRole == None or "") and (userEmail == None or "") ) or (userId == None or "") ):
            # User ID CANNOT be empty, however, ONE of userRole or userEmail can be
            print("JSON fields empty, stopping.")
            abort(400, "Bad request - JSON fields empty")
            return 
  
        # Update both
        SQLQuery = "UPDATE [CW2].[Users] SET [Role] = IsNull(LOWER(?), [Role]), [Email] = IsNull(LOWER(?), [Email]) WHERE [UserId] = ?"
        cursor.execute(SQLQuery, userRole, userEmail, userId)

        if (cursor.rowcount > 0):
            #Row added successfully
            print("Row updated successfully")
            return make_response(201, "Row updated successfully")
        else:
            # No rows added
            print("Failed to update row")
            abort( 404, f"User with id {userId} not found.")
        cursor.close()

    except pyodbc.Error as e:
        print("pyodbc Error:", e)
        abort(500, f"Server encountered an error: {e}")
    

####    ####    ####    ####    ####    ####    ####    ####    ####    ####    ####    ####    
# Deletes row from Users with given Id
def deleteUserById(userId):

    if not userId:
        print("No user provided")
        abort(400, "No user provided")
        return
    
    try:
        cursor = conn.cursor()

        # Delete the user by UserID
        SQLQuery = "DELETE FROM [CW2].[Users] WHERE [UserID] = ?"
        cursor.execute(SQLQuery, userId)
        conn.commit()  # Commit changes 

        if cursor.rowcount > 0:  # rowcount gives the number of rows affected
            print("User deleted successfully.")
            return make_response(200, "User deleted successfully.")
        else:
            print("No user found")
            abort(404, f"No user exists with userId: {userId} ")

    except pyodbc.Error as e:
        print("pyodbc Error:", e)
        abort(500, f"Server encountered an error: {e}")

####    ####    ####    ####    ####    ####    ####    ####    ####    ####    ####    ####    
# Returns user in JSON obj
def getUserById(userId):
    if not userId:
        print("No user provided")
        abort(400, f"{userId} is not a valid userId")
        return
    
    try:
        cursor = conn.cursor()

        SQLQuery = "SELECT * FROM [CW2].[Users] WHERE [UserId] = ?"
        cursor.execute(SQLQuery, userId)
 
        row = cursor.fetchone()

        if row:
            # Convert py dictionary to JSON
            JSONreturn = {"UserId" : row.UserId, "Email" : row.Email, "Role" : row.Role}
            print("User: ", jsonify(JSONreturn))
            return make_response(jsonify(JSONreturn), 200)
        else:
            print("No user found")
            abort( 404, f"User with id {userId} not found.")

    except pyodbc.Error as e:
        print("pyodbc Error:", e)
        abort(500, f"Server encountered an error: {e}")


####    ####    ####    ####    ####    ####    ####    ####    ####    ####    ####    ####    
# Gets Id of user with given email (more useful that only dealing with user id's)
# Safe to use, as i have "unique'd" the email column of the users table, so no repeat emails
def getIdByEmail(email):
    if not email:
        print("No email provided")
        abort(400, f"{email} is not a valid email")
        return
    
    try:
        cursor = conn.cursor()

        SQLQuery = "SELECT [UserId] FROM [CW2].[Users] WHERE [Email] = ?"
        cursor.execute(SQLQuery, email)
 
        row = cursor.fetchone()

        if row: 
            print("User: ", row[0])
            return make_response({"UserId" : row[0]}, 200)
        else:
            print("No user found")
            abort(404, f"User with email {email} not found.")

    except pyodbc.Error as e:
        print("pyodbc Error:", e)
        abort(500, f"Server encountered an error: {e}")
 ####    ####    ####    ####    ####    ####    ####    ####    ####    ####    ####    ####    

if conn is None:
    print("Connection failed.")
else:
    print("Connected to DB.")