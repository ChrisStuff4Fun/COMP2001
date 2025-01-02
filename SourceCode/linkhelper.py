from datetime import datetime
from flask import abort, make_response, jsonify, request
import pyodbc
import trails
import features
import locationpoints
import auth

# SQL Login stuffs
SERVER   = "DIST-6-505.uopnet.plymouth.ac.uk"
DATABASE = "COMP2001_CCatlin"
USERNAME = "CCatlin"
PASSWORD = "HmqA769+"
TRUSTSERVERCERTIFICATE = "yes"  # Needed for connections to Uni DB Server

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
        return make_response(jsonify({"error": "No valid TrailId provided"}), 400)
    
    try:
        cursor = conn.cursor()
        SQLQuery = "SELECT [LocationPointId] FROM [CW2].[TrailLocationPoints] WHERE [TrailId] = ? ORDER BY [OrderNum] ASC"
        cursor.execute(SQLQuery, TrailId)
        records = cursor.fetchall()

        if not records:
            return make_response(jsonify({"error": "None found"}), 404)

        userData = []  # Create dict obj and populate
        for row in records:
            userData.append(locationpoints.getLocationPointById(row.LocationPointId))

        return jsonify(userData)

    except pyodbc.Error as e:
        return make_response(jsonify({"error": f"Server encountered an error: {e}"}), 500)


####    ####    ####    ####    ####    ####    ####    ####    ####    ####    ####    ####
# Gets all trails that use a location point
def getTrailsByLocationPoint(LocationPointId):
    if not LocationPointId:
        return make_response(jsonify({"error": "No valid LocationPointId provided"}), 400)
    
    try:
        cursor = conn.cursor()
        SQLQuery = "SELECT [TrailId] FROM [CW2].[TrailLocationPoints] WHERE [LocationPointId] = ?"
        cursor.execute(SQLQuery, LocationPointId)
        records = cursor.fetchall()

        
        if not records:
            return make_response(jsonify({"error": "None found"}), 404)

        userData = []  # Create dict obj and populate
        for row in records:
            print (row.TrailId)
            userData.append(trails.getTrailById(row.TrailId))
        return jsonify(userData)

    except pyodbc.Error as e:
        return make_response(jsonify({"error": f"Server encountered an error: {e}"}), 500)


####    ####    ####    ####    ####    ####    ####    ####    ####    ####    ####    ####
# Creates new TrailLocationPoint link entity
def newTrailLocationPoint():
    TrailLocationPointJSON = request.get_json()

    if not TrailLocationPointJSON:
        abort(400, description="No TrailLocationPointJSON provided")

    if not auth.authUser(TrailLocationPointJSON.get("authEmail"), TrailLocationPointJSON.get("authPW")) or not auth.checkOwnerPerms(TrailLocationPointJSON.get("authEmail")):
        abort(401, description="Access denied")

    TrailId = TrailLocationPointJSON.get("TrailId")
    LocationPointId = TrailLocationPointJSON.get("LocationPointId")

    # Check for nulls
    if not TrailId or not LocationPointId:
        abort(400, description="Provided JSON field(s) empty")

    try:
        cursor = conn.cursor()
        SQLQuery1 = "INSERT INTO [CW2].[TrailLocationPoints] ([TrailId], [LocationPointId]) VALUES (?, ?)"
        cursor.execute(SQLQuery1, TrailId, LocationPointId)
        conn.commit()

        if cursor.rowcount > 0:
            return make_response(jsonify({"message": "Row added successfully"}), 201)
        else:
            abort(400, description="Failed to add row")

    except pyodbc.Error as e:
        abort(500, description=f"Server encountered an error: {e}")


####    ####    ####    ####    ####    ####    ####    ####    ####    ####    ####    ####
# Deletes link entity
def deleteTrailLocationPoint():
    TrailLocationPointJSON = request.get_json()

    if not TrailLocationPointJSON:
        abort(400, description="No TrailLocationPointJSON provided")

    if not auth.authUser(TrailLocationPointJSON.get("authEmail"), TrailLocationPointJSON.get("authPW")) or not auth.checkOwnerPerms(TrailLocationPointJSON.get("authEmail")):
        abort(401, description="Access denied")

    TrailId = TrailLocationPointJSON.get("TrailId")
    LocationPointId = TrailLocationPointJSON.get("LocationPointId")

    if not TrailId and not LocationPointId:
        abort(400, description="No fields provided")

    try:
        cursor = conn.cursor()
        if not TrailId:  # LocationPoint was deleted
            SQLQuery = "DELETE FROM [CW2].[TrailLocationPoints] WHERE [LocationPointId] = ?"
            cursor.execute(SQLQuery, LocationPointId)
        elif not LocationPointId:  # Trail was deleted
            SQLQuery = "DELETE FROM [CW2].[TrailLocationPoints] WHERE [TrailId] = ?"
            cursor.execute(SQLQuery, TrailId)
        else:  # Individual point was deleted
            SQLQuery = "DELETE FROM [CW2].[TrailLocationPoints] WHERE [TrailId] = ? AND [LocationPointId] = ?"
            cursor.execute(SQLQuery, TrailId, LocationPointId)
        conn.commit()

        if cursor.rowcount > 0:
            return make_response(jsonify({"message": "TrailLocationPoint deleted successfully."}), 200)
        else:
            abort(404, description="No TrailLocationPoint found")

    except pyodbc.Error as e:
        abort(500, description=f"Server encountered an error: {e}")


####    ####    ####    ####    ####    ####    ####    ####    ####    ####    ####    ####
# Gets all features belonging to a trail
def getFeaturesByTrail(TrailId):
    if not TrailId:
        abort(400, description="No valid TrailId provided")
    
    try:
        cursor = conn.cursor()
        SQLQuery = "SELECT [FeatureId] FROM [CW2].[TrailFeatures] WHERE [TrailId] = ?"
        cursor.execute(SQLQuery, TrailId)
        records = cursor.fetchall()

        if not records:
            abort(404, description="None found")

        userData = []  # Create dict obj and populate
        for row in records:
            userData.append(features.getFeaturePointById(row.FeatureId))
        return jsonify(userData)

    except pyodbc.Error as e:
        abort(500, description=f"Server encountered an error: {e}")


####    ####    ####    ####    ####    ####    ####    ####    ####    ####    ####    ####
# Gets all trails with a feature
def getTrailsByFeature(FeatureId):
    if not FeatureId:
        abort(400, description="No valid FeatureId provided")
    
    try:
        cursor = conn.cursor()
        SQLQuery = "SELECT [TrailId] FROM [CW2].[TrailFeatures] WHERE [FeatureId] = ?"
        cursor.execute(SQLQuery, FeatureId)
        records = cursor.fetchall()

        if not records:
            abort(404, description="None found")

        userData = []  # Create dict obj and populate
        for row in records:
            userData.append(trails.getTrailById(row.TrailId))
        return jsonify(userData)

    except pyodbc.Error as e:
        abort(500, description=f"Server encountered an error: {e}")


####    ####    ####    ####    ####    ####    ####    ####    ####    ####    ####    ####
# Create new TrailFeature link entity
def newTrailFeature():
    TrailFeatureJSON = request.get_json()

    if not TrailFeatureJSON:
        abort(400, description="No TrailFeatureJSON provided")

    if not auth.authUser(TrailFeatureJSON.get("authEmail"), TrailFeatureJSON.get("authPW")) or not auth.checkOwnerPerms(TrailFeatureJSON.get("authEmail")):
        abort(401, description="Access denied")

    FeatureId = TrailFeatureJSON.get("FeatureId")
    TrailId = TrailFeatureJSON.get("TrailId")

    # Check for nulls
    if not FeatureId or not TrailId:
        abort(400, description="Provided JSON field(s) empty")

    try:
        cursor = conn.cursor()
        SQLQuery1 = "INSERT INTO [CW2].[TrailFeatures] ([FeatureId], [TrailId]) VALUES (?, ?)"
        cursor.execute(SQLQuery1, TrailId, FeatureId)
        conn.commit()

        if cursor.rowcount > 0:
            return make_response(jsonify({"message": "Row added successfully"}), 201)
        else:
            abort(400, description="Failed to add row")

    except pyodbc.Error as e:
        abort(500, description=f"Server encountered an error: {e}")


####    ####    ####    ####    ####    ####    ####    ####    ####    ####    ####    ####
# Delete link entity
def deleteTrailFeature():
    TrailFeatureJSON = request.get_json()

    if not TrailFeatureJSON:
        abort(400, description="No TrailFeatureJSON provided")

    if not auth.authUser(TrailFeatureJSON.get("authEmail"), TrailFeatureJSON.get("authPW")) or not auth.checkOwnerPerms(TrailFeatureJSON.get("authEmail")):
        abort(401, description="Access denied")

    TrailId = TrailFeatureJSON.get("TrailId")
    FeatureId = TrailFeatureJSON.get("FeatureId")

    if not TrailId and not FeatureId:
        abort(400, description="No fields provided")

    try:
        cursor = conn.cursor()
        if not TrailId:  # Feature was deleted
            SQLQuery = "DELETE FROM [CW2].[TrailFeatures] WHERE [FeatureId] = ?"
            cursor.execute(SQLQuery, FeatureId)
        elif not FeatureId:  # Trail was deleted
            SQLQuery = "DELETE FROM [CW2].[TrailFeatures] WHERE [TrailId] = ?"
            cursor.execute(SQLQuery, TrailId)
        else:  # Individual TrailFeature was deleted
            SQLQuery = "DELETE FROM [CW2].[TrailFeatures] WHERE [TrailId] = ? AND [FeatureId] = ?"
            cursor.execute(SQLQuery, TrailId, FeatureId)
        conn.commit()

        if cursor.rowcount > 0:
            return make_response(jsonify({"message": "TrailFeature deleted successfully."}), 200)
        else:
            abort(404, description="No TrailFeature found")

    except pyodbc.Error as e:
        abort(500, description=f"Server encountered an error: {e}")


####    ####    ####    ####    ####    ####    ####    ####    ####    ####    ####    ####
# Checks if user with given Id exists in users table
def checkOwnerExists(userId):
    if not userId:
        abort(400, description="No valid userId provided")

    try:
        cursor = conn.cursor()
        SQLQuery = "SELECT * FROM [CW2].[Users] WHERE [UserId] = ?"
        cursor.execute(SQLQuery, userId)
        record = cursor.fetchone()

        if not record:
            abort(404, description="No such user found")

        return jsonify({"message": "User found", "UserId": userId})

    except pyodbc.Error as e:
        abort(500, description=f"Server encountered an error: {e}")
