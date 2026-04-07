from requests import Session
import bcrypt
from fastapi import APIRouter,Depends,HTTPException,status
from services.auth_service.models.user import UserRole_Schemas, User_Schemas
from services.auth_service.database import get_connection
import logging
from services.auth_service.auth.jwt_handler import create_access_token
from services.auth_service.auth.dependencies  import check_token
from datetime import timedelta
from pydantic import BaseModel,Field
import string
import secrets
from datetime import datetime
from typing import Optional
from common.database import insert_teacher_query, select_user_query,delete_user_query,select_one_user_query


router =APIRouter()
logger=logging.getLogger("auth_routes")


async def generate_secure_alphanumeric(conn=None,length=5,):
    # Combines all ASCII letters (a-z, A-Z) and digits (0-9)
    if conn == None:
        raise HTTPException(status_code=500, detail="Database connection error for ID generation")
    async with conn.cursor() as cursor:
      while True:
       characters = string.ascii_letters + string.digits
       # Uses secrets.choice in a loop for secure selection
       user_id_result = ''.join(secrets.choice(characters) for _ in range(length))
       fetchone_result = await select_one_user_query(user_id_result)
       if not fetchone_result :
        return user_id_result
     

    

class Student_InitialSignUp_Request(BaseModel):
    password:str
    user_name:str
    
@router.post("/signup")
async def sign_up(data: Student_InitialSignUp_Request, db=Depends(get_connection)):
    try: 
          conn,cursor,dict_cursor = db
          
          await cursor.execute("select 1 from Users where username = %s",(data.user_name,))
          get_user_check = await cursor.fetchone()
          if not get_user_check:
           generation_user_id= await generate_secure_alphanumeric(conn,)
           student_userid = f"student_{generation_user_id}_MSDI"
           password_bbytes = data.password.encode("utf-8")
           hashed_password = bcrypt.hashpw(password_bbytes, bcrypt.gensalt())
           encode_password = hashed_password.decode("utf-8")

           current_time_stamp = datetime.now().isoformat()

              
           await cursor.execute("Insert into Users (username,role,user_id,password,created_date) values (%s,%s,%s,%s,%s)",
           (data.user_name,UserRole_Schemas.STUDENT.value,student_userid,encode_password,current_time_stamp))
           await conn.commit()
           return {
            "message":f"Signed successfully {data.user_name}",
            "user_id": student_userid
           }
          else:
            raise HTTPException(status_code=400, detail="User already exists with this username...")      

    except Exception as e:
         logger.error(f"Error during signup: {e}")
         raise HTTPException(status_code=500, detail="unthenticated - signup failed")  
    

#login through sso, for student, teacher, higher official teacher, but for admin login through password only, for student, teacher, higher official teacher login through user_id only, based on that user_id the role will be identified and token will be generated with respect to the role and username in the payload of the token, for admin login through password only, if the role is admin then only it will check for password and if password is correct then only token will be generated with respect to the role and username in the payload of the token
class UserLoginRequest(BaseModel):
    user_id:str
    sso_token: Optional[str] = None

@router.post("/login")
async def Userlogin(data: UserLoginRequest,db=Depends(get_connection)):

  try:
         conn,cursor,dict_cursor = db
         await cursor.execute ("Select username, role,user_id from Users where user_id =%s",(data.user_id,))
         sql_insert_query = await cursor.fetchone()
         print("**** sql_insert_query is :",sql_insert_query)
         
         if not sql_insert_query:
             raise HTTPException(status_code=404,detail="User not found")
         
         
         dbdata_username,dbdata_userrole,user_id = sql_insert_query
         print("**** dbdata_username is :",dbdata_username)
         print("**** dbdata_userrole is :",dbdata_userrole)
         if dbdata_userrole.lower() == UserRole_Schemas.STUDENT.value:
          access_token = create_access_token(data={"sub": dbdata_username,"role":UserRole_Schemas.STUDENT.value,"user_id":user_id},expires_delta=timedelta(minutes=15))
         elif dbdata_userrole.lower() == UserRole_Schemas.TEACHER.value:
            access_token = create_access_token(data={"sub": dbdata_username,"role":UserRole_Schemas.TEACHER.value,"user_id":user_id},expires_delta=timedelta(minutes=15))
         elif dbdata_userrole.lower() == UserRole_Schemas.HIGHER_TEACHER.value:
            access_token = create_access_token(data={"sub": dbdata_username,"role":UserRole_Schemas.HIGHER_TEACHER.value,"user_id":user_id},expires_delta=timedelta(minutes=15))   
         elif dbdata_userrole.lower() == UserRole_Schemas.ADMIN.value:
                 raise HTTPException(status_code=403, detail="Admin cannot login here") 
         else:
                raise HTTPException(status_code=401, detail="Invalid credentials check user_id and role properly to login")
         return {
           "access_token": access_token,
           "message": f"Logined successfully : {data.user_id}",
           "username": dbdata_username,
           "role":dbdata_userrole.lower()
        }     
         
  except HTTPException:
    raise
  except Exception as e:
    logger.error(f"Error during login: {e}")
    raise HTTPException(status_code=500, detail="Internal server error")



class AdminLoginRequest(BaseModel):
    password:str=Field(...,min_length=8)
    user_id:str
    
@router.post("/admin/login")
async def admin_login(data : AdminLoginRequest, db=Depends(get_connection)):
     conn,cursor,dict_cursor = db
     await cursor.execute("Select username,role,password from Users where user_id = %s",(data.user_id,))
     sql_user_query = await cursor.fetchone()
     if not sql_user_query:
         raise HTTPException(status_code=404,detail="Admin not found")
     
     dbdata_username,dbdata_userrole,dbdata_password = sql_user_query
     if bcrypt.checkpw(data.password.encode("utf-8"), dbdata_password.encode("utf-8")):
         if dbdata_userrole.lower() == UserRole_Schemas.ADMIN.value:
                    access_token = create_access_token(data={"sub": dbdata_username,"role":UserRole_Schemas.ADMIN.value},expires_delta=timedelta(minutes=15))
                    return {
                        "access_token": access_token,
                        "message": f"Admin Logined successfully {data.user_id}",
                        "username": dbdata_username,
                        "role": dbdata_userrole.lower()
                    }
             
         else:    
             raise HTTPException(status_code=401, detail="Invalid credentials password, please check user_id and role properly to login as admin")

     else:
        raise HTTPException(status_code=403, detail="Only Admin can login here") 
         



class AdminCreateUserRequest(BaseModel):
    role:str
    user_name:str

@router.post("/admin/pre_create_users")
async def admin_create_teacher_accounts(data: AdminCreateUserRequest, db = Depends(get_connection),payload :str = Depends(check_token)):
    """
    Admin can pre-create Teacher and Higher Official Teacher accounts only.
    Admin cannot register students here.
    """
    try:
        conn,cursor,dict_cursor = db
        current_user_role, user_id = payload
        if  current_user_role != UserRole_Schemas.ADMIN.value:
            raise HTTPException(status_code=403, detail="Only Admin can create users")
        
        await cursor.execute("select 1 from Users where username = %s",(data.user_name,))
        get_user_check = await cursor.fetchone()
        if not get_user_check:
            
         # Generate user_id and create user logic here
         generation_user_id = await generate_secure_alphanumeric(conn,)
        
         if data.role.lower() == UserRole_Schemas.TEACHER.value:   #from frontend, for teacher or higher official teacher, from admin end generation, firstly user_role and user_name should be define then only by hitting it, from backend it will be sent, based on that only the user_id will be generated and stored in db with respective role with details
          user_id = f"teacher_{generation_user_id}_MSDI"
          await insert_teacher_query(data.user_name,UserRole_Schemas.TEACHER.value,user_id,User_Schemas.current_time_stamp)
          
       
         elif data.role.lower() == UserRole_Schemas.HIGHER_TEACHER.value:
            user_id = f"higher_official_teacher_{generation_user_id}_MSDI"
            sql_insert_query = "Insert into Users (username,role,user_id,created_date) values (%s,%s,%s,%s)"
            params_tuple = (data.user_name,UserRole_Schemas.HIGHER_TEACHER.value,user_id,User_Schemas.current_time_stamp)
            await cursor.execute(sql_insert_query,params_tuple)
            await conn.commit()
         else:
            raise HTTPException(status_code=400, detail="Admin can only create Teacher or Higher Official Teacher accounts")
        
        else:
            raise HTTPException(status_code=400, detail="User already exists with this username...")
        
        return {"message": f"Admin Gained {user_id} for role {data.role} for the username is {data.user_name}. The User ID is : {user_id}"}
    
    except Exception as e:
        logger.error(f"Error during admin teacher signup: {e}")
        raise HTTPException(status_code=401, detail="Admin signup failed")


# Example: Admin can view/edit teacher,offical teacher data ,student (NOTES: Student profile alone from admin end can't register)
@router.get("/admin/users_view_edit")
async def list_students(db = Depends(get_connection),payload :str = Depends(check_token)):
    conn,cursor,dict_cursor = db
    current_user_role, user_id = payload
    if  current_user_role != UserRole_Schemas.ADMIN.value:
        raise HTTPException(status_code=403, detail="Only Admin can access student list")
    # Query all
    await dict_cursor.execute("SELECT * FROM Users WHERE role = %s", (UserRole_Schemas.TEACHER.value,))
    Teachers = await dict_cursor.fetchall()
    await dict_cursor.execute("SELECT * FROM Users WHERE role = %s", (UserRole_Schemas.HIGHER_TEACHER.value,))
    Official_Teacher = await dict_cursor.fetchall()
    await dict_cursor.execute("SELECT * FROM Users WHERE role = %s", (UserRole_Schemas.STUDENT.value,))
    Students = await dict_cursor.fetchall()

    return {
        "users": Teachers + Official_Teacher + Students
    }
   

    


@router.delete("/admin/{exact_user_id}/delete")
async def delete_account(exact_user_id : str, db = Depends(get_connection), payload :str = Depends(check_token)):
    conn,cursor,dict_cursor = db
    current_user_role, user_id = payload
    if current_user_role != UserRole_Schemas.ADMIN.value:
        raise HTTPException(status_code=403, detail="Only Admin can access student list")
    # Query all students
    
    # await cursor.execute("SELECT user_id FROM Users WHERE user_id = %s", (exact_user_id,))
    # select_result_set = await cursor.fetchone()
    select_result_set = await select_user_query(exact_user_id)
    if not select_result_set:
        raise HTTPException(status_code=404, detail="User not found")
    await delete_user_query(exact_user_id)
    return {"message": f"User_id {exact_user_id} deleted successfully"}


    

          

 

