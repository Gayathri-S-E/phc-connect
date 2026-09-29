// Master TypeScript definitions for PHC Connect (Smart Health & Supply Chain Resilience)

export type ScopeLevel = 'GLOBAL' | 'STATE' | 'DISTRICT' | 'FACILITY' | 'SELF';

export type RoleCode = 
  | 'PATIENT'
  | 'DOCTOR'
  | 'NURSE'
  | 'PHC_IN_CHARGE'
  | 'PHARMACIST'
  | 'DISTRICT_HEALTH_OFFICER'
  | 'DISTRICT_SUPPLY_OFFICER'
  | 'DISTRICT_EMERGENCY_COORDINATOR'
  | 'STATE_HEALTH_ADMIN'
  | 'STATE_SUPPLY_MANAGER'
  | 'STATE_PUBLIC_HEALTH_ANALYST'
  | 'NATIONAL_HEALTH_AUTHORITY'
  | 'SUPER_ADMIN'
  | 'SYSTEM_ADMIN'
  | 'AUDITOR'
  | 'LAB_TECHNICIAN'
  | 'INVENTORY_OFFICER';

export interface UserRoleAssignment {
  id: string;
  role_id: string;
  role_code: RoleCode;
  role_name: string;
  facility_id?: string | null;
  organization_id?: string | null;
  scope_level: ScopeLevel;
}

export interface UserProfile {
  id: string;
  email: string;
  first_name: string;
  last_name: string;
  full_name?: string;
  phone_number?: string | null;
  is_active: boolean;
  is_verified: boolean;
  facility_id?: string | null;
  facility_name?: string | null;
  district?: string | null;
  state?: string | null;
  roles: (UserRoleAssignment | string)[];
  permissions: string[];
}

export interface AuthTokens {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in?: number;
}

export interface LoginResponse {
  data: {
    user: UserProfile;
    tokens: AuthTokens;
  };
}

export interface NavigationItem {
  section: string;
  key: string;
  path: string;
  icon: string;
}

export interface NavigationResponse {
  data: {
    items: NavigationItem[];
    permissions: string[];
    roles: any[];
    scope: string;
  };
}

export interface ApiError {
  status: number;
  title: string;
  detail: string;
  type?: string;
  validationErrors?: Record<string, string[]>;
}

// Healthcare & Clinical Models
export interface Appointment {
  id: string;
  patient_id: string;
  patient_name?: string;
  facility_id: string;
  doctor_id?: string;
  doctor_name?: string;
  appointment_date: string;
  slot_time: string;
  token_number: number;
  status: 'SCHEDULED' | 'CHECKED_IN' | 'IN_CONSULTATION' | 'COMPLETED' | 'CANCELLED';
  reason_for_visit?: string;
  triage_score?: number;
  created_at: string;
}

export interface PatientVitals {
  id?: string;
  patient_id: string;
  systolic_bp: number;
  diastolic_bp: number;
  heart_rate: number;
  respiratory_rate: number;
  temperature: number;
  spo2: number;
  blood_sugar?: number;
  early_warning_score?: number;
  recorded_at?: string;
}

export interface Consultation {
  id: string;
  appointment_id?: string;
  patient_id: string;
  doctor_id: string;
  chief_complaints: string;
  examination_notes?: string;
  diagnosis_codes: string[];
  status: 'IN_PROGRESS' | 'FINALIZED';
  created_at: string;
}

export interface PrescriptionItem {
  id?: string;
  medication_id: string;
  medication_name?: string;
  generic_name?: string;
  dosage: string;
  frequency: string;
  duration_days: number;
  quantity_prescribed: number;
  quantity_dispensed?: number;
  instructions?: string;
  batch_number?: string;
}

export interface Prescription {
  id: string;
  consultation_id?: string;
  patient_id: string;
  patient_name?: string;
  doctor_id: string;
  doctor_name?: string;
  facility_id: string;
  facility_name?: string;
  status: 'PENDING_DISPENSING' | 'PARTIALLY_DISPENSED' | 'DISPENSED' | 'CANCELLED';
  items: PrescriptionItem[];
  created_at: string;
}

export interface LabOrder {
  id: string;
  consultation_id?: string;
  patient_id: string;
  patient_name?: string;
  doctor_id: string;
  test_names: string[];
  priority: 'ROUTINE' | 'URGENT';
  status: 'PENDING_COLLECTION' | 'SAMPLE_COLLECTED' | 'PROCESSING' | 'COMPLETED' | 'VERIFIED';
  results?: Array<{
    test_name: string;
    value: string;
    unit: string;
    reference_range: string;
    is_abnormal: boolean;
  }>;
  created_at: string;
}

// Inventory & Supply Chain Models
export interface InventoryItem {
  id: string;
  facility_id: string;
  facility_name?: string;
  medication_id: string;
  medication_code?: string;
  generic_name: string;
  brand_name?: string;
  dosage_form: string;
  strength: string;
  quantity_on_hand: number;
  quantity_reserved: number;
  reorder_level: number;
  unit: string;
  is_low_stock?: boolean;
}

export interface InventoryBatch {
  id: string;
  inventory_item_id: string;
  batch_number: string;
  manufacture_date?: string;
  expiry_date: string;
  current_quantity: number;
  status: 'ACTIVE' | 'QUARANTINED' | 'EXPIRED' | 'RECALLED';
  days_to_expiry?: number;
}

export interface SupplyRequest {
  id: string;
  request_number: string;
  facility_id: string;
  facility_name?: string;
  district?: string;
  medication_id: string;
  medication_name?: string;
  requested_quantity: number;
  approved_quantity?: number;
  priority: 'ROUTINE' | 'URGENT' | 'EMERGENCY';
  status: 'PENDING_REVIEW' | 'ALLOCATED' | 'DISPATCHED' | 'RECEIVED' | 'REJECTED' | 'ESCALATED_STATE';
  clinical_justification?: string;
  created_at: string;
}

export interface StockTransfer {
  id: string;
  transfer_number: string;
  source_facility_id: string;
  source_facility_name?: string;
  destination_facility_id: string;
  destination_facility_name?: string;
  medication_id: string;
  medication_name?: string;
  quantity: number;
  status: 'PENDING_APPROVAL' | 'APPROVED' | 'IN_TRANSIT' | 'RECEIVED' | 'CANCELLED';
  created_at: string;
}

// Governance, Emergency & Analytics Models
export interface GovernanceAction {
  id: string;
  title: string;
  description: string;
  priority: 'ROUTINE' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
  status: 'PENDING' | 'IN_PROGRESS' | 'RESPONDED' | 'CLOSED' | 'OVERDUE';
  facility_id?: string;
  facility_name?: string;
  district?: string;
  state?: string;
  due_at?: string;
  created_at: string;
}

export interface EmergencyIncident {
  id: string;
  title: string;
  category: 'EPIDEMIC' | 'NATURAL_DISASTER' | 'MASS_CASUALTY' | 'INFRASTRUCTURE' | 'COLD_CHAIN_FAILURE';
  severity: 'MODERATE' | 'MAJOR' | 'CRITICAL';
  status: 'ACTIVE' | 'CONTAINED' | 'RESOLVED';
  district: string;
  state: string;
  description: string;
  affected_facilities?: Array<{ id: string; name: string }>;
  created_at: string;
}
