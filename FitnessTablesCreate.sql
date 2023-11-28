DROP TABLE IF EXISTS Users CASCADE;
CREATE TABLE Users (
  username VARCHAR(50),
  email VARCHAR(255) NOT NULL CHECK (email ~* '^[A-Za-z0-9._%-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,4}$'),
  firstname VARCHAR(50) NOT NULL CHECK (firstname ~ '^[A-Za-z]+$'),
  lastname VARCHAR(50) NOT NULL CHECK (lastname ~ '^[A-Za-z]+$'),
  age INTEGER NOT NULL CHECK (age >= 0 AND age <= 120),
  gender VARCHAR(10) NOT NULL CHECK (gender IN ('male', 'female')),
  height REAL NOT NULL CHECK (height >= 0.0),
  PRIMARY KEY (username)
);

DROP TABLE IF EXISTS Friends CASCADE;
CREATE TABLE Friends (
  usernamea VARCHAR(50),
  usernameb VARCHAR(50) CHECK (usernamea <> usernameb),
   PRIMARY KEY (usernamea, usernameb),
   FOREIGN KEY (usernamea) REFERENCES Users(username),
   FOREIGN KEY (usernameb) REFERENCES Users(username)
);

DROP TABLE IF EXISTS Exercises CASCADE;
CREATE TABLE Exercises (
  exercisename VARCHAR(50),
  muscle VARCHAR(50) NOT NULL,
  description VARCHAR(255) NOT NULL,
  difficulty INTEGER NOT NULL,
  PRIMARY KEY (exercisename)
);

DROP TABLE IF EXISTS Favorites CASCADE;
CREATE TABLE Favorites (
  username VARCHAR(50),
  exercisename VARCHAR(50),
  PRIMARY KEY (username,exercisename),
  FOREIGN KEY (username) REFERENCES Users(username),
  FOREIGN KEY (exercisename) REFERENCES Exercises(exercisename)
);

DROP TABLE IF EXISTS RecordKeep CASCADE;
CREATE TABLE RecordKeep (
  recordid serial,
  username VARCHAR(50),
  note VARCHAR(255),
  time TIMESTAMP NOT NULL,
  PRIMARY KEY (recordid, username),
  FOREIGN KEY (username) REFERENCES Users(username) ON DELETE CASCADE
);

DROP TABLE IF EXISTS WorkoutRecordsWorkOnExercises CASCADE;
CREATE TABLE WorkoutRecordsWorkOnExercises (
  recordid INTEGER,
  username VARCHAR(50),
  sets INTEGER NOT NULL,
  repitition INTEGER,
  weightlifted REAL,
  exercisename VARCHAR(50) NOT NULL,
  PRIMARY KEY (recordid, username),
  FOREIGN KEY (recordid, username) REFERENCES RecordKeep(recordid,username) ON DELETE CASCADE,
  FOREIGN KEY (exercisename) REFERENCES Exercises(exercisename)
);

DROP TABLE IF EXISTS NutritionRecords CASCADE;
CREATE TABLE NutritionRecords (
  recordid INTEGER,
  username VARCHAR(50),
  description VARCHAR(255),
  calorie REAL NOT NULL,
  protein REAL NOT NULL,
  PRIMARY KEY (recordid, username),
  FOREIGN KEY (recordid, username) REFERENCES RecordKeep(recordid,username) ON DELETE CASCADE
);

DROP TABLE IF EXISTS HealthRecords CASCADE;
CREATE TABLE HealthRecords (
  recordid INTEGER,
  username VARCHAR(50),
  weight REAL NOT NULL,
  bodyfatpercentage REAL,
  bloodpressure INTEGER,
  restingheartrate INTEGER,
  PRIMARY KEY (recordid, username),
  FOREIGN KEY (recordid, username) REFERENCES RecordKeep(recordid,username) ON DELETE CASCADE
);

DROP TABLE IF EXISTS GoalRecords CASCADE;
CREATE TABLE GoalRecords (
  recordid INTEGER,
  username VARCHAR(50),
  goaltype VARCHAR(30) NOT NULL,
  targetvalue real NOT NULL,
  deadline TIMESTAMP NOT NULL,
  PRIMARY KEY (recordid, username),
  FOREIGN KEY (recordid, username) REFERENCES RecordKeep(recordid,username) ON DELETE CASCADE
);

DROP TABLE IF EXISTS CommentsMakeCommentsOn CASCADE;
CREATE TABLE CommentsMakeCommentsOn (
  commentid serial,
  commentuser VARCHAR(50),
  recordid INT NOT NULL,
  recorduser VARCHAR(50) NOT NULL,
  content VARCHAR(255) NOT NULL,
  time TIMESTAMP NOT NULL,
  PRIMARY KEY (commentid, commentuser),
  FOREIGN KEY (commentuser) REFERENCES Users(username) ON DELETE CASCADE,
  FOREIGN KEY (recordid, recorduser) REFERENCES RecordKeep(recordid, username)
);

DROP TABLE IF EXISTS Groups CASCADE;
CREATE TABLE Groups (
  groupid serial,
  groupname VARCHAR(50) NOT NULL,
   PRIMARY KEY (groupid)
);

DROP TABLE IF EXISTS UsersInGroups CASCADE;
CREATE TABLE UsersInGroups (
  groupid INTEGER,
  username VARCHAR(50),
  PRIMARY KEY (groupid, username),
  FOREIGN KEY (groupid) REFERENCES Groups(groupid),
  FOREIGN KEY (username) REFERENCES Users(username)
);








