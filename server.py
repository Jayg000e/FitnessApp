
"""
Columbia's COMS W4111.001 Introduction to Databases
Example Webserver
To run locally:
    python3 server.py
Go to http://localhost:8111 in your browser.
A debugger such as "pdb" may be helpful for debugging.
Read about it online.
"""
import os
  # accessible as a variable in index.html:
from sqlalchemy import *
from sqlalchemy.pool import NullPool
from flask import Flask, request, render_template, g, redirect, Response, abort,jsonify
from sqlalchemy.exc import SQLAlchemyError

tmpl_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates')
app = Flask(__name__, template_folder=tmpl_dir)


#
# The following is a dummy URI that does not connect to a valid database. You will need to modify it to connect to your Part 2 database in order to use the data.
#
# XXX: The URI should be in the format of:
#
#     postgresql://USER:PASSWORD@34.75.94.195/proj1part2
#
# For example, if you had username gravano and password foobar, then the following line would be:
#
#     DATABASEURI = "postgresql://gravano:foobar@34.75.94.195/proj1part2"
#
DATABASEURI = "postgresql://postgres:admin@localhost:5432/fitness"
# DATABASEURI = "postgresql://jg4692:169492@34.74.171.121/proj1part2"


#
# This line creates a database engine that knows how to connect to the URI above.
#
engine = create_engine(DATABASEURI)

#
# Example of running queries in your database
# Note that this will probably not work if you already have a table named 'test' in your database, containing meaningful data. This is only an example showing you how to run queries in your database using SQLAlchemy.
#
conn = engine.connect()




@app.before_request
def before_request():
  """
  This function is run at the beginning of every web request
  (every time you enter an address in the web browser).
  We use it to setup a database connection that can be used throughout the request.

  The variable g is globally accessible.
  """
  try:
    g.conn = engine.connect()
  except:
    print("uh oh, problem connecting to database")
    import traceback; traceback.print_exc()
    g.conn = None

@app.teardown_request
def teardown_request(exception):
  """
  At the end of the web request, this makes sure to close the database connection.
  If you don't, the database could run out of memory!
  """
  try:
    g.conn.close()
  except Exception as e:
    pass

@app.route('/')
def index():
  return render_template("index.html")


@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()  
    username = data['username']
    email = data['email']
    try:
        query = text("SELECT username FROM users WHERE username = :username AND email = :email")
        result = g.conn.execute(query, {"username": username, "email": email}).fetchone()
        if result:
            return jsonify(success=True, username=username)
        else:
            return jsonify(success=False, message="Username or email not found")
    except SQLAlchemyError as e:
        return jsonify(success=False, message="An error occurred: " + str(e)), 500
    

@app.route('/profile/<username>') 
def profile(username): 
    profile = g.conn.execute(text("SELECT * FROM users WHERE username = :username"), {"username": username})
    profile = dict(zip(profile.keys(), profile.fetchone()))
    friends = g.conn.execute(text(" SELECT usernameb AS friend FROM Friends WHERE usernamea = :username"), {"username": username})
    friends = friends.fetchall()
    group_query = text("""
            SELECT g.groupname, g.groupid
            FROM UsersInGroups ug
            JOIN Groups g ON ug.groupid = g.groupid
            WHERE ug.username = :username
        """)
    groups = g.conn.execute(group_query, {"username": username})
    groups = groups.fetchall()
    return render_template("profile.html", profile=profile,friends=friends,groups=groups)

@app.route('/friend/<username>') 
def friend(username): 
    friends = g.conn.execute(text(" SELECT usernameb AS friend FROM Friends WHERE usernamea = :username"), {"username": username})
    friends = friends.fetchall()
    return render_template("friend.html", friends=friends)

@app.route('/group/<int:groupid>')
def group(groupid):
    # Retrieve the group's name
    group_name = g.conn.execute(text("SELECT groupname FROM Groups WHERE groupid = :groupid"), {"groupid": groupid})
    group_name = group_name.fetchone()

    # If group is found, retrieve the users
    if group_name:
        users_query = text("""
            SELECT u.username, u.firstname, u.lastname
            FROM UsersInGroups ug
            JOIN Users u ON ug.username = u.username
            WHERE ug.groupid = :groupid
        """)
        users = g.conn.execute(users_query, {"groupid": groupid})
        users = users.fetchall()
        return render_template('group.html', users=users, groupid=groupid, groupname=group_name[0])
    
@app.route('/records/<username>')
def records(username):
  # Create a dictionary to hold all the user's records
  user_records = {
      'workout_records': [],
      'nutrition_records': [],
      'health_records': [],
      'goal_records': []
  }
  
  # Retrieve workout records
  workout_records_query = text("""
      SELECT wr.*, e.exercisename
      FROM WorkoutRecordsWorkOnExercises wr
      JOIN Exercises e ON wr.exercisename = e.exercisename
      WHERE wr.username = :username
  """)
  workout_records_result = g.conn.execute(workout_records_query, {"username": username})
  user_records['workout_records'] = workout_records_result.fetchall()
  
  # Retrieve nutrition records
  nutrition_records_query = text("""
      SELECT *
      FROM NutritionRecords
      WHERE username = :username
  """)
  nutrition_records_result = g.conn.execute(nutrition_records_query, {"username": username})
  user_records['nutrition_records'] = nutrition_records_result.fetchall()

  # Retrieve health records
  health_records_query = text("""
      SELECT *
      FROM HealthRecords
      WHERE username = :username
  """)
  health_records_result = g.conn.execute(health_records_query, {"username": username})
  user_records['health_records'] = health_records_result.fetchall()

  # Retrieve goal records
  goal_records_query = text("""
      SELECT *
      FROM GoalRecords
      WHERE username = :username
  """)
  goal_records_result = g.conn.execute(goal_records_query, {"username": username})
  user_records['goal_records'] = goal_records_result.fetchall()

  for record_type, records in user_records.items():
    transformed_records=[]
    for record in records:
        # Fetch the comments for each record
        comments_query = text("""
            SELECT *
            FROM CommentsMakeCommentsOn c
            WHERE c.recordid = :recordid AND c.recorduser = :username
            ORDER BY c.time DESC
        """)
        print(record.recordid,record.username)
        comments_result = g.conn.execute(comments_query, {
            "recordid": record.recordid,
            "username": record.username  
        })
        transformed_records.append((record,comments_result.fetchall()))
    user_records[record_type]=transformed_records

  # Render all the records using the template
  return render_template('records.html', username=username, records=user_records)

@app.route('/worldchannel') 
def worldchannel(): 
    # Retrieve all records for the given username
    records_query = text("""
    SELECT rk.recordid, rk.note, rk.time, rk.username
    FROM RecordKeep rk
    ORDER BY rk.time DESC;
    """)
    records = g.conn.execute(records_query)
    records = records.fetchall()

    # For each record, fetch the associated comments
    comments_query_template = text("""
    SELECT cm.*
    FROM CommentsMakeCommentsOn cm
    WHERE cm.recordid = :recordid AND cm.recorduser = :username
    ORDER BY cm.time DESC;
    """)

    # Create a dictionary to hold records and their comments
    records_with_comments = []
    for record in records:
        # Fetch comments for the current record
        comments_result = g.conn.execute(comments_query_template, {
            "recordid": record.recordid,
            "username": record.username  # assuming 'username' is the same for RecordKeep and CommentsMakeCommentsOn
        })
        comments = comments_result.fetchall()
        
        # Append the record and its comments as a tuple to the list
        records_with_comments.append((record, comments))

    # Pass the list of records with their comments to the template
    return render_template('worldchannel.html', records_with_comments=records_with_comments)





if __name__ == "__main__":
  import click

  @click.command()
  @click.option('--debug', is_flag=True)
  @click.option('--threaded', is_flag=True)
  @click.argument('HOST', default='0.0.0.0')
  @click.argument('PORT', default=8111, type=int)
  def run(debug, threaded, host, port):
    """
    This function handles command line parameters.
    Run the server using:

        python3 server.py

    Show the help text using:

        python3 server.py --help

    """

    HOST, PORT = host, port
    print("running on %s:%d" % (HOST, PORT))
    app.run(host=HOST, port=PORT, debug=debug, threaded=threaded)

  run()
