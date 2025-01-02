from datetime import datetime
from flask import abort, make_response, jsonify, request
import pyodbc
import linkhelper
import auth

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
# Gets all features
def getFeatures():
    cursor = conn.cursor() 

    SQLQuery = "SELECT * FROM [CW2].[Features]"

    try:
        cursor.execute(SQLQuery)
        records = cursor.fetchall()

        userData = []    # Create dict obj and populate
        for row in records:
            userData.append({
                'FeatureId': row.FeatureId,
                'Feature': row.Feature
            })

        # Convert to JSON obj
        cursor.close()
        return make_response(jsonify(userData), 200)

    except pyodbc.Error as e:
        print("pyodbc Error:", e)
        abort(500, description=f"Server encountered an error: {e}")

####    ####    ####    ####    ####    ####    ####    ####    ####    ####    ####    ####
# Adds a feature with given description
def addFeature():

    pointJSON = request.get_json()

    if (pointJSON == None):
        abort(400, description="No JSON obj given")
    
    if not auth.authUser(pointJSON.get("authEmail"), pointJSON.get("authPW")) or not auth.checkOwnerPerms(pointJSON.get("authEmail")):
        abort(401, description="Access denied")
    
    feature  = pointJSON.get("Feature")

    if(feature == None):
        abort(400, description="Field empty")

    try:
        cursor = conn.cursor() 
        SQLQuery1 = "INSERT INTO [CW2].[Features] ([Feature]) VALUES(?)"  # Build query and exec
        cursor.execute(SQLQuery1, feature)
        conn.commit() # Commit changes

        if (cursor.rowcount > 0):  
            #Row added successfully
            print("Row added successfully")
            return make_response(jsonify({"message": "Row added successfully"}), 201)
        else:
            # No rows added
            print("Failed to add row")
            abort(400, description="Failed to add row")

        cursor.close()

    except pyodbc.Error as e:
        print("pyodbc Error:", e)
        abort(500, description=f"Server encountered an error: {e}")


####    ####    ####    ####    ####    ####    ####    ####    ####    ####    ####    ####
# Gets a feature with given Id
def getFeaturePointById(FeatureId):

    if (FeatureId == None):
        abort(400, description="No Id given")

    cursor = conn.cursor() 
    SQLQuery = "SELECT * FROM [CW2].[Features] WHERE [FeatureId] = ?"

    try:
        cursor.execute(SQLQuery, FeatureId)
        records = cursor.fetchone()

        if (not records):
            abort(404, description="Feature not found")

        userData = {
                'FeatureId': records.FeatureId,
                'Feature': records.Feature,
            }

        # Convert to JSON obj
        cursor.close()
        return jsonify(userData)

    except pyodbc.Error as e:
        print("pyodbc Error:", e)
        abort(500, description=f"Server encountered an error: {e}")


####    ####    ####    ####    ####    ####    ####    ####    ####    ####    ####    ####
# Deletes a feature with given Id
def deleteFeatureById(FeatureId):
    if not FeatureId:
        print("No Id provided")
        abort(400, description="No Id provided")
    
    userJSON = request.get_json()

    if not auth.authUser(userJSON.get("authEmail"), userJSON.get("authPW")) or not auth.checkOwnerPerms(userJSON.get("authEmail")):
        abort(401, description="Access denied")

    try:
        cursor = conn.cursor()
        SQLQuery = "DELETE FROM [CW2].[Features] WHERE [FeatureId] = ?"
        cursor.execute(SQLQuery, FeatureId)
        conn.commit()  # Commit changes 

        if cursor.rowcount > 0:  # rowcount gives the number of rows affected
            print("Feature deleted successfully.")
            linkhelper.deleteTrailFeature({"FeatureId" : FeatureId}) # Delete link entities
            return make_response(jsonify({"message": "Feature deleted successfully."}), 200)
        else:
            print("No Feature found")
            abort(404, description=f"No Feature exists with FeatureId: {FeatureId}")

    except pyodbc.Error as e:
        print("pyodbc Error:", e)
        abort(500, description=f"Server encountered an error: {e}")


####    ####    ####    ####    ####    ####    ####    ####    ####    ####    ####    ####
# Edits a feature with given Id
def editFeatureById():

    featureJSON = request.get_json()

    if not featureJSON:
        print("JSON Object not parsed, stopping.")
        abort(400, description="No Feature provided")
    
    if not auth.authUser(featureJSON.get("authEmail"), featureJSON.get("authPW")) or not auth.checkOwnerPerms(featureJSON.get("authEmail")):
        abort(401, description="Access denied")

    FeatureId = featureJSON.get("FeatureId")
    Feature   = featureJSON.get("Feature")

    # Check for nulls
    if ((Feature == None) or (FeatureId == None) ):
        print("JSON fields empty, stopping.")
        abort(400, description="Bad request - JSON fields empty")

    try:
        cursor = conn.cursor()
        SQLQuery = "UPDATE [CW2].[Features] SET [Feature] = IsNull(?, [Feature]) WHERE [FeatureId] = ?"
        cursor.execute(SQLQuery, Feature, FeatureId)

        if (cursor.rowcount > 0):
            # Row updated successfully
            print("Row updated successfully")
            return make_response(jsonify({"message": "Row updated successfully"}), 201)
        else:
            # No rows updated
            print("Failed to update row")
            abort(404, description=f"Feature with id {FeatureId} not found.")

        cursor.close()

    except pyodbc.Error as e:
        print("pyodbc Error:", e)
        abort(500, description=f"Server encountered an error: {e}")
