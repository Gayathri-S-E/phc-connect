from fastapi import APIRouter

from app.api.v1.auth import router as auth_router
from app.api.v1.users import router as users_router
from app.api.v1.roles import router as roles_router
from app.api.v1.facilities import router as facilities_router
from app.api.v1.audit_logs import router as audit_router
from app.api.v1.healthcare import router as healthcare_router
from app.api.v1.patient_portal import router as patient_portal_router
from app.api.v1.doctor_portal import router as doctor_portal_router
from app.api.v1.nurse_portal import router as nurse_portal_router
from app.api.v1.pharmacy import router as pharmacy_router
from app.api.v1.pharmacist_portal import router as pharmacist_portal_router
from app.api.v1.lab_portal import router as lab_portal_router
from app.api.v1.facility_admin_portal import router as facility_admin_portal_router
from app.api.v1.intelligence import router as intelligence_router
from app.api.v1.supply_chain import router as supply_chain_router
from app.api.v1.insights import router as insights_router

api_router = APIRouter(prefix="/api/v1")

api_router.include_router(auth_router)
api_router.include_router(users_router)
api_router.include_router(roles_router)
api_router.include_router(facilities_router)
api_router.include_router(audit_router)
api_router.include_router(patient_portal_router)
api_router.include_router(doctor_portal_router)
api_router.include_router(nurse_portal_router)
api_router.include_router(pharmacist_portal_router)
api_router.include_router(lab_portal_router)
api_router.include_router(facility_admin_portal_router)
api_router.include_router(healthcare_router)
api_router.include_router(pharmacy_router)
api_router.include_router(intelligence_router)
api_router.include_router(supply_chain_router)
api_router.include_router(insights_router)
