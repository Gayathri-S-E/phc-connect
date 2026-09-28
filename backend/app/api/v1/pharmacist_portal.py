"""
Pharmacist Portal — Role 04
============================
Endpoints for the PHC Pharmacist covering:
  * Dispense Queue         – pending prescriptions with FEFO batch preview
  * Stock Alert Dashboard  – low-stock / shortage-risk medicines at facility
  * Drug Information AI    – bilingual EN+Tamil drug info, interactions, storage
  * Counselling Notes      – record medication counselling given to patient
"""

import uuid
from datetime import date
from typing import List, Optional

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.deps import (
    AuthenticatedUserContext,
    RequestContext,
    get_current_user,
    get_db_session,
    get_request_context,
    require_permission,
)
from app.core.exceptions import BadRequestException, ResourceNotFoundException
from app.core.permissions import SystemPermissions
from app.models.healthcare import (
    Prescription,
    PrescriptionItem,
    PrescriptionStatus,
)
from app.models.pharmacy import BatchStatus, InventoryItem
from app.schemas.common import DataResponse
from app.schemas.pharmacy import (
    DispensingRecordResponse,
    InventoryItemResponse,
)
from app.services.pharmacy_service import PharmacyService

from pydantic import BaseModel, ConfigDict, Field

router = APIRouter(prefix="/pharmacist", tags=["Pharmacist Portal"])


# ============================================================================
# LOCAL SCHEMAS (pharmacist-specific DTOs)
# ============================================================================

class FEFOBatchPreview(BaseModel):
    """First-Expire batch allocation preview shown to pharmacist before dispensing."""
    model_config = ConfigDict(from_attributes=True)

    batch_id: uuid.UUID
    batch_number: str
    expiry_date: date
    available_quantity: int


class PrescriptionQueueItem(BaseModel):
    """Pending prescription in the pharmacist dispense queue."""
    model_config = ConfigDict(from_attributes=True)

    prescription_id: uuid.UUID
    patient_name: str
    patient_identifier: str
    doctor_name: str
    issued_at: str
    item_count: int
    items: List[dict]          # [{ medication_name, qty_prescribed, fefo_batches }]


class StockAlertItem(BaseModel):
    """Medicine running at or below reorder level — needs replenishment."""
    model_config = ConfigDict(from_attributes=True)

    inventory_item_id: uuid.UUID
    medication_id: uuid.UUID
    medication_name: str
    quantity_on_hand: int
    reorder_level: int
    minimum_stock_level: int
    stock_status: str           # LOW_STOCK, SHORTAGE_RISK, OUT_OF_STOCK
    days_of_stock_remaining: Optional[int] = None
    near_expiry_quantity: int = 0  # units expiring within 30 days


class DrugInfoRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    medication_id: uuid.UUID
    query_type: str = Field(
        default="general",
        description=(
            "general | interactions | storage | substitution | counselling_points"
        ),
    )
    co_medications: Optional[List[str]] = Field(
        default=None,
        description="Generic names of co-administered medicines for interaction check",
    )
    patient_condition: Optional[str] = Field(
        default=None,
        description="Relevant comorbidity or condition (e.g. CKD, pregnancy)",
    )


class DrugInfoResponse(BaseModel):
    medication_name: str
    query_type: str
    information_en: str
    information_ta: str          # Tamil translation
    warnings: List[str] = []
    counselling_points_en: List[str] = []
    counselling_points_ta: List[str] = []
    references: List[str] = []


class CounsellingNoteCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    prescription_id: uuid.UUID
    patient_id: uuid.UUID
    counselling_summary: str = Field(min_length=10, max_length=2000)
    language_used: str = Field(default="TAMIL", description="TAMIL | ENGLISH | BILINGUAL")
    patient_understood: bool = True
    follow_up_recommended: bool = False
    follow_up_notes: Optional[str] = None


class CounsellingNoteResponse(BaseModel):
    prescription_id: uuid.UUID
    patient_id: uuid.UUID
    pharmacist_id: uuid.UUID
    counselling_summary: str
    language_used: str
    patient_understood: bool
    follow_up_recommended: bool
    follow_up_notes: Optional[str]
    recorded_at: str


# ---------------------------------------------------------------------------
# Drug knowledge base (embedded Tamil Nadu essential medicines list + TN STG)
# ---------------------------------------------------------------------------

_DRUG_KB: dict = {
    "metformin": {
        "class": "Biguanide antidiabetic",
        "mechanism_en": "Decreases hepatic glucose production and improves insulin sensitivity.",
        "mechanism_ta": "கல்லீரலில் குளுக்கோஸ் உற்பத்தியை குறைக்கிறது மற்றும் இன்சுலின் உணர்திறனை மேம்படுத்துகிறது.",
        "storage_en": "Store below 30°C, protected from moisture.",
        "storage_ta": "30°C க்கும் குறைவான வெப்பநிலையில், ஈரப்பதத்திலிருந்து பாதுகாத்து சேமிக்கவும்.",
        "counselling_en": [
            "Take with or after meals to reduce GI side effects.",
            "Do not skip doses — consistency is key in diabetes management.",
            "Avoid alcohol — increases risk of lactic acidosis.",
            "Monitor for symptoms of hypoglycaemia when combined with other diabetes medicines.",
        ],
        "counselling_ta": [
            "வயிற்று பிரச்சினைகளை குறைக்க உணவுடன் அல்லது உணவிற்கு பிறகு எடுத்துக்கொள்ளுங்கள்.",
            "மருந்தை தவிர்க்காதீர்கள் — சர்க்கரை நோய் கட்டுப்பாட்டிற்கு தொடர்ச்சி முக்கியம்.",
            "மதுவை தவிர்க்கவும் — லாக்டிக் அமிலமேற்றத்தின் அபாயம் அதிகரிக்கும்.",
            "மற்ற நீரிழிவு மருந்துகளுடன் இணைக்கும்போது இரத்தச்சர்க்கரைக் குறைவு அறிகுறிகளை கவனிக்கவும்.",
        ],
        "interactions": {
            "contrast_dye": "HOLD metformin 48 h before and after iodinated contrast — risk of AKI and lactic acidosis.",
            "alcohol": "Increased risk of lactic acidosis.",
            "rifampicin": "May reduce metformin plasma levels.",
        },
        "contraindications": ["eGFR < 30 mL/min", "active liver disease", "lactic acidosis history"],
        "references": ["Tamil Nadu STG Diabetes 2023", "WHO Essential Medicines 23rd List"],
    },
    "amlodipine": {
        "class": "Calcium channel blocker (dihydropyridine)",
        "mechanism_en": "Inhibits calcium influx into vascular smooth muscle, reducing peripheral resistance.",
        "mechanism_ta": "வாஸ்குலர் மென் தசையில் கால்சியம் நுழைவை தடுத்து, புற எதிர்ப்பை குறைக்கிறது.",
        "storage_en": "Store at room temperature (15–30°C).",
        "storage_ta": "அறை வெப்பநிலையில் (15–30°C) சேமிக்கவும்.",
        "counselling_en": [
            "Take at the same time each day — works best with consistent dosing.",
            "Ankle swelling is a common side effect; elevate legs if it occurs.",
            "Do not stop suddenly — BP may rebound.",
            "Grapefruit and grapefruit juice may increase drug levels.",
        ],
        "counselling_ta": [
            "ஒவ்வொரு நாளும் ஒரே நேரத்தில் எடுத்துக்கொள்ளுங்கள்.",
            "கணுக்கால் வீக்கம் பொதுவான பக்க விளைவு — ஏற்பட்டால் கால்களை உயர்த்தி வையுங்கள்.",
            "திடீரென நிறுத்தாதீர்கள் — இரத்த அழுத்தம் திரும்பி வரலாம்.",
            "திராட்சைப்பழம் மற்றும் அதன் சாறு மருந்தின் அளவை அதிகரிக்கலாம்.",
        ],
        "interactions": {
            "simvastatin": "Limit simvastatin to 20 mg/day when combined — myopathy risk.",
            "cyclosporine": "Elevated cyclosporine levels; monitor.",
            "grapefruit": "Avoid — increases amlodipine exposure by up to 40%.",
        },
        "contraindications": ["cardiogenic shock", "severe aortic stenosis", "unstable angina (relative)"],
        "references": ["Tamil Nadu STG Hypertension 2023", "JNC-8 Guidelines"],
    },
    "amoxicillin": {
        "class": "Beta-lactam antibiotic (aminopenicillin)",
        "mechanism_en": "Inhibits bacterial cell wall synthesis by binding to penicillin-binding proteins.",
        "mechanism_ta": "பெனிசிலின்-பிணைப்பு புரதங்களை பிணைத்து பாக்டீரியா செல் சுவர் தொகுப்பை தடுக்கிறது.",
        "storage_en": "Store in a cool, dry place (below 25°C). Reconstituted suspension: refrigerate and use within 7 days.",
        "storage_ta": "குளிர்ந்த, வறண்ட இடத்தில் சேமிக்கவும் (25°C க்கு கீழ்). கலந்த சஸ்பென்ஷன்: குளிர்சாதனப்பெட்டியில் வைத்து 7 நாட்களுக்குள் பயன்படுத்தவும்.",
        "counselling_en": [
            "Complete the full course even if you feel better — prevents resistance.",
            "Take with or without food.",
            "Stop and seek medical advice immediately if rash, hives, or difficulty breathing occurs.",
        ],
        "counselling_ta": [
            "நன்றாக இருந்தாலும் மருந்துகுறியை முழுமையாக எடுத்துக்கொள்ளுங்கள் — எதிர்ப்பை தடுக்கும்.",
            "உணவுடன் அல்லது இல்லாமல் எடுத்துக்கொள்ளலாம்.",
            "தடிப்பு, தோல் எரிச்சல் அல்லது மூச்சுத்திணறல் ஏற்பட்டால் உடனே மருத்துவரை நாடுங்கள்.",
        ],
        "interactions": {
            "warfarin": "May enhance anticoagulant effect; monitor INR.",
            "methotrexate": "Decreased renal excretion — toxicity risk.",
            "oral_contraceptives": "Theoretical reduction in OCP efficacy (clinical significance low).",
        },
        "contraindications": ["penicillin allergy", "infectious mononucleosis (high rash risk)"],
        "references": ["Tamil Nadu STG Respiratory Infections 2023", "WHO AWaRe Classification"],
    },
    "paracetamol": {
        "class": "Analgesic / antipyretic",
        "mechanism_en": "Inhibits prostaglandin synthesis centrally; exact mechanism of analgesia unclear.",
        "mechanism_ta": "மத்திய நரம்பு மண்டலத்தில் புரோஸ்டாக்லாண்டின் தொகுப்பை தடுக்கிறது.",
        "storage_en": "Store at room temperature away from heat and moisture.",
        "storage_ta": "வெப்பம் மற்றும் ஈரப்பதத்திலிருந்து விலகி அறை வெப்பநிலையில் சேமிக்கவும்.",
        "counselling_en": [
            "Do not exceed 4 g/day in adults (3 g/day in elderly or liver disease).",
            "Avoid alcohol — increases risk of liver damage.",
            "Check all medications for hidden paracetamol to avoid accidental overdose.",
        ],
        "counselling_ta": [
            "பெரியவர்களுக்கு ஒரு நாளைக்கு 4 கிராமுக்கு அதிகமாக எடுக்காதீர்கள்.",
            "மதுவை தவிர்க்கவும் — கல்லீரல் பாதிப்பு அபாயம் அதிகரிக்கும்.",
            "தற்செயலான அதிக அளவு தவிர்க்க மற்ற மருந்துகளில் மறைந்துள்ள பாராசிட்டமாலை சரிபாருங்கள்.",
        ],
        "interactions": {
            "warfarin": "High-dose paracetamol may enhance anticoagulant effect.",
            "rifampicin": "May increase hepatotoxic metabolite formation.",
            "isoniazid": "Increased hepatotoxicity risk.",
        },
        "contraindications": ["severe hepatic impairment", "known hypersensitivity"],
        "references": ["Tamil Nadu NEML 2023", "WHO Essential Medicines 23rd List"],
    },
}

_GENERIC_DRUG_INFO = {
    "information_en": (
        "This medication is part of the Tamil Nadu National Essential Medicine List (NEML). "
        "Please consult the Tamil Nadu State Treatment Guidelines (STG) for full dosing and clinical protocols. "
        "Refer to the pharmacy team for patient-specific counselling."
    ),
    "information_ta": (
        "இந்த மருந்து தமிழ்நாடு தேசிய அத்தியாவசிய மருந்து பட்டியலின் (NEML) ஒரு பகுதியாகும். "
        "முழு அளவு மற்றும் மருத்துவ நெறிமுறைகளுக்கு தமிழ்நாடு மாநில சிகிச்சை வழிகாட்டுதல்களை (STG) பார்க்கவும்."
    ),
}


def _lookup_drug(medication_name: str) -> Optional[dict]:
    """Case-insensitive prefix match against embedded knowledge base."""
    normalized = medication_name.lower()
    for key, data in _DRUG_KB.items():
        if normalized.startswith(key) or key in normalized:
            return data
    return None


def _build_drug_info_response(
    medication_name: str,
    query_type: str,
    kb: Optional[dict],
    co_medications: Optional[List[str]],
    patient_condition: Optional[str],
) -> DrugInfoResponse:
    if not kb:
        return DrugInfoResponse(
            medication_name=medication_name,
            query_type=query_type,
            information_en=_GENERIC_DRUG_INFO["information_en"],
            information_ta=_GENERIC_DRUG_INFO["information_ta"],
            warnings=["Detailed drug record not available in local KB. Refer to TN-STG formulary."],
            counselling_points_en=[],
            counselling_points_ta=[],
            references=["Tamil Nadu State Treatment Guidelines 2023"],
        )

    warnings: List[str] = []
    references = kb.get("references", [])

    # Interaction check
    if query_type in ("interactions", "general") and co_medications:
        for co_med in co_medications:
            co_norm = co_med.lower()
            for interaction_key, interaction_msg in kb.get("interactions", {}).items():
                if interaction_key in co_norm or co_norm in interaction_key:
                    warnings.append(f"⚠️ Interaction with {co_med}: {interaction_msg}")

    # Condition-specific warnings
    if patient_condition:
        cond = patient_condition.lower()
        for ci in kb.get("contraindications", []):
            if any(kw in cond for kw in ci.lower().split()):
                warnings.append(f"⚠️ Possible contraindication in patient with '{patient_condition}': {ci}")

    if query_type == "storage":
        info_en = kb.get("storage_en", "No specific storage requirements found.")
        info_ta = kb.get("storage_ta", "குறிப்பிட்ட சேமிப்பு தேவைகள் கிடைக்கவில்லை.")
    elif query_type == "interactions":
        interactions = kb.get("interactions", {})
        info_en = " | ".join(f"{k}: {v}" for k, v in interactions.items()) or "No significant interactions on record."
        info_ta = "தொடர்புகளுக்கான தமிழ் விவரம்: மேலே உள்ள விவரங்களை பார்க்கவும்."
    elif query_type == "substitution":
        info_en = f"{medication_name} is an essential medicine in the TN NEML. Substitution should be guided by a physician."
        info_ta = f"{medication_name} தமிழ்நாடு NEML-ல் ஒரு அத்தியாவசிய மருந்து. மாற்று மருந்து குறித்த முடிவை மருத்துவர் வழிகாட்டல் கொண்டு எடுக்கவும்."
    else:  # general / counselling_points
        info_en = f"[{kb['class']}] {kb.get('mechanism_en', '')}"
        info_ta = f"[{kb['class']}] {kb.get('mechanism_ta', '')}"

    return DrugInfoResponse(
        medication_name=medication_name,
        query_type=query_type,
        information_en=info_en,
        information_ta=info_ta,
        warnings=warnings,
        counselling_points_en=kb.get("counselling_en", []),
        counselling_points_ta=kb.get("counselling_ta", []),
        references=references,
    )


# ============================================================================
# IN-MEMORY COUNSELLING STORE (per-process; replace with DB table in production)
# ============================================================================

_counselling_store: List[dict] = []


# ============================================================================
# ENDPOINTS
# ============================================================================

@router.get(
    "/prescriptions/pending",
    response_model=DataResponse[List[PrescriptionQueueItem]],
    dependencies=[Depends(require_permission(SystemPermissions.PRESCRIPTIONS_DISPENSE))],
    summary="Pharmacist Dispense Queue",
    description=(
        "Returns all ISSUED prescriptions for a facility, ordered by issue time. "
        "Each item includes FEFO batch previews so the pharmacist can plan stock allocation "
        "before confirming dispensing."
    ),
)
async def get_dispense_queue(
    facility_id: uuid.UUID = Query(..., description="Facility UUID to scope the queue"),
    user_ctx: AuthenticatedUserContext = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
):
    """
    Dispense queue: all ISSUED prescriptions with their items and FEFO batch previews.
    Zero stock-leakage guarantee: batch_id is shown only to pharmacist (not patient).
    """
    service = PharmacyService(session)

    # Load ISSUED prescriptions with items + consultation (for doctor name) + patient
    stmt = (
        select(Prescription)
        .where(
            Prescription.facility_id == facility_id,
            Prescription.status == PrescriptionStatus.ISSUED,
        )
        .options(
            selectinload(Prescription.items),
            selectinload(Prescription.patient),
            selectinload(Prescription.doctor),
        )
        .order_by(Prescription.created_at.asc())
    )
    result = await session.execute(stmt)
    prescriptions = result.scalars().all()

    queue: List[PrescriptionQueueItem] = []
    for rx in prescriptions:
        items_preview = []
        for item in rx.items:
            # Find FEFO batches for this medication at this facility
            inv_item = await service.repo.get_inventory_item(
                facility_id=facility_id,
                medication_id=item.medication_id,
            )
            fefo_batches: List[FEFOBatchPreview] = []
            if inv_item:
                usable = sorted(
                    [b for b in inv_item.batches if b.status == BatchStatus.AVAILABLE and b.current_quantity > 0],
                    key=lambda b: (b.expiry_date, b.created_at),
                )
                fefo_batches = [
                    FEFOBatchPreview(
                        batch_id=b.id,
                        batch_number=b.batch_number,
                        expiry_date=b.expiry_date,
                        available_quantity=b.current_quantity,
                    )
                    for b in usable
                ]

            items_preview.append({
                "prescription_item_id": str(item.id),
                "medication_name": item.medication_name,
                "dosage": item.dosage,
                "quantity_prescribed": item.quantity_prescribed,
                "quantity_dispensed": item.quantity_dispensed,
                "quantity_remaining": item.quantity_prescribed - item.quantity_dispensed,
                "status": item.status.value if item.status else "PENDING",
                "fefo_batches": [b.model_dump() for b in fefo_batches],
            })

        patient = rx.patient
        doctor = rx.doctor
        queue.append(
            PrescriptionQueueItem(
                prescription_id=rx.id,
                patient_name=f"{patient.first_name} {patient.last_name}" if patient else "Unknown",
                patient_identifier=patient.patient_identifier if patient else "",
                doctor_name=f"Dr. {doctor.full_name}" if doctor else "Unknown",
                issued_at=rx.created_at.isoformat(),
                item_count=len(rx.items),
                items=items_preview,
            )
        )

    return DataResponse(data=queue)


@router.get(
    "/stock-alerts",
    response_model=DataResponse[List[StockAlertItem]],
    dependencies=[Depends(require_permission(SystemPermissions.INVENTORY_ITEM_READ))],
    summary="Stock Alert Dashboard",
    description=(
        "Returns all medicines at or below reorder level (LOW_STOCK, SHORTAGE_RISK, OUT_OF_STOCK) "
        "for the pharmacist's facility. Also flags near-expiry quantities (≤30 days)."
    ),
)
async def get_stock_alerts(
    facility_id: uuid.UUID = Query(..., description="Facility UUID"),
    user_ctx: AuthenticatedUserContext = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
):
    """Stock alert dashboard — critical medicine shortages and near-expiry items."""
    service = PharmacyService(session)

    # Fetch all inventory items for this facility with low stock
    items, _ = await service.repo.list_inventory_items(
        facility_id=facility_id,
        low_stock_only=True,
        offset=0,
        limit=500,
    )

    today = date.today()
    near_expiry_window = 30  # days

    alerts: List[StockAlertItem] = []
    for inv in items:
        # Compute stock status
        qty = inv.quantity_on_hand
        if qty == 0:
            stock_status = "OUT_OF_STOCK"
        elif qty <= inv.minimum_stock_level:
            stock_status = "SHORTAGE_RISK"
        elif qty <= inv.reorder_level:
            stock_status = "LOW_STOCK"
        else:
            continue  # shouldn't happen given low_stock_only=True

        # Count near-expiry units
        near_expiry_qty = sum(
            b.current_quantity
            for b in inv.batches
            if b.status == BatchStatus.AVAILABLE
            and (b.expiry_date - today).days <= near_expiry_window
        )

        # Rough days-of-stock estimation (not tracked historically — show None if no movement data)
        alerts.append(
            StockAlertItem(
                inventory_item_id=inv.id,
                medication_id=inv.medication_id,
                medication_name=inv.medication.name if inv.medication else "Unknown",
                quantity_on_hand=qty,
                reorder_level=inv.reorder_level,
                minimum_stock_level=inv.minimum_stock_level,
                stock_status=stock_status,
                days_of_stock_remaining=None,
                near_expiry_quantity=near_expiry_qty,
            )
        )

    return DataResponse(data=alerts)


@router.post(
    "/drug-info",
    response_model=DataResponse[DrugInfoResponse],
    dependencies=[Depends(require_permission(SystemPermissions.PRESCRIPTIONS_DISPENSE))],
    summary="Pharmacist Drug Information AI",
    description=(
        "Returns bilingual (English + Tamil) drug information for a medication, including "
        "storage conditions, drug interactions, contraindications, and patient counselling points. "
        "Powered by the embedded Tamil Nadu Essential Medicines Knowledge Base."
    ),
)
async def get_drug_information(
    payload: DrugInfoRequest,
    user_ctx: AuthenticatedUserContext = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
):
    """Drug info AI: bilingual EN+Tamil drug profiles, interaction warnings, counselling points."""
    from app.repositories.healthcare_repository import HealthcareRepository
    health_repo = HealthcareRepository(session)

    med = await health_repo.get_medication_by_id(payload.medication_id)
    if not med:
        raise ResourceNotFoundException("Medication", str(payload.medication_id))

    kb = _lookup_drug(med.name)
    response = _build_drug_info_response(
        medication_name=med.name,
        query_type=payload.query_type,
        kb=kb,
        co_medications=payload.co_medications,
        patient_condition=payload.patient_condition,
    )
    return DataResponse(data=response)


@router.post(
    "/counselling-notes",
    response_model=DataResponse[CounsellingNoteResponse],
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission(SystemPermissions.PRESCRIPTIONS_DISPENSE))],
    summary="Record Medication Counselling Note",
    description=(
        "Records that the pharmacist has counselled the patient on their medications. "
        "Captures language used, comprehension confirmation, and follow-up recommendations."
    ),
)
async def record_counselling_note(
    payload: CounsellingNoteCreate,
    user_ctx: AuthenticatedUserContext = Depends(get_current_user),
    req_ctx: RequestContext = Depends(get_request_context),
    session: AsyncSession = Depends(get_db_session),
):
    """Record a medication counselling note for a dispensed prescription."""
    from datetime import datetime, timezone

    # Validate prescription exists
    service = PharmacyService(session)
    presc = await service.health_repo.get_prescription_by_id(payload.prescription_id)
    if not presc:
        raise ResourceNotFoundException("Prescription", str(payload.prescription_id))

    note = {
        "prescription_id": str(payload.prescription_id),
        "patient_id": str(payload.patient_id),
        "pharmacist_id": str(user_ctx.user.id),
        "counselling_summary": payload.counselling_summary,
        "language_used": payload.language_used,
        "patient_understood": payload.patient_understood,
        "follow_up_recommended": payload.follow_up_recommended,
        "follow_up_notes": payload.follow_up_notes,
        "recorded_at": datetime.now(timezone.utc).isoformat(),
    }
    _counselling_store.append(note)

    return DataResponse(
        data=CounsellingNoteResponse(
            prescription_id=payload.prescription_id,
            patient_id=payload.patient_id,
            pharmacist_id=user_ctx.user.id,
            counselling_summary=payload.counselling_summary,
            language_used=payload.language_used,
            patient_understood=payload.patient_understood,
            follow_up_recommended=payload.follow_up_recommended,
            follow_up_notes=payload.follow_up_notes,
            recorded_at=note["recorded_at"],
        )
    )


@router.get(
    "/counselling-notes/{prescription_id}",
    response_model=DataResponse[List[CounsellingNoteResponse]],
    dependencies=[Depends(require_permission(SystemPermissions.PRESCRIPTIONS_READ))],
    summary="Retrieve Counselling Notes for Prescription",
)
async def get_counselling_notes(
    prescription_id: uuid.UUID,
    user_ctx: AuthenticatedUserContext = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
):
    """Retrieve all counselling notes for a prescription (pharmacist audit trail)."""
    notes = [
        CounsellingNoteResponse(**{
            **n,
            "prescription_id": uuid.UUID(n["prescription_id"]),
            "patient_id": uuid.UUID(n["patient_id"]),
            "pharmacist_id": uuid.UUID(n["pharmacist_id"]),
        })
        for n in _counselling_store
        if n["prescription_id"] == str(prescription_id)
    ]
    return DataResponse(data=notes)
