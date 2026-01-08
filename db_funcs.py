import mysql.connector
import pandas as pd
import streamlit as st

# Fungsi untuk koneksi database
@st.cache_resource
def init_connection():
    try:
        cnx = mysql.connector.connect(#tambahkan kredensial database Anda di sini
            user='',
            password='',
            host='',
            port='',
            database=''
        )
        return cnx
    except mysql.connector.Error as err:
        st.error(f"Error connecting to MySQL: {err}")
        return None

# Fungsi untuk mendapatkan daftar tabel
def get_tables(connection):
    try:
        cursor = connection.cursor()
        cursor.execute("SHOW TABLES")
        tables = cursor.fetchall()
        cursor.close()
        return [table[0] for table in tables]
    except mysql.connector.Error as err:
        st.error(f"Error getting tables: {err}")
        return []

# Fungsi untuk mendapatkan data dari tabel
def get_table_data(connection, table_name):
    try:
        cursor = connection.cursor()
        cursor.execute(f"SELECT * FROM {table_name}")
        data = cursor.fetchall()
        columns = [desc[0] for desc in cursor.description]
        cursor.close()
        return pd.DataFrame(data, columns=columns)
    except mysql.connector.Error as err:
        st.error(f"Error fetching data from {table_name}: {err}")
        return pd.DataFrame()

# Fungsi untuk menghitung jumlah baris
def get_row_count(connection, table_name):
    try:
        cursor = connection.cursor()
        cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
        count = cursor.fetchone()[0]
        cursor.close()
        return count
    except mysql.connector.Error as err:
        return 0

# New function to get disease details by code
def get_disease_details_by_code(connection, kode_penyakit):
    try:
        cursor = connection.cursor(dictionary=True) # Return rows as dictionaries
        query = "SELECT * FROM disease_details_table WHERE kode_penyakit = %s"
        cursor.execute(query, (kode_penyakit,))
        details = cursor.fetchone()
        cursor.close()
        return details
    except mysql.connector.Error as err:
        st.error(f"Error fetching disease details for {kode_penyakit}: {err}")
        return None

# New function to insert diagnosis as a new case
def insert_new_case_to_db(diagnosis_result, user_answers):
    cnx = init_connection()
    if cnx is None:
        return False

    try:
        cursor = cnx.cursor()

        # 1. Generate unique d_case ID
        cursor.execute("SELECT d_case FROM case_base_table ORDER BY d_case DESC LIMIT 1;")
        last_d_case = cursor.fetchone()

        if last_d_case:
            last_id_num = int(last_d_case[0][1:]) # e.g., 'C100' -> 100
            new_id_num = last_id_num + 1
            new_d_case = f"C{new_id_num:03d}"
        else:
            new_d_case = "C001"

        # 2. Convert user_answers to G01-G21 format (0 or 1)
        symptom_values = []
        for answer in user_answers:
            if answer == 'Ya':
                symptom_values.append(1)
            elif answer == 'Tidak':
                symptom_values.append(0)
            else:
                symptom_values.append(0) # Treat 'Tidak Diketahui' as 0 for insertion

        # Ensure we have 21 symptom values (G01 to G21)
        if len(symptom_values) != 21:
            st.error(f"Unexpected number of symptom answers: {len(symptom_values)}. Expected 21.")
            return False

        # 3. Construct INSERT statement
        penyakit_code = diagnosis_result['kode_penyakit']

        cols = ['d_case', 'penyakit'] + [f'G{i:02d}' for i in range(1, 22)]
        placeholders = ', '.join(['%s'] * len(cols))
        columns_str = ', '.join(cols)

        insert_query = f"""
        INSERT INTO case_base_table ({columns_str})
        VALUES ({placeholders})
        """

        values_to_insert = [new_d_case, penyakit_code] + symptom_values

        # 4. Execute INSERT statement
        cursor.execute(insert_query, tuple(values_to_insert))
        cnx.commit()
        return True

    except Exception as e:
        st.error(f"An error occurred during case insertion: {e}")
        return False
    finally:
        if cnx and cnx.is_connected():
            cnx.close()
