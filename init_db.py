import sqlite3

conn = sqlite3.connect("notes.db")
conn.execute("PRAGMA foreign_keys = ON;")

with open("schema.sql") as f:
    conn.executescript(f.read())

conn.commit()
conn.close()

print("Database intialized successfully")