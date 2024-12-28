# linkhelper.py

from datetime import datetime
from flask import abort, make_response, jsonify
import pyodbc
import trails
import features
import locationpoints

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

# This file is used for link entities and foreign keys to make the code easier than using one massive function for a single process


####    ####    ####    ####    ####    ####    ####    ####    ####    ####    ####    ####
# Gets all location points belonging to a trail
def getLocationPointsByTrail(TrailId):
    if not TrailId:
        print("No TrailId provided")
        abort(400, "No valid TrailId")
        return
    
    try:
        cursor = conn.cursor()
        SQLQuery = "SELECT [LocationPointId] FROM [CW2].[TrailLocationPoints] WHERE [TrailId] = ? ORDER BY [OrderNum] ASC"
        cursor.execute(SQLQuery, TrailId)
        records = cursor.fetchall()

        if(records == None):
            abort(404, "None found")
            return None

        userData = []    # Create dict obj and populate
        for row in records:
            userData.append(locationpoints.getLocationPointById(row.LocationPointId))

        return jsonify(userData)

    except pyodbc.Error as e:
        print("pyodbc Error:", e)
        abort(500, f"Server encountered an error: {e}")


####    ####    ####    ####    ####    ####    ####    ####    ####    ####    ####    ####
# Gets all trails that use a location point
def getTrailsByLocationPoint(LocationPointId):
    if not LocationPointId:
        print("No LocationPointId provided")
        abort(400, "No valid LocationPointId")
        return
    
    try:
        cursor = conn.cursor()
        SQLQuery = "SELECT [TrailId] FROM [CW2].[TrailLocationPoints] WHERE [LocationPointId] = ?"
        cursor.execute(SQLQuery, LocationPointId)
        records = cursor.fetchall()

        if(records == None):
            abort(404, "None found")
            return None

        userData = []    # Create dict obj and populate
        for row in records:
            userData.append(trails.getTrailById(row.TrailId))
        return jsonify(userData)

    except pyodbc.Error as e:
        print("pyodbc Error:", e)
        abort(500, f"Server encountered an error: {e}")


####    ####    ####    ####    ####    ####    ####    ####    ####    ####    ####    ####
# Creates new TrailLocationPoint link entity
def newTrailLocationPoint(TrailLocationPointJSON):

    if not TrailLocationPointJSON:
        print("JSON Object not parsed, stopping.")
        abort(400, "No TrailLocationPointJSON provided")
        return

    TrailId = TrailLocationPointJSON.get("TrailId")
    LocationPointId  = TrailLocationPointJSON.get("LocationPointId")

    # Check for nulls
    if ( (TrailId == None or "") or (LocationPointId == None or "") ):
        print("JSON field(s) empty, stopping.")
        abort(400, "Provided JSON field(s) empty")
        return 

    # If we get here, data has been given correctly

    try:
        cursor = conn.cursor() 
        SQLQuery1 = "INSERT INTO [CW2].[TrailLocationPoints] ([LocationPoint], [Role]) VALUES (?, ?)"  # Build query and exec
        cursor.execute(SQLQuery1, TrailId, LocationPointId)
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
# Deletes link entity
def deleteTrailLocationPoint(TrailLocationPointJSON):
    
    if not TrailLocationPointJSON:
        print("No TrailLocationPointJSON provided")
        abort(400, "No TrailLocationPointJSON provided")
        return
    
    TrailId = TrailLocationPointJSON.get("TrailId")
    LocationPointId  = TrailLocationPointJSON.get("LocationPointId")

    if ((TrailId == None or "") and (LocationPointId == None or "")):
        abort(400, "No fields provided")
        return

    
    try:
        cursor = conn.cursor()
        if (TrailId == None or ""): # LocationPoint was deleted
            SQLQuery = "DELETE FROM [CW2].[TrailLocationPoints] WHERE [LocationPointId] = ?"
            cursor.execute(SQLQuery, LocationPointId)
        elif (LocationPointId == None or ""): # Trail was deleted
            SQLQuery = "DELETE FROM [CW2].[TrailLocationPoints] WHERE [TrailId] = ?"
            cursor.execute(SQLQuery, TrailId)
        else: # Induvidual point was deleted
            SQLQuery = "DELETE FROM [CW2].[TrailLocationPoints] WHERE [TrailId] = ? AND [LocationPointId] = ?"
            cursor.execute(SQLQuery, TrailId, LocationPointId)
        conn.commit()  # Commit changes 

        if cursor.rowcount > 0:  # rowcount gives the number of rows affected
            print("TrailLocationPoint deleted successfully.")
            return make_response("TrailLocationPoint deleted successfully.", 200)
        else:
            print("No TrailLocationPoint found")
            abort(404, f"No TrailLocationPoint exists")

    except pyodbc.Error as e:
        print("pyodbc Error:", e)
        abort(500, f"Server encountered an error: {e}")


####    ####    ####    ####    ####    ####    ####    ####    ####    ####    ####    ####
# Gets all features belonging to a trail
def getFeaturesByTrail(TrailId):
    if not TrailId:
        print("No TrailId provided")
        abort(400, "No valid TrailId")
        return
    
    try:
        cursor = conn.cursor()
        SQLQuery = "SELECT [FeatureId] FROM [CW2].[TrailFeatures] WHERE [TrailId] = ?"
        cursor.execute(SQLQuery, TrailId)
        records = cursor.fetchall()

        if(records == None):
            abort(404, "None found")
            return None

        userData = []    # Create dict obj and populate
        for row in records:
            userData.append(features.getFeaturePointById(row.FeatureId))
        return jsonify(userData)

    except pyodbc.Error as e:
        print("pyodbc Error:", e)
        abort(500, f"Server encountered an error: {e}")

####    ####    ####    ####    ####    ####    ####    ####    ####    ####    ####    ####
# Gets all trails with a feature
def getTrailsByFeature(FeatureId):
    if not FeatureId:
        print("No FeatureId provided")
        abort(400, "No valid FeatureId")
        return
    
    try:
        cursor = conn.cursor()
        SQLQuery = "SELECT [TrailId] FROM [CW2].[TrailFeatures] WHERE [FeatureId] = ?"
        cursor.execute(SQLQuery, FeatureId)
        records = cursor.fetchall()

        if(records == None):
            abort(404, "None found")
            return None

        userData = []    # Create dict obj and populate
        for row in records:
            userData.append(trails.getTrailById(row.TrailId))
        return jsonify(userData)

    except pyodbc.Error as e:
        print("pyodbc Error:", e)
        abort(500, f"Server encountered an error: {e}")



####    ####    ####    ####    ####    ####    ####    ####    ####    ####    ####    ####
# Create new TrailFeature link entity
def newTrailFeature(TrailFeatureJSON):
    if not TrailFeatureJSON:
        print("JSON Object not parsed, stopping.")
        abort(400, "No TrailFeatureJSON provided")
        return

    FeatureId = TrailFeatureJSON.get("FeatureId")
    TrailId   = TrailFeatureJSON.get("TrailId")

    # Check for nulls
    if ( (FeatureId == None or "") or (TrailId == None or "") ):
        print("JSON field(s) empty, stopping.")
        abort(400, "Provided JSON field(s) empty")
        return 

    # If we get here, data has been given correctly

    try:
        cursor = conn.cursor() 
        SQLQuery1 = "INSERT INTO [CW2].[TrailFeatures] ([FeatureId], [TrailId]) VALUES (?, ?)"  # Build query and exec
        cursor.execute(SQLQuery1, TrailId, FeatureId)
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
# Delete link entity
def deleteTrailFeature(TrailFeatureJSON):
       
    if not TrailFeatureJSON:
        print("No TrailFeatureJSON provided")
        abort(400, "No TrailFeatureJSON provided")
        return
    
    TrailId    = TrailFeatureJSON.get("TrailId")
    FeatureId  = TrailFeatureJSON.get("FeatureId")

    if ((TrailId == None or "") and (FeatureId == None or "")):
        abort(400, "No fields provided")
        return

    try:
        cursor = conn.cursor()
        if (TrailId == None or ""): # Feature was deleted
            SQLQuery = "DELETE FROM [CW2].[TrailFeatures] WHERE [FeatureId] = ?"
            cursor.execute(SQLQuery, FeatureId)
        elif (FeatureId == None or ""): # Trail was deleted
            SQLQuery = "DELETE FROM [CW2].[TrailFeatures] WHERE [TrailId] = ?"
            cursor.execute(SQLQuery, TrailId)
        else: # Induvidual TrailFeature was deleted
            SQLQuery = "DELETE FROM [CW2].[TrailFeatures] WHERE [TrailId] = ? AND [FeatureId] = ?"
            cursor.execute(SQLQuery, TrailId, FeatureId)
        conn.commit()  # Commit changes 

        if cursor.rowcount > 0:  # rowcount gives the number of rows affected
            print("TrailFeature deleted successfully.")
            return make_response("TrailFeature deleted successfully.", 200)
        else:
            print("No TrailFeature found")
            abort(404, f"No TrailFeature exists")

    except pyodbc.Error as e:
        print("pyodbc Error:", e)
        abort(500, f"Server encountered an error: {e}")



####    ####    ####    ####    ####    ####    ####    ####    ####    ####    ####    ####
# Checks if user with given Id exists in users table
def checkOwnerExists(userId):
    # No null check needed, done in master function
    try:
        cursor = conn.cursor()

        SQLQuery = "SELECT * FROM [CW2].[Users] WHERE [UserId] = ?"
        cursor.execute(SQLQuery, userId)
 
        row = cursor.fetchone()

        if row:
            # User exists
            return True
        else:
            # User doesn't exist
            return False

    except pyodbc.Error as e:
        print("pyodbc Error:", e)
        abort(500, f"Server encountered an error: {e}")


####    ####    ####    ####    ####    ####    ####    ####    ####    ####    ####    ####
# Checks if user with given Id exists in users table
def checkOwnerPerms(userId):
    # No null check needed, done in master function
    try:
        cursor = conn.cursor()

        SQLQuery = "SELECT [Role] FROM [CW2].[Users] WHERE [UserId] = ?"
        cursor.execute(SQLQuery, userId)
 
        row = cursor.fetchone()

        if row:
            if (row[0] == "admin"):
                return True
        else:
            # User doesn't exist
            return False

    except pyodbc.Error as e:
        print("pyodbc Error:", e)
        abort(500, f"Server encountered an error: {e}")