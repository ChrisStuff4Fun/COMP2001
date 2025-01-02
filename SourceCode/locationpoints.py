from datetime import datetime
from flask import abort, make_response, jsonify, request
import pyodbc
import linkhelper
import auth

# SQL Login details
SERVER   = "DIST-6-505.uopnet.plymouth.ac.uk"
DATABASE = "COMP2001_CCatlin"
USERNAME = "CCatlin"
PASSWORD = "HmqA769+"
TRUSTSERVERCERTIFICATE = "yes"  # Needed for connections to Uni DB Server

# Create connection string
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

        userData = []  # Create dict object and populate
        for row in records:
            userData.append({
                'LocationPointId': row.LocationPointId,
                'Latitude': row.Latitude,
                'Longitude': row.Longitude
            })

        cursor.close()
        return make_response(jsonify(userData), 200)

    except pyodbc.Error as e:
        print("pyodbc Error:", e)
        abort(500, f"Server encountered an error: {e}")

####    ####    ####    ####    ####    ####    ####    ####    ####    ####    ####    ####
# Adds a location point with given latitude and longitude
def addLocationPoint():

    pointJSON = request.get_json()

    if not auth.authUser(pointJSON.get("authEmail"), pointJSON.get("authPW")):
        abort(401, "Access denied")
        return

    if not pointJSON:
        abort(400, "No JSON object provided")
        return
    
    lat = pointJSON.get("Latitude")
    long = pointJSON.get("Longitude")

    if (lat is None or long is None or lat == "" or long == ""):
        abort(400, "Latitude and Longitude fields are required")
        return

    try:
        cursor = conn.cursor()
        SQLQuery1 = "INSERT INTO [CW2].[LocationPoints] ([Latitude], [Longitude]) VALUES (?, ?)"
        cursor.execute(SQLQuery1, lat, long)
        conn.commit()  # Commit changes

        if cursor.rowcount > 0:
            print("Row added successfully")
            return make_response(jsonify({"message": "Row added successfully"}), 201)
        else:
            print("Failed to add row")
            abort(400, "Failed to add row")

        cursor.close()

    except pyodbc.Error as e:
        print("pyodbc Error:", e)
        abort(500, f"Server encountered an error: {e}")


####    ####    ####    ####    ####    ####    ####    ####    ####    ####    ####    ####
# Gets a location point with given Id
def getLocationPointById(LocationPointId):

    if not LocationPointId:
        abort(400, "No Id provided")
        return

    cursor = conn.cursor()
    SQLQuery = "SELECT * FROM [CW2].[LocationPoints] WHERE [LocationPointId] = ?"

    try:
        cursor.execute(SQLQuery, LocationPointId)
        record = cursor.fetchone()

        if not record:
            abort(404, "Location point not found")
            return

        userData = {
            'LocationPointId': record.LocationPointId,
            'Latitude': record.Latitude,
            'Longitude': record.Longitude
        }

        cursor.close()
        return make_response(jsonify(userData), 200)

    except pyodbc.Error as e:
        print("pyodbc Error:", e)
        abort(500, f"Server encountered an error: {e}")


####    ####    ####    ####    ####    ####    ####    ####    ####    ####    ####    ####
# Deletes a location point with given Id
def deleteLocationPointById(LocationPointId):

    authJSON = request.get_json()

    if not auth.authUser(authJSON.get("authEmail"), authJSON.get("authPW")):
        abort(401, "Access denied")
        return

    if not LocationPointId:
        abort(400, "No Id provided")
        return

    try:
        cursor = conn.cursor()
        SQLQuery = "DELETE FROM [CW2].[LocationPoints] WHERE [LocationPointId] = ?"
        cursor.execute(SQLQuery, LocationPointId)
        conn.commit()  # Commit changes

        if cursor.rowcount > 0:
            print("LocationPoint deleted successfully.")
            linkhelper.deleteTrailLocationPoint({"LocationPointId": LocationPointId})

            return make_response(jsonify({"message": "LocationPoint deleted successfully."}), 200)
        else:
            print("No LocationPoint found")
            abort(404, f"No LocationPoint exists with LocationPointId: {LocationPointId}")

    except pyodbc.Error as e:
        print("pyodbc Error:", e)
        abort(500, f"Server encountered an error: {e}")


####    ####    ####    ####    ####    ####    ####    ####    ####    ####    ####    ####
# Edits a location point with given Id
def editLocationPointById():

    pointJSON = request.get_json()

    if not auth.authUser(pointJSON.get("authEmail"), pointJSON.get("authPW")):
        abort(401, "Access denied")
        return

    if not pointJSON:
        abort(400, "No JSON object provided")
        return

    LocationPointId = pointJSON.get("id")
    lat = pointJSON.get("Latitude")
    long = pointJSON.get("Longitude")

    if (LocationPointId is None or lat is None or long is None or lat == "" or long == ""):
        abort(400, "Bad request - Missing required fields")
        return

    try:
        cursor = conn.cursor()
        SQLQuery = "UPDATE [CW2].[LocationPoints] SET [Latitude] = IsNull(?, [Latitude]), [Longitude] = IsNull(?, [Longitude]) WHERE [LocationPointId] = ?"
        cursor.execute(SQLQuery, lat, long, LocationPointId)

        if cursor.rowcount > 0:
            print("Row updated successfully")
            return make_response(jsonify({"message": "Row updated successfully"}), 200)
        else:
            print("Failed to update row")
            abort(404, f"LocationPoint with id {LocationPointId} not found.")

        cursor.close()

    except pyodbc.Error as e:
        print("pyodbc Error:", e)
        abort(500, f"Server encountered an error: {e}")
