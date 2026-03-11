import sqlite3
import os

def export_database_to_sql(sqlite_db_path, output_sql_path):
    """Export SQLite database to SQL file that can be used with other databases"""
    
    # Connect to SQLite database
    conn = sqlite3.connect(sqlite_db_path)
    cursor = conn.cursor()
    
    # Get all table names
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    
    with open(output_sql_path, 'w', encoding='utf-8') as sql_file:
        sql_file.write("-- Exported from SQLite database\n")
        sql_file.write("-- Generated on {}\n\n".format(str(__import__('datetime').datetime.now())))
        
        for table in tables:
            table_name = table[0]
            
            # Skip SQLite system tables
            if table_name.startswith('sqlite_'):
                continue
                
            # Get table info to recreate table structure
            cursor.execute(f"PRAGMA table_info({table_name});")
            columns_info = cursor.fetchall()
            
            # Write CREATE TABLE statement
            sql_file.write(f"-- Create table {table_name}\n")
            sql_file.write(f"DROP TABLE IF EXISTS `{table_name}`;\n")
            
            # Build column definitions
            column_defs = []
            for col_info in columns_info:
                col_name = col_info[1]
                col_type = col_info[2]
                not_null = "NOT NULL" if col_info[3] == 1 else ""
                primary_key = "PRIMARY KEY" if col_info[5] == 1 else ""
                
                # Convert SQLite types to MySQL/PostgreSQL compatible types
                if 'INTEGER' in col_type.upper() and 'PRIMARY KEY' in primary_key:
                    col_type = "INT AUTO_INCREMENT"  # MySQL auto-increment
                    # Or use SERIAL for PostgreSQL
                
                column_def = f"`{col_name}` {col_type} {not_null} {primary_key}".strip()
                column_defs.append(column_def)
            
            # Write the CREATE TABLE statement
            sql_file.write(f"CREATE TABLE `{table_name}` (\n")
            sql_file.write("  " + ",\n  ".join(column_defs))
            sql_file.write("\n);\n\n")
            
            # Write INSERT statements for data
            cursor.execute(f"SELECT * FROM {table_name};")
            rows = cursor.fetchall()
            
            if rows:
                # Get column names
                column_names = [description[0] for description in cursor.description]
                
                sql_file.write(f"-- Insert data into {table_name}\n")
                for row in rows:
                    # Prepare values, handling strings and NULL values
                    values = []
                    for i, val in enumerate(row):
                        if val is None:
                            values.append('NULL')
                        elif isinstance(val, str):
                            # Escape single quotes in strings
                            escaped_val = val.replace("'", "''")
                            values.append(f"'{escaped_val}'")
                        else:
                            values.append(str(val))
                    
                    sql_file.write(f"INSERT INTO `{table_name}` ({', '.join([f'`{name}`' for name in column_names])}) VALUES ({', '.join(values)});\n")
                
                sql_file.write("\n")
    
    conn.close()
    print(f"Database exported to {output_sql_path}")

# Export the current database
export_database_to_sql('society.db', 'society_export.sql')