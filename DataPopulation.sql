--User table
INSERT INTO Users (username, email, firstname, lastname, age, gender, height) VALUES
('john_doe', 'john.doe@example.com', 'John', 'Doe', 30, 'male', 177.8),
('jane_smith', 'jane.smith@example.com', 'Jane', 'Smith', 28, 'female', 167.6),
('alice_jones', 'alice.jones@example.com', 'Alice', 'Jones', 25, 'female', 165.1),
('bob_brown', 'bob.brown@example.com', 'Bob', 'Brown', 35, 'male', 185.4),
('charlie_green', 'charlie.green@example.com', 'Charlie', 'Green', 29, 'male', 172.7),
('daisy_white', 'daisy.white@example.com', 'Daisy', 'White', 24, 'female', 162.6),
('edward_black', 'edward.black@example.com', 'Edward', 'Black', 31, 'male', 170.2),
('fiona_gray', 'fiona.gray@example.com', 'Fiona', 'Gray', 27, 'female', 165.1),
('george_yellow', 'george.yellow@example.com', 'George', 'Yellow', 32, 'male', 177.8),
('hannah_blue', 'hannah.blue@example.com', 'Hannah', 'Blue', 26, 'female', 160.0);

--friends table
DO $$
DECLARE
    curr_user VARCHAR(50);
    num_friends INT;
    random_friends VARCHAR(50)[];
BEGIN
    -- Iterate through each user
    FOR curr_user IN (SELECT username FROM Users) LOOP
        
        -- Randomly decide how many friends a user will have, let's say between 1 to 5
        num_friends := CAST(FLOOR(RANDOM() * 5 + 1) AS INT);
        
        -- Fetch random distinct users as friends using subquery
        SELECT ARRAY_AGG(sub.username) INTO random_friends
        FROM (
            SELECT username
            FROM Users
            WHERE username <> curr_user
            ORDER BY RANDOM()
            LIMIT num_friends
        ) AS sub;

        -- Add the friendships to the table
        FOR i IN 1 .. array_length(random_friends, 1) LOOP
            INSERT INTO Friends(usernamea, usernameb)
            VALUES (curr_user, random_friends[i])
            ON CONFLICT DO NOTHING; -- Prevents inserting duplicates
        END LOOP;

    END LOOP;
END $$;






-- exercise table
INSERT INTO Exercises (exercisename, muscle, description, difficulty) VALUES
('Push-up', 'Chest', 'A bodyweight exercise that targets the chest and triceps.', 2),
('Pull-up', 'Back', 'A bodyweight exercise that targets the upper back and biceps.', 4),
('Squat', 'Legs', 'A compound exercise that targets the quads, hamstrings, and glutes.', 3),
('Deadlift', 'Back', 'A compound exercise targeting the back, glutes, and hamstrings.', 5),
('Bench Press', 'Chest', 'A weightlifting exercise targeting the chest, shoulders, and triceps.', 3),
('Bicep Curl', 'Biceps', 'Targets the biceps using dumbbells or a barbell.', 2),
('Tricep Extension', 'Triceps', 'Targets the triceps using dumbbells or a cable machine.', 2),
('Leg Press', 'Legs', 'Targets the quads and hamstrings using a leg press machine.', 3),
('Shoulder Press', 'Shoulders', 'A weightlifting exercise targeting the shoulders.', 3),
('Lateral Raise', 'Shoulders', 'Targets the side deltoids using dumbbells.', 1);


--favorite table
DO $$
DECLARE
    user_name VARCHAR(50);
    random_exercise VARCHAR(255);
    num_exercises INT;
    iter INT;
BEGIN
    -- Iterate through each user
    FOR user_name IN (SELECT username FROM Users) LOOP

        -- Random number of exercises for each user (e.g., between 1 to 5 exercises)
        num_exercises := CAST(FLOOR(RANDOM() * 5 + 1) AS INT);

        FOR iter IN 1..num_exercises LOOP
            -- Select a random exercise
            SELECT exercisename INTO random_exercise
            FROM Exercises
            ORDER BY RANDOM()
            LIMIT 1;

            -- Insert the favorite exercise for the user
            INSERT INTO Favorites(username, exercisename) 
            VALUES (user_name, random_exercise)
            ON CONFLICT(username, exercisename) DO NOTHING;

        END LOOP;

    END LOOP;
END $$;



--recordkeep table associated subentities table
DO $$
DECLARE
    curr_id INT;
    users_arr VARCHAR(50)[]; 
    exercise_arr VARCHAR[];

    nutrition_items TEXT[] := ARRAY['Chicken breast', 'Banana', 'Spinach salad', 'Grilled salmon', 'Whey protein shake', 'Oatmeal', 'Egg whites', 'Quinoa', 'Greek Yogurt', 'Almonds'];

    health_notes TEXT[] := ARRAY['Weekly weight check', 'Monthly body fat check', 'Daily blood pressure monitoring', 'Checked resting heart rate', 'BMI measurement', 'Tracked daily steps', 'Hydration levels check', 'Post-diet weight check', 'Mental wellness check', 'Flexibility assessment'];

    goal_types_arr TEXT[] := ARRAY['Weight loss', 'Stamina increase', 'Strength gain', 'Flexibility improvement', 'Cardiovascular health', 'Muscle building', 'Endurance training', 'Speed training', 'Balance training', 'Agility training'];

    i INT = 1;

BEGIN
    -- Get the first 10 usernames
    SELECT ARRAY_AGG(username) INTO users_arr FROM Users LIMIT 10;
	SELECT array_agg(exercisename) INTO exercise_arr FROM Exercises;
    WHILE i <= 10 LOOP
        -- HealthRecords
        INSERT INTO RecordKeep (username, note, time) 
        VALUES (users_arr[i], health_notes[i], current_timestamp + i * INTERVAL '1 hour') 
        RETURNING recordid INTO curr_id;

        INSERT INTO HealthRecords (recordid, username, weight, bodyfatpercentage, bloodpressure, restingheartrate) 
        VALUES (curr_id, users_arr[i], 55 + i*2, 18 + i*0.5, 110 + i*2, 60 + i);

        -- WorkoutRecords
        INSERT INTO RecordKeep (username, note, time) 
        VALUES (users_arr[i], 'Workout session', current_timestamp + i * INTERVAL '2 hours') 
        RETURNING recordid INTO curr_id;

        INSERT INTO WorkoutRecordsWorkOnExercises (recordid, username, sets, repitition, weightlifted, exercisename) 
        VALUES (curr_id, users_arr[i], i, 10 + i, 10*i, exercise_arr[(i+2) % 10 + 1]);

        -- NutritionRecords
        INSERT INTO RecordKeep (username, note, time) 
        VALUES (users_arr[i], 'Dietary Log', current_timestamp + i * INTERVAL '3 hours') 
        RETURNING recordid INTO curr_id;

        INSERT INTO NutritionRecords (recordid, username, description, calorie, protein) 
        VALUES (curr_id, users_arr[i], nutrition_items[(i+3) % 10 + 1], 100 + 50*i, 10 + 2*i);

        -- GoalRecords
        INSERT INTO RecordKeep (username, note, time) 
        VALUES (users_arr[i], 'Set a new goal', current_timestamp + i * INTERVAL '4 hours') 
        RETURNING recordid INTO curr_id;

        INSERT INTO GoalRecords (recordid, username, goaltype, targetvalue, deadline) 
        VALUES (curr_id, users_arr[i], goal_types_arr[(i+4) % 10 + 1], 10 + i*5, current_timestamp + (i*10) * INTERVAL '1 day');

        i := i + 1;
    END LOOP;
    
END $$;





--comment table
DO $$
DECLARE
    commenting_user VARCHAR(50);
    record_owner VARCHAR(50);
    target_record_id INT;
    num_comments INT;
    iter INT;
    random_content VARCHAR(255);
    comments_arr TEXT[] := ARRAY['Great progress!', 
                                'Keep it up!', 
                                'Awesome!', 
                                'You are doing well!', 
                                'Nice work!', 
                                'This is impressive!', 
                                'Way to go!', 
                                'Looks promising!', 
                                'Fantastic!', 
                                'Good job!'];
BEGIN
    -- Iterate through each user for commenting
    FOR commenting_user IN (SELECT username FROM Users) LOOP
        -- Random number of comments for each user (e.g., between 1 to 5 comments)
        num_comments := CAST(FLOOR(RANDOM() * 5 + 1) AS INT);

        FOR iter IN 1..num_comments LOOP
            -- Select a random record from another user
            SELECT recordid, username INTO target_record_id, record_owner
            FROM RecordKeep
            WHERE username != commenting_user  -- Ensuring the user comments on another user's record
            ORDER BY RANDOM()
            LIMIT 1;

            -- Randomly select a comment content from the predefined array
            random_content := comments_arr[CAST(FLOOR(RANDOM() * 10 + 1) AS INT)];

            -- Insert the comment
            INSERT INTO CommentsMakeCommentsOn(commentuser, recordid, recorduser, content, time) 
            VALUES (commenting_user, target_record_id, record_owner, random_content, NOW());

        END LOOP;

    END LOOP;
END $$;

-- group table
INSERT INTO Groups (groupname)
    VALUES 
        ('Yoga Enthusiasts'),
        ('Gym Rats'),
        ('Healthy Eating 101'),
        ('Marathon Trainees'),
        ('Mindful Meditation'),
        ('Cycling Club'),
        ('Vegan Warriors'),
        ('Daily HIIT'),
        ('Holistic Health'),
        ('Keto Comrades');

-- userinroup table
DO $$
DECLARE
    curr_user VARCHAR(50);
    num_groups INT;
    random_groups INT[];
BEGIN
    -- Iterate through each user
    FOR curr_user IN (SELECT username FROM Users LIMIT 10) LOOP
        
        -- Randomly decide how many groups a user will join, let's say between 1 to 5
        num_groups := CAST(FLOOR(RANDOM() * 5 + 1) AS INT);
        
        -- Fetch the random group IDs using a subquery to ensure proper limit
        SELECT ARRAY_AGG(sub.groupid) INTO random_groups
        FROM (
            SELECT groupid
            FROM Groups
            ORDER BY RANDOM()
            LIMIT num_groups
        ) AS sub;

        -- Check if the array is not null, then add the user to those groups
        IF random_groups IS NOT NULL THEN
            FOR i IN 1 .. array_length(random_groups, 1) LOOP
                INSERT INTO UsersInGroups (groupid, username)
                VALUES (random_groups[i], curr_user)
                ON CONFLICT(groupid, username) DO NOTHING; -- Prevents inserting duplicates
            END LOOP;
        END IF;

    END LOOP;
END $$;








