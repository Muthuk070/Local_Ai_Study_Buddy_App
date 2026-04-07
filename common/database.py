from services.auth_service.database import get_connection_ctx
import json


async def select_user_query(exact_user_id):
    async with get_connection_ctx() as (conn, cursor, dict_cursor):
        await cursor.execute("SELECT user_id FROM Users WHERE user_id = %s", (exact_user_id,))
        select_result_set = await cursor.fetchone()
        return select_result_set


async def delete_user_query(exact_user_id):
    async with get_connection_ctx() as (conn, cursor, dict_cursor):
        await cursor.execute("DELETE from Users where user_id =%s",(exact_user_id,))  
        await conn.commit()


async def select_one_user_query(user_id_result):
    async with get_connection_ctx() as (conn, cursor, dict_cursor):
        await cursor.execute("select 1 from Users where user_id = %s",(user_id_result,))
        fetchone_result = await cursor.fetchone()
        return fetchone_result


async def insert_teacher_query(user_name,role,user_id,time_stamp):
    async with get_connection_ctx() as (conn, cursor, dict_cursor):
        await cursor.execute("Insert into Users (username,role,user_id,created_date) values (%s,%s,%s,%s)",
       (user_name,role,user_id,time_stamp) )
        await conn.commit()



# SQL constant for inserting into `notes`.
async def insert_note_record(note_id, teacher_id, class_standard, subject, status, total_chunks_created):
        async with get_connection_ctx() as (conn, cursor, dict_cursor):
            await cursor.execute("Insert into notes (log_id,teacher_id,class_standard,subjects,status,total_chunks_created) values (%s,%s,%s,%s,%s,%s)",
                (note_id,teacher_id,class_standard,subject,status,total_chunks_created))
            await conn.commit()


# SQL constant for inserting into `notes_chunks`.
async def insert_notes_chunk_record (conn,cursor,chunk,embedding,total_tokens,extracted_input_chunk_size,extracted_input_token_length,
                       metadata_payload,note_id):
    
    if isinstance (metadata_payload,dict):
        metadata_payload = json.dumps(metadata_payload)

        await cursor.execute("INSERT INTO notes_chunks (note_id,chunk_text,embedding,metadata_payload,extracted_input_chunk_size,extracted_input_token_length,total_tokens) values (%s,%s,%s,%s,%s,%s,%s)",
                        (note_id,chunk,embedding,metadata_payload,extracted_input_chunk_size,extracted_input_token_length,total_tokens))
        await conn.commit()


async def notes_fetch():
    async with get_connection_ctx() as (conn, cursor, dict_cursor):
        await cursor.execute("""SELECT distinct class_standard, subjects FROM notes WHERE status='active'""")
        rows = await cursor.fetchall()
        return rows      




       
