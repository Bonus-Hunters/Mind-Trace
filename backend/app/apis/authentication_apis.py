import os
from pathlib import Path
from fastapi import APIRouter, Body
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from core.database import authentication as auth
from core.config_loader import ConfigLoader
from core.database.repos import EmployeesRepository, CompanyRepository
from core.database.postgresDatabase import PostgresDatabase
from core.database.tables_data import Employees, Company


router = APIRouter()
loader = ConfigLoader()
db = PostgresDatabase()


class UserData(BaseModel):
    email: str
    password: str
    name: str


@router.post("/send_otp")
async def send_OTP(data: UserData):
    print(f"BACKEND: email sent: {data.email}")
    valid, otp = auth.send_email(
        loader.get("MIND_TRACE_EMAIL"), data.email, loader.get("MIND_TRACE_PASSWORD")
    )
    if valid:
        return {"otp": otp}
    else:
        return JSONResponse(status_code=500)


@router.post("/register_user")
async def register_user(data: UserData):
    print(f"BACKEND: in register user {data.name} , {data.email}, {data.password}")
    try:
        company_repo = CompanyRepository(db.get_session_maker())
        domain = auth.get_email_domain(data.email)
        """
            let name of company same as domain for now 
            TODO: 
                - 1. let user enter company's name if he's the first to register from that company
                - is there a more practical method? 
        """
        company_data = Company(**{"domain": domain, "name": domain})
        company_id = await company_repo.create(company_data)
        del company_repo
        if company_id is not False:
            employee_repo = EmployeesRepository(db.get_session_maker())
            employee_data = Employees(
                **{
                    "name": data.name,
                    "email": data.email,
                    "password": auth.hash_password(data.password),
                    "company_id": company_id,
                    "role": None,
                    "voice_print": None,
                    "skills": None,
                }
            )
            employee_id = await employee_repo.create(employee_data)
            # del employee_repo
            print(f"BACKEND: {employee_id }")
            print("BACKEND: Employee added to db succ")
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})
