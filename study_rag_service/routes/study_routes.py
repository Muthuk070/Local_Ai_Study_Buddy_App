import uuid
import sys
import json
import os
import logging
import math
from  study_rag_service.ingestion.file_loader import validate_file
from  study_rag_service.ingestion.file_loader import extract_pdf_content
from  study_rag_service.ingestion.chunker import tiktoken_len
from  study_rag_service.ingestion.chunker import text_splitter
from services.auth_service.database import get_connection
from services.auth_service.models.user import UserRole_Schemas
from study_rag_service.rag.prompt_templates import soft_handle_prompt
from  study_rag_service.vector_db.client import store_chunk
from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException
from study_rag_service.ingestion.chunker import get_model
from study_rag_service.vector_db.client import store_chunk
from services.auth_service.auth.dependencies import check_token
from study_rag_service.vector_db.client import collection
from openai import OpenAI
from study_rag_service.note_quality import page_wise_figures
from study_rag_service.ingestion.file_loader import create_folder
from study_rag_service.ingestion.file_loader import extract_fig_sentences_from_chunks
from study_rag_service.ingestion.file_loader import get_pages_for_small_store
from study_rag_service.rag.prompt_templates import soft_handle_prompt
from study_rag_service.rag.retriever import mysql_cosine_fallback
from common.database import insert_note_record,insert_notes_chunk_record,notes_fetch


# Initialize embedding model once at the module level to avoid reloading it on every request, which can be resource-intensive and lead to performance issues.
embedding_model = get_model()


router = APIRouter()

# GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
# if not GOOGLE_API_KEY:
#     raise RuntimeError("Missing GOOGLE_API_KEY in .env")

# client = genai.Client(api_key=GOOGLE_API_KEY)
# llm_model_name  = os.getenv("GEMINI_MODEL")

client = OpenAI(
    api_key = os.getenv("OPEN_ROUTER_KEY"),
    base_url="https://openrouter.ai/api/v1"
)



def is_general_question(q):
    q = q.lower().strip()
    return q in ["hi", "hello", "hey", "how are you", "what is your name","thanks","thank you"]


def call_llm(context, question, subject, KEYS):
    try:
        prompt = soft_handle_prompt(context, question, subject, KEYS)
        response = client.chat.completions.create(model = os.getenv("OPEN_ROUTER_MODEL"),   
        messages=[{"role": "user","content": prompt}])
        bot_answer = response.choices[0].message.content or "Sorry, I couldn’t generate a response."
        return {"answer": bot_answer}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI Error: {str(e)}")
    




@router.post("/upload_notes")
async def upload_notes(
    class_standard : str = Form (...),
    subject : str = Form(...),
    file : UploadFile = File(...),
    db = Depends(get_connection), payload = Depends(check_token)
):
    
        conn,cursor,dict_cursor = db
        current_user_role, user_id = payload  # Unpack the tuple returned by check_token
        
        teacher_id = user_id
        
        if current_user_role == UserRole_Schemas.TEACHER.value: 
                
                print("Welcome Teacher, you can proceed with uploading the notes for your class and subject")
        else:
                raise HTTPException(status_code=404, detail="Only Teacher can be seen this Dashbaord endpoint site, upon check not found with this user_id for teacher dashboard access, please check the user_id properly to access teacher dashboard")
        
        
        validate_file(file.filename)  #backend validating the file type, whether its valid pdf or not


        # 1. Save and Extract
        try:
         content = await file.read()
         folder_path = create_folder(class_standard, subject)
         file_path = os.path.join(folder_path, file.filename)
         
         with open(file_path, "wb") as f:
          f.write(content)

        except Exception as e:
          raise HTTPException(status_code=500, detail=f"File saving failed: {str(e)}")


        #2. Extracting the raw content from the file and also doing some cleaning to remove unwanted characters and formatting issues that might affect the chunking and embedding generation process, also to ensure that the extracted text is in a suitable format for further processing and storage in the vector database for efficient retrieval during search queries based on user input.
        print("Extracting raw content...")
        raw_text = extract_pdf_content(file_path)
        

       # raw_text = raw_text[:300000]
        
        os.remove(file_path) #removing the temporarily stored file after processing
        
        # 3. Get token for all the extracted +minial cleaned text 
        Y = tiktoken_len(raw_text)
        

        chunks = text_splitter.create_documents([raw_text]) #list of chunks created by the text splitter
        print(f"Total Chunks Created: {len(chunks)}") #each chunks count

        note_id=str(uuid.uuid4())
        subject = subject.lower().strip().replace(" ", "_")
        class_standard = class_standard.lower().strip()

        #     Metadata structure ready for ChromaDB/Pinecone + storing this info in notes_chunks table
        metadata = {
                "class_standard":class_standard,  
                "subject":subject,  
                "teacher_id":teacher_id, 
                "status" : "active",
                "Total_chunks_created": Y
            }
        
        await insert_note_record(note_id, teacher_id, class_standard, subject, metadata['status'],metadata['Total_chunks_created']) 
        # await cursor.execute("Insert into notes (log_id,teacher_id,class_standard,subjects,status,total_chunks_created) values (%s,%s,%s,%s,%s,%s)",
        #     (note_id,teacher_id,class_standard,subject,metadata['status'],metadata['Total_chunks_created']))
        # await conn.commit()
        
        
        # 4. Debug Loop
        for i in range(len(chunks)):
            current_content = chunks[i].page_content 
            print(f"\n{'='*20} CHUNK {i} {'='*20}")
            
            X = tiktoken_len(current_content)
            embeddings = embedding_model.encode(current_content).tolist() #generating the vector embeddings for each chunk
            embedding_json = json.dumps(embeddings)
            
        
            await store_chunk(current_content,embeddings,metadata,note_id,i) #storing the chunk with metadata and embedding in the vector database for efficient retrieval during search queries based on user input and also storing the same in relational database for better organization of the data and also for backup purposes
            await insert_notes_chunk_record (conn,cursor,current_content,embedding_json,Y,len(chunks[i].page_content),X,metadata,note_id) #storing the chunk with metadata and embedding in the vector database for efficient retrieval during search queries based on user input and also storing the same in relational database for better organization of the data and also for backup purposes
        
            if i > 0:
                previous_content = chunks[i-1].page_content
                # Overlap check logic
                prev_tail = previous_content[-100:].strip()
                overlap_found = prev_tail[:100] in current_content
                
                print(f"Overlap Status: {'✅ VALID' if overlap_found else '❌ FAILED'}")
    
        print("final store chunks list: ",store_chunk)  #here i wants to print the final list of chunks with metadata and embeddings that will be sent to the vector database for storage and retrieval of relevant chunks based on the user query and also for better organization of the data in the vector database
    
        return {
                "message":f"Notes Processed successfully"
            }




@router.get("/get_student_study_details") #after students login, the system should show the list of class standards and subjects for which the notes are available for study, so that the student can select the class standard and subject to start studying the notes and also to ask questions to the chatbot based on the selected class standard and subject.
async def student_study(
        db=Depends(get_connection),payload=Depends(check_token)
 ):
    conn,cursor,dict_cursor = db

    # await cursor.execute("""SELECT distinct class_standard, subjects FROM notes WHERE status='active'""")

    # rows = await cursor.fetchall()
    rows = await notes_fetch()  #fetching the data from the database using the function defined in common/database.py to get the available class standards and subjects for which the notes are available for study, so that the student can select the class standard and subject to start studying the notes and also to ask questions to the chatbot based on the selected class standard and subject.

    if not rows:
        raise HTTPException(status_code=404, detail="No data available")

    # ✅ Group data
    result = {}

    for cls, sub in rows:
        if cls not in result:
            result[cls] = []
        if sub not in result[cls]:
            result[cls].append(sub)

    return {
        "available_notes": result
    }





@router.post("/chatbot_ask_questions")
async def chatbot_ask_questions(
     question:str=Form(...),
     class_standard:str=Form(...),
     subject:str=Form(...),
     db=Depends(get_connection),payload=Depends(check_token)):
     
   conn, cursor, dict_cursor = db
   current_user_role, user_id = payload

   print("📂 DB Path exists?")
   print(os.path.exists("./chroma_db"))

   if current_user_role == UserRole_Schemas.STUDENT.value:
    print("✅ Student authorized")
    print("Total docs in DB:", collection.count(),'.....................[]=-')

    # ✅ 1. Handle general questions
    if is_general_question(question):
        return {
        "message": call_llm("", question,"Greetings",[])
    }

    else:
     try:
        # ✅ 2. Convert question → embedding (FIXED)
        question_embedding = embedding_model.encode(question).tolist()
        

        # ✅ 3. Query ChromaDB
        results = collection.query(
        query_embeddings=[question_embedding],
        n_results=3,
        where={
        "$and": [
            {"class_standard": str(class_standard).lower().strip()},
            {"subject": str(subject).lower().strip()}
        ]
    }
)
       # print("🔍 Chroma RAW RESULTS:", results,'./')
       # print("📄 DOCUMENTS:", results.get("documents"))
        #print("📏 DISTANCES:", results.get("distances"))

        
        # ✅ 4. Extract documents safely (FIXED)
        top_chunks = results.get("documents", [[]])[0]
        print("Chroma top_chunks:", top_chunks)


        # ✅ 5. Fallback to DB for cosine similarity search by using cursor if Chroma fails or top chunks is not retrived by Chroma
        if not top_chunks:
         print("⚠️ No results from Chroma → using DB fallback")
            
        # call cosine similarity function, with passing valid arguments and the the threshold. we'll still return the top-K nearest chunks using the threshold limit set
         fallback_chunks = await mysql_cosine_fallback(
                conn,
                dict_cursor,
                question_embedding,
                class_standard,
                subject,
                top_k=3,
                candidate_limit=1000,
                min_similarity=0.65,
                min_results=1,
            )
    
         print()

         if not fallback_chunks:
                return {"message": {"answer": "No relevant content found in notes"}}
            # use DB results as top_chunks
         top_chunks = fallback_chunks
         print("Normal DB vector (cosine similarity search) top chunks:", top_chunks)

        small_store=[]
        small_store = extract_fig_sentences_from_chunks(top_chunks)
        keyss = get_pages_for_small_store(small_store, page_wise_figures)
        print("Matched page keys:", keyss)

        # # ✅ 6. Build context
        context = "\n\n".join(top_chunks)

        print("📚 Retrived Top Context length:", len(context))

        # ✅ 7. Call LLM
        llm_response = call_llm(context, question, subject,keyss)

        return {
            "message": llm_response
        }

     except Exception as e:
        print("❌ ERROR:", str(e))
        raise HTTPException( status_code=500, detail=f"Error processing question: {str(e)}")  
     
   raise HTTPException(status_code=404, detail="Only Student can be seen this Dashbaord endpoint site, upon check not found with this role for student dashboard access, please check the role  properly to access student dashboard")
     
    
    

     












    ##takes for to prompt function calling, to check whether the overall file context is valid or not by checking the threshold. 
    ###text02 = prompt_to_check_threshold(text)
    ###validate_file(file.filename)  #validating the file type

    ####temp_path = await save_temp_file(file) #saving the file by read & writing in a temporarily file creation for processing

    ###if file.filename.endswith(".pdf"):    #cleaning the data by extracting text from the file based on the file type
    ###    text002 = extract_pdf_content(temp_path)

     


    ###if text002 == "" or text002 is None:#threshold is overall above 70% so we can proceed with the teacher upaloded file for chunking & embedding generation and storing in vector db, else we can reject the file and ask for better quality file.
    
        
    