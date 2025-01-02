import requests
import ast
import pyodbc

authURL = "https://web.socem.plymouth.ac.uk/COMP2001/auth/api/users"



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


def authUser(email, pw):
    creds = {"email": email, 
             "password" : pw}
    
    response = requests.post(authURL, json=creds)

    print(response.text)

    if (response.status_code == 200): # If response is ok

        if ( ast.literal_eval(response.text)[1] == "True"): # And user is verified
              return True # Return true

    return False # Otherwise return false





####    ####    ####    ####    ####    ####    ####    ####    ####    ####    ####    ####
# Checks if user with given Email exists in users table
def checkOwnerPerms(Email):
    # No null check needed, done in master function
    try:
        cursor = conn.cursor()

        SQLQuery = "SELECT [Role] FROM [CW2].[Users] WHERE [Email] = ?"
        cursor.execute(SQLQuery, Email)
 
        row = cursor.fetchone()

        if row:
            if (row[0] == "admin"):
                return True
        else:
            # User doesn't exist
            return False

    except pyodbc.Error as e:
        print("pyodbc Error:", e)
