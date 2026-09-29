import random
import secrets
import uuid
from datetime import date, datetime, timezone
from typing import Dict, List, Optional, Sequence, Tuple
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import BadRequestException, ConflictException, PermissionDeniedException, ResourceNotFoundException
from app.models.healthcare import (
    Appointment,
    AppointmentStatus,
    AttendanceStatus,
    ClinicalAmendment,
    ComplaintStatus,
    Consultation,
    ConsultationStatus,
    Diagnosis,
    DiagnosisCode,
    FeedbackComplaint,
    HealthAwarenessSlide,
    LabOrder,
    LabOrderStatus,
    LabResult,
    Medication,
    Patient,
    PatientNotification,
    Prescription,
    PrescriptionItem,
    PrescriptionItemStatus,
    PrescriptionStatus,
    Referral,
    ReferralStatus,
    StaffAttendance,
    Vitals,
)
from app.repositories.audit_repository import AuditRepository
from app.repositories.facility_repository import FacilityRepository
from app.repositories.healthcare_repository import HealthcareRepository
from app.schemas.healthcare import (
    AppointmentCreate,
    AppointmentStatusUpdate,
    ClinicalAmendmentCreate,
    ClinicalHistoryResponse,
    ConsultationCreate,
    ConsultationFinalizeRequest,
    ConsultationResponse,
    DiagnosisCreate,
    DoctorClinicalAdvisoryRequest,
    DoctorClinicalAdvisoryResponse,
    DoctorOPDQueueItem,
    FeedbackComplaintCreate,
    FeedbackComplaintResponse,
    FeedbackComplaintStatusUpdate,
    HealthAwarenessSlideResponse,
    LabDiagnosticGuidanceRequest,
    LabDiagnosticGuidanceResponse,
    LabOrderCreate,
    LabPanelResultCreate,
    LabPanelResultItem,
    LabResultCreate,
    LabSampleCollectRequest,
    LabWorklistItem,
    MedicationCreate,
    NurseImmunizationGuidanceRequest,
    NurseImmunizationGuidanceResponse,
    PatientCreate,
    PatientNotificationCreate,
    PatientNotificationResponse,
    PatientPrescriptionFulfillmentItem,
    PatientPrescriptionFulfillmentResponse,
    PatientResponse,
    PatientUpdate,
    PatientWellnessChatRequest,
    PatientWellnessChatResponse,
    PrescriptionCreate,
    PrescriptionDispenseRequest,
    ReferralCreate,
    ReferralStatusUpdate,
    StaffAttendanceCheckIn,
    StaffAttendanceCheckOut,
    StaffAttendanceResponse,
    VitalsCreate,
    VitalsResponse,
)


def _generate_patient_identifier() -> str:
    now = datetime.now(timezone.utc)
    rand_suffix = f"{secrets.randbelow(900000) + 100000}"
    return f"PAT-{now.strftime('%Y%m')}-{rand_suffix}"


class HealthcareService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.repo = HealthcareRepository(session)
        self.facility_repo = FacilityRepository(session)
        self.audit_repo = AuditRepository(session)

    # --- Patient Management ---
    async def register_patient(
        self,
        data: PatientCreate,
        actor_id: Optional[uuid.UUID] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> Patient:
        fac = await self.facility_repo.get_facility_by_id(data.primary_facility_id)
        if not fac:
            raise ResourceNotFoundException("Facility", str(data.primary_facility_id))

        patient: Optional[Patient] = None
        for attempt in range(5):
            identifier = _generate_patient_identifier()
            if await self.repo.get_patient_by_identifier(identifier):
                continue

            p = Patient(
                user_id=data.user_id,
                primary_facility_id=data.primary_facility_id,
                patient_identifier=identifier,
                first_name=data.first_name,
                last_name=data.last_name,
                date_of_birth=data.date_of_birth,
                gender=data.gender,
                phone_number=data.phone_number,
                blood_group=data.blood_group,
                address=data.address,
                emergency_contact_name=data.emergency_contact_name,
                emergency_contact_phone=data.emergency_contact_phone,
                emergency_contact_relation=data.emergency_contact_relation,
                preferred_language=data.preferred_language or "en",
                chronic_conditions=data.chronic_conditions,
                allergies=data.allergies,
                is_active=True,
            )
            try:
                async with self.session.begin_nested():
                    await self.repo.create_patient(p)
                patient = p
                break
            except Exception:
                if attempt == 4:
                    raise ConflictException("Could not generate a unique patient identifier. Please retry.")

        if not patient:
            raise ConflictException("Failed to register patient with unique identifier.")

        await self.audit_repo.record_event(
            action="PATIENT_REGISTERED",
            resource_type="patient",
            resource_id=str(patient.id),
            actor_id=actor_id,
            facility_id=patient.primary_facility_id,
            new_state={"identifier": patient.patient_identifier, "name": f"{patient.first_name} {patient.last_name}"},
            ip_address=ip_address,
            user_agent=user_agent,
        )
        return patient

    async def get_patient(self, patient_id: uuid.UUID) -> Patient:
        patient = await self.repo.get_patient_by_id(patient_id)
        if not patient:
            raise ResourceNotFoundException("Patient", str(patient_id))
        return patient

    async def get_patient_by_user_id(self, user_id: uuid.UUID) -> Optional[Patient]:
        return await self.repo.get_patient_by_user_id(user_id)

    async def update_patient(
        self,
        patient_id: uuid.UUID,
        data: PatientUpdate,
        actor_id: Optional[uuid.UUID] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> Patient:
        patient = await self.get_patient(patient_id)
        old_state = {"phone": patient.phone_number, "is_active": patient.is_active}

        if data.first_name is not None:
            patient.first_name = data.first_name
        if data.last_name is not None:
            patient.last_name = data.last_name
        if data.phone_number is not None:
            patient.phone_number = data.phone_number
        if data.address is not None:
            patient.address = data.address
        if data.emergency_contact_name is not None:
            patient.emergency_contact_name = data.emergency_contact_name
        if data.emergency_contact_phone is not None:
            patient.emergency_contact_phone = data.emergency_contact_phone
        if data.emergency_contact_relation is not None:
            patient.emergency_contact_relation = data.emergency_contact_relation
        if data.preferred_language is not None:
            patient.preferred_language = data.preferred_language
        if data.chronic_conditions is not None:
            patient.chronic_conditions = data.chronic_conditions
        if data.allergies is not None:
            patient.allergies = data.allergies
        if data.is_active is not None:
            patient.is_active = data.is_active

        await self.repo.update_patient(patient)

        await self.audit_repo.record_event(
            action="PATIENT_UPDATED",
            resource_type="patient",
            resource_id=str(patient.id),
            actor_id=actor_id,
            facility_id=patient.primary_facility_id,
            old_state=old_state,
            new_state={"phone": patient.phone_number, "is_active": patient.is_active},
            ip_address=ip_address,
            user_agent=user_agent,
        )
        return patient

    async def search_patients(
        self,
        facility_id: Optional[uuid.UUID] = None,
        query: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> Tuple[Sequence[Patient], int]:
        offset = (page - 1) * page_size
        return await self.repo.search_patients(
            facility_id=facility_id,
            query=query,
            offset=offset,
            limit=page_size,
        )

    # --- Appointment Management ---
    async def create_appointment(
        self,
        data: AppointmentCreate,
        actor_id: Optional[uuid.UUID] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> Appointment:
        await self.get_patient(data.patient_id)
        fac = await self.facility_repo.get_facility_by_id(data.facility_id)
        if not fac:
            raise ResourceNotFoundException("Facility", str(data.facility_id))

        token_num = await self.repo.get_next_token_number(data.facility_id, data.appointment_date)

        appointment = Appointment(
            patient_id=data.patient_id,
            facility_id=data.facility_id,
            doctor_id=data.doctor_id,
            token_number=token_num,
            priority=data.priority or "ROUTINE",
            time_slot=data.time_slot,
            appointment_date=data.appointment_date,
            status=AppointmentStatus.SCHEDULED,
            reason=data.reason,
        )
        await self.repo.create_appointment(appointment)

        # In-app notification for patient
        try:
            notification = PatientNotification(
                patient_id=data.patient_id,
                title_en=f"Appointment Confirmed - Token #{token_num}",
                title_ta=f"முன்பதிவு உறுதி செய்யப்பட்டது - டோக்கன் #{token_num}",
                message_en=f"Your appointment at {fac.name} is scheduled for {data.appointment_date.strftime('%d-%b-%Y %I:%M %p')} with Token #{token_num}.",
                message_ta=f"{fac.name} மருத்துவமனையில் உங்கள் சந்திப்பு {data.appointment_date.strftime('%d-%b-%Y')} அன்று டோக்கன் #{token_num} உடன் பதிவு செய்யப்பட்டுள்ளது.",
                notification_type="APPOINTMENT",
                reference_id=str(appointment.id),
            )
            await self.repo.create_patient_notification(notification)
        except Exception:
            pass

        await self.audit_repo.record_event(
            action="APPOINTMENT_SCHEDULED",
            resource_type="appointment",
            resource_id=str(appointment.id),
            actor_id=actor_id,
            facility_id=appointment.facility_id,
            new_state={"date": appointment.appointment_date.isoformat(), "token_number": token_num, "status": appointment.status.value},
            ip_address=ip_address,
            user_agent=user_agent,
        )
        return appointment

    async def update_appointment_status(
        self,
        appointment_id: uuid.UUID,
        data: AppointmentStatusUpdate,
        actor_id: Optional[uuid.UUID] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> Appointment:
        appt = await self.repo.get_appointment_by_id(appointment_id)
        if not appt:
            raise ResourceNotFoundException("Appointment", str(appointment_id))

        # Enforce State Machine Invariants
        if appt.status in (AppointmentStatus.COMPLETED, AppointmentStatus.CANCELLED, AppointmentStatus.NO_SHOW):
            raise BadRequestException(f"Cannot change status of an appointment that is in terminal status '{appt.status.value}'.")

        valid_transitions = {
            AppointmentStatus.SCHEDULED: {AppointmentStatus.CHECKED_IN, AppointmentStatus.CANCELLED, AppointmentStatus.NO_SHOW},
            AppointmentStatus.CHECKED_IN: {AppointmentStatus.IN_CONSULTATION, AppointmentStatus.CANCELLED, AppointmentStatus.NO_SHOW},
            AppointmentStatus.IN_CONSULTATION: {AppointmentStatus.COMPLETED, AppointmentStatus.CANCELLED},
        }
        allowed = valid_transitions.get(appt.status, set())
        if data.status not in allowed:
            raise BadRequestException(f"Invalid appointment state transition from '{appt.status.value}' to '{data.status.value}'.")


        old_status = appt.status.value
        appt.status = data.status
        if data.cancellation_reason:
            appt.cancellation_reason = data.cancellation_reason

        # Generate in-app PatientNotification for cross-role visibility
        try:
            status_labels = {
                AppointmentStatus.CHECKED_IN: ("Checked In", "சரிபார்க்கப்பட்டது"),
                AppointmentStatus.IN_CONSULTATION: ("In Consultation", "ஆலோசனையில்"),
                AppointmentStatus.COMPLETED: ("Consultation Completed", "ஆலோசனை முடிந்தது"),
                AppointmentStatus.CANCELLED: ("Appointment Cancelled", "சந்திப்பு ரத்து செய்யப்பட்டது"),
            }
            if data.status in status_labels:
                label_en, label_ta = status_labels[data.status]
                notification = PatientNotification(
                    patient_id=appt.patient_id,
                    title_en=f"Appointment Status Update: {label_en}",
                    title_ta=f"சந்திப்பு நிலை புதுப்பிப்பு: {label_ta}",
                    message_en=f"Your appointment status has been updated to '{label_en}'.",
                    message_ta=f"உங்கள் சந்திப்பு நிலை '{label_ta}' என மாற்றப்பட்டுள்ளது.",
                    notification_type="APPOINTMENT",
                    reference_id=str(appt.id),
                )
                await self.repo.create_patient_notification(notification)
        except Exception:
            pass

        await self.audit_repo.record_event(
            action="APPOINTMENT_STATUS_UPDATED",
            resource_type="appointment",
            resource_id=str(appt.id),
            actor_id=actor_id,
            facility_id=appt.facility_id,
            old_state={"status": old_status},
            new_state={"status": appt.status.value},
            ip_address=ip_address,
            user_agent=user_agent,
        )
        return appt

    async def list_appointments(
        self,
        facility_id: Optional[uuid.UUID] = None,
        patient_id: Optional[uuid.UUID] = None,
        doctor_id: Optional[uuid.UUID] = None,
        status: Optional[AppointmentStatus] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> Tuple[Sequence[Appointment], int]:
        offset = (page - 1) * page_size
        return await self.repo.list_appointments(
            facility_id=facility_id,
            patient_id=patient_id,
            doctor_id=doctor_id,
            status=status,
            offset=offset,
            limit=page_size,
        )

    # --- Clinical Encounters & Consultations ---
    async def start_consultation(
        self,
        data: ConsultationCreate,
        doctor_id: uuid.UUID,
        facility_id: uuid.UUID,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> Consultation:
        patient_id = data.patient_id
        if not patient_id and data.appointment_id:
            appt = await self.repo.get_appointment_by_id(data.appointment_id)
            if appt:
                patient_id = appt.patient_id
        if not patient_id:
            raise BadRequestException("Either patient_id or appointment_id must be provided.")

        patient = await self.get_patient(patient_id)

        # If linked to appointment, check and update appointment status
        existing_consultation = None
        if data.appointment_id:
            appt = await self.repo.get_appointment_by_id(data.appointment_id)
            if appt:
                appt.status = AppointmentStatus.IN_CONSULTATION
            existing_consultation = await self.repo.get_consultation_by_appointment(data.appointment_id)

        if existing_consultation:
            existing_consultation.doctor_id = doctor_id
            existing_consultation.status = ConsultationStatus.IN_PROGRESS
            if data.chief_complaint:
                existing_consultation.chief_complaint = data.chief_complaint
            if data.clinical_notes:
                existing_consultation.clinical_notes = data.clinical_notes
            if data.examination_findings:
                existing_consultation.examination_findings = data.examination_findings
            await self.repo.session.flush()
            consultation = existing_consultation
        else:
            vitals_dict = data.triage_vitals.model_dump() if data.triage_vitals else None
            consultation = Consultation(
                appointment_id=data.appointment_id,
                patient_id=patient_id,
                doctor_id=doctor_id,
                facility_id=facility_id,
                status=ConsultationStatus.IN_PROGRESS,
                triage_vitals=vitals_dict,
                chief_complaint=data.chief_complaint,
                clinical_notes=data.clinical_notes,
                examination_findings=data.examination_findings,
                started_at=datetime.now(timezone.utc),
            )
            await self.repo.create_consultation(consultation)

        if data.triage_vitals and not existing_consultation:
            v_rec = Vitals(
                consultation_id=consultation.id,
                systolic_bp=data.triage_vitals.systolic_bp,
                diastolic_bp=data.triage_vitals.diastolic_bp,
                pulse_rate=data.triage_vitals.pulse_rate,
                temperature_celsius=data.triage_vitals.temperature_celsius,
                respiratory_rate=data.triage_vitals.respiratory_rate,
                spo2_percent=data.triage_vitals.spo2_percent,
                weight_kg=data.triage_vitals.weight_kg,
                height_cm=data.triage_vitals.height_cm,
                recorded_by_id=doctor_id,
                recorded_at=datetime.now(timezone.utc),
            )
            if v_rec.weight_kg and v_rec.height_cm and v_rec.height_cm > 0:
                h_m = v_rec.height_cm / 100.0
                v_rec.bmi = round(v_rec.weight_kg / (h_m * h_m), 1)
            await self.repo.create_vitals(v_rec)

        await self.audit_repo.record_event(
            action="CONSULTATION_STARTED",
            resource_type="consultation",
            resource_id=str(consultation.id),
            actor_id=doctor_id,
            facility_id=facility_id,
            new_state={"patient_id": str(patient.id), "doctor_id": str(doctor_id)},
            ip_address=ip_address,
            user_agent=user_agent,
        )
        return await self.repo.get_consultation_by_id(consultation.id)

    async def finalize_consultation(
        self,
        consultation_id: uuid.UUID,
        data: ConsultationFinalizeRequest,
        doctor_id: uuid.UUID,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> Consultation:
        consultation = await self.repo.get_consultation_by_id(consultation_id)
        if not consultation:
            raise ResourceNotFoundException("Consultation", str(consultation_id))

        if consultation.status != ConsultationStatus.IN_PROGRESS:
            raise BadRequestException(f"Cannot finalize consultation in status '{consultation.status.value}'.")

        # Update clinical notes if provided
        if data.clinical_notes is not None:
            consultation.clinical_notes = data.clinical_notes
        if data.examination_findings is not None:
            consultation.examination_findings = data.examination_findings

        # Add diagnoses
        if data.diagnoses:
            for diag in data.diagnoses:
                diag_obj = Diagnosis(
                    consultation_id=consultation.id,
                    patient_id=consultation.patient_id,
                    icd10_code=diag.icd10_code,
                    condition_name=diag.condition_name,
                    diagnosis_type=diag.diagnosis_type,
                    notes=diag.notes,
                )
                consultation.diagnoses.append(diag_obj)

        consultation.status = ConsultationStatus.FINALIZED
        consultation.finalized_at = datetime.now(timezone.utc)

        # Mark linked appointment as completed
        if consultation.appointment_id:
            appt = await self.repo.get_appointment_by_id(consultation.appointment_id)
            if appt:
                appt.status = AppointmentStatus.COMPLETED

        await self.audit_repo.record_event(
            action="CONSULTATION_FINALIZED",
            resource_type="consultation",
            resource_id=str(consultation.id),
            actor_id=doctor_id,
            facility_id=consultation.facility_id,
            new_state={"status": ConsultationStatus.FINALIZED.value, "finalized_at": consultation.finalized_at.isoformat()},
            ip_address=ip_address,
            user_agent=user_agent,
        )
        return await self.repo.get_consultation_by_id(consultation.id)

    async def record_vitals(
        self,
        consultation_id: uuid.UUID,
        data: VitalsCreate,
        recorder_id: uuid.UUID,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> Vitals:
        consultation = await self.get_consultation(consultation_id)
        if consultation.status == ConsultationStatus.CANCELLED:
            raise BadRequestException("Cannot record vitals on a cancelled consultation.")

        v_rec = Vitals(
            consultation_id=consultation.id,
            systolic_bp=data.systolic_bp,
            diastolic_bp=data.diastolic_bp,
            pulse_rate=data.pulse_rate,
            temperature_celsius=data.temperature_celsius,
            respiratory_rate=data.respiratory_rate,
            spo2_percent=data.spo2_percent,
            weight_kg=data.weight_kg,
            height_cm=data.height_cm,
            recorded_by_id=recorder_id,
            recorded_at=datetime.now(timezone.utc),
        )
        if v_rec.weight_kg and v_rec.height_cm and v_rec.height_cm > 0:
            h_m = v_rec.height_cm / 100.0
            v_rec.bmi = round(v_rec.weight_kg / (h_m * h_m), 1)
        await self.repo.create_vitals(v_rec)

        await self.audit_repo.record_event(
            action="VITALS_RECORDED",
            resource_type="vitals",
            resource_id=str(v_rec.id),
            actor_id=recorder_id,
            facility_id=consultation.facility_id,
            new_state={"consultation_id": str(consultation.id), "pulse": v_rec.pulse_rate, "spo2": v_rec.spo2_percent},
            ip_address=ip_address,
            user_agent=user_agent,
        )
        return v_rec

    async def add_amendment(
        self,
        consultation_id: uuid.UUID,
        data: ClinicalAmendmentCreate,
        doctor_id: uuid.UUID,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> ClinicalAmendment:
        consultation = await self.get_consultation(consultation_id)
        if consultation.status != ConsultationStatus.FINALIZED:
            raise BadRequestException("Amendments can only be appended to finalized clinical encounters.")

        amendment = ClinicalAmendment(
            consultation_id=consultation.id,
            amendment_reason=data.amendment_reason,
            amendment_notes=data.amendment_notes,
            amended_by_id=doctor_id,
            created_at=datetime.now(timezone.utc),
        )
        await self.repo.create_amendment(amendment)

        await self.audit_repo.record_event(
            action="CLINICAL_AMENDMENT_RECORDED",
            resource_type="clinical_amendment",
            resource_id=str(amendment.id),
            actor_id=doctor_id,
            facility_id=consultation.facility_id,
            new_state={"reason": amendment.amendment_reason, "consultation_id": str(consultation.id)},
            ip_address=ip_address,
            user_agent=user_agent,
        )
        return amendment

    async def get_consultation(self, consultation_id: uuid.UUID) -> Consultation:
        consultation = await self.repo.get_consultation_by_id(consultation_id)
        if not consultation:
            raise ResourceNotFoundException("Consultation", str(consultation_id))
        return consultation

    async def get_patient_clinical_history(self, patient_id: uuid.UUID) -> ClinicalHistoryResponse:
        patient = await self.get_patient(patient_id)
        consultations = await self.repo.list_consultations_by_patient(patient_id)
        consultation_dtos = [ConsultationResponse.model_validate(c) for c in consultations]

        return ClinicalHistoryResponse(
            patient=PatientResponse.model_validate(patient),
            consultations=consultation_dtos,
        )

    # --- Prescriptions ---
    async def create_prescription(
        self,
        data: PrescriptionCreate,
        doctor_id: uuid.UUID,
        facility_id: uuid.UUID,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> Prescription:
        consultation = await self.repo.get_consultation_by_id(data.consultation_id)
        if not consultation:
            raise ResourceNotFoundException("Consultation", str(data.consultation_id))

        prescription = Prescription(
            consultation_id=consultation.id,
            patient_id=consultation.patient_id,
            doctor_id=doctor_id,
            facility_id=facility_id,
            status=PrescriptionStatus.ISSUED,
            notes=data.notes,
        )
        await self.repo.create_prescription(prescription)

        for item in data.items:
            p_item = PrescriptionItem(
                prescription_id=prescription.id,
                medication_name=item.medication_name,
                medication_code=item.medication_code,
                medication_id=item.medication_id,
                dosage=item.dosage,
                frequency=item.frequency,
                duration_days=item.duration_days,
                quantity_prescribed=item.quantity_prescribed,
                quantity_dispensed=0,
                instructions=item.instructions,
                status=PrescriptionItemStatus.PENDING,
            )
            self.session.add(p_item)

        await self.session.flush()

        await self.audit_repo.record_event(
            action="PRESCRIPTION_ISSUED",
            resource_type="prescription",
            resource_id=str(prescription.id),
            actor_id=doctor_id,
            facility_id=facility_id,
            new_state={"items_count": len(data.items)},
            ip_address=ip_address,
            user_agent=user_agent,
        )
        return await self.repo.get_prescription_by_id(prescription.id)

    async def get_prescription(self, prescription_id: uuid.UUID) -> Prescription:
        prescription = await self.repo.get_prescription_by_id(prescription_id)
        if not prescription:
            raise ResourceNotFoundException("Prescription", str(prescription_id))
        return prescription

    async def dispense_prescription(
        self,
        prescription_id: uuid.UUID,
        data: PrescriptionDispenseRequest,
        pharmacist_id: uuid.UUID,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> Prescription:
        prescription = await self.get_prescription(prescription_id)

        if prescription.status not in (PrescriptionStatus.ISSUED, PrescriptionStatus.PARTIALLY_DISPENSED):
            raise BadRequestException(f"Cannot dispense prescription in status '{prescription.status.value}'.")

        all_completed = True
        for item in prescription.items:
            if item.id in data.dispensed_items:
                qty_to_dispense = data.dispensed_items[item.id]
                if qty_to_dispense <= 0:
                    continue
                remaining = item.quantity_prescribed - item.quantity_dispensed
                if qty_to_dispense > remaining:
                    raise BadRequestException(
                        f"Cannot dispense {qty_to_dispense} units for medication '{item.medication_name}'. "
                        f"Remaining prescribed quantity is {remaining}."
                    )
                item.quantity_dispensed += qty_to_dispense
                if item.quantity_dispensed >= item.quantity_prescribed:
                    item.status = PrescriptionItemStatus.DISPENSED
                else:
                    item.status = PrescriptionItemStatus.PENDING
                    all_completed = False
            elif item.status != PrescriptionItemStatus.DISPENSED:
                all_completed = False

        prescription.status = PrescriptionStatus.COMPLETED if all_completed else PrescriptionStatus.PARTIALLY_DISPENSED
        await self.session.flush()

        await self.audit_repo.record_event(
            action="PRESCRIPTION_DISPENSED",
            resource_type="prescription",
            resource_id=str(prescription.id),
            actor_id=pharmacist_id,
            facility_id=prescription.facility_id,
            new_state={"status": prescription.status.value},
            ip_address=ip_address,
            user_agent=user_agent,
        )
        return prescription

    # --- Laboratory Management ---
    async def create_lab_order(
        self,
        data: LabOrderCreate,
        doctor_id: uuid.UUID,
        facility_id: uuid.UUID,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> LabOrder:
        consultation = await self.repo.get_consultation_by_id(data.consultation_id)
        if not consultation:
            raise ResourceNotFoundException("Consultation", str(data.consultation_id))

        order = LabOrder(
            consultation_id=consultation.id,
            patient_id=consultation.patient_id,
            ordered_by_doctor_id=doctor_id,
            facility_id=facility_id,
            test_category=data.test_category,
            clinical_notes=data.clinical_notes,
            status=LabOrderStatus.ORDERED,
            ordered_at=datetime.now(timezone.utc),
        )
        await self.repo.create_lab_order(order)

        await self.audit_repo.record_event(
            action="LAB_ORDER_CREATED",
            resource_type="lab_order",
            resource_id=str(order.id),
            actor_id=doctor_id,
            facility_id=facility_id,
            new_state={"category": order.test_category},
            ip_address=ip_address,
            user_agent=user_agent,
        )
        return await self.repo.get_lab_order_by_id(order.id)

    @staticmethod
    def evaluate_critical_lab_value(
        test_name: str,
        result_value: str,
        is_pregnant: bool = False,
    ) -> Tuple[bool, Optional[str]]:
        """
        Automated Critical (Panic) Value Detection based on Tamil Nadu STG
        and National Health Programmes (NVBDCP, NTEP, RMNCH+A).
        """
        import re
        t_norm = test_name.lower().strip()
        v_norm = result_value.lower().strip()

        def _parse_num(s: str) -> Optional[float]:
            m = re.search(r"[-+]?(?:\d*\.\d+|\d+)", s)
            return float(m.group(0)) if m else None

        num = _parse_num(v_norm)

        # 1. Hemoglobin / Hb
        if any(k in t_norm for k in ["hemoglobin", "haemoglobin", "hb"]):
            if num is not None:
                threshold = 8.0 if is_pregnant else 7.0
                if num < threshold:
                    return (
                        True,
                        f"CRITICAL PANIC: Hemoglobin {num} g/dL ({'Severe Anemia in Pregnancy' if is_pregnant else 'Severe Anemia'}). Immediate clinical alert sent. Blood transfusion evaluation required per TN STG."
                    )

        # 2. Platelet Count / Thrombocytes
        if any(k in t_norm for k in ["platelet", "thrombocyte"]):
            if num is not None and num < 50000:
                return (
                    True,
                    f"CRITICAL PANIC: Platelet count {int(num)}/µL (<50,000/µL). Dengue warning sign / spontaneous bleeding risk. Immediate fluid monitoring and tertiary referral evaluation required."
                )

        # 3. Blood Glucose / RBS / FBS / PPBS
        if any(k in t_norm for k in ["glucose", "sugar", "rbs", "fbs", "ppbs"]):
            if num is not None:
                if num > 400:
                    return (
                        True,
                        f"CRITICAL PANIC: Blood Glucose {int(num)} mg/dL (>400 mg/dL). Severe Hyperglycemia with ketoacidosis / hyperosmolar state risk. Urgent IV fluid and insulin protocol."
                    )
                elif num < 50:
                    return (
                        True,
                        f"CRITICAL PANIC: Blood Glucose {int(num)} mg/dL (<50 mg/dL). Severe Hypoglycemia. Administer immediate oral glucose / IV 25% Dextrose."
                    )

        # 4. Dengue NS1 Antigen or IgM
        if "dengue" in t_norm:
            if any(p in v_norm for p in ["pos", "reactive", "+", "detected"]):
                return (
                    True,
                    "CRITICAL ALERT: Dengue NS1/IgM POSITIVE. IDSP notifiable vector-borne case. Initiate hematocrit monitoring and oral/IV rehydration."
                )

        # 5. Malaria Rapid Test / Smear
        if "malaria" in t_norm or "plasmodium" in t_norm:
            if any(p in v_norm for p in ["pos", "reactive", "+", "detected", "falciparum", "vivax"]):
                return (
                    True,
                    "CRITICAL ALERT: Malaria POSITIVE. Notifiable under NVBDCP. Prompt initiation of species-specific ACT / Chloroquine per national protocol."
                )

        # 6. Sputum AFB / Tuberculosis
        if any(k in t_norm for k in ["sputum", "afb", "tuberculosis", "tb"]):
            if any(p in v_norm for p in ["pos", "reactive", "+", "detected", "seen"]):
                return (
                    True,
                    "CRITICAL ALERT: Sputum AFB POSITIVE for Acid-Fast Bacilli (Tuberculosis). Notifiable condition under NTEP (Nikshay). Initiate infection control and TB DOTS regimen."
                )

        # 7. Serum Potassium (K+)
        if "potassium" in t_norm or "k+" in t_norm:
            if num is not None:
                if num > 6.0:
                    return (True, f"CRITICAL PANIC: Hyperkalemia (K+ {num} mEq/L). Life-threatening cardiac arrhythmia risk. Urgent ECG.")
                elif num < 2.8:
                    return (True, f"CRITICAL PANIC: Hypokalemia (K+ {num} mEq/L). Cardiac arrhythmia and muscle paralysis risk.")

        return (False, None)

    async def collect_lab_sample(
        self,
        order_id: uuid.UUID,
        data: LabSampleCollectRequest,
        technician_id: uuid.UUID,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> LabOrder:
        order = await self.repo.get_lab_order_by_id(order_id)
        if not order:
            raise ResourceNotFoundException("Lab Order", str(order_id))

        if order.status in (LabOrderStatus.COMPLETED, LabOrderStatus.CANCELLED):
            raise BadRequestException(f"Cannot collect sample for lab order in status '{order.status.value}'.")

        now = datetime.now(timezone.utc)
        order.sample_type = data.sample_type
        order.sample_barcode = data.sample_barcode or f"SPL-{order_id.hex[:8].upper()}"
        order.sample_collected_at = now
        order.status = LabOrderStatus.SAMPLE_COLLECTED
        if data.collection_notes:
            order.clinical_notes = (order.clinical_notes or "") + f"\n[Sample Collection]: {data.collection_notes}"
        await self.session.flush()

        await self.audit_repo.record_event(
            action="LAB_SAMPLE_COLLECTED",
            resource_type="lab_order",
            resource_id=str(order.id),
            actor_id=technician_id,
            facility_id=order.facility_id,
            new_state={
                "status": order.status.value,
                "sample_type": order.sample_type,
                "sample_barcode": order.sample_barcode,
            },
            ip_address=ip_address,
            user_agent=user_agent,
        )
        return order

    async def add_lab_result(
        self,
        order_id: uuid.UUID,
        data: LabResultCreate,
        technician_id: uuid.UUID,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> LabResult:
        order = await self.repo.get_lab_order_by_id(order_id)
        if not order:
            raise ResourceNotFoundException("Lab Order", str(order_id))

        if order.status in (LabOrderStatus.CANCELLED, LabOrderStatus.COMPLETED):
            raise BadRequestException(f"Cannot add results to a lab order in status '{order.status.value}'.")

        is_crit, crit_alert = self.evaluate_critical_lab_value(data.test_name, data.result_value)

        result = LabResult(
            lab_order_id=order.id,
            test_name=data.test_name,
            result_value=data.result_value,
            reference_range=data.reference_range,
            unit=data.unit,
            is_abnormal=data.is_abnormal or is_crit,
            critical_alert=crit_alert,
            performed_by_id=technician_id,
            notes=data.notes,
        )
        await self.repo.add_lab_result(result)
        order.status = LabOrderStatus.IN_ANALYSIS

        await self.audit_repo.record_event(
            action="LAB_RESULT_RECORDED",
            resource_type="lab_result",
            resource_id=str(result.id),
            actor_id=technician_id,
            facility_id=order.facility_id,
            new_state={
                "test": result.test_name,
                "value": result.result_value,
                "is_critical": is_crit,
                "critical_alert": crit_alert,
            },
            ip_address=ip_address,
            user_agent=user_agent,
        )
        return result

    async def add_lab_panel_results(
        self,
        order_id: uuid.UUID,
        data: LabPanelResultCreate,
        technician_id: uuid.UUID,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> List[LabResult]:
        order = await self.repo.get_lab_order_by_id(order_id)
        if not order:
            raise ResourceNotFoundException("Lab Order", str(order_id))

        if order.status in (LabOrderStatus.CANCELLED, LabOrderStatus.COMPLETED):
            raise BadRequestException(f"Cannot add results to a lab order in status '{order.status.value}'.")

        created_results = []
        for item in data.results:
            is_crit, crit_alert = self.evaluate_critical_lab_value(item.test_name, item.result_value)
            result = LabResult(
                lab_order_id=order.id,
                test_name=item.test_name,
                result_value=item.result_value,
                reference_range=item.reference_range,
                unit=item.unit,
                is_abnormal=item.is_abnormal or is_crit,
                critical_alert=crit_alert,
                performed_by_id=technician_id,
                notes=item.notes,
            )
            await self.repo.add_lab_result(result)
            created_results.append(result)

        order.status = LabOrderStatus.IN_ANALYSIS
        await self.session.flush()

        await self.audit_repo.record_event(
            action="LAB_PANEL_RESULTS_RECORDED",
            resource_type="lab_order",
            resource_id=str(order.id),
            actor_id=technician_id,
            facility_id=order.facility_id,
            new_state={"count": len(created_results)},
            ip_address=ip_address,
            user_agent=user_agent,
        )
        return created_results

    async def verify_lab_order(
        self,
        order_id: uuid.UUID,
        verifier_id: uuid.UUID,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> LabOrder:
        order = await self.repo.get_lab_order_by_id(order_id)
        if not order:
            raise ResourceNotFoundException("Lab Order", str(order_id))

        if order.status in (LabOrderStatus.CANCELLED, LabOrderStatus.COMPLETED):
            raise BadRequestException(f"Cannot verify a lab order that is already in status '{order.status.value}'.")

        if not order.results:
            raise BadRequestException("Cannot verify a lab order with no recorded results.")

        now = datetime.now(timezone.utc)
        for r in order.results:
            r.verified_by_id = verifier_id
            r.verified_at = now

        order.status = LabOrderStatus.COMPLETED
        order.completed_at = now
        await self.session.flush()

        # Generate in-app PatientNotification for lab result release
        try:
            test_names = ", ".join(r.test_name for r in order.results) if order.results else "Diagnostic Test"
            notification = PatientNotification(
                patient_id=order.patient_id,
                title_en=f"Lab Results Ready: {test_names}",
                title_ta=f"ஆய்வக முடிவுகள் தயார்: {test_names}",
                message_en=f"Your diagnostic laboratory test report for {test_names} has been finalized and verified.",
                message_ta=f"{test_names} க்கான உங்கள் ஆய்வக சோதனை அறிக்கை முடிவடைந்து சரிபார்க்கப்பட்டது.",
                notification_type="LAB_RESULT",
                reference_id=str(order.id),
            )
            await self.repo.create_patient_notification(notification)
        except Exception:
            pass

        await self.audit_repo.record_event(
            action="LAB_ORDER_VERIFIED",
            resource_type="lab_order",
            resource_id=str(order.id),
            actor_id=verifier_id,
            facility_id=order.facility_id,
            new_state={"status": LabOrderStatus.COMPLETED.value},
            ip_address=ip_address,
            user_agent=user_agent,
        )
        return await self.repo.get_lab_order_by_id(order.id)

    # --- Referrals ---
    async def create_referral(
        self,
        data: ReferralCreate,
        doctor_id: uuid.UUID,
        from_facility_id: uuid.UUID,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> Referral:
        consultation = await self.repo.get_consultation_by_id(data.consultation_id)
        if not consultation:
            raise ResourceNotFoundException("Consultation", str(data.consultation_id))

        referral = Referral(
            consultation_id=consultation.id,
            patient_id=consultation.patient_id,
            from_facility_id=from_facility_id,
            to_facility_id=data.to_facility_id,
            to_facility_name=data.to_facility_name,
            referral_reason=data.referral_reason,
            urgency=data.urgency,
            clinical_summary=data.clinical_summary,
            status=ReferralStatus.PENDING,
            referred_by_doctor_id=doctor_id,
        )
        await self.repo.create_referral(referral)

        await self.audit_repo.record_event(
            action="PATIENT_REFERRED",
            resource_type="referral",
            resource_id=str(referral.id),
            actor_id=doctor_id,
            facility_id=from_facility_id,
            new_state={"to_facility": referral.to_facility_name, "urgency": referral.urgency.value},
            ip_address=ip_address,
            user_agent=user_agent,
        )
        return referral

    async def update_referral_status(
        self,
        referral_id: uuid.UUID,
        data: ReferralStatusUpdate,
        actor_id: Optional[uuid.UUID] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> Referral:
        referral = await self.repo.get_referral_by_id(referral_id)
        if not referral:
            raise ResourceNotFoundException("Referral", str(referral_id))

        if referral.status in (ReferralStatus.COMPLETED, ReferralStatus.REJECTED):
            raise BadRequestException(f"Cannot change status of a referral that is already in terminal status '{referral.status.value}'.")

        old_status = referral.status.value
        referral.status = data.status
        await self.session.flush()

        await self.audit_repo.record_event(
            action="REFERRAL_STATUS_UPDATED",
            resource_type="referral",
            resource_id=str(referral.id),
            actor_id=actor_id,
            old_state={"status": old_status},
            new_state={"status": referral.status.value},
            ip_address=ip_address,
            user_agent=user_agent,
        )
        return referral

    # --- Medication Master Reference Data ---
    async def create_medication(
        self,
        data: MedicationCreate,
        actor_id: Optional[uuid.UUID] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> Medication:
        med = Medication(
            generic_name=data.generic_name,
            brand_name=data.brand_name,
            strength=data.strength,
            dosage_form=data.dosage_form,
            route=data.route,
            unit=data.unit,
            is_active=True,
        )
        await self.repo.create_medication(med)
        await self.audit_repo.record_event(
            action="MEDICATION_CATALOG_CREATED",
            resource_type="medication",
            resource_id=str(med.id),
            actor_id=actor_id,
            new_state={"name": med.generic_name, "strength": med.strength},
            ip_address=ip_address,
            user_agent=user_agent,
        )
        return med

    async def list_medications(self, active_only: bool = True) -> Sequence[Medication]:
        return await self.repo.list_medications(active_only=active_only)

    # --- Patient Medicine Fulfillment (Safe Patient View) ---
    async def get_patient_prescriptions_fulfillment(
        self, patient_id: uuid.UUID
    ) -> List[PatientPrescriptionFulfillmentResponse]:
        prescriptions = await self.repo.list_prescriptions(patient_id=patient_id)
        results = []
        for rx in prescriptions:
            fac = await self.facility_repo.get_facility_by_id(rx.facility_id)
            fac_name = fac.name if fac else "Primary Health Centre"

            items = []
            for it in rx.items:
                if it.status == PrescriptionItemStatus.DISPENSED:
                    item_fulfill = "COLLECTED"
                elif it.quantity_dispensed > 0 and it.quantity_dispensed < it.quantity_prescribed:
                    item_fulfill = "PARTIALLY_AVAILABLE"
                elif rx.status == PrescriptionStatus.ISSUED:
                    item_fulfill = "READY_FOR_COLLECTION"
                elif it.status == PrescriptionItemStatus.CANCELLED:
                    item_fulfill = "TEMPORARILY_UNAVAILABLE"
                else:
                    item_fulfill = "PROCESSING"

                items.append(
                    PatientPrescriptionFulfillmentItem(
                        id=it.id,
                        medication_name=it.medication_name,
                        dosage=it.dosage,
                        frequency=it.frequency,
                        duration_days=it.duration_days,
                        quantity_prescribed=it.quantity_prescribed,
                        fulfillment_status=item_fulfill,
                        instructions=it.instructions,
                    )
                )

            if rx.status == PrescriptionStatus.COMPLETED:
                overall = "COLLECTED"
            elif rx.status == PrescriptionStatus.PARTIALLY_DISPENSED:
                overall = "PARTIALLY_AVAILABLE"
            elif rx.status == PrescriptionStatus.ISSUED:
                overall = "READY_FOR_COLLECTION"
            elif rx.status == PrescriptionStatus.CANCELLED:
                overall = "CANCELLED"
            else:
                overall = "PROCESSING"

            doctor_name = "Assigned Medical Officer"
            if rx.consultation and rx.consultation.doctor:
                doctor_name = rx.consultation.doctor.full_name

            results.append(
                PatientPrescriptionFulfillmentResponse(
                    id=rx.id,
                    consultation_id=rx.consultation_id,
                    prescription_date=rx.created_at,
                    facility_name=fac_name,
                    doctor_name=doctor_name,
                    notes=rx.notes,
                    overall_status=overall,
                    items=items,
                )
            )
        return results

    # --- Feedback & Complaints ---
    async def submit_feedback_complaint(
        self,
        patient_id: uuid.UUID,
        data: FeedbackComplaintCreate,
        actor_id: Optional[uuid.UUID] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> FeedbackComplaint:
        patient = await self.get_patient(patient_id)
        now = datetime.now(timezone.utc)
        rand_suffix = f"{secrets.randbelow(90000) + 10000}"
        tracking_num = f"CMP-{now.strftime('%Y%m')}-{rand_suffix}"

        complaint = FeedbackComplaint(
            tracking_number=tracking_num,
            patient_id=patient_id,
            facility_id=data.facility_id or patient.primary_facility_id,
            category=data.category,
            subject=data.subject,
            description=data.description,
            status=ComplaintStatus.SUBMITTED,
        )
        await self.repo.create_feedback_complaint(complaint)

        await self.audit_repo.record_event(
            action="FEEDBACK_COMPLAINT_SUBMITTED",
            resource_type="feedback_complaint",
            resource_id=str(complaint.id),
            actor_id=actor_id,
            facility_id=complaint.facility_id,
            new_state={"tracking_number": tracking_num, "category": complaint.category},
            ip_address=ip_address,
            user_agent=user_agent,
        )
        return complaint

    async def get_feedback_complaint_by_tracking(self, tracking_number: str) -> FeedbackComplaint:
        complaint = await self.repo.get_feedback_complaint_by_tracking(tracking_number)
        if not complaint:
            raise ResourceNotFoundException("Feedback/Complaint", tracking_number)
        return complaint

    async def list_patient_feedback_complaints(self, patient_id: uuid.UUID) -> Sequence[FeedbackComplaint]:
        return await self.repo.list_feedback_complaints_by_patient(patient_id)

    async def list_all_feedback_complaints(
        self,
        facility_id: Optional[uuid.UUID] = None,
        status: Optional[ComplaintStatus] = None,
    ) -> Sequence[FeedbackComplaint]:
        return await self.repo.list_feedback_complaints(facility_id=facility_id, status=status)

    async def update_feedback_complaint_status(
        self,
        complaint_id: uuid.UUID,
        data: "FeedbackComplaintStatusUpdate",
        resolver_id: Optional[uuid.UUID] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> FeedbackComplaint:
        """Allow facility admin / MPHS to move a complaint through the workflow."""
        complaint = await self.repo.get_feedback_complaint_by_id(complaint_id)
        if not complaint:
            raise ResourceNotFoundException("Complaint", str(complaint_id))

        old_status = complaint.status
        complaint.status = data.status
        if data.resolution_notes is not None:
            complaint.resolution_notes = data.resolution_notes
        if data.status == ComplaintStatus.RESOLVED and not complaint.resolved_at:
            complaint.resolved_at = datetime.now(timezone.utc)

        await self.session.flush()
        await self.audit_repo.record_event(
            action="COMPLAINT_STATUS_UPDATED",
            resource_type="feedback_complaint",
            resource_id=str(complaint_id),
            actor_id=resolver_id,
            facility_id=complaint.facility_id,
            old_state={"status": old_status},
            new_state={"status": complaint.status, "resolution_notes": complaint.resolution_notes},
            ip_address=ip_address,
            user_agent=user_agent,
        )
        return complaint


    async def list_patient_notifications(self, patient_id: uuid.UUID) -> Sequence[PatientNotification]:
        return await self.repo.list_patient_notifications(patient_id)

    async def mark_patient_notification_read(
        self, notification_id: uuid.UUID, patient_id: uuid.UUID
    ) -> PatientNotification:
        notification = await self.repo.get_patient_notification(notification_id, patient_id)
        if not notification:
            raise ResourceNotFoundException("Notification", str(notification_id))
        notification.is_read = True
        await self.session.flush()
        return notification

    # --- Health Awareness Slides ---
    async def list_health_awareness_slides(
        self, category: Optional[str] = None
    ) -> Sequence[HealthAwarenessSlide]:
        return await self.repo.list_health_awareness_slides(category=category, active_only=True)

    # --- Dedicated Bilingual AI Wellness Assistant ---
    async def chat_with_wellness_assistant(
        self,
        message: str,
        language: str = "en",
        patient_id: Optional[uuid.UUID] = None,
    ) -> PatientWellnessChatResponse:
        emergency_keywords = [
            "chest pain", "heart attack", "can't breathe", "cannot breathe", "difficulty breathing",
            "stroke", "paralysis", "unconscious", "heavy bleeding", "severe burn", "seizure",
            "நெஞ்சு வலி", "சுவாசிக்க முடியவில்லை", "மயக்கம்", "அதிக ரத்தப்போக்கு", "வலிப்பு",
        ]
        msg_lower = message.lower()
        is_emergency = any(k in msg_lower for k in emergency_keywords)

        if is_emergency:
            if language == "ta":
                reply = (
                    "⚠️ எச்சரிக்கை: நீங்கள் குறிப்பிட்டுள்ள அறிகுறிகள் அவசர மருத்துவ கவனிப்பு தேவைப்படலாம். "
                    "தயவுசெய்து உடனடியாக உங்கள் அருகிலுள்ள ஆரம்ப சுகாதார நிலையம் (PHC) அல்லது அவசர சிகிச்சை மையத்திற்கு செல்லவும் "
                    "அல்லது உடனடியாக 108 ஆம்புலன்ஸை அழைக்கவும். தாமதிக்க வேண்டாம்!"
                )
                phc_action = "அவசர சிகிச்சைக்காக உடனடியாக ஆரம்ப சுகாதார நிலையம் அல்லது மருத்துவமனைக்கு செல்லவும்."
                disclaimer = "இந்த AI உதவி தகவல் நோக்கங்களுக்காக மட்டுமே. இது மருத்துவ சிகிச்சை அல்லது நோய் கண்டறிதலுக்கு மாற்றாகாது."
                suggested_q = ["அருகிலுள்ள PHC எங்கே உள்ளது?", "108 ஆம்புலன்ஸ் தொடர்புகொள்வது எப்படி?"]
            else:
                reply = (
                    "⚠️ WARNING: The symptoms you described may indicate a medical emergency. "
                    "Please visit your nearest Primary Health Centre (PHC), Government Hospital emergency room, "
                    "or call 108 immediately. Do not delay emergency care!"
                )
                phc_action = "Visit the nearest PHC Emergency Counter or call emergency helpline 108."
                disclaimer = "This AI Wellness Assistant provides general wellness information only and cannot replace professional medical emergency evaluation."
                suggested_q = ["Find nearest PHC", "Emergency contact numbers"]

            return PatientWellnessChatResponse(
                reply=reply,
                language=language,
                is_emergency_warning=True,
                suggested_phc_action=phc_action,
                disclaimer=disclaimer,
                suggested_questions=suggested_q,
            )

        if any(w in msg_lower for w in ["diabetes", "sugar", "சர்க்கரை", "நீரிழிவு"]):
            if language == "ta":
                reply = (
                    "நீரிழிவு நோய் (Diabetes) தடுப்பு மற்றும் மேலாண்மை குறிப்புகள்:\n"
                    "1. நார்ச்சத்து நிறைந்த உணவுகள் (காய்கறிகள், சிறுதானியங்கள், பருப்பு வகைகள்) சாப்பிடுங்கள்.\n"
                    "2. இனிப்பு, சுத்திகரிக்கப்பட்ட மாவு (மைதா), குளிர்பானங்களைத் தவிருங்கள்.\n"
                    "3. தினமும் குறைந்தது 30 நிமிடங்கள் நடைப்பயிற்சி செய்யுங்கள்.\n"
                    "4. உங்கள் ஆரம்ப சுகாதார நிலையத்தில் (PHC) இலவச ரத்த சர்க்கரை பரிசோதனை செய்து கொள்ளலாம்."
                )
                phc_action = "உங்கள் PHC-யில் ரத்த சர்க்கரை (RBS/FBS) பரிசோதனை செய்து கொள்ளவும்."
                suggested_q = ["ஆரோக்கியமான உணவு முறை என்ன?", "உடற்பயிற்சி எவ்வளவு நேரம் செய்ய வேண்டும்?"]
            else:
                reply = (
                    "Diabetes Prevention & Management Guidelines:\n"
                    "1. Eat a balanced diet rich in fiber (vegetables, millets, whole grains, lentils).\n"
                    "2. Avoid refined sugars, ultra-processed snacks, and sweetened beverages.\n"
                    "3. Aim for at least 30 minutes of moderate aerobic exercise (brisk walking) daily.\n"
                    "4. Periodic blood glucose screening is available free at your nearest PHC."
                )
                phc_action = "Schedule a routine wellness checkup and blood sugar screening at your PHC."
                suggested_q = ["What foods help prevent diabetes?", "How much water should I drink daily?"]
        elif any(w in msg_lower for w in ["bp", "blood pressure", "hypertension", "ரத்த அழுத்தம்"]):
            if language == "ta":
                reply = (
                    "ரத்த அழுத்தத்தை (BP) கட்டுக்குள் வைக்க வழிமுறைகள்:\n"
                    "1. உணவில் உப்பின் அளவைக் குறைக்கவும் (ஒரு நாளைக்கு 1 தேக்கரண்டிக்கும் குறைவாக).\n"
                    "2. பொட்டாசியம் நிறைந்த புதிய பழங்கள் மற்றும் காய்கறிகளை உண்ணுங்கள்.\n"
                    "3. தினமும் நடைப்பயிற்சி, தியானம் மற்றும் போதுமான தூக்கம் (7-8 மணி நேரம்) அவசியம்.\n"
                    "4. PHC-யில் வழக்கமான BP பரிசோதனை செய்துகொள்ளுங்கள்."
                )
                phc_action = "வழக்கமான BP பரிசோதனைக்கு உங்கள் PHC-யை அணுகவும்."
                suggested_q = ["உப்பின் அளவைக் குறைப்பது எப்படி?", "மன அழுத்தத்தை குறைப்பது எப்படி?"]
            else:
                reply = (
                    "Healthy Blood Pressure Management Tips:\n"
                    "1. Reduce sodium intake in daily cooking (<5g of salt/day).\n"
                    "2. Eat potassium-rich fresh fruits and vegetables.\n"
                    "3. Maintain 7-8 hours of restful sleep and manage daily stress.\n"
                    "4. Get your BP checked regularly at your local PHC."
                )
                phc_action = "Visit your PHC for regular blood pressure monitoring."
                suggested_q = ["How to reduce daily stress?", "What is ideal sleep duration?"]
        elif any(w in msg_lower for w in ["water", "hydration", "தண்ணீர்", "நீர்"]):
            if language == "ta":
                reply = (
                    "உடல் நீரேற்றம் (Hydration) குறிப்புகள்:\n"
                    "• பெரியவர்கள் தினமும் குறைந்தது 2.5 முதல் 3 லிட்டர் பாதுகாப்பான குடிநீர் குடிக்க வேண்டும்.\n"
                    "• வெயில் காலங்களில் இளநீர், மோர் போன்ற இயற்கை பானங்கள் உடலுக்கு நல்லது.\n"
                    "• சுத்திகரிக்கப்பட்ட அல்லது காய்ச்சி வடிகட்டிய நீரையே பருகவும்."
                )
                phc_action = "தாகம், சோர்வு அதிகம் இருந்தால் மருத்துவரிடம் ஆலோசனை பெறவும்."
                suggested_q = ["நாள்தோறும் எவ்வளவு தண்ணீர் குடிக்க வேண்டும்?", "ஆரோக்கியமான பழக்கங்கள் என்ன?"]
            else:
                reply = (
                    "Hydration Best Practices:\n"
                    "• Drink 2.5 to 3 liters of clean, safe water every day.\n"
                    "• Stay hydrated with natural fluids like tender coconut water and buttermilk in warm weather.\n"
                    "• Always drink boiled or filtered safe water."
                )
                phc_action = "Consult your PHC medical officer if you experience persistent dehydration."
                suggested_q = ["How much exercise is recommended daily?", "Healthy breakfast ideas"]
        elif any(w in msg_lower for w in ["exercise", "walking", "fitness", "உடற்பயிற்சி", "நடைப்பயிற்சி"]):
            if language == "ta":
                reply = (
                    "தினசரி உடற்பயிற்சி மற்றும் ஆரோக்கியம்:\n"
                    "• தினமும் 30 நிமிடங்கள் விறுவிறுப்பான நடைப்பயிற்சி செய்வது இதயத்திற்கு மிகவும் நல்லது.\n"
                    "• எளிய யோகா மற்றும் நீட்சி பயிற்சிகள் உடலை சுறுசுறுப்பாக வைக்கும்.\n"
                    "• நீண்ட நேரம் ஒரே இடத்தில் அமர்வதைத் தவிர்த்து, அடிக்கடி சிறு நடைப்பயிற்சி செய்யுங்கள்."
                )
                phc_action = "உங்கள் உடல் தகுதிக்கு ஏற்ப உடற்பயிற்சி செய்ய மருத்துவரிடம் ஆலோசனை பெறவும்."
                suggested_q = ["தினமும் நடைப்பயிற்சியின் நன்மைகள் என்ன?", "ஆரோக்கியமான உணவு முறை"]
            else:
                reply = (
                    "Daily Fitness & Exercise Guidance:\n"
                    "• Aim for at least 30 minutes of brisk walking 5 days a week for cardiovascular health.\n"
                    "• Incorporate light stretching and mobility exercises to maintain joint flexibility.\n"
                    "• Avoid prolonged sitting — take 2-minute movement breaks every hour."
                )
                phc_action = "Discuss personalized exercise tolerance with your PHC Medical Officer."
                suggested_q = ["How to stay fit with busy schedule?", "Tips for better sleep"]
        else:
            if language == "ta":
                reply = (
                    "வணக்கம்! நான் உங்கள் PHC நல்வாழ்வு உதவியாளர் (AI Wellness Assistant).\n"
                    "ஆரோக்கியமான உணவு முறை, உடற்பயிற்சி, நீரேற்றம், தூக்கம், நோய் தடுப்பு முறைகள் மற்றும் உங்கள் ஆரம்ப சுகாதார நிலைய சேவைகள் குறித்து நான் உங்களுக்கு உதவ முடியும்.\n\n"
                    "உங்களுக்கு ஏதேனும் குறிப்பிட்ட உடல்நலக் கோளாறு இருந்தால், உங்கள் PHC மருத்துவரை நேரில் அணுகி ஆலோசனை பெறுங்கள்."
                )
                phc_action = "ஆலோசனை அல்லது பரிசோதனைக்கு ஆரம்ப சுகாதார நிலையத்தை அணுகவும்."
                suggested_q = [
                    "தினமும் ஆரோக்கியமாக இருக்க என்ன செய்யணும்?",
                    "சர்க்கரை நோயை தடுப்பது எப்படி?",
                    "ரத்த அழுத்தத்தை கட்டுப்படுத்துவது எப்படி?",
                ]
            else:
                reply = (
                    "Hello! I am your PHC AI Wellness Assistant.\n"
                    "I can guide you on balanced nutrition, daily fitness, hydration, sleep hygiene, preventive health awareness, and understanding services at your local Primary Health Centre (PHC).\n\n"
                    "For clinical diagnoses, treatment plans, or prescription medicines, please consult your PHC Medical Officer."
                )
                phc_action = "Book an appointment or visit your Primary Health Centre for professional consultation."
                suggested_q = [
                    "How can I stay healthy every day?",
                    "What foods help maintain a balanced diet?",
                    "How can I prevent diabetes and hypertension?",
                ]

        disclaimer = (
            "இந்த AI உதவி கல்வி மற்றும் நல்வாழ்வு வழிகாட்டுதலுக்கு மட்டுமே. இது மருத்துவ சிகிச்சைக்கு மாற்றாகாது."
            if language == "ta"
            else "This AI Wellness Assistant provides health promotion guidance only and does not provide medical diagnoses or prescriptions."
        )

        return PatientWellnessChatResponse(
            reply=reply,
            language=language,
            is_emergency_warning=False,
            suggested_phc_action=phc_action,
            disclaimer=disclaimer,
            suggested_questions=suggested_q,
        )

    # ============================================================================
    # STAFF DUTY ATTENDANCE (Role 02 Doctor & Role 03 Nurse)
    # ============================================================================
    async def record_staff_check_in(
        self,
        user_id: uuid.UUID,
        facility_id: uuid.UUID,
        shift: str = "GENERAL",
        notes: Optional[str] = None,
        actor_id: Optional[uuid.UUID] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> StaffAttendance:
        today = datetime.now(timezone.utc).date()
        existing = await self.repo.get_staff_attendance_by_date(user_id, today)
        if existing:
            return existing

        now = datetime.now(timezone.utc)
        attendance = StaffAttendance(
            user_id=user_id,
            facility_id=facility_id,
            attendance_date=today,
            check_in_time=now,
            status=AttendanceStatus.PRESENT,
            shift=shift,
            notes=notes,
        )
        record = await self.repo.record_staff_check_in(attendance)
        await self.audit_repo.record_event(
            action="STAFF_DUTY_CHECKED_IN",
            resource_type="staff_attendance",
            resource_id=str(record.id),
            actor_id=actor_id or user_id,
            facility_id=facility_id,
            new_state={"attendance_date": today.isoformat(), "shift": shift},
            ip_address=ip_address,
            user_agent=user_agent,
        )
        return record

    async def record_staff_check_out(
        self,
        user_id: uuid.UUID,
        notes: Optional[str] = None,
        actor_id: Optional[uuid.UUID] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> StaffAttendance:
        today = datetime.now(timezone.utc).date()
        record = await self.repo.get_staff_attendance_by_date(user_id, today)
        if not record:
            raise BadRequestException("No active duty check-in found for today.")

        now = datetime.now(timezone.utc)
        record.check_out_time = now
        if notes:
            record.notes = (record.notes or "") + f" [Check-out: {notes}]"
        await self.session.flush()

        await self.audit_repo.record_event(
            action="STAFF_DUTY_CHECKED_OUT",
            resource_type="staff_attendance",
            resource_id=str(record.id),
            actor_id=actor_id or user_id,
            facility_id=record.facility_id,
            new_state={"check_out_time": now.isoformat()},
            ip_address=ip_address,
            user_agent=user_agent,
        )
        return record

    async def get_staff_attendance_today(self, user_id: uuid.UUID) -> Optional[StaffAttendance]:
        today = datetime.now(timezone.utc).date()
        return await self.repo.get_staff_attendance_by_date(user_id, today)

    # ============================================================================
    # DOCTOR OPD QUEUE & CLINICAL ENCOUNTER WORKFLOW (Role 02)
    # ============================================================================
    async def get_doctor_opd_queue(
        self,
        facility_id: uuid.UUID,
        doctor_id: Optional[uuid.UUID] = None,
        target_date: Optional[date] = None,
    ) -> List[DoctorOPDQueueItem]:
        appointments = await self.repo.list_opd_queue(
            facility_id=facility_id,
            target_date=target_date,
            doctor_id=doctor_id,
        )

        today = datetime.now(timezone.utc).date()
        items = []
        for appt in appointments:
            p = appt.patient
            age = today.year - p.date_of_birth.year - (
                (today.month, today.day) < (p.date_of_birth.month, p.date_of_birth.day)
            )

            latest_vitals_dto = None
            if appt.consultation and appt.consultation.vitals_records:
                latest_v = appt.consultation.vitals_records[-1]
                latest_vitals_dto = VitalsResponse.model_validate(latest_v)

            items.append(
                DoctorOPDQueueItem(
                    appointment_id=appt.id,
                    patient_id=p.id,
                    patient_name=f"{p.first_name} {p.last_name}",
                    uhid=p.patient_identifier,
                    gender=p.gender,
                    age_years=age,
                    token_number=appt.token_number or 0,
                    priority=appt.priority,
                    time_slot=appt.time_slot,
                    status=appt.status,
                    appointment_date=appt.appointment_date,
                    reason=appt.reason,
                    latest_vitals=latest_vitals_dto,
                )
            )
        return items

    # ============================================================================
    # NURSE TRIAGE VITALS & EARLY WARNING SCORING (Role 03)
    # ============================================================================
    async def record_nurse_triage_vitals(
        self,
        appointment_id: uuid.UUID,
        vitals_data: VitalsCreate,
        nurse_id: uuid.UUID,
        actor_id: Optional[uuid.UUID] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> Tuple[Vitals, Appointment]:
        appt = await self.repo.get_appointment_by_id(appointment_id)
        if not appt:
            raise ResourceNotFoundException("Appointment", str(appointment_id))

        # 1. Automated Early Warning Score / Triage Priority Evaluation
        is_emergency = False
        is_priority = False
        triage_flags = []

        if vitals_data.spo2_percent is not None and vitals_data.spo2_percent < 90:
            is_emergency = True
            triage_flags.append(f"Critical Hypoxia (SpO2 {vitals_data.spo2_percent}%)")
        elif vitals_data.spo2_percent is not None and vitals_data.spo2_percent < 95:
            is_priority = True
            triage_flags.append(f"Suboptimal SpO2 ({vitals_data.spo2_percent}%)")

        if vitals_data.systolic_bp is not None:
            if vitals_data.systolic_bp >= 180 or vitals_data.systolic_bp < 80:
                is_emergency = True
                triage_flags.append(f"Hypertensive Crisis/Shock (SBP {vitals_data.systolic_bp})")
            elif vitals_data.systolic_bp >= 140 or (vitals_data.diastolic_bp and vitals_data.diastolic_bp >= 90):
                is_priority = True
                triage_flags.append("Stage-2 Hypertension")

        if vitals_data.pulse_rate is not None:
            if vitals_data.pulse_rate >= 130 or vitals_data.pulse_rate < 40:
                is_emergency = True
                triage_flags.append(f"Severe Arrhythmia/Tachycardia (Pulse {vitals_data.pulse_rate})")
            elif vitals_data.pulse_rate >= 100:
                is_priority = True
                triage_flags.append("Tachycardia")

        if vitals_data.temperature_celsius is not None:
            if vitals_data.temperature_celsius >= 39.5:
                is_emergency = True
                triage_flags.append(f"Hyperpyrexia ({vitals_data.temperature_celsius}°C)")
            elif vitals_data.temperature_celsius >= 38.0:
                is_priority = True
                triage_flags.append("High Fever")

        if is_emergency:
            calculated_priority = "EMERGENCY"
        elif is_priority:
            calculated_priority = "PRIORITY"
        else:
            calculated_priority = "ROUTINE"

        # Elevate appointment priority if triage detected higher acuity
        if calculated_priority == "EMERGENCY" or (calculated_priority == "PRIORITY" and appt.priority != "EMERGENCY"):
            appt.priority = calculated_priority

        # 2. Ensure linked consultation exists for recording vitals
        consultation = await self.repo.get_consultation_by_appointment(appointment_id)
        if not consultation:
            consultation = Consultation(
                appointment_id=appt.id,
                patient_id=appt.patient_id,
                doctor_id=appt.doctor_id or nurse_id,
                facility_id=appt.facility_id,
                status=ConsultationStatus.IN_PROGRESS,
                chief_complaint=appt.reason,
                started_at=datetime.now(timezone.utc),
            )
            await self.repo.create_consultation(consultation)

        # 3. Calculate BMI
        bmi = None
        if vitals_data.weight_kg and vitals_data.height_cm and vitals_data.height_cm > 0:
            h_m = vitals_data.height_cm / 100.0
            bmi = round(vitals_data.weight_kg / (h_m * h_m), 1)

        triage_notes = ", ".join(triage_flags) if triage_flags else (vitals_data.triage_notes or "Normal vitals")
        vitals = Vitals(
            consultation_id=consultation.id,
            systolic_bp=vitals_data.systolic_bp,
            diastolic_bp=vitals_data.diastolic_bp,
            pulse_rate=vitals_data.pulse_rate,
            temperature_celsius=vitals_data.temperature_celsius,
            respiratory_rate=vitals_data.respiratory_rate,
            spo2_percent=vitals_data.spo2_percent,
            weight_kg=vitals_data.weight_kg,
            height_cm=vitals_data.height_cm,
            bmi=bmi,
            triage_level=calculated_priority,
            triage_notes=triage_notes,
            recorded_by_id=nurse_id,
            recorded_at=datetime.now(timezone.utc),
        )
        saved_vitals = await self.repo.create_vitals(vitals)

        # Mark appointment checked-in and ready for doctor
        if appt.status == AppointmentStatus.SCHEDULED:
            appt.status = AppointmentStatus.CHECKED_IN

        await self.session.flush()

        await self.audit_repo.record_event(
            action="NURSE_TRIAGE_VITALS_RECORDED",
            resource_type="vitals",
            resource_id=str(saved_vitals.id),
            actor_id=actor_id or nurse_id,
            facility_id=appt.facility_id,
            new_state={
                "triage_level": calculated_priority,
                "appointment_id": str(appt.id),
                "token_number": appt.token_number,
            },
            ip_address=ip_address,
            user_agent=user_agent,
        )
        return saved_vitals, appt

    # ============================================================================
    # DOCTOR CLINICAL AI ADVISORY (STG & Contraindication Screening)
    # ============================================================================
    async def get_doctor_clinical_advisory(
        self, request: DoctorClinicalAdvisoryRequest
    ) -> DoctorClinicalAdvisoryResponse:
        code = (request.icd10_code or "").upper()
        name = (request.condition_name or "").lower()
        allergies = (request.patient_allergies or "").lower()
        chronics = (request.patient_chronic_conditions or "").lower()
        lang = request.language or "en"

        # 1. Condition & Protocol Resolution
        if "I10" in code or "hypertension" in name or "bp" in name:
            condition = "Primary Essential Hypertension (ICD-10 I10)"
            stg = (
                "Tamil Nadu STG: Step 1 monotherapy with Amlodipine 5mg OD or Telmisartan 40mg OD. "
                "Step 2 combination: Amlodipine 5mg + Telmisartan 40mg. Monitor BP every 2-4 weeks until target <130/80 mmHg."
            )
            recommended = ["Amlodipine 5mg", "Telmisartan 40mg", "Hydrochlorothiazide 12.5mg"]
            monitoring = ["Serum Creatinine & eGFR", "Serum Electrolytes (K+)", "Urine Albumin/Creatinine ratio"]
            counseling = [
                "Strict dietary sodium restriction (<2g sodium = 1 level teaspoon salt per day).",
                "Minimum 30 mins brisk walking 5 days a week.",
                "Avoid stopping medication abruptly even when feeling well.",
            ]
        elif "E11" in code or "diabetes" in name or "sugar" in name:
            condition = "Type 2 Diabetes Mellitus (ICD-10 E11)"
            stg = (
                "Tamil Nadu STG: First-line Metformin 500mg BD after meals, titrate to 1000mg BD. "
                "Add Glimepiride 1mg-2mg OD before breakfast if HbA1c > 7.5% after 3 months. Target HbA1c < 7.0%."
            )
            recommended = ["Metformin 500mg", "Glimepiride 1mg", "Teneligliptin 20mg"]
            monitoring = ["HbA1c every 90 days", "Fasting & Postprandial Blood Glucose", "Annual diabetic retinopathy & foot examination"]
            counseling = [
                "Emphasize complex millets, green vegetables, and low glycemic index foods.",
                "Daily foot inspection for calluses, blisters, or loss of sensation.",
                "Carry fast-acting glucose tablets or candy for hypoglycemia prevention.",
            ]
        elif "A90" in code or "dengue" in name:
            condition = "Dengue Fever / Febrile Syndrome (ICD-10 A90)"
            stg = (
                "Tamil Nadu STG: Supportive hydration with ORS and tender coconut water. "
                "Fever control STRICTLY with Paracetamol 500mg QDS. ABSOLUTE CONTRAINDICATION FOR NSAIDs & ASPIRIN."
            )
            recommended = ["Paracetamol 500mg", "Oral Rehydration Salts (ORS)"]
            monitoring = ["Daily CBC with Platelet count and Hematocrit", "Dengue NS1 Ag (Day 1-5) or IgM (Day 5+)", "Warning signs: persistent vomiting, abdominal pain, mucosal bleeding"]
            counseling = [
                "Drink minimum 2.5-3 liters fluids daily (ORS, rice kanji, lemon juice).",
                "Report immediately if severe abdominal pain, gum bleeding, or black stools occur.",
                "Use mosquito bed nets and eliminate water stagnation at home.",
            ]
        elif "D50" in code or "anemia" in name or "iron" in name:
            condition = "Iron Deficiency Anemia (ICD-10 D50)"
            stg = (
                "Tamil Nadu STG: Oral Iron & Folic Acid (IFA) 1 tablet BD with Vitamin C source. "
                "Deworming with Albendazole 400mg stat. Refer for parenteral iron sucrose if Hb < 7 g/dL."
            )
            recommended = ["Iron & Folic Acid (100mg elemental iron + 500mcg folic acid)", "Albendazole 400mg", "Vitamin C 500mg"]
            monitoring = ["Repeat Hemoglobin after 30 days (expected rise >= 1 g/dL)", "Peripheral blood smear"]
            counseling = [
                "Take IFA with lemon water or amla; DO NOT take with tea or milk.",
                "Include drumstick leaves (moringa), dates, jaggery, and sundal in daily meals.",
            ]
        else:
            condition = request.condition_name or "General Clinical Encounter"
            stg = "Follow Tamil Nadu Primary Health Centre Standard Treatment Protocols. Prioritize essential generic medicines."
            recommended = ["Paracetamol 500mg", "ORS Packets", "Cetirizine 10mg"]
            monitoring = ["Routine vital signs", "Clinical reassessment in 3-5 days"]
            counseling = ["Adequate hydration, balanced nutrition, and completion of full prescribed course."]

        # 2. Contraindication & Allergy Screening
        contraindications = []
        interactions = []

        proposed_lower = [m.lower() for m in request.proposed_medications]

        # Penicillin / Beta-lactam allergy
        if "penicillin" in allergies:
            for p in proposed_lower:
                if any(x in p for x in ["amoxicillin", "ampicillin", "penicillin", "augmentin"]):
                    contraindications.append(
                        f"CRITICAL CONTRAINDICATION: Patient has documented Penicillin allergy. '{p}' must NOT be prescribed. Risk of severe anaphylaxis."
                    )

        # Sulfa allergy
        if "sulfa" in allergies or "sulfonamide" in allergies:
            for p in proposed_lower:
                if any(x in p for x in ["cotrimoxazole", "bactrim", "septrin", "sulfamethoxazole"]):
                    contraindications.append(
                        f"CRITICAL CONTRAINDICATION: Patient has documented Sulfa allergy. '{p}' can trigger Stevens-Johnson syndrome."
                    )

        # Dengue + NSAID risk
        if "dengue" in condition.lower() or "dengue" in name:
            for p in proposed_lower:
                if any(x in p for x in ["diclofenac", "ibuprofen", "aspirin", "aceclofenac", "combiflam"]):
                    contraindications.append(
                        f"ABSOLUTE CONTRAINDICATION: NSAID '{p}' in suspected Dengue increases capillary fragility and causes severe gastrointestinal hemorrhage."
                    )

        # Asthma + Beta-Blocker risk
        if "asthma" in chronics:
            for p in proposed_lower:
                if any(x in p for x in ["propranolol", "atenolol", "metoprolol"]):
                    contraindications.append(
                        f"WARNING: Beta-blocker '{p}' in an asthmatic patient can precipitate severe life-threatening bronchospasm."
                    )

        # CKD + NSAID risk
        if any(x in chronics for x in ["ckd", "kidney", "renal"]):
            for p in proposed_lower:
                if any(x in p for x in ["diclofenac", "ibuprofen", "aceclofenac", "naproxen"]):
                    contraindications.append(
                        f"WARNING: NSAID '{p}' in chronic renal disease causes acute decline in GFR and worsening azotemia."
                    )

        disclaimer = (
            "This advisory is a clinical decision-support tool aligned with Tamil Nadu STG guidelines. "
            "The treating Medical Officer retains final professional diagnostic and prescribing responsibility."
        )

        return DoctorClinicalAdvisoryResponse(
            condition=condition,
            stg_protocol=stg,
            recommended_drugs=recommended,
            contraindication_warnings=contraindications,
            interaction_alerts=interactions,
            monitoring_parameters=monitoring,
            patient_counseling_points=counseling,
            language=lang,
            disclaimer=disclaimer,
        )

    # ============================================================================
    # NURSE IMMUNIZATION & ANC GUIDANCE (Role 03)
    # ============================================================================
    async def get_nurse_immunization_guidance(
        self, request: NurseImmunizationGuidanceRequest
    ) -> NurseImmunizationGuidanceResponse:
        lang = request.language or "en"
        due = []
        upcoming = []
        anc_guidance = None
        red_flags = []

        if request.is_pregnant:
            category = "Maternal & Antenatal Care (ANC) Protocol"
            gw = request.gestational_weeks or 12
            if gw <= 12:
                anc_guidance = "1st Trimester: Register within 12 weeks, Hb, Blood grouping, Urine Albumin/Sugar, HIV/HBsAg/VDRL, USG Dating scan, Td-1."
                due = ["Td-1 (Tetanus-diphtheria)", "Folic Acid 5mg daily"]
                upcoming = ["Td-2 (at 16-20 weeks)", "IFA & Calcium tablets starting from 2nd trimester"]
            elif 13 <= gw <= 26:
                anc_guidance = "2nd Trimester: Anomaly Scan (18-20 weeks), Oral Glucose Challenge Test (OGCT), Td-2, start IFA 1 tab BD and Calcium 500mg BD."
                due = ["Td-2 (if 4 weeks after Td-1)", "IFA tablets (100mg elemental iron)", "Calcium 500mg tablets"]
                upcoming = ["Growth Scan at 28-32 weeks", "Repeat Hb test"]
            else:
                anc_guidance = "3rd Trimester: Bi-weekly visits until 36 weeks, then weekly. Birth preparedness plan, verify institutional delivery facility, verify 108 readiness."
                due = ["IFA and Calcium ongoing", "Repeat Hemoglobin check", "Blood pressure & weight monitoring"]
                upcoming = ["Institutional delivery registration at PHC/Government Hospital"]

            red_flags = [
                "Severe headache, blurred vision, or epigastric pain (Pre-eclampsia warning)",
                "Vaginal bleeding or watery discharge (Placenta previa / PROM)",
                "Decreased fetal movements after 28 weeks (<10 movements in 12 hours)",
                "Hemoglobin < 7 g/dL (Severe anemia requiring hospital referral)",
            ]
        else:
            category = "Universal Immunization Program (UIP - Tamil Nadu)"
            months = request.patient_age_months if request.patient_age_months is not None else 0

            if months < 1:
                due = ["BCG (0.1 ml Intradermal left arm)", "OPV-0 (2 drops oral)", "Hepatitis B birth dose (0.5 ml IM within 24h)"]
                upcoming = ["Pentavalent-1, OPV-1, Rotavirus-1, fIPV-1, PCV-1 at 6 weeks"]
            elif 1 <= months < 2:
                due = ["Pentavalent-1 (0.5 ml IM anterolateral thigh)", "OPV-1 (2 drops)", "Rotavirus-1 (5 drops)", "fIPV-1 (0.1 ml ID right arm)", "PCV-1 (0.5 ml IM)"]
                upcoming = ["Pentavalent-2, OPV-2, Rotavirus-2 at 10 weeks"]
            elif 2 <= months < 3:
                due = ["Pentavalent-2 (0.5 ml IM)", "OPV-2 (2 drops)", "Rotavirus-2 (5 drops)"]
                upcoming = ["Pentavalent-3, OPV-3, Rotavirus-3, fIPV-2, PCV-2 at 14 weeks"]
            elif 3 <= months < 9:
                due = ["Pentavalent-3 (0.5 ml IM)", "OPV-3 (2 drops)", "Rotavirus-3 (5 drops)", "fIPV-2 (0.1 ml ID)", "PCV-2 (0.5 ml IM)"]
                upcoming = ["MR-1, PCV-Booster, Vitamin A 1st dose at 9 months completed"]
            elif 9 <= months < 16:
                due = ["MR-1 (Measles-Rubella 0.5 ml SC)", "PCV Booster (0.5 ml IM)", "Vitamin A 1st dose (1 ml / 1 lakh IU oral)"]
                upcoming = ["MR-2, DPT Booster-1, OPV Booster, Vitamin A-2 at 16-24 months"]
            elif 16 <= months < 60:
                due = ["MR-2 (0.5 ml SC)", "DPT Booster-1 (0.5 ml IM)", "OPV Booster (2 drops)", "Vitamin A-2 (2 ml / 2 lakh IU)"]
                upcoming = ["DPT Booster-2 at 5-6 years"]
            else:
                due = ["DPT Booster-2 at 5-6 years" if months <= 72 else "Td vaccine at 10 years and 16 years"]
                upcoming = ["Annual deworming with Albendazole", "Bi-annual Vitamin A until 5 years"]

            red_flags = [
                "High fever > 39.5°C or persistent crying > 3 hours post-immunization",
                "Convulsions or lethargy",
                "Abscess or swelling at injection site",
            ]

        cold_chain = "Cold Chain Requirement: Maintain ILR temperature between +2°C and +8°C. Do NOT freeze Td, Pentavalent, or Hepatitis-B."

        return NurseImmunizationGuidanceResponse(
            category=category,
            due_vaccines=due,
            upcoming_vaccines=upcoming,
            anc_milestone_guidance=anc_guidance,
            triage_red_flags=red_flags,
            cold_chain_reminder=cold_chain,
            language=lang,
        )

    # ========================================================================
    # ROLE 05: LAB TECHNICIAN & PATHOLOGIST PORTAL METHODS
    # ========================================================================

    async def get_lab_worklist(
        self,
        facility_id: uuid.UUID,
        status: Optional[LabOrderStatus] = None,
        test_category: Optional[str] = None,
    ) -> List[LabWorklistItem]:
        orders = await self.repo.list_lab_worklist(
            facility_id=facility_id,
            status=status,
            test_category=test_category,
        )
        today = date.today()
        worklist = []
        for order in orders:
            p = order.patient
            d = order.doctor

            # Calculate age
            age = None
            if p and p.date_of_birth:
                age = today.year - p.date_of_birth.year - (
                    (today.month, today.day) < (p.date_of_birth.month, p.date_of_birth.day)
                )

            # Check critical alerts
            has_crit = any(bool(r.critical_alert) or r.is_abnormal for r in order.results)

            worklist.append(
                LabWorklistItem(
                    id=order.id,
                    consultation_id=order.consultation_id,
                    patient_id=order.patient_id,
                    patient_name=f"{p.first_name} {p.last_name}" if p else "Unknown",
                    patient_identifier=p.patient_identifier if p else "",
                    age=age,
                    gender=p.gender.value if p and hasattr(p.gender, "value") else (str(p.gender) if p else None),
                    doctor_name=f"Dr. {d.full_name}" if d else "Medical Officer",
                    test_category=order.test_category,
                    clinical_notes=order.clinical_notes,
                    sample_type=order.sample_type,
                    sample_barcode=order.sample_barcode,
                    sample_collected_at=order.sample_collected_at,
                    status=order.status,
                    ordered_at=order.ordered_at,
                    results=order.results,
                    has_critical_alert=has_crit,
                )
            )
        return worklist

    def get_diagnostic_guidance(self, request: LabDiagnosticGuidanceRequest) -> LabDiagnosticGuidanceResponse:
        t_name = request.test_name.strip()
        val = request.result_value.strip()
        lang = request.language.lower() if request.language else "en"

        is_crit, crit_msg = self.evaluate_critical_lab_value(t_name, val, is_pregnant=request.is_pregnant)

        # Knowledge base of common PHC lab tests
        t_lower = t_name.lower()

        if "hemoglobin" in t_lower or "hb" in t_lower:
            interp_en = f"Hemoglobin level recorded at {val} g/dL."
            interp_ta = f"ஹீமோகுளோபின் அளவு {val} g/dL என பதிவாகியுள்ளது."
            action_en = "Ensure dietary counseling, IFA tablet supplementation, and follow-up in 1 month if mild/moderate. Severe anemia (<7 g/dL) requires immediate doctor review."
            action_ta = "லேசான/நடுத்தர இரத்த சோகைக்கு இரும்புச்சத்து மாத்திரைகள் மற்றும் உணவுக் கட்டுப்பாடு வழங்கவும். தீவிர இரத்த சோகைக்கு (<7 g/dL) உடனடி மருத்துவர் பரிசீலனை தேவை."
            mandate = "RMNCH+A ANC High-Risk Pregnancy Registry (if pregnant and Hb < 11)"
            refs = ["Tamil Nadu Standard Treatment Guidelines 2023", "National Anemia Mukt Bharat Protocol"]
        elif "glucose" in t_lower or "sugar" in t_lower or "rbs" in t_lower or "fbs" in t_lower:
            interp_en = f"Blood Glucose measured at {val} mg/dL."
            interp_ta = f"இரத்த சர்க்கரை அளவு {val} mg/dL என அளவிடப்பட்டுள்ளது."
            action_en = "Verify fasting/postprandial state. Assess for diabetic ketoacidosis symptoms if >300 mg/dL. Adjust hypoglycemic therapy per STG."
            action_ta = "நோயாளி சாப்பிட்ட நேரத்தை சரிபார்க்கவும். சர்க்கரை >300 mg/dL இருந்தால் DKA அறிகுறிகளை கவனிக்கவும். நெறிமுறைப்படி மருந்தை சரிசெய்யவும்."
            mandate = "NPCDCS Non-Communicable Disease Registry"
            refs = ["Tamil Nadu STG Diabetes Mellitus 2023", "ICMR Guidelines for Type 2 Diabetes"]
        elif "platelet" in t_lower:
            interp_en = f"Platelet count reported at {val}/µL."
            interp_ta = f"பிளேட்லெட் எண்ணிக்கை {val}/µL என பதிவாகியுள்ளது."
            action_en = "Values <100,000/µL require daily hematocrit and platelet monitoring. <50,000/µL indicates high bleeding risk; keep blood bank on standby."
            action_ta = "<100,000/µL எனில் தினசரி இரத்த பரிசோதனை தேவை. <50,000/µL தீவிர இரத்தப்போக்கு அபாயத்தை குறிக்கிறது; இரத்த வங்கியை தயார் நிலையில் வைக்கவும்."
            mandate = "IDSP Daily Dengue/Vector-borne Surveillance"
            refs = ["Tamil Nadu STG Dengue Clinical Management 2023", "NVBDCP Guidelines"]
        elif "dengue" in t_lower:
            interp_en = f"Dengue Diagnostic Test finding: {val}."
            interp_ta = f"டெங்கு கண்டறியும் பரிசோதனை முடிவு: {val}."
            action_en = "Positive results require immediate notification to IDSP unit, fluid balance chart maintenance, and warning signs monitoring (abdominal pain, vomiting, mucosal bleed)."
            action_ta = "பாசிட்டிவ் எனில் உடனடியாக IDSP-க்கு தகவல் தெரிவிக்கவும். நோயாளிக்கு போதிய நீரேற்றம் மற்றும் எச்சரிக்கை அறிகுறிகளை கண்காணிக்கவும்."
            mandate = "IDSP Form L (Immediate Notifiable Disease)"
            refs = ["Tamil Nadu Guidelines on Dengue Fever Management", "NVBDCP"]
        elif "malaria" in t_lower:
            interp_en = f"Malaria Diagnostic Test finding: {val}."
            interp_ta = f"மலேரியா கண்டறியும் பரிசோதனை முடிவு: {val}."
            action_en = "Positive cases require radical treatment with Artemisinin-based Combination Therapy (ACT) or Chloroquine + Primaquine as per species."
            action_ta = "பாசிட்டிவ் எனில் NVBDCP வழிகாட்டுதலின்படி உடனடியாக ACT அல்லது குளோரோகுயின் சிகிச்சை தொடங்க வேண்டும்."
            mandate = "NVBDCP Malaria Elimination Registry (Form M-1)"
            refs = ["National Vector Borne Disease Control Programme Guidelines 2023"]
        elif "sputum" in t_lower or "afb" in t_lower or "tb" in t_lower:
            interp_en = f"Sputum Examination finding: {val}."
            interp_ta = f"கபம் பரிசோதனை முடிவு: {val}."
            action_en = "Positive smear indicates active pulmonary tuberculosis. Immediately register on Nikshay, initiate weight-banded FDC treatment, and screen household contacts."
            action_ta = "பாசிட்டிவ் எனில் நிக்ஷய் தளத்தில் பதிவு செய்து, உடனடியாக FDC மாத்திரை சிகிச்சை தொடங்கவும், குடும்பத்தினரை பரிசோதிக்கவும்."
            mandate = "NTEP Nikshay Portal (Mandatory Notification under Clinical Establishments Act)"
            refs = ["National Tuberculosis Elimination Programme (NTEP) Technical Guidelines"]
        else:
            interp_en = f"Test '{t_name}' evaluated with result '{val}'."
            interp_ta = f"'{t_name}' பரிசோதனை முடிவு '{val}' என மதிப்பிடப்பட்டுள்ளது."
            action_en = "Correlate with clinical findings and doctor prescription. Verify abnormal values with sample recollection if hemolysis or clot suspected."
            action_ta = "மருத்துவ அறிகுறிகளுடன் ஒப்பிட்டு பார்க்கவும். சந்தேகம் இருப்பின் மீண்டும் மாதிரி எடுத்து பரிசோதிக்கவும்."
            mandate = None
            refs = ["Tamil Nadu Essential Diagnostic List (EDL)"]

        crit_ta = "ஆபத்தான பரிசோதனை முடிவு கண்டறியப்பட்டுள்ளது. உடனடி மருத்துவ கவனிப்பு தேவை." if is_crit else None

        return LabDiagnosticGuidanceResponse(
            test_name=t_name,
            result_value=val,
            interpretation_en=interp_en,
            interpretation_ta=interp_ta,
            is_critical=is_crit,
            critical_alert_en=crit_msg,
            critical_alert_ta=crit_ta,
            action_guidance_en=action_en,
            action_guidance_ta=action_ta,
            reporting_mandate=mandate,
            references=refs,
        )


