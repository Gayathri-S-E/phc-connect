import uuid
from datetime import date, datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field

from app.models.healthcare import (
    AppointmentStatus,
    AttendanceStatus,
    ComplaintStatus,
    ConsultationStatus,
    DiagnosisType,
    LabOrderStatus,
    PrescriptionItemStatus,
    PrescriptionStatus,
    ReferralStatus,
    ReferralUrgency,
)


# --- Patient Schemas ---
class PatientCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    first_name: str = Field(min_length=1, max_length=100)
    last_name: str = Field(min_length=1, max_length=100)
    date_of_birth: date
    gender: str = Field(min_length=1, max_length=20)
    phone_number: str = Field(min_length=5, max_length=50)
    primary_facility_id: uuid.UUID
    blood_group: Optional[str] = Field(default=None, max_length=10)
    address: Optional[str] = None
    emergency_contact_name: Optional[str] = Field(default=None, max_length=100)
    emergency_contact_phone: Optional[str] = Field(default=None, max_length=50)
    emergency_contact_relation: Optional[str] = Field(default=None, max_length=50)
    preferred_language: Optional[str] = Field(default="en", max_length=10)
    chronic_conditions: Optional[str] = None
    allergies: Optional[str] = None
    user_id: Optional[uuid.UUID] = None


class PatientUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    first_name: Optional[str] = Field(default=None, min_length=1, max_length=100)
    last_name: Optional[str] = Field(default=None, min_length=1, max_length=100)
    phone_number: Optional[str] = Field(default=None, min_length=5, max_length=50)
    address: Optional[str] = None
    emergency_contact_name: Optional[str] = Field(default=None, max_length=100)
    emergency_contact_phone: Optional[str] = Field(default=None, max_length=50)
    emergency_contact_relation: Optional[str] = Field(default=None, max_length=50)
    preferred_language: Optional[str] = Field(default=None, max_length=10)
    chronic_conditions: Optional[str] = None
    allergies: Optional[str] = None
    is_active: Optional[bool] = None


class PatientResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    patient_identifier: str
    first_name: str
    last_name: str
    date_of_birth: date
    gender: str
    phone_number: str
    primary_facility_id: uuid.UUID
    blood_group: Optional[str] = None
    address: Optional[str] = None
    emergency_contact_name: Optional[str] = None
    emergency_contact_phone: Optional[str] = None
    emergency_contact_relation: Optional[str] = None
    preferred_language: str = "en"
    chronic_conditions: Optional[str] = None
    allergies: Optional[str] = None
    is_active: bool
    created_at: datetime
    updated_at: datetime


# --- Appointment Schemas ---
class AppointmentCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    patient_id: uuid.UUID
    facility_id: uuid.UUID
    doctor_id: Optional[uuid.UUID] = None
    appointment_date: datetime
    reason: str = Field(min_length=2)
    priority: Optional[str] = Field(default="ROUTINE", max_length=20)
    time_slot: Optional[str] = Field(default=None, max_length=50)


class AppointmentStatusUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: AppointmentStatus
    cancellation_reason: Optional[str] = None


class AppointmentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    patient_id: uuid.UUID
    facility_id: uuid.UUID
    doctor_id: Optional[uuid.UUID] = None
    token_number: Optional[int] = None
    priority: str = "ROUTINE"
    time_slot: Optional[str] = None
    appointment_date: datetime
    status: AppointmentStatus
    reason: str
    cancellation_reason: Optional[str] = None
    created_at: datetime
    updated_at: datetime


# --- Vitals & Diagnosis Schemas ---
class TriageVitals(BaseModel):
    systolic_bp: Optional[int] = Field(default=None, ge=40, le=300)
    diastolic_bp: Optional[int] = Field(default=None, ge=20, le=200)
    pulse_rate: Optional[int] = Field(default=None, ge=30, le=250)
    temperature_celsius: Optional[float] = Field(default=None, ge=30.0, le=45.0)
    respiratory_rate: Optional[int] = Field(default=None, ge=5, le=60)
    spo2_percent: Optional[int] = Field(default=None, ge=50, le=100)
    weight_kg: Optional[float] = Field(default=None, ge=0.5, le=500.0)
    height_cm: Optional[float] = Field(default=None, ge=20.0, le=300.0)


class VitalsCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    systolic_bp: Optional[int] = Field(default=None, ge=40, le=300)
    diastolic_bp: Optional[int] = Field(default=None, ge=20, le=200)
    pulse_rate: Optional[int] = Field(default=None, ge=30, le=250)
    temperature_celsius: Optional[float] = Field(default=None, ge=30.0, le=45.0)
    respiratory_rate: Optional[int] = Field(default=None, ge=5, le=60)
    spo2_percent: Optional[int] = Field(default=None, ge=50, le=100)
    weight_kg: Optional[float] = Field(default=None, ge=0.5, le=500.0)
    height_cm: Optional[float] = Field(default=None, ge=20.0, le=300.0)
    triage_level: Optional[str] = Field(default="ROUTINE", max_length=20)
    triage_notes: Optional[str] = None


class VitalsResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    consultation_id: uuid.UUID
    systolic_bp: Optional[int] = None
    diastolic_bp: Optional[int] = None
    pulse_rate: Optional[int] = None
    temperature_celsius: Optional[float] = None
    respiratory_rate: Optional[int] = None
    spo2_percent: Optional[int] = None
    weight_kg: Optional[float] = None
    height_cm: Optional[float] = None
    bmi: Optional[float] = None
    triage_level: Optional[str] = "ROUTINE"
    triage_notes: Optional[str] = None
    recorded_by_id: uuid.UUID
    recorded_at: datetime
    created_at: datetime


class ClinicalAmendmentCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    amendment_reason: str = Field(min_length=3)
    amendment_notes: str = Field(min_length=3)


class ClinicalAmendmentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    consultation_id: uuid.UUID
    amendment_reason: str
    amendment_notes: str
    amended_by_id: uuid.UUID
    created_at: datetime


class MedicationCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    generic_name: str = Field(min_length=2, max_length=255)
    brand_name: Optional[str] = Field(default=None, max_length=255)
    strength: str = Field(min_length=1, max_length=100)
    dosage_form: str = Field(min_length=1, max_length=100)
    route: str = Field(min_length=1, max_length=100)
    unit: str = Field(min_length=1, max_length=50)


class MedicationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    generic_name: str
    brand_name: Optional[str] = None
    strength: str
    dosage_form: str
    route: str
    unit: str
    is_active: bool
    created_at: datetime


class DiagnosisCodeResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    code: str
    description: str
    category: str
    version: str
    is_active: bool


class DiagnosisCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    icd10_code: str = Field(min_length=2, max_length=20)
    condition_name: str = Field(min_length=2, max_length=255)
    diagnosis_type: DiagnosisType = DiagnosisType.PRIMARY
    notes: Optional[str] = None


class DiagnosisResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    consultation_id: uuid.UUID
    patient_id: uuid.UUID
    icd10_code: str
    condition_name: str
    diagnosis_type: DiagnosisType
    notes: Optional[str] = None
    created_at: datetime


# --- Prescription Schemas ---
class PrescriptionItemCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    medication_name: str = Field(min_length=2, max_length=255)
    medication_code: Optional[str] = Field(default=None, max_length=100)
    medication_id: Optional[uuid.UUID] = None
    dosage: str = Field(min_length=1, max_length=100)
    frequency: str = Field(min_length=1, max_length=100)
    duration_days: int = Field(ge=1, le=365)
    quantity_prescribed: int = Field(ge=1)
    instructions: Optional[str] = None


class PrescriptionItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    prescription_id: uuid.UUID
    medication_name: str
    medication_code: Optional[str] = None
    medication_id: Optional[uuid.UUID] = None
    dosage: str
    frequency: str
    duration_days: int
    quantity_prescribed: int
    quantity_dispensed: int
    instructions: Optional[str] = None
    status: PrescriptionItemStatus



class PrescriptionCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    consultation_id: uuid.UUID
    notes: Optional[str] = None
    items: List[PrescriptionItemCreate] = Field(min_length=1)


class PrescriptionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    consultation_id: uuid.UUID
    patient_id: uuid.UUID
    doctor_id: uuid.UUID
    facility_id: uuid.UUID
    status: PrescriptionStatus
    notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    items: List[PrescriptionItemResponse] = []


class PrescriptionDispenseRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    dispensed_items: Dict[uuid.UUID, int] = Field(
        description="Map of prescription_item_id to quantity dispensed"
    )


# --- Lab Schemas ---
class LabOrderCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    consultation_id: uuid.UUID
    test_category: str = Field(min_length=2, max_length=100)
    clinical_notes: Optional[str] = None


class LabResultCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    test_name: str = Field(min_length=2, max_length=255)
    result_value: str = Field(min_length=1, max_length=255)
    reference_range: Optional[str] = Field(default=None, max_length=100)
    unit: Optional[str] = Field(default=None, max_length=50)
    is_abnormal: bool = False
    notes: Optional[str] = None


class LabResultResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    lab_order_id: uuid.UUID
    test_name: str
    result_value: str
    reference_range: Optional[str] = None
    unit: Optional[str] = None
    is_abnormal: bool
    critical_alert: Optional[str] = None
    performed_by_id: uuid.UUID
    verified_by_id: Optional[uuid.UUID] = None
    notes: Optional[str] = None
    verified_at: Optional[datetime] = None
    created_at: datetime


class LabOrderResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    consultation_id: uuid.UUID
    patient_id: uuid.UUID
    ordered_by_doctor_id: uuid.UUID
    facility_id: uuid.UUID
    test_category: str
    clinical_notes: Optional[str] = None
    sample_type: Optional[str] = None
    sample_barcode: Optional[str] = None
    sample_collected_at: Optional[datetime] = None
    status: LabOrderStatus
    ordered_at: datetime
    completed_at: Optional[datetime] = None
    created_at: datetime
    results: List[LabResultResponse] = []


# --- Referral Schemas ---
class ReferralCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    consultation_id: uuid.UUID
    to_facility_name: str = Field(min_length=2, max_length=255)
    to_facility_id: Optional[uuid.UUID] = None
    referral_reason: str = Field(min_length=2)
    urgency: ReferralUrgency = ReferralUrgency.ROUTINE
    clinical_summary: Optional[str] = None


class ReferralStatusUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: ReferralStatus


class ReferralResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    consultation_id: uuid.UUID
    patient_id: uuid.UUID
    from_facility_id: uuid.UUID
    to_facility_id: Optional[uuid.UUID] = None
    to_facility_name: str
    referral_reason: str
    urgency: ReferralUrgency
    clinical_summary: Optional[str] = None
    status: ReferralStatus
    referred_by_doctor_id: uuid.UUID
    created_at: datetime
    updated_at: datetime


# --- Consultation Schemas ---
class ConsultationCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    patient_id: Optional[uuid.UUID] = None
    appointment_id: Optional[uuid.UUID] = None
    chief_complaint: str = Field(min_length=2)
    triage_vitals: Optional[TriageVitals] = None
    clinical_notes: Optional[str] = None
    examination_findings: Optional[str] = None


class ConsultationFinalizeRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    clinical_notes: Optional[str] = None
    examination_findings: Optional[str] = None
    diagnoses: Optional[List[DiagnosisCreate]] = None


class ConsultationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    appointment_id: Optional[uuid.UUID] = None
    patient_id: uuid.UUID
    doctor_id: uuid.UUID
    facility_id: uuid.UUID
    status: ConsultationStatus
    triage_vitals: Optional[Dict[str, Any]] = None
    chief_complaint: str
    clinical_notes: Optional[str] = None
    examination_findings: Optional[str] = None
    started_at: datetime
    finalized_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    diagnoses: List[DiagnosisResponse] = []
    prescriptions: List[PrescriptionResponse] = []
    lab_orders: List[LabOrderResponse] = []
    referrals: List[ReferralResponse] = []
    vitals_records: List[VitalsResponse] = []
    amendments: List[ClinicalAmendmentResponse] = []



# --- Comprehensive Clinical History ---
class ClinicalHistoryResponse(BaseModel):
    patient: PatientResponse
    consultations: List[ConsultationResponse]


# --- Feedback & Complaints ---
class FeedbackComplaintCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    category: str = Field(min_length=2, max_length=50)  # "SERVICE", "FACILITY", "APPOINTMENT", "MEDICINE", "OTHER"
    subject: str = Field(min_length=2, max_length=200)
    description: str = Field(min_length=5)
    facility_id: Optional[uuid.UUID] = None


class FeedbackComplaintStatusUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: ComplaintStatus
    resolution_notes: Optional[str] = None


class FeedbackComplaintResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    tracking_number: str
    patient_id: uuid.UUID
    facility_id: Optional[uuid.UUID] = None
    category: str
    subject: str
    description: str
    status: ComplaintStatus
    resolution_notes: Optional[str] = None
    resolved_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime


# --- In-App Notifications ---
class PatientNotificationCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    patient_id: uuid.UUID
    title_en: str = Field(min_length=1, max_length=200)
    title_ta: str = Field(min_length=1, max_length=200)
    message_en: str = Field(min_length=1)
    message_ta: str = Field(min_length=1)
    notification_type: str = Field(default="INFO", max_length=50)
    reference_id: Optional[str] = None


class PatientNotificationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    patient_id: uuid.UUID
    title_en: str
    title_ta: str
    message_en: str
    message_ta: str
    notification_type: str
    is_read: bool
    reference_id: Optional[str] = None
    created_at: datetime


# --- Health Awareness Slides ---
class HealthAwarenessSlideResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    category: str
    title_en: str
    title_ta: str
    tip_en: str
    tip_ta: str
    motivation_en: str
    motivation_ta: str
    action_en: str
    action_ta: str
    image_key: Optional[str] = None
    display_order: int
    is_active: bool


# --- Patient-Facing Medicine Fulfillment ---
class PatientPrescriptionFulfillmentItem(BaseModel):
    id: uuid.UUID
    medication_name: str
    dosage: str
    frequency: str
    duration_days: int
    quantity_prescribed: int
    fulfillment_status: str  # "PROCESSING", "READY_FOR_COLLECTION", "PARTIALLY_AVAILABLE", "TEMPORARILY_UNAVAILABLE", "COLLECTED"
    instructions: Optional[str] = None


class PatientPrescriptionFulfillmentResponse(BaseModel):
    id: uuid.UUID
    consultation_id: uuid.UUID
    prescription_date: datetime
    facility_name: str
    doctor_name: str
    notes: Optional[str] = None
    overall_status: str
    items: List[PatientPrescriptionFulfillmentItem] = []


# --- Patient AI Wellness Assistant ---
class PatientWellnessChatRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    message: str = Field(min_length=1, max_length=2000)
    language: Optional[str] = Field(default="en", max_length=10)  # "en" or "ta"
    conversation_id: Optional[str] = None


class PatientWellnessChatResponse(BaseModel):
    reply: str
    language: str
    is_emergency_warning: bool = False
    suggested_phc_action: Optional[str] = None
    disclaimer: str
    suggested_questions: List[str] = []


# --- Staff Duty Attendance Schemas ---
class StaffAttendanceCheckIn(BaseModel):
    model_config = ConfigDict(extra="forbid")

    facility_id: Optional[uuid.UUID] = None
    shift: Optional[str] = Field(default="GENERAL", max_length=50)
    notes: Optional[str] = None


class StaffAttendanceCheckOut(BaseModel):
    model_config = ConfigDict(extra="forbid")

    notes: Optional[str] = None


class StaffAttendanceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    user_id: uuid.UUID
    facility_id: uuid.UUID
    attendance_date: date
    check_in_time: datetime
    check_out_time: Optional[datetime] = None
    status: AttendanceStatus
    shift: str
    notes: Optional[str] = None
    created_at: datetime


# --- Doctor OPD Queue & Clinical Advisory ---
class DoctorOPDQueueItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    appointment_id: uuid.UUID
    patient_id: uuid.UUID
    patient_name: str
    uhid: str
    gender: str
    age_years: int
    token_number: int
    priority: str
    time_slot: Optional[str] = None
    status: AppointmentStatus
    appointment_date: datetime
    reason: str
    latest_vitals: Optional[VitalsResponse] = None


class DoctorClinicalAdvisoryRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    icd10_code: Optional[str] = Field(default=None, max_length=20)
    condition_name: Optional[str] = Field(default=None, max_length=255)
    proposed_medications: List[str] = Field(default_factory=list)
    patient_allergies: Optional[str] = None
    patient_chronic_conditions: Optional[str] = None
    language: Optional[str] = Field(default="en", max_length=10)


class DoctorClinicalAdvisoryResponse(BaseModel):
    condition: str
    stg_protocol: str
    recommended_drugs: List[str] = []
    contraindication_warnings: List[str] = []
    interaction_alerts: List[str] = []
    monitoring_parameters: List[str] = []
    patient_counseling_points: List[str] = []
    language: str
    disclaimer: str


# --- Nurse Immunization & Triage Guidance ---
class NurseImmunizationGuidanceRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    patient_age_months: Optional[int] = Field(default=None, ge=0, le=240)
    is_pregnant: bool = False
    gestational_weeks: Optional[int] = Field(default=None, ge=1, le=44)
    language: Optional[str] = Field(default="en", max_length=10)


class NurseImmunizationGuidanceResponse(BaseModel):
    category: str
    due_vaccines: List[str] = []
    upcoming_vaccines: List[str] = []
    anc_milestone_guidance: Optional[str] = None
    triage_red_flags: List[str] = []
    cold_chain_reminder: str
    language: str


# --- Lab Technician & Pathologist Portal Schemas ---
class LabSampleCollectRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    sample_type: str = Field(min_length=2, max_length=100)
    sample_barcode: Optional[str] = Field(default=None, max_length=100)
    collection_notes: Optional[str] = None


class LabWorklistItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    consultation_id: uuid.UUID
    patient_id: uuid.UUID
    patient_name: str
    patient_identifier: str
    age: Optional[int] = None
    gender: Optional[str] = None
    doctor_name: str
    test_category: str
    clinical_notes: Optional[str] = None
    sample_type: Optional[str] = None
    sample_barcode: Optional[str] = None
    sample_collected_at: Optional[datetime] = None
    status: LabOrderStatus
    ordered_at: datetime
    results: List[LabResultResponse] = []
    has_critical_alert: bool = False


class LabPanelResultItem(BaseModel):
    model_config = ConfigDict(extra="forbid")

    test_name: str = Field(min_length=2, max_length=255)
    result_value: str = Field(min_length=1, max_length=255)
    reference_range: Optional[str] = Field(default=None, max_length=100)
    unit: Optional[str] = Field(default=None, max_length=50)
    is_abnormal: bool = False
    notes: Optional[str] = None


class LabPanelResultCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    results: List[LabPanelResultItem] = Field(min_length=1)


class LabDiagnosticGuidanceRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    test_name: str = Field(min_length=2, max_length=255)
    result_value: str = Field(min_length=1, max_length=255)
    patient_age: Optional[int] = Field(default=None, ge=0, le=150)
    patient_gender: Optional[str] = None
    is_pregnant: bool = False
    language: Optional[str] = Field(default="en", max_length=10)


class LabDiagnosticGuidanceResponse(BaseModel):
    test_name: str
    result_value: str
    interpretation_en: str
    interpretation_ta: str
    is_critical: bool = False
    critical_alert_en: Optional[str] = None
    critical_alert_ta: Optional[str] = None
    action_guidance_en: str
    action_guidance_ta: str
    reporting_mandate: Optional[str] = None
    references: List[str] = []


# ===========================================================================
# ROLE 06 — FACILITY ADMIN / MPHS PORTAL SCHEMAS
# ===========================================================================

class ColdChainEquipmentCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    equipment_type: str = Field(min_length=2, max_length=50, description="ILR, DEEP_FREEZER, COLD_BOX, etc.")
    serial_number: str = Field(min_length=3, max_length=100)
    model_name: str = Field(min_length=2, max_length=100)
    min_temp_c: float = Field(default=2.0)
    max_temp_c: float = Field(default=8.0)


class ColdChainEquipmentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    facility_id: uuid.UUID
    equipment_type: str
    serial_number: str
    model_name: str
    min_temp_c: float
    max_temp_c: float
    current_temp_c: Optional[float] = None
    last_logged_at: Optional[datetime] = None
    is_functional: bool
    is_temperature_in_range: bool
    created_at: datetime


class ColdChainLogCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    temperature_c: float
    excursion_reason: Optional[str] = None
    notes: Optional[str] = None


class ColdChainLogResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    equipment_id: uuid.UUID
    temperature_c: float
    is_excursion: bool
    excursion_reason: Optional[str] = None
    notes: Optional[str] = None
    recorded_at: datetime
    created_at: datetime


class OutreachCampCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    camp_name: str = Field(min_length=3, max_length=200)
    target_village: str = Field(min_length=2, max_length=100)
    scheduled_date: date
    supervisor_id: Optional[uuid.UUID] = None
    target_beneficiaries: int = Field(default=50, ge=1)
    notes: Optional[str] = None


class OutreachCampResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    facility_id: uuid.UUID
    camp_name: str
    target_village: str
    scheduled_date: date
    supervisor_id: Optional[uuid.UUID] = None
    status: str
    target_beneficiaries: int
    actual_beneficiaries_served: int
    notes: Optional[str] = None
    created_at: datetime


class OutreachCampUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: Optional[str] = None
    actual_beneficiaries_served: Optional[int] = Field(default=None, ge=0)
    notes: Optional[str] = None


class StaffAttendanceSummaryItem(BaseModel):
    user_id: uuid.UUID
    full_name: str
    role_code: str
    present_days: int
    half_days: int
    absent_days: int
    on_leave_days: int
    on_duty_camp_days: int
    attendance_rate_percent: float


class FacilityReportResponse(BaseModel):
    facility_id: uuid.UUID
    facility_name: str
    report_month: int
    report_year: int
    total_opd_patients: int
    total_consultations: int
    total_prescriptions_issued: int
    total_lab_tests_ordered: int
    total_lab_tests_completed: int
    total_referrals: int
    total_staff: int
    staff_attendance_rate_percent: float
    cold_chain_excursions: int
    outreach_camps_scheduled: int
    outreach_camps_completed: int
    beneficiaries_served: int
    grievances_received: int
    grievances_resolved: int
    grievance_resolution_rate_percent: float
