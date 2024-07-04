import sqlite3

from app.config import settings


# noinspection SqlDialectInspection
def create_table():
    # Create mock data
    # Connect to the SQLite database (or create it if it doesn't exist)
    conn = sqlite3.connect(settings.db_path)

    # Create a cursor object to interact with the database
    cursor = conn.cursor()

    # Create the user_info table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS user_info (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        email TEXT NOT NULL UNIQUE,
        age INTEGER
    )
    ''')

    # Commit the changes and close the connection
    conn.commit()
    conn.close()

    print("Table 'user_info' created successfully.")


# noinspection SqlDialectInspection
def create_user():
    # Connect to the SQLite database
    conn = sqlite3.connect(settings.db_path)
    cursor = conn.cursor()

    # Insert 10 records into the user_info table
    users = [
        ('Alice', 'alice@example.com', 25),
        ('Bob', 'bob@example.com', 30),
        ('Charlie', 'charlie@example.com', 22),
        ('David', 'david@example.com', 28),
        ('Eve', 'eve@example.com', 27),
        ('Frank', 'frank@example.com', 33),
        ('Grace', 'grace@example.com', 24),
        ('Heidi', 'heidi@example.com', 29),
        ('Ivan', 'ivan@example.com', 31),
        ('Judy', 'judy@example.com', 26)
    ]

    cursor.executemany('''
        INSERT INTO user_info (name, email, age)
        VALUES (?, ?, ?)
        ''', users)

    # Commit the changes and close the connection
    conn.commit()
    conn.close()

    print("10 records inserted successfully.")


# noinspection SqlDialectInspection
def get_user_by_id(_user_id):
    # Connect to the SQLite database
    conn = sqlite3.connect(settings.db_path)
    cursor = conn.cursor()

    # Query the user_info table for a record with the specified id
    cursor.execute('SELECT * FROM user_info WHERE id = ?', (_user_id,))
    _user = cursor.fetchone()

    # Get column names
    column_names = [description[0] for description in cursor.description]

    # Close the connection
    conn.close()

    if _user:
        # Convert the record to a dictionary
        user_dict = dict(zip(column_names, _user))
        return user_dict
    else:
        return None

# Step #1: define mock data, after created comment it out.
# create_table()
# create_user()
# print(get_user_by_id(1))
