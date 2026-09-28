import asyncio
import os
import sys
import uuid
from typing import Dict, List, Set

# Ensure backend root is on sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from sqlalchemy import select
from app.core.database import AsyncSessionLocal, Base, engine
from app.core.permissions import SystemPermissions
from app.core.security import get_password_hash
from app.models.facility import Facility, FacilityType
from app.models.identity import Permission, Role, RolePermission, ScopeLevel, User, UserRole
from app.models.organization import Organization, OrganizationType

# Baseline Role Definitions
ROLES_CONFIG = [
    {
        "code": "SUPER_ADMIN",
        "name": "Super Administrator",
        "description": "Platform root authority with access to all governance, configurations, and operations.",
        "permissions": SystemPermissions.all_permissions(),
    },
    {
        "code": "SYSTEM_ADMIN",
        "name": "System Administrator",
        "description": "Administrative authority for user provisioning, facilities, and dynamic RBAC.",
        "permissions": {
            SystemPermissions.IDENTITY_USER_CREATE,
            SystemPermissions.IDENTITY_USER_READ,
            SystemPermissions.IDENTITY_USER_UPDATE,
            SystemPermissions.IDENTITY_USER_DEACTIVATE,
            SystemPermissions.IDENTITY_ROLE_ASSIGN,
            SystemPermissions.IDENTITY_ROLE_MANAGE,
            SystemPermissions.IDENTITY_FACILITY_MANAGE,
            SystemPermissions.AUDIT_LOG_READ,
            SystemPermissions.SYSTEM_CONFIG_MANAGE,
            SystemPermissions.ALERTS_READ,
            SystemPermissions.ALERTS_ACKNOWLEDGE,
        },
    },
    {
        "code": "AUDITOR",
        "name": "Compliance & Security Auditor",
        "description": "Read-only access to audit logs, security telemetry, and compliance reports.",
        "permissions": {
            SystemPermissions.AUDIT_LOG_READ,
            SystemPermissions.IDENTITY_USER_READ,
            SystemPermissions.INVENTORY_ITEM_READ,
            SystemPermissions.PROCUREMENT_ORDER_READ,
            SystemPermissions.SHIPMENTS_READ,
        },
    },
    {
        "code": "DOCTOR",
        "name": "Medical Officer",
        "description": "Primary healthcare physician conducting consultations, writing prescriptions, and ordering lab tests.",
        "permissions": {
            SystemPermissions.PATIENTS_PROFILE_READ,
            SystemPermissions.PATIENTS_RECORDS_READ,
            SystemPermissions.APPOINTMENTS_VIEW,
            SystemPermissions.CONSULTATIONS_CONDUCT,
            SystemPermissions.PRESCRIPTIONS_CREATE,
            SystemPermissions.PRESCRIPTIONS_READ,
            SystemPermissions.LABS_ORDER_CREATE,
            SystemPermissions.LABS_ORDER_READ,
            SystemPermissions.INVENTORY_ITEM_READ,
            SystemPermissions.DASHBOARDS_CLINICAL_VIEW,
            SystemPermissions.ALERTS_READ,
        },
    },
    {
        "code": "NURSE",
        "name": "Clinical Nurse / Triage Staff",
        "description": "Triage vitals recording, patient intake, appointment roster management.",
        "permissions": {
            SystemPermissions.PATIENTS_PROFILE_CREATE,
            SystemPermissions.PATIENTS_PROFILE_READ,
            SystemPermissions.PATIENTS_PROFILE_UPDATE,
            SystemPermissions.PATIENTS_VITALS_RECORD,
            SystemPermissions.APPOINTMENTS_MANAGE,
            SystemPermissions.APPOINTMENTS_VIEW,
            SystemPermissions.PRESCRIPTIONS_READ,
            SystemPermissions.INVENTORY_ITEM_READ,
            SystemPermissions.ALERTS_READ,
        },
    },
    {
        "code": "PHARMACIST",
        "name": "Pharmacist / Dispensary Officer",
        "description": "Medication dispensing, FEFO batch allocation, and facility inventory management.",
        "permissions": {
            SystemPermissions.PRESCRIPTIONS_READ,
            SystemPermissions.PRESCRIPTIONS_DISPENSE,
            SystemPermissions.INVENTORY_ITEM_READ,
            SystemPermissions.INVENTORY_ITEM_CREATE,
            SystemPermissions.INVENTORY_STOCK_ADJUST,
            SystemPermissions.INVENTORY_MOVEMENT_RECORD,
            SystemPermissions.INVENTORY_TRANSFER_REQUEST,
            SystemPermissions.SHORTAGES_INCIDENT_REPORT,
            SystemPermissions.ALERTS_READ,
        },
    },
    {
        "code": "LAB_TECHNICIAN",
        "name": "Laboratory Technician",
        "description": "Performs laboratory diagnostic tests and records results.",
        "permissions": {
            SystemPermissions.LABS_ORDER_READ,
            SystemPermissions.LABS_RESULT_RECORD,
            SystemPermissions.LABS_RESULT_VERIFY,
            SystemPermissions.PATIENTS_PROFILE_READ,
        },
    },
    {
        "code": "INVENTORY_OFFICER",
        "name": "Facility Storekeeper",
        "description": "Warehouse receipts, physical count adjustments, stock movements, and transfer requests.",
        "permissions": {
            SystemPermissions.INVENTORY_ITEM_READ,
            SystemPermissions.INVENTORY_ITEM_CREATE,
            SystemPermissions.INVENTORY_STOCK_ADJUST,
            SystemPermissions.INVENTORY_MOVEMENT_RECORD,
            SystemPermissions.INVENTORY_TRANSFER_REQUEST,
            SystemPermissions.INVENTORY_TRANSFER_RECEIVE,
            SystemPermissions.SHORTAGES_INCIDENT_REPORT,
            SystemPermissions.ALERTS_READ,
            SystemPermissions.DASHBOARDS_SUPPLY_VIEW,
        },
    },
    {
        "code": "DISTRICT_SUPPLY_OFFICER",
        "name": "District Supply Chain Officer",
        "description": "Approves inter-facility transfers, monitors district shortages, and issues requisitions.",
        "permissions": {
            SystemPermissions.INVENTORY_ITEM_READ,
            SystemPermissions.INVENTORY_TRANSFER_APPROVE,
            SystemPermissions.INVENTORY_TRANSFER_DISPATCH,
            SystemPermissions.PROCUREMENT_REQUEST_CREATE,
            SystemPermissions.PROCUREMENT_REQUEST_APPROVE,
            SystemPermissions.SHORTAGES_INCIDENT_ESCALATE,
            SystemPermissions.SHORTAGES_INCIDENT_RESOLVE,
            SystemPermissions.SHIPMENTS_READ,
            SystemPermissions.DASHBOARDS_SUPPLY_VIEW,
            SystemPermissions.AI_FORECAST_VIEW,
            SystemPermissions.AI_RISK_ANALYZE,
            SystemPermissions.ALERTS_READ,
            SystemPermissions.ALERTS_ACKNOWLEDGE,
        },
    },
    {
        "code": "PATIENT",
        "name": "Citizen / Patient",
        "description": "Personal health portal access for clinical history, appointments, feedback, and AI wellness.",
        "permissions": {
            SystemPermissions.PATIENTS_PROFILE_READ,
            SystemPermissions.PATIENTS_PROFILE_UPDATE,
            SystemPermissions.PATIENTS_RECORDS_READ,
            SystemPermissions.APPOINTMENTS_VIEW,
            SystemPermissions.PRESCRIPTIONS_READ,
            SystemPermissions.PATIENTS_FEEDBACK_SUBMIT,
            SystemPermissions.PATIENTS_FEEDBACK_READ,
            SystemPermissions.PATIENTS_AWARENESS_READ,
            SystemPermissions.PATIENTS_AI_WELLNESS_CHAT,
            SystemPermissions.PATIENTS_NOTIFICATIONS_READ,
        },
    },
]


async def seed_data():
    print("Beginning database seeding...")
    async with AsyncSessionLocal() as session:
        # 1. Seed Permissions
        print("Seeding canonical permissions...")
        db_perms: Dict[str, Permission] = {}
        for code in SystemPermissions.all_permissions():
            stmt = select(Permission).where(Permission.code == code)
            res = await session.execute(stmt)
            existing = res.scalar_one_or_none()
            if not existing:
                parts = code.split(".")
                mod = parts[0] if len(parts) > 0 else "general"
                res_name = parts[1] if len(parts) > 1 else "resource"
                act = parts[2] if len(parts) > 2 else "action"

                perm = Permission(
                    code=code,
                    module=mod,
                    resource=res_name,
                    action=act,
                    description=f"Permission to {act} on {res_name} in module {mod}.",
                    is_active=True,
                )
                session.add(perm)
                await session.flush()
                db_perms[code] = perm
            else:
                db_perms[code] = existing

        # 2. Seed Roles and map Permissions
        print("Seeding approved roles and role-permission mappings...")
        for r_conf in ROLES_CONFIG:
            stmt = select(Role).where(Role.code == r_conf["code"])
            res = await session.execute(stmt)
            role = res.scalar_one_or_none()
            if not role:
                role = Role(
                    name=r_conf["name"],
                    code=r_conf["code"],
                    description=r_conf["description"],
                    is_system=True,
                    is_active=True,
                )
                session.add(role)
                await session.flush()

            # Assign permissions
            for perm_code in r_conf["permissions"]:
                perm_obj = db_perms.get(perm_code)
                if perm_obj:
                    check_rp = select(RolePermission).where(
                        RolePermission.role_id == role.id,
                        RolePermission.permission_id == perm_obj.id,
                    )
                    rp_res = await session.execute(check_rp)
                    if not rp_res.scalar_one_or_none():
                        rp = RolePermission(role_id=role.id, permission_id=perm_obj.id)
                        session.add(rp)
            await session.flush()

        # 3. Seed Sample Organization & Facilities
        print("Seeding initial Organization and PHC Facilities...")
        org_code = "TN-DPH-01"
        stmt = select(Organization).where(Organization.code == org_code)
        res = await session.execute(stmt)
        org = res.scalar_one_or_none()
        if not org:
            org = Organization(
                name="Department of Public Health & Preventive Medicine",
                code=org_code,
                org_type=OrganizationType.STATE_HEALTH_DEPT,
                is_active=True,
            )
            session.add(org)
            await session.flush()

        # Sample PHC 1
        phc_code = "PHC-KOV-001"
        stmt = select(Facility).where(Facility.code == phc_code)
        res = await session.execute(stmt)
        phc1 = res.scalar_one_or_none()
        if not phc1:
            phc1 = Facility(
                organization_id=org.id,
                name="Primary Health Centre Kovalam",
                code=phc_code,
                facility_type=FacilityType.PHC,
                state="Tamil Nadu",
                district="Chengalpattu",
                address="East Coast Road, Kovalam",
                latitude=12.7915,
                longitude=80.2520,
                is_active=True,
            )
            session.add(phc1)
            await session.flush()

        # Additional PHCs for Discovery
        sample_facilities = [
            {
                "code": "PHC-KEL-002",
                "name": "Primary Health Centre Kelambakkam",
                "facility_type": FacilityType.PHC,
                "state": "Tamil Nadu",
                "district": "Chengalpattu",
                "address": "OMR Main Road, Kelambakkam",
                "latitude": 12.7842,
                "longitude": 80.2215,
            },
            {
                "code": "CHC-WAL-003",
                "name": "Community Health Centre Walajabad",
                "facility_type": FacilityType.CHC,
                "state": "Tamil Nadu",
                "district": "Kanchipuram",
                "address": "Bazaar Street, Walajabad",
                "latitude": 12.7958,
                "longitude": 79.8164,
            },
            {
                "code": "PHC-MAH-004",
                "name": "Primary Health Centre Mahabalipuram",
                "facility_type": FacilityType.PHC,
                "state": "Tamil Nadu",
                "district": "Chengalpattu",
                "address": "Five Rathas Road, Mahabalipuram",
                "latitude": 12.6269,
                "longitude": 80.1927,
            },
        ]
        for f_data in sample_facilities:
            stmt = select(Facility).where(Facility.code == f_data["code"])
            res = await session.execute(stmt)
            if not res.scalar_one_or_none():
                fac_obj = Facility(
                    organization_id=org.id,
                    name=f_data["name"],
                    code=f_data["code"],
                    facility_type=f_data["facility_type"],
                    state=f_data["state"],
                    district=f_data["district"],
                    address=f_data["address"],
                    latitude=f_data["latitude"],
                    longitude=f_data["longitude"],
                    is_active=True,
                )
                session.add(fac_obj)
        await session.flush()

        # 4. Seed Bilingual Health Awareness Slides
        print("Seeding Health Awareness & Motivational Slides (English & Tamil)...")
        from app.models.healthcare import HealthAwarenessSlide
        sample_slides = [
            {
                "category": "EXERCISE",
                "title_en": "Daily Physical Activity & Walking",
                "title_ta": "தினசரி உடற்பயிற்சி மற்றும் நடைப்பயிற்சி",
                "tip_en": "Aim for at least 30 minutes of brisk walking every day to protect your heart and regulate blood sugar.",
                "tip_ta": "இதய ஆரோக்கியத்திற்கும் சர்க்கரை அளவை கட்டுப்படுத்தவும் தினமும் 30 நிமிடங்கள் விறுவிறுப்பாக நடக்கவும்.",
                "motivation_en": "Small daily steps lead to lifelong vitality and disease prevention!",
                "motivation_ta": "தினசரி சிறு முயற்சிகளே வாழ்நாள் ஆரோக்கியத்திற்கும் நோய் தடுப்பிற்கும் வழிவகுக்கும்!",
                "action_en": "Start with a 15-minute morning walk and gradually increase your pace.",
                "action_ta": "காலையில் 15 நிமிட நடைப்பயிற்சியுடன் தொடங்கி படிப்படியாக நேரத்தை அதிகரிக்கவும்.",
                "image_key": "exercise_walk",
                "display_order": 1,
            },
            {
                "category": "NUTRITION",
                "title_en": "Balanced Nutrition & Fresh Produce",
                "title_ta": "சமச்சீர் உணவு மற்றும் காய்கறிகள்",
                "tip_en": "Fill half your plate with colorful vegetables, greens, and lentils while cutting down refined sugars and fried snacks.",
                "tip_ta": "உங்கள் உணவில் சரிபாதி காய்கறிகள், கீரைகள் மற்றும் பயறு வகைகளை சேர்த்து, எண்ணெய் பலகாரங்களை குறைக்கவும்.",
                "motivation_en": "Nutritious food is your strongest daily medicine.",
                "motivation_ta": "சத்தான உணவே உங்கள் உடலின் சிறந்த பாதுகாப்பு கவசம்.",
                "action_en": "Incorporate traditional millets (ragi, kambu) and seasonal greens into your meals.",
                "action_ta": "பாரம்பரிய சிறுதானியங்கள் மற்றும் கீரைகளை தினசரி உணவில் சேர்த்துக் கொள்ளுங்கள்.",
                "image_key": "nutrition_plate",
                "display_order": 2,
            },
            {
                "category": "HYDRATION_SLEEP",
                "title_en": "Hydration & Restful Sleep",
                "title_ta": "உடல் நீரேற்றம் மற்றும் சீரான தூக்கம்",
                "tip_en": "Drink 2.5 to 3 liters of boiled/filtered water daily and ensure 7-8 hours of uninterrupted night sleep.",
                "tip_ta": "தினமும் 2.5 முதல் 3 லிட்டர் காய்ச்சி வடிகட்டிய தண்ணீர் குடிக்கவும், 7-8 மணி நேரம் நிம்மதியாக தூங்கவும்.",
                "motivation_en": "A well-rested, hydrated body heals and recovers faster.",
                "motivation_ta": "போதுமான தூக்கமும் நீரேற்றமும் உடலை புத்துணர்ச்சியுடனும் நோயின்றியும் வைக்கும்.",
                "action_en": "Keep a water bottle nearby and switch off screens 30 minutes before bedtime.",
                "action_ta": "தூங்குவதற்கு 30 நிமிடங்களுக்கு முன் மொபைல் திரைகளைப் பார்ப்பதைத் தவிர்க்கவும்.",
                "image_key": "hydration_sleep",
                "display_order": 3,
            },
            {
                "category": "MENTAL_WELLNESS",
                "title_en": "Mental Wellbeing & Stress Relief",
                "title_ta": "மன அமைதி மற்றும் மன அழுத்த மேலாண்மை",
                "tip_en": "Practice 10 minutes of deep breathing, meditation, or spending time in nature every day.",
                "tip_ta": "தினமும் 10 நிமிடங்கள் மூச்சுப்பயிற்சி அல்லது தியானம் செய்து மனதை அமைதியாக வையுங்கள்.",
                "motivation_en": "Peace of mind is the foundation of whole-body wellness.",
                "motivation_ta": "மன அமைதியே முழுமையான உடல் ஆரோக்கியத்தின் அடித்தளம்.",
                "action_en": "Take conscious slow deep breaths whenever you feel tense.",
                "action_ta": "மன அழுத்தம் ஏற்படும் போது மெதுவாக ஆழமாக மூச்சை இழுத்து விடவும்.",
                "image_key": "mental_peace",
                "display_order": 4,
            },
            {
                "category": "HYGIENE",
                "title_en": "Hand Hygiene & Disease Prevention",
                "title_ta": "கை சுகாதாரம் மற்றும் நோய் தடுப்பு",
                "tip_en": "Wash your hands thoroughly with soap for 20 seconds before meals and after coming from outdoors.",
                "tip_ta": "உணவருந்துவதற்கு முன்பும், வெளியில் இருந்து வந்த பிறகும் கைகளை சோப்பினால் 20 வினாடிகள் கழுவவும்.",
                "motivation_en": "Clean hands save lives and keep your family safe from infections.",
                "motivation_ta": "சுத்தமான கைகளே தொற்று நோய்களிலிருந்து உங்கள் குடும்பத்தைக் காக்கும்.",
                "action_en": "Carry a pocket sanitizer and maintain clean personal hygiene.",
                "action_ta": "சுகாதாரமான பழக்கவழக்கங்களை தினசரி பழக்கமாக்கிக் கொள்ளுங்கள்.",
                "image_key": "hygiene_wash",
                "display_order": 5,
            },
            {
                "category": "DISEASE_PREVENTION",
                "title_en": "Chronic Care: Diabetes & Hypertension",
                "title_ta": "நீரிழிவு மற்றும் ரத்த அழுத்த மேலாண்மை",
                "tip_en": "Get your blood pressure and blood sugar checked every 3 months at your local PHC free of charge.",
                "tip_ta": "உங்கள் அருகிலுள்ள PHC-யில் 3 மாதங்களுக்கு ஒருமுறை இலவசமாக ரத்த அழுத்தம் மற்றும் சர்க்கரை பரிசோதனை செய்து கொள்ளுங்கள்.",
                "motivation_en": "Early detection prevents long-term heart, kidney, and eye complications.",
                "motivation_ta": "ஆரம்பகால பரிசோதனை இதய மற்றும் சிறுநீரக கோளாறுகளை முற்றிலும் தடுக்கும்.",
                "action_en": "Book a routine wellness checkup at your nearest Primary Health Centre today.",
                "action_ta": "இன்றே உங்கள் ஆரம்ப சுகாதார நிலையத்தில் வழக்கமான மருத்துவ பரிசோதனைக்கு பதிவு செய்யுங்கள்.",
                "image_key": "chronic_care",
                "display_order": 6,
            },
            {
                "category": "VACCINATION",
                "title_en": "Preventive Immunization & Vaccines",
                "title_ta": "தடுப்பூசி மற்றும் நோய் எதிர்ப்பு சக்தி",
                "tip_en": "Keep childhood, pregnancy, and seasonal immunization schedules up to date at your nearest PHC.",
                "tip_ta": "குழந்தைகள் மற்றும் கர்ப்பிணிகளுக்கான அனைத்து அரசு தடுப்பூசிகளையும் குறித்த காலத்தில் போட்டுக் கொள்ளுங்கள்.",
                "motivation_en": "Vaccines provide lifelong shield against dangerous infectious diseases.",
                "motivation_ta": "தடுப்பூசிகள் தொற்று நோய்களுக்கு எதிரான வாழ்நாள் கவசமாகும்.",
                "action_en": "Check your family's immunization records at the PHC nursing desk.",
                "action_ta": "PHC செவிலியரிடம் உங்கள் குடும்பத்தின் தடுப்பூசி அட்டவணையை சரிபார்க்கவும்.",
                "image_key": "vaccine_shield",
                "display_order": 7,
            },
            {
                "category": "WARNING_SIGNS",
                "title_en": "Warning Signs: When to Visit PHC",
                "title_ta": "எச்சரிக்கை அறிகுறிகள்: எப்போது மருத்துவரை அணுக வேண்டும்?",
                "tip_en": "Persistent high fever, severe breathlessness, sudden chest heaviness, or unhealed wounds require prompt medical evaluation.",
                "tip_ta": "தொடர் காய்ச்சல், மூச்சுத்திணறல், நெஞ்சு வலி அல்லது ஆறாத புண்கள் இருந்தால் உடனடியாக மருத்துவரை அணுகவும்.",
                "motivation_en": "Do not ignore warning signs — timely medical care saves lives.",
                "motivation_ta": "அறிகுறிகளை அலட்சியப்படுத்தாதீர்கள் — சரியான நேர சிகிச்சை உயிரைக் காக்கும்.",
                "action_en": "Visit your PHC Doctor immediately or call 108 in case of emergencies.",
                "action_ta": "அவசர காலத்தில் உடனடியாக PHC-க்கு செல்லவும் அல்லது 108 ஆம்புலன்ஸை அழைக்கவும்.",
                "image_key": "warning_signs",
                "display_order": 8,
            },
        ]
        for slide_data in sample_slides:
            stmt = select(HealthAwarenessSlide).where(HealthAwarenessSlide.category == slide_data["category"])
            res = await session.execute(stmt)
            if not res.scalar_one_or_none():
                slide_obj = HealthAwarenessSlide(**slide_data)
                session.add(slide_obj)
        await session.flush()

        # 5. Seed Root Administrator (Configured via env or fallback for local dev)
        admin_email = os.getenv("INITIAL_ADMIN_EMAIL", "superadmin@smarthealth.gov.in")
        admin_pass = os.getenv("INITIAL_ADMIN_PASSWORD", "SuperAdmin@2026!Secure")

        stmt = select(User).where(User.email == admin_email)
        res = await session.execute(stmt)
        admin_user = res.scalar_one_or_none()
        if not admin_user:
            print(f"Creating root administrator: {admin_email}")
            admin_user = User(
                email=admin_email,
                hashed_password=get_password_hash(admin_pass),
                full_name="National System Administrator",
                phone_number="+919876543210",
                organization_id=org.id,
                facility_id=phc1.id,
                is_active=True,
                is_verified=True,
            )
            session.add(admin_user)
            await session.flush()

            # Assign SUPER_ADMIN role with GLOBAL scope
            stmt = select(Role).where(Role.code == "SUPER_ADMIN")
            res = await session.execute(stmt)
            super_role = res.scalar_one()

            user_role = UserRole(
                user_id=admin_user.id,
                role_id=super_role.id,
                organization_id=org.id,
                facility_id=phc1.id,
                scope_level=ScopeLevel.GLOBAL,
            )
            session.add(user_role)
            await session.flush()

        await session.commit()
        print("Database seeding completed successfully.")


if __name__ == "__main__":
    asyncio.run(seed_data())

