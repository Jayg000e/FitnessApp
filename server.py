
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
from flask import Flask, request, render_template, g, redirect, Response, abort,jsonify ,url_for, flash
from sqlalchemy.exc import SQLAlchemyError,IntegrityError
from datetime import datetime, time
from responseGenerator import responseGenerator


tmpl_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates')
app = Flask(__name__, template_folder=tmpl_dir)
app.secret_key = 'jg4692'


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

@app.route('/login', methods=['GET','POST'])
def login():
    if request.method == "POST":
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
    return render_template("login.html")

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        try:
          # Retrieve form data
          username = request.form['username']
          email = request.form['email']
          firstname = request.form['firstname']
          lastname = request.form['lastname']
          age = request.form['age']
          gender = request.form['gender']
          height = request.form['height']
          g.conn.execute(text("""INSERT INTO Users (username, email,firstname,lastname,age,gender,height) 
              VALUES (:username, :email, :firstname, :lastname, :age, :gender, :height) """), 
              {"username": username, "email": email,"firstname":firstname,"lastname":lastname,"age":age,"gender":gender,"height":height})
          g.conn.commit()
          # After inserting the user, you can redirect to login page or somewhere else
          flash('User registered successfully!', 'success')
          return redirect(url_for('login'))
        except:
          flash('Invalid registration, try again with valid input', 'error')
          return redirect(url_for('register'))
    
    # If the request is GET, just render the registration form
    return render_template('register.html')

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

@app.route('/exercise/<username>') 
def exercise(username):
    # Fetch favorite exercises
    favorite_exercises_query = text('''
        SELECT e.exercisename, e.muscle, e.description, e.difficulty
        FROM Exercises e
        JOIN Favorites f ON f.exercisename = e.exercisename
        WHERE f.username = :username;
    ''')

    # Fetch non-favorite exercises
    non_favorite_exercises_query = text('''
        SELECT e.exercisename, e.muscle, e.description, e.difficulty
        FROM Exercises e
        WHERE e.exercisename NOT IN (
            SELECT exercisename
            FROM Favorites
            WHERE username = :username
        );
    ''')

    # Execute the queries
    favorite_exercises = g.conn.execute(favorite_exercises_query, {"username": username}).fetchall()
    non_favorite_exercises = g.conn.execute(non_favorite_exercises_query, {"username": username}).fetchall()
    
    # Render the template with separate lists for favorites and non-favorites
    return render_template("exercise.html", username=username, favorite_exercises=favorite_exercises, non_favorite_exercises=non_favorite_exercises)


@app.route('/friend/<username>') 
def friend(username): 
    friends = g.conn.execute(text(" SELECT usernameb AS friend FROM Friends WHERE usernamea = :username"), {"username": username})
    friends = friends.fetchall()
    return render_template("friend.html", friends=friends,username=username)

@app.route('/usergroup/<username>') 
def usergroup(username): 
    query = text("""
        SELECT g.groupid, g.groupname 
        FROM Groups g
        JOIN UsersInGroups ug ON g.groupid = ug.groupid 
        WHERE ug.username = :username
    """)
    user_groups = g.conn.execute(query, {"username": username}).fetchall()
    return render_template("usergroup.html", user_groups=user_groups,username=username)

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
            WHERE wr.username IN (SELECT ug.username FROM UsersInGroups ug WHERE ug.groupid = :groupid)
        """)
        workout_records_result = g.conn.execute(workout_records_query, {"groupid": groupid})
        user_records['workout_records'] = workout_records_result.fetchall()
        
        # Retrieve nutrition records
        nutrition_records_query = text("""
            SELECT *
            FROM NutritionRecords
            WHERE username IN (SELECT ug.username FROM UsersInGroups ug WHERE ug.groupid = :groupid)
        """)
        nutrition_records_result = g.conn.execute(nutrition_records_query, {"groupid": groupid})
        user_records['nutrition_records'] = nutrition_records_result.fetchall()

        # Retrieve health records
        health_records_query = text("""
            SELECT *
            FROM HealthRecords
            WHERE username IN (SELECT ug.username FROM UsersInGroups ug WHERE ug.groupid = :groupid)
        """)
        health_records_result = g.conn.execute(health_records_query, {"groupid": groupid})
        user_records['health_records'] = health_records_result.fetchall()

        # Retrieve goal records
        goal_records_query = text("""
            SELECT *
            FROM GoalRecords
            WHERE username IN (SELECT ug.username FROM UsersInGroups ug WHERE ug.groupid = :groupid)
        """)
        goal_records_result = g.conn.execute(goal_records_query, {"groupid": groupid})
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
        return render_template('group.html', users=users, groupid=groupid, groupname=group_name[0],records=user_records)
    
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
      JOIN RecordKeep rk ON wr.username = rk.username AND wr.recordid = rk.recordid
      ORDER BY rk.time DESC
      LIMIT 5
  """)
  workout_records_result = g.conn.execute(workout_records_query)
  user_records['workout_records'] = workout_records_result.fetchall()
  
  # Retrieve nutrition records
  nutrition_records_query = text("""
      SELECT *
      FROM NutritionRecords nr
      JOIN RecordKeep rk ON nr.username = rk.username AND nr.recordid = rk.recordid
      ORDER BY rk.time DESC
      LIMIT 5
                                 
  """)
  nutrition_records_result = g.conn.execute(nutrition_records_query)
  user_records['nutrition_records'] = nutrition_records_result.fetchall()

  # Retrieve health records
  health_records_query = text("""
      SELECT *
      FROM HealthRecords hr
      JOIN RecordKeep rk ON hr.username = rk.username AND hr.recordid = rk.recordid
      ORDER BY rk.time DESC
      LIMIT 5
  """)
  health_records_result = g.conn.execute(health_records_query)
  user_records['health_records'] = health_records_result.fetchall()

  # Retrieve goal records
  goal_records_query = text("""
      SELECT *
      FROM GoalRecords gr
      JOIN RecordKeep rk ON gr.username = rk.username AND gr.recordid = rk.recordid
      ORDER BY rk.time DESC
      LIMIT 5
  """)
  goal_records_result = g.conn.execute(goal_records_query)
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
  return render_template('worldchannel.html', records=user_records)

@app.route('/add_friend', methods=['POST'])
def add_friend():
    current_user_username = request.form['currentUser']
    new_friend_username = request.form['newFriendUsername']
    if current_user_username == new_friend_username:
        # Optionally, flash a message to the user
        flash('You cannot add yourself as a friend.', 'error')
        return redirect(url_for('friend', username=current_user_username))

    try:
        query = text("""
            INSERT INTO Friends (usernamea, usernameb) 
            VALUES (:current_user_username, :new_friend_username)""")
        g.conn.execute(query, {"current_user_username":current_user_username, "new_friend_username":new_friend_username})
        g.conn.commit()
        
        # Optionally, flash a success message to the user
        flash('Friend added successfully!', 'success')

        # Redirect to the friend page of the current user
        return redirect(url_for('friend', username=current_user_username))

    except IntegrityError:
        # Handle the unique constraint violation, if the friendship already exists
        # Optionally, flash a message to the user
        flash('This friendship already exists.', 'error')
        return redirect(url_for('friend', username=current_user_username))

    except Exception as e:
        # Handle any other exception that occurs
        # Optionally, flash a message to the user
        flash('An error occurred while adding a friend.', 'error')
        return redirect(url_for('friend', username=current_user_username))
    
@app.route('/add_group', methods=['POST'])
def add_group():
    current_user_username = request.form['currentUser']
    newGroupId = request.form['newGroupId']
    # Ensure a group name was provided
    if not newGroupId:
      return redirect(url_for('usergroup', username=current_user_username))
    try:
      query = text("INSERT INTO UsersInGroups (groupid,username) VALUES (:groupid,:username) ")
      g.conn.execute(query,{"groupid":newGroupId,"username":current_user_username})
      g.conn.commit()
        # Optionally, flash a success message to the user
      flash('Group added successfully!', 'success')
      return redirect(url_for('usergroup', username=current_user_username))
      
    except:
        # Handle the unique constraint violation, if the friendship already exists
        # Optionally, flash a message to the user
        flash('An error occured, please try to add another group.', 'error')
        return redirect(url_for('usergroup', username=current_user_username))
    
@app.route('/create_group', methods=['POST'])
def create_group():
    current_user_username = request.form['currentUser2']
    groupname = request.form['groupname']
    # Ensure a group name was provided
    if not groupname:
      return redirect(url_for('usergroup', username=current_user_username))
    try:
       # Prepare the INSERT statement with the RETURNING clause
      query = text("INSERT INTO Groups (groupname) VALUES (:groupname) RETURNING groupid")
      result = g.conn.execute(query, {"groupname": groupname})
      
      # Fetch the generated groupid
      groupid = result.fetchone()[0]
      join_group_query = text("INSERT INTO UsersInGroups (groupid,username) VALUES (:groupid,:username) ")
      g.conn.execute(join_group_query,{"groupid":groupid,"username":current_user_username})
      g.conn.commit()
      flash('Group created successfully!', 'success')
      return redirect(url_for('usergroup', username=current_user_username))
    except:
      flash('Error creating group', 'error')
      return redirect(url_for('usergroup', username=current_user_username))
      
@app.route('/add_favorites', methods=['POST'])
def add_favorites():
    username = request.form['username']
    selected_exercises = request.form.getlist('favorite')  # 'favorite' is the name of the checkboxes
    
    # Check if any exercises were selected
    if not selected_exercises:
        flash('No exercises selected to add to favorites.', 'warning')
        return redirect(url_for('exercise', username=username))

    try:
        for exercisename in selected_exercises:
            insert_favorite_query = text('''
                INSERT INTO Favorites (username, exercisename) VALUES (:username, :exercisename)
            ''')
            g.conn.execute(insert_favorite_query, {"username": username, "exercisename": exercisename})
        g.conn.commit()
        flash('Selected exercises added to favorites.', 'success')
    except Exception as e:
        # If there is any exception, rollback the transaction
        g.conn.rollback()
        flash('An error occurred while adding to favorites.', 'error')
    # Redirect back to the exercises page
    return redirect(url_for('exercise', username=username))
@app.route('/create_exercise', methods=['POST'])
def create_exercise():
    
  exercisename = request.form['exercisename']
  muscle = request.form['muscle']
  description = request.form['description']
  difficulty = request.form['difficulty']
  
  try:
      insert_query = text('''
          INSERT INTO Exercises (exercisename, muscle, description, difficulty) 
          VALUES (:exercisename, :muscle, :description, :difficulty)
      ''')
      g.conn.execute(insert_query, {
          "exercisename": exercisename,
          "muscle": muscle,
          "description": description,
          "difficulty": difficulty
      })
      g.conn.commit()
      flash('Exercise created successfully!', 'success')
  except Exception as e:
      g.conn.rollback()
      flash('Error creating exercise: ' + str(e), 'error')

  return redirect(url_for('exercise', username=request.form['username']))

@app.route('/comment', methods=['POST'])
def comment():
  print(request.form,"requestttt")
  recordUser = request.form['recordUser']
  recordId = request.form['recordId']
  commentUser = request.form['commentUser']
  content = request.form['content']
  try:
      insert_query = text('''
          INSERT INTO CommentsMakeCommentsOn (commentuser, recordid, recorduser, content, time) 
          VALUES (:commentUser, :recordId, :recordUser, :content, :time)
      ''')
      g.conn.execute(insert_query, {
          "commentUser": commentUser,
          "recordId": recordId,
          "recordUser": recordUser,
          "content": content,
          "time": datetime.utcnow(),
      })
      g.conn.commit()
      flash('Comment successfully!', 'success')
  except Exception as e:
      g.conn.rollback()
      flash('Error commenting: ' + str(e), 'error')

  return redirect(url_for('records', username=request.form['recordUser']))

@app.route('/add_nutrition_record/<username>', methods=['GET', 'POST'])
def add_nutrition_record(username):
    
    if request.method == 'POST':
        recordkeep_sql = text(
          "INSERT INTO RecordKeep (username, note, time) "
          "VALUES (:username, :note, :time) RETURNING recordid"
        )
        recordid = g.conn.execute(
           recordkeep_sql, {
              "username": username,
              "note": request.form['note'],
              "time": datetime.utcnow(),
           }
        ).scalar()
        nutrition_sql = text(
          "INSERT INTO NutritionRecords (recordid, username, description, calorie, protein) "
          "VALUES (:recordid, :username, :description, :calorie, :protein)"
        )
        g.conn.execute(
           nutrition_sql, {
              "recordid": recordid,
              "username": username,
              "description": request.form['description'],
              "calorie": request.form['calorie'],
              "protein": request.form['protein']
           }
        )
        g.conn.commit()
        return redirect(url_for('records',username=username))
    return render_template('nutritionrecord.html',username=username) 



@app.route('/add_goal_record/<username>', methods=['GET', 'POST'])
def add_goal_record(username):
    
    if request.method == 'POST':
        recordkeep_sql = text(
          "INSERT INTO RecordKeep (username, note, time) "
          "VALUES (:username, :note, :time) RETURNING recordid"
        )
        recordid = g.conn.execute(
           recordkeep_sql, {
              "username": username,
              "note": request.form['note'],
              "time": datetime.utcnow(),
           }
        ).scalar()
        goal_sql = text(
          "INSERT INTO GoalRecords (recordid, username, goaltype, targetvalue, deadline) "
          "VALUES (:recordid, :username, :goaltype, :targetvalue, :deadline)"
        )
        deadline_date = request.form['deadline_date']
    
        # Assume midnight time if only date is provided
        deadline_time = time(0, 0)  # This sets the time to 00:00 (midnight)
        
        # Combine the date and time to form a complete datetime object
        deadline = datetime.combine(datetime.strptime(deadline_date, '%Y-%m-%d'), deadline_time)
        
        # Convert the datetime to a string in the format required by your database
        deadline_timestamp = deadline.strftime('%Y-%m-%d %H:%M:%S')

        g.conn.execute(
           goal_sql, {
              "recordid": recordid,
              "username": username,
              "goaltype": request.form['goaltype'],
              "targetvalue": request.form['targetvalue'],
              "deadline": deadline_timestamp
           }
        )
        g.conn.commit()
        return redirect(url_for('records',username=username))
    return render_template('goalrecord.html',username=username) 

@app.route('/add_health_record/<username>', methods=['GET', 'POST'])
def add_health_record(username):
    
    if request.method == 'POST':
        recordkeep_sql = text(
          "INSERT INTO RecordKeep (username, note, time) "
          "VALUES (:username, :note, :time) RETURNING recordid"
        )
        recordid = g.conn.execute(
           recordkeep_sql, {
              "username": username,
              "note": request.form['note'],
              "time": datetime.utcnow(),
           }
        ).scalar()
        health_sql = text(
          "INSERT INTO HealthRecords (recordid, username, weight, bodyfatpercentage, bloodpressure, restingheartrate) "
          "VALUES (:recordid, :username, :weight, :bodyfatpercentage, :bloodpressure, :restingheartrate)"
        )
        g.conn.execute(
           health_sql, {
              "recordid": recordid,
              "username": username,
              "weight": request.form['weight'],
              "bodyfatpercentage": request.form['bodyfatpercentage'],
              "bloodpressure": request.form['bloodpressure'],
              "restingheartrate": request.form['restingheartrate']
           }
        )
        g.conn.commit()
        return redirect(url_for('records',username=username))
    return render_template('healthrecord.html',username=username) 

@app.route('/add_workout_record/<username>', methods=['GET', 'POST'])
def add_workout_record(username):
    
    if request.method == 'POST':
        recordkeep_sql = text(
          "INSERT INTO RecordKeep (username, note, time) "
          "VALUES (:username, :note, :time) RETURNING recordid"
        )
        recordid = g.conn.execute(
           recordkeep_sql, {
              "username": username,
              "note": request.form['note'],
              "time": datetime.utcnow(),
           }
        ).scalar()
        workout_sql = text(
          "INSERT INTO WorkoutRecordsWorkOnExercises (recordid, username, sets, repitition, weightlifted, exercisename) "
          "VALUES (:recordid, :username, :sets, :repitition, :weightlifted, :exercisename)"
        )
        g.conn.execute(
           workout_sql, {
              "recordid": recordid,
              "username": username,
              "sets": request.form['sets'],
              "weightlifted": request.form['weightlifted'],
              "exercisename": request.form['exercisename'],
              "repitition": request.form['repetition'],
           }
        )
        g.conn.commit()
        return redirect(url_for('records',username=username))
    else:
      exercises=g.conn.execute(
           text("SELECT * from Exercises")
        ).fetchall()
      return render_template('workoutrecord.html',username=username,exercises=exercises) 


@app.route('/get_advise',methods=['POST']) 
def get_advise(): 
  username=request.form["recordUser"]
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
  advise=responseGenerator(user_records)
  return render_template('records.html', username=request.form["recordUser"], records=user_records,advise=advise)


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
