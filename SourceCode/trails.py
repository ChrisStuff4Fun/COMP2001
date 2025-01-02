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
# Returns all trails in a JSON array
def getTrails():
    cursor = conn.cursor() 
    SQLQuery = "SELECT * FROM [CW2].[Trails]"

    try:
        cursor.execute(SQLQuery)
        records = cursor.fetchall()

        if (records == None):
            return make_response(jsonify([]), 200)
            
        userData = []    # Create dict obj and populate
        for row in records:
            userData.append({
                "TrailId" : row.TrailId, "TrailName" : row.TrailName, "TrailSummary" : row.TrailSummary,
                "TrailDescription" : row.TrailDescription, "Difficulty" : row.Difficulty, 
                "Location" : row.Location, "Length" : row.Length, "Elevation" : row.Elevation,
                "RouteType" : row.RouteType, "OwnerId" : row.OwnerId
            })

        # Convert to JSON obj
        cursor.close()
        return make_response(jsonify(userData), 200)

    except pyodbc.Error as e:
        print("pyodbc Error:", e)
        abort(500, f"Server encountered an error: {e}")

####    ####    ####    ####    ####    ####    ####    ####    ####    ####    ####    ####
# Adds a trail with given params 
# "TrailName": String (50)
# "TrailSummary" : String (200)
# "TrailDescription": String (1000)
# "Difficulty" : String (20)
# "Location" : String (100)
# "Length" : int (Metres)
# "Elevation" : int (Metres)
# "RouteType" : String (20)
# "OwnerId" : Foreign key - Users.UserId
def addTrail():

    trailJSON = request.get_json()

    if not trailJSON:
        print("JSON Object not parsed, stopping.")
        abort(400, "No trail provided")
        return
    
    if not auth.authUser(trailJSON.get("authEmail"), trailJSON.get("authPW")) or not auth.checkOwnerPerms(trailJSON.get("authEmail")):
        abort(401, "Access denied")
        return

    name        = trailJSON.get("TrailName")
    summary     = trailJSON.get("TrailSummary")
    description = trailJSON.get("TrailDescription")
    difficulty  = trailJSON.get("Difficulty")
    location    = trailJSON.get("Location")
    length      = trailJSON.get("Length")
    elevation   = trailJSON.get("Elevation")
    routeType   = trailJSON.get("RouteType")
    owner       = trailJSON.get("OwnerId")

    # Check for nulls
    if((name == None) or (difficulty == None) or (location == None) or (length == None) or 
       (elevation == None) or (routeType == None) or (owner == None)):
        abort(400, "Bad request, field(s) null")
        return
    
    # Check if owner exists
    if( not linkhelper.checkOwnerExists(owner) ):
        abort(404, f"Cannot find user with Id: {owner}")
        return

    # If we get here, fields are valid, so populate.
    try:
        cursor = conn.cursor() 

        SQLQuery1 = """INSERT INTO [CW2].[Trails] 
        ([TrailName], [TrailSummary], [TrailDescription], [Difficulty], [Location], [Length], [Elevation], [RouteType], [OwnerId])
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)"""  # Build query and exec
        cursor.execute(SQLQuery1, name, summary, description, difficulty, location, length, elevation, routeType, owner)
        conn.commit() # Commit changes

        if (cursor.rowcount > 0):  
            #Row added successfully
            print("Row added successfully")
            return make_response(jsonify({"message": "Row added successfully"}), 201)
        else:
            # No rows added
            print("Failed to add row")
            abort(400, "Failed to add row")

        cursor.close()

    except pyodbc.Error as e:
        print("pyodbc Error:", e)
        abort(500, f"Server encountered an error: {e}")


####    ####    ####    ####    ####    ####    ####    ####    ####    ####    ####    ####
# Gets trail JSON obj with given Id
def getTrailById(TrailId):

    if not TrailId:
        print("No Id, stopping.")
        abort(400, "No TrailId provided")
        return
    
    try:
        cursor = conn.cursor()
        SQLQuery = "SELECT * FROM [CW2].[Trails] WHERE [TrailId] = ?"
        cursor.execute(SQLQuery, TrailId)
        row = cursor.fetchone()

        if row:
            # Convert py dictionary to JSON
            JSONreturn = {"TrailId" : row.TrailId, "TrailName" : row.TrailName, "TrailSummary" : row.TrailSummary,
                          "TrailDescription" : row.TrailDescription, "Difficulty" : row.Difficulty, 
                          "Location" : row.Location, "Length" : row.Length, "Elevation" : row.Elevation,
                          "RouteType" : row.RouteType, "OwnerId" : row.OwnerId,
                          "Features" : linkhelper.getFeaturesByTrail(TrailId),
                          "LocationPoints" : linkhelper.getLocationPointsByTrail(TrailId)
                          }
            print("Trail: ", jsonify(JSONreturn))
            return make_response(jsonify(JSONreturn), 200)
        else:
            print("No trail found")
            abort( 404, f"Trail with id {TrailId} not found.")
            return

    except pyodbc.Error as e:
        print("pyodbc Error:", e)
        abort(500, f"Server encountered an error: {e}")
        return
    

####    ####    ####    ####    ####    ####    ####    ####    ####    ####    ####    ####
# Gets trail JSON array with given owner
def getTrailByOwner(userId):

    if not userId:
        print("No Id, stopping.")
        abort(400, "No OwnerId provided")
        return
    
    try:
        cursor = conn.cursor()
        SQLQuery = "SELECT * FROM [CW2].[Trails] WHERE [OwnerId] = ?"
        cursor.execute(SQLQuery, userId)
        
        rows = cursor.fetchall()

        if not rows:       
            print("No trail found")
            abort( 404, f"Trails with OwnerId {userId} not found.")
            return

        userData = []
        for row in rows:
            # Convert py dictionary to JSON
            userData.append({"TrailId" : row.TrailId, "TrailName" : row.TrailName, "TrailSummary" : row.TrailSummary,
                          "TrailDescription" : row.TrailDescription, "Difficulty" : row.Difficulty, 
                          "Location" : row.Location, "Length" : row.Length, "Elevation" : row.Elevation,
                          "RouteType" : row.RouteType, "OwnerId" : row.OwnerId})
           
        print("Trails: ", jsonify(userData))
        return make_response(jsonify(userData), 200)


    except pyodbc.Error as e:
        print("pyodbc Error:", e)
        abort(500, f"Server encountered an error: {e}")
        return
    

####    ####    ####    ####    ####    ####    ####    ####    ####    ####    ####    ####
# Gets Id of a trail with a given name
def getIdByName(TrailName):

    if not TrailName:
        print("No Name, stopping.")
        abort(400, "No name provided")
        return
    
    try:
        cursor = conn.cursor()
        SQLQuery = "SELECT [TrailId] FROM [CW2].[Trails] WHERE [TrailName] = ?"
        cursor.execute(SQLQuery, TrailName)
        row = cursor.fetchone()

        if row:
            return make_response(jsonify({"TrailId" : row[0]}), 200) 
        else:
            print("No trail found")
            abort( 404, f"Trail with name {TrailName} not found.")
            return

    except pyodbc.Error as e:
        print("pyodbc Error:", e)
        abort(500, f"Server encountered an error: {e}")
        return
    

####    ####    ####    ####    ####    ####    ####    ####    ####    ####    ####    ####
# Deletes a trail with a given Id
def deleteTrailById(TrailId):

    authJSON = request.get_json()

    if not auth.authUser(authJSON.get("authEmail"), authJSON.get("authPW")) or not auth.checkOwnerPerms(authJSON.get("authEmail")):
        abort(401, "Access denied")
        return
    
    if not TrailId:
        print("No trail provided")
        abort(400, "No trail provided")
        return
    
    try:
        cursor = conn.cursor()
        SQLQuery = "DELETE FROM [CW2].[Trails] WHERE [TrailId] = ?"
        cursor.execute(SQLQuery, TrailId)
        conn.commit()  # Commit changes 

        if cursor.rowcount > 0:  # rowcount gives the number of rows affected
            print("Trail deleted successfully.")

            linkhelper.deleteTrailFeature({"TrailId" : TrailId})   # Delete all link entities
            linkhelper.deleteTrailLocationPoint({"TrailId" : TrailId})

            return make_response(jsonify({"message": "Trail deleted successfully."}), 200)
        else:
            print("No trail found")
            abort(404, f"No trail exists with TrailId: {TrailId}")
            return

    except pyodbc.Error as e:
        print("pyodbc Error:", e)
        abort(500, f"Server encountered an error: {e}")
        return

####    ####    ####    ####    ####    ####    ####    ####    ####    ####    ####    ####
# Updates a trail with given Id (In JSON obj)
def updateTrailById():

    trailJSON = request.get_json()

    if not auth.authUser(trailJSON.get("authEmail"), trailJSON.get("authPW")) or not auth.checkOwnerPerms(trailJSON.get("authEmail")):
        abort(401, "Access denied")
        return

    id          = trailJSON.get("TrailId")
    name        = trailJSON.get("TrailName")
    summary     = trailJSON.get("TrailSummary")
    description = trailJSON.get("TrailDescription")
    difficulty  = trailJSON.get("Difficulty")
    location    = trailJSON.get("Location")
    length      = trailJSON.get("Length")
    elevation   = trailJSON.get("Elevation")
    routeType   = trailJSON.get("RouteType")
    owner       = trailJSON.get("OwnerId")

    if (id == None):
        abort(400, "No TrailId provided")
        return
    
    if (owner != None):
        # Check if owner exists
        if( not linkhelper.checkOwnerExists(owner) ):
            abort(404, f"Cannot find user with Id: {owner}")
            return
        
    try:
        cursor = conn.cursor()
        SQLQuery = """UPDATE [CW2].[Trails] SET [TrailName] = IsNull(?, [TrailName]), [TrailSummary] = IsNull(?, [TrailSummary]), 
        [TrailDescription] = IsNull(?, [TrailDescription]), [Difficulty] = IsNull(?, [Difficulty]), [Location] = IsNull(?, [Location]), 
        [Lenghth] = IsNull(?, [Lenghth]), [Elevation] = IsNull(?, [Elevation]), [RouteType] = IsNull(?, [RouteType]),
        [OwnerId] = IsNull(?, [OwnerId]) WHERE [TrailId] = ?"""
        cursor.execute(SQLQuery, name, summary, description, difficulty, location, length, elevation, routeType, owner, id)

        if (cursor.rowcount > 0):
            #Row updated successfully
            print("Row updated successfully")
            return make_response(jsonify({"message": "Row updated successfully"}), 200)
        else:
            # No rows updated
            print("Failed to update row")
            abort(404, f"Trail with id {id} not found.")
            return
        
    except pyodbc.Error as e:
        print("pyodbc Error:", e)
        abort(500, f"Server encountered an error: {e}")
        return
