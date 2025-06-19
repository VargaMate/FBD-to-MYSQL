import fdb
import mysql.connector

fb_path = 'Your path to the fbd file'

fb_conn = fdb.connect(
    dsn=f'localhost:{fb_path}',
    user='SYSDBA',
    password='masterkey'
)
fb_cursor = fb_conn.cursor()

mysql_conn = mysql.connector.connect(
    host='127.0.0.1',
    user='root',
    password='',
    database='database_name'
)
mysql_cursor = mysql_conn.cursor()

fb_cursor.execute("""
    SELECT RDB$RELATION_NAME
    FROM RDB$RELATIONS
    WHERE RDB$SYSTEM_FLAG = 0 AND RDB$VIEW_BLR IS NULL
""")
tables = [row[0].strip() for row in fb_cursor.fetchall()]

for table in tables:
    try:
        fb_cursor.execute(f"SELECT * FROM {table} ROWS 1")  # Get structure
        columns = [desc[0].strip() for desc in fb_cursor.description]
        types = [desc[1].__name__ for desc in fb_cursor.description]

        mysql_types = []
        for t in types:
            if 'int' in t:
                mysql_types.append('INT')
            elif 'str' in t or 'bytes' in t:
                mysql_types.append('VARCHAR(255)')
            elif 'float' in t or 'decimal' in t:
                mysql_types.append('FLOAT')
            elif 'date' in t or 'time' in t:
                mysql_types.append('DATETIME')
            else:
                mysql_types.append('TEXT')

        create_sql = f"CREATE TABLE IF NOT EXISTS {table} (" + ", ".join([
            f"`{columns[i]}` {mysql_types[i]}" for i in range(len(columns))
        ]) + ") CHARACTER SET utf8mb4"

        mysql_cursor.execute(create_sql)

        # Copy all data
        fb_cursor.execute(f"SELECT * FROM {table}")
        insert_sql = f"INSERT INTO {table} ({', '.join(columns)}) VALUES ({', '.join(['%s'] * len(columns))})"
        for row in fb_cursor.fetchall():
            mysql_cursor.execute(insert_sql, row)
        mysql_conn.commit()
        print(f"✅ Created and copied: {table}")

    except Exception as e:
        print(f"❌ Failed: {table} — {e}")

fb_cursor.close()
mysql_cursor.close()
fb_conn.close()
mysql_conn.close()
