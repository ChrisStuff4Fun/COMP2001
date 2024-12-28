# locationpoints.py

from datetime import datetime
from flask import abort, make_response, jsonify
import pyodbc
import linkhelper

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
# Gets all location points
def getLocationPoints():
    cursor = conn.cursor() 

    SQLQuery = "SELECT * FROM [CW2].[LocationPoints]"

    try:
        cursor.execute(SQLQuery)
        records = cursor.fetchall()

        userData = []    # Create dict obj and populate
        for row in records:
            userData.append({
                'LocationPointId': row.LocationPointId,
                'Latitude': row.Latitude,
                'Longitude': row.Longitude
            })

        # Convert to JSON obj
        cursor.close()
        return make_response(jsonify(userData), 200)

    except pyodbc.Error as e:
        print("pyodbc Error:", e)
        abort(500, f"Server encountered an error: {e}")

####    ####    ####    ####    ####    ####    ####    ####    ####    ####    ####    ####
# Adds a location point with given latitude and longitude
def addLocationPoint(pointJSON):

    if (pointJSON == None):
        abort(400, "No JSON obj given")
        return
    
    lat  = pointJSON.get("Latitude")
    long = pointJSON.get("Longitude")

    if( (lat == None or "") or (long == None or "") ):
        abort(400, "Field(s) empty")
        return

    try:
        cursor = conn.cursor() 
        SQLQuery1 = "INSERT INTO [CW2].[LocationPoints] ([Latitude], [Longitude]) VALUES(?, ?)"  # Build query and exec
        cursor.execute(SQLQuery1, lat, long)
        conn.commit() # Commit changes

        if (cursor.rowcount > 0):  
            #Row added successfully
            print("Row added successfully")
            return make_response("Row added successfully", 201)
        else:
            # No rows added
            print("Failed to add row")
            abort(400, "Failed to add row")

        cursor.close()

    except pyodbc.Error as e:
        print("pyodbc Error:", e)
        abort(500, f"Server encountered an error: {e}")


####    ####    ####    ####    ####    ####    ####    ####    ####    ####    ####    ####
# Gets a location point with given Id
def getLocationPointById(LocationPointId):

    if (LocationPointId == None or ""):
        abort(400, "No Id given")
        return

    cursor = conn.cursor() 
    SQLQuery = "SELECT * FROM [CW2].[LocationPoints] WHERE [LocationPointId] = ?"

    try:
        cursor.execute(SQLQuery, LocationPointId)
        records = cursor.fetchone()

        if (records == None):
            abort(404, "Location point not found")
            return

        userData = {
                'LocationPointId': records.LocationPointId,
                'Latitude': records.Latitude,
                'Longitude': records.Longitude
            }

        # Convert to JSON obj
        cursor.close()
        return userData

    except pyodbc.Error as e:
        print("pyodbc Error:", e)
        abort(500, f"Server encountered an error: {e}")


####    ####    ####    ####    ####    ####    ####    ####    ####    ####    ####    ####
# Deletes a location point with given Id
def deleteLocationPointById(LocationPointId):
    if not LocationPointId:
        print("No Id provided")
        abort(400, "No Id provided")
        return
    
    try:
        cursor = conn.cursor()
        SQLQuery = "DELETE FROM [CW2].[LocationPoints] WHERE [LocationPointId] = ?"
        cursor.execute(SQLQuery, LocationPointId)
        conn.commit()  # Commit changes 

        if cursor.rowcount > 0:  # rowcount gives the number of rows affected
            print("LocationPoint deleted successfully.")

            linkhelper.deleteTrailLocationPoint({"LocationPointId" : LocationPointId})

            return make_response("LocationPoint deleted successfully.", 200)
        else:
            print("No LocationPoint found")
            abort(404, f"No LocationPoint exists with LocationPointId: {LocationPointId}")
            return

    except pyodbc.Error as e:
        print("pyodbc Error:", e)
        abort(500, f"Server encountered an error: {e}")
        return


####    ####    ####    ####    ####    ####    ####    ####    ####    ####    ####    ####
# Edits a location point with given Id
def editLocationPointById(pointJSON):

    if not pointJSON:
        print("JSON Object not parsed, stopping.")
        abort(400, "No LocationPoint provided")
        return

    LocationPointId = pointJSON.get("id")
    lat             = pointJSON.get("Latitude")
    long            = pointJSON.get("Longitude")

    #Check for nulls
    if ( ( (lat == None or "") and (long == None or "") ) or (LocationPointId == None or "") ):
        print("JSON fields empty, stopping.")
        abort(400, "Bad request - JSON fields empty")
        return 

    try:
        cursor = conn.cursor()
        SQLQuery = "UPDATE [CW2].[LocationPoints] SET [Latitude] = IsNull(?, [Latitude]), [Longitude] = IsNull(?, [Longitude]) WHERE [LocationPointId] = ?"
        cursor.execute(SQLQuery, lat, long, LocationPointId)

        if (cursor.rowcount > 0):
            #Row added successfully
            print("Row updated successfully")
            return make_response("Row updated successfully", 201)
        else:
            # No rows added
            print("Failed to update row")
            abort( 404, f"LocationPoint with id {LocationPointId} not found.")
        cursor.close()

    except pyodbc.Error as e:
        print("pyodbc Error:", e)
        abort(500, f"Server encountered an error: {e}")
    

