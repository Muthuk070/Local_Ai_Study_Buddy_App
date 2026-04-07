import json
import chromadb

client = chromadb.PersistentClient(path="./chroma_db")

collection = client.get_or_create_collection("study_notes")


async def store_chunk(chunk, embedding, metadata, note_id,i):

    chunk_id = f"{note_id}_{i}"
    collection.add(
        documents=[chunk],
        embeddings=[embedding],
        ids=[chunk_id],
        metadatas=[metadata]
    )
    




# async def stored_chunk(conn,cursor,chunk,embedding,total_tokens,extracted_input_chunk_size,extracted_input_token_length,
#                        metadata_payload,note_id):
    
    
#     if isinstance (metadata_payload,dict):
#         metadata_payload = json.dumps(metadata_payload)

#         await cursor.execute("INSERT INTO notes_chunks (note_id,chunk_text,embedding,metadata_payload,extracted_input_chunk_size,extracted_input_token_length,total_tokens) values (%s,%s,%s,%s,%s,%s,%s)",
#                         (note_id,chunk,embedding,metadata_payload,extracted_input_chunk_size,extracted_input_token_length,total_tokens))
#         await conn.commit()
    


