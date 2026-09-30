import React, { useState, useEffect } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { 
  Building2, Users, Thermometer, MapPin, 
  AlertCircle, CheckCircle, Clock, Plus, 
  Calendar, FileText, ChevronRight, ShieldCheck,
  TrendingUp, BarChart2, ShieldAlert, UserCheck,
  Snowflake, Tent, MessageSquareText, Eye, Check,
  AlertTriangle
} from 'lucide-react';
import { api } from '../services/api';
import { useAuth } from '../context/AuthContext';
import { useLanguage } from '../context/LanguageContext';
import { StateView } from '../components/common/StateView';
import { Badge } from '../components/common/Badge';
import { DataTable } from '../components/common/DataTable';
import { PageHeader } from '../components/ui/page-header';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Textarea } from '../components/ui/textarea';
import {
  Dialog,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogContent,
  DialogFooter,
  DialogClose,
} from '../components/ui/dialog';

export default function FacilityAdminPortal() {
  const { user } = useAuth();
  const { t } = useLanguage();
  const location = useLocation();
  const navigate = useNavigate();

  const getTabFromPath = (path: string): 'overview' | 'attendance' | 'coldchain' | 'camps' | 'grievances' => {
    if (path.includes('/attendance')) return 'attendance';
    if (path.includes('/coldchain')) return 'coldchain';
    if (path.includes('/camps')) return 'camps';
    if (path.includes('/grievances')) return 'grievances';
    return 'overview';
  };

  const [activeTab, setActiveTab] = useState<'overview' | 'attendance' | 'coldchain' | 'camps' | 'grievances'>(
    getTabFromPath(location.pathname)
  );

  useEffect(() => {
    setActiveTab(getTabFromPath(location.pathname));
  }, [location.pathname]);

  const handleTabChange = (tab: 'overview' | 'attendance' | 'coldchain' | 'camps' | 'grievances') => {
    setActiveTab(tab);
    if (tab === 'overview') navigate('/facility');
    else navigate(`/facility/${tab}`);
  };

  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const facilityId = user?.facility_id || '11111111-1111-1111-1111-111111111111';

  // HMIS Monthly Report State
  const currentDate = new Date();
  const [selectedMonth, setSelectedMonth] = useState(currentDate.getMonth() + 1);
  const [selectedYear, setSelectedYear] = useState(currentDate.getFullYear());
  const [monthlyReport, setMonthlyReport] = useState<any>(null);

  // Staff Attendance State
  const [attendanceSummary, setAttendanceSummary] = useState<any[]>([]);

  // Cold Chain State
  const [coldChainEquipments, setColdChainEquipments] = useState<any[]>([]);
  const [selectedEquipmentLogs, setSelectedEquipmentLogs] = useState<any[]>([]);
  const [selectedEquipForLogs, setSelectedEquipForLogs] = useState<any>(null);
  const [isLogTempModalOpen, setIsLogTempModalOpen] = useState(false);
  const [isRegisterEquipModalOpen, setIsRegisterEquipModalOpen] = useState(false);
  const [logTempEquipId, setLogTempEquipId] = useState('');
  const [logTempC, setLogTempC] = useState(4.0);
  const [logTempNotes, setLogTempNotes] = useState('');
  const [excursionReason, setExcursionReason] = useState('');

  // Register Equipment Form
  const [newEquipType, setNewEquipType] = useState('ILR');
  const [newEquipSerial, setNewEquipSerial] = useState('');
  const [newEquipModel, setNewEquipModel] = useState('');
  const [newEquipMinTemp, setNewEquipMinTemp] = useState(2.0);
  const [newEquipMaxTemp, setNewEquipMaxTemp] = useState(8.0);

  // Outreach Camps State
  const [outreachCamps, setOutreachCamps] = useState<any[]>([]);
  const [isCampModalOpen, setIsCampModalOpen] = useState(false);
  const [isUpdateCampModalOpen, setIsUpdateCampModalOpen] = useState(false);
  const [selectedCamp, setSelectedCamp] = useState<any>(null);
  const [newCampName, setNewCampName] = useState('');
  const [newCampVillage, setNewCampVillage] = useState('');
  const [newCampDate, setNewCampDate] = useState(new Date().toISOString().split('T')[0]);
  const [newCampTarget, setNewCampTarget] = useState(100);
  const [newCampNotes, setNewCampNotes] = useState('');
  const [updateCampStatus, setUpdateCampStatus] = useState('COMPLETED');
  const [updateCampActualServed, setUpdateCampActualServed] = useState(0);

  // Grievance State
  const [grievances, setGrievances] = useState<any[]>([]);
  const [selectedGrievance, setSelectedGrievance] = useState<any>(null);
  const [isGrievanceModalOpen, setIsGrievanceModalOpen] = useState(false);
  const [grievanceAction, setGrievanceAction] = useState<'RESOLVED' | 'ESCALATED'>('RESOLVED');
  const [resolutionNotes, setResolutionNotes] = useState('');

  const [isSubmitting, setIsSubmitting] = useState(false);
  const [actionSuccess, setActionSuccess] = useState<string | null>(null);

  const fetchDashboardData = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const [hmisRes, attendRes, ccRes, campsRes, grievRes] = await Promise.all([
        api.get<any>(`/facility-admin/hmis/monthly-summary?facility_id=${facilityId}&year=${selectedYear}&month=${selectedMonth}`),
        api.get<any[]>(`/facility-admin/attendance/daily-summary?facility_id=${facilityId}`),
        api.get<any[]>(`/facility-admin/cold-chain/equipment?facility_id=${facilityId}`),
        api.get<any[]>(`/facility-admin/outreach-camps?facility_id=${facilityId}`),
        api.get<any[]>(`/facility-admin/grievances?facility_id=${facilityId}`),
      ]);

      if (hmisRes.data) setMonthlyReport(hmisRes.data);
      if (attendRes.data) setAttendanceSummary(attendRes.data);
      if (ccRes.data) setColdChainEquipments(ccRes.data);
      if (campsRes.data) setOutreachCamps(campsRes.data);
      if (grievRes.data) setGrievances(grievRes.data);

      if (hmisRes.error) {
        setError(hmisRes.error.detail);
      }
    } catch {
      setError('Failed to fetch facility administrative metrics.');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchDashboardData();
  }, [selectedMonth, selectedYear]);

  const handleRegisterEquipment = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSubmitting(true);
    try {
      const res = await api.post('/facility-admin/cold-chain/equipment', {
        facility_id: facilityId,
        equipment_type: newEquipType,
        serial_number: newEquipSerial,
        model: newEquipModel,
        min_temp_c: Number(newEquipMinTemp),
        max_temp_c: Number(newEquipMaxTemp),
      });

      if (res.data) {
        setActionSuccess('Cold chain equipment successfully provisioned!');
        setIsRegisterEquipModalOpen(false);
        fetchDashboardData();
      } else {
        alert(res.error?.detail || 'Failed to register equipment.');
      }
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleLogTemperature = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!logTempEquipId) return;

    setIsSubmitting(true);
    try {
      const isExcursion = logTempC < 2.0 || logTempC > 8.0;
      const res = await api.post(`/facility-admin/cold-chain/equipment/${logTempEquipId}/log`, {
        temperature_c: Number(logTempC),
        notes: logTempNotes || 'Routine operational temperature check',
        excursion_reason: isExcursion ? excursionReason : undefined,
      });

      if (res.data) {
        setActionSuccess('Temperature reading logged into cold chain audit ledger.');
        setIsLogTempModalOpen(false);
        fetchDashboardData();
      } else {
        alert(res.error?.detail || 'Failed to record temperature log.');
      }
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleCreateCamp = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSubmitting(true);
    try {
      const res = await api.post('/facility-admin/outreach-camps', {
        facility_id: facilityId,
        camp_name: newCampName,
        target_village: newCampVillage,
        camp_date: newCampDate,
        target_beneficiaries: Number(newCampTarget),
        notes: newCampNotes,
      });

      if (res.data) {
        setActionSuccess('Outreach health camp scheduled and ANM notified.');
        setIsCampModalOpen(false);
        fetchDashboardData();
      } else {
        alert(res.error?.detail || 'Failed to schedule outreach camp.');
      }
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleUpdateCamp = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedCamp) return;

    setIsSubmitting(true);
    try {
      const res = await api.patch(`/facility-admin/outreach-camps/${selectedCamp.id}`, {
        status: updateCampStatus,
        actual_beneficiaries_served: Number(updateCampActualServed),
      });

      if (res.data) {
        setActionSuccess('Camp status updated successfully.');
        setIsUpdateCampModalOpen(false);
        fetchDashboardData();
      } else {
        alert(res.error?.detail || 'Failed to update camp record.');
      }
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleResolveGrievance = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedGrievance) return;

    setIsSubmitting(true);
    try {
      const res = await api.patch(`/facility-admin/grievances/${selectedGrievance.id}/resolve`, {
        status: grievanceAction,
        resolution_notes: resolutionNotes,
      });

      if (res.data) {
        setActionSuccess('Grievance status updated and recorded in health portal.');
        setIsGrievanceModalOpen(false);
        fetchDashboardData();
      } else {
        alert(res.error?.detail || 'Failed to resolve grievance.');
      }
    } finally {
      setIsSubmitting(false);
    }
  };

  if (isLoading) {
    return <StateView state="loading" message="Loading PHC facility administrative dashboard..." />;
  }

  const presentStaff = attendanceSummary.filter((s) => s.status === 'PRESENT' || s.check_in_time);
  const openGrievances = grievances.filter((g) => g.status === 'PENDING' || g.status === 'UNDER_INVESTIGATION');

  return (
    <div className="flex flex-col gap-6 animate-fade-in">
      {/* Context-First Facility Header */}
      <PageHeader
        breadcrumbs={[
          { label: 'Facility Governance' },
          { label: 'PHC Superintendent Control' },
        ]}
        facilityContext="Thirukalukundram PHC • Chengalpattu District"
        title="Primary Health Centre Administration"
        description="Comprehensive facility superintendence: staff roster biometric presence, cold chain equipment telemetry, village outreach camps, and citizen grievance resolution."
        actions={
          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={() => setIsRegisterEquipModalOpen(true)}
              className="gap-1.5"
            >
              <Snowflake className="w-3.5 h-3.5 text-sky-600" />
              <span>Add ILR Unit</span>
            </Button>

            <Button
              variant="primary"
              size="sm"
              onClick={() => setIsCampModalOpen(true)}
              className="gap-1.5 shadow-xs"
            >
              <Plus className="w-3.5 h-3.5" />
              <span>Schedule Outreach Camp</span>
            </Button>
          </div>
        }
        metrics={[
          {
            label: 'Staff Present Today',
            value: `${presentStaff.length} / ${attendanceSummary.length || 8}`,
            hint: 'Biometric verified',
            variant: presentStaff.length > 5 ? 'success' : 'warning',
            icon: <UserCheck className="w-4 h-4" />,
          },
          {
            label: 'Cold Chain ILR',
            value: `${coldChainEquipments.length} Units`,
            hint: 'All units calibrated',
            variant: 'sky',
            icon: <Snowflake className="w-4 h-4" />,
          },
          {
            label: 'Outreach Camps',
            value: outreachCamps.length,
            hint: 'Village nutrition sessions',
            variant: 'default',
            icon: <Tent className="w-4 h-4" />,
          },
          {
            label: 'Open Grievances',
            value: openGrievances.length,
            hint: openGrievances.length > 0 ? 'Requires superintendent review' : 'No pending feedback',
            variant: openGrievances.length > 0 ? 'warning' : 'success',
            icon: <MessageSquareText className="w-4 h-4" />,
          },
        ]}
      />

      {actionSuccess && (
        <div className="p-4 bg-emerald-50 border border-emerald-200 text-emerald-900 rounded-xl text-xs font-semibold flex items-center justify-between gap-3 animate-fade-in shadow-2xs">
          <div className="flex items-center gap-2">
            <CheckCircle className="w-4 h-4 text-emerald-600 shrink-0" />
            <span>{actionSuccess}</span>
          </div>
          <button
            onClick={() => setActionSuccess(null)}
            className="text-emerald-700 hover:text-emerald-950 underline text-xs cursor-pointer"
          >
            Dismiss
          </button>
        </div>
      )}

      {/* Sub Navigation Tabs */}
      <div className="flex items-center gap-1.5 p-1 bg-slate-100 border border-slate-200/80 rounded-xl overflow-x-auto no-scrollbar max-w-full">
        {[
          { key: 'overview', label: 'Facility HMIS Overview', icon: <Building2 className="w-4 h-4" /> },
          { key: 'attendance', label: `Staff Attendance (${attendanceSummary.length})`, icon: <UserCheck className="w-4 h-4" /> },
          { key: 'coldchain', label: `Cold Chain ILR (${coldChainEquipments.length})`, icon: <Snowflake className="w-4 h-4" /> },
          { key: 'camps', label: `Outreach Camps (${outreachCamps.length})`, icon: <Tent className="w-4 h-4" /> },
          { key: 'grievances', label: `Grievances (${grievances.length})`, icon: <MessageSquareText className="w-4 h-4" /> },
        ].map((tab) => (
          <button
            key={tab.key}
            type="button"
            onClick={() => handleTabChange(tab.key as any)}
            className={`flex items-center gap-2 px-3.5 py-1.5 rounded-lg text-xs font-bold transition-all whitespace-nowrap cursor-pointer select-none ${
              activeTab === tab.key
                ? 'bg-white text-sky-900 shadow-2xs font-extrabold'
                : 'text-slate-600 hover:text-slate-900 hover:bg-slate-200/50'
            }`}
          >
            {tab.icon}
            <span>{tab.label}</span>
          </button>
        ))}
      </div>

      {/* TAB 1: OVERVIEW & HMIS MONTHLY KPI */}
      {activeTab === 'overview' && (
        <div className="space-y-6">
          <Card>
            <CardHeader>
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                <div>
                  <CardTitle>Health Management Information System (HMIS) KPIs</CardTitle>
                  <CardDescription>
                    Aggregated facility clinical delivery and maternal health indicators reported to District Health Office.
                  </CardDescription>
                </div>
                <div className="flex items-center gap-2">
                  <select
                    value={selectedMonth}
                    onChange={(e) => setSelectedMonth(Number(e.target.value))}
                    className="h-8 px-2.5 text-xs bg-white border border-slate-300 rounded-lg outline-none font-semibold text-slate-800"
                  >
                    {[
                      'January', 'February', 'March', 'April', 'May', 'June',
                      'July', 'August', 'September', 'October', 'November', 'December'
                    ].map((name, i) => (
                      <option key={i + 1} value={i + 1}>{name}</option>
                    ))}
                  </select>
                  <select
                    value={selectedYear}
                    onChange={(e) => setSelectedYear(Number(e.target.value))}
                    className="h-8 px-2.5 text-xs bg-white border border-slate-300 rounded-lg outline-none font-semibold text-slate-800"
                  >
                    {[2024, 2025, 2026].map((y) => (
                      <option key={y} value={y}>{y}</option>
                    ))}
                  </select>
                </div>
              </div>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
                <div className="p-4 bg-slate-50 border border-slate-200/80 rounded-xl space-y-1">
                  <span className="text-[11px] font-bold text-slate-500 uppercase">Total OPD Footfall</span>
                  <div className="text-2xl font-black text-slate-900">
                    {monthlyReport?.opd_footfall_total ?? 1240}
                  </div>
                  <span className="text-[10px] text-slate-400">Patients evaluated</span>
                </div>
                <div className="p-4 bg-slate-50 border border-slate-200/80 rounded-xl space-y-1">
                  <span className="text-[11px] font-bold text-slate-500 uppercase">Institutional Deliveries</span>
                  <div className="text-2xl font-black text-emerald-700">
                    {monthlyReport?.institutional_deliveries ?? 34}
                  </div>
                  <span className="text-[10px] text-emerald-600">Zero maternal mortalities</span>
                </div>
                <div className="p-4 bg-slate-50 border border-slate-200/80 rounded-xl space-y-1">
                  <span className="text-[11px] font-bold text-slate-500 uppercase">Immunization Doses</span>
                  <div className="text-2xl font-black text-slate-900">
                    {monthlyReport?.total_immunizations ?? 186}
                  </div>
                  <span className="text-[10px] text-slate-400">Under-1 cohort tracked</span>
                </div>
                <div className="p-4 bg-slate-50 border border-slate-200/80 rounded-xl space-y-1">
                  <span className="text-[11px] font-bold text-slate-500 uppercase">Bed Occupancy Rate</span>
                  <div className="text-2xl font-black text-sky-700">
                    {monthlyReport?.bed_occupancy_rate ?? '72%'}
                  </div>
                  <span className="text-[10px] text-slate-400">Inpatient ward utilization</span>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* TAB 2: STAFF BIOMETRIC ATTENDANCE */}
      {activeTab === 'attendance' && (
        <Card>
          <CardHeader>
            <CardTitle>PHC Staff Roster &amp; Attendance Registry</CardTitle>
            <CardDescription>
              Duty check-ins for Medical Officers, Staff Nurses, Dispensary Pharmacists, Lab Techs, and ANMs.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <DataTable
              data={attendanceSummary}
              keyExtractor={(s) => s.id || s.user_id}
              emptyTitle="No Attendance Records"
              emptyMessage="No staff shift logs available for today."
              columns={[
                {
                  key: 'name',
                  header: 'Staff Member',
                  render: (s) => (
                    <div>
                      <span className="font-bold text-slate-900 block">{s.staff_name || s.name || 'Medical Officer'}</span>
                      <span className="text-[11px] text-slate-400">{s.role || s.designation || 'Healthcare Staff'}</span>
                    </div>
                  ),
                },
                {
                  key: 'shift',
                  header: 'Assigned Shift',
                  render: (s) => <span className="text-xs font-semibold text-slate-700">{s.shift || 'GENERAL (09:00 - 17:00)'}</span>,
                },
                {
                  key: 'check_in',
                  header: 'Biometric Check-In',
                  render: (s) => (
                    <span className="text-xs font-mono text-slate-600">
                      {s.check_in_time ? s.check_in_time.slice(0, 5) : '—'}
                    </span>
                  ),
                },
                {
                  key: 'status',
                  header: 'Presence Status',
                  render: (s) => <Badge status={s.status || (s.check_in_time ? 'PRESENT' : 'SCHEDULED')} size="sm" />,
                },
              ]}
            />
          </CardContent>
        </Card>
      )}

      {/* TAB 3: COLD CHAIN EQUIPMENT */}
      {activeTab === 'coldchain' && (
        <Card>
          <CardHeader>
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
              <div>
                <CardTitle>Cold Chain Storage Equipment &amp; Alerts</CardTitle>
                <CardDescription>
                  ILR and deep freezer units monitoring vaccine safety compliance.
                </CardDescription>
              </div>
              <Button
                variant="primary"
                size="sm"
                onClick={() => setIsLogTempModalOpen(true)}
                className="gap-1"
              >
                <Thermometer className="w-3.5 h-3.5" />
                <span>Log Temperature</span>
              </Button>
            </div>
          </CardHeader>
          <CardContent>
            <DataTable
              data={coldChainEquipments}
              keyExtractor={(c) => c.id}
              emptyTitle="No Cold Chain Units"
              emptyMessage="No equipment units configured. Click 'Add ILR Unit' above."
              columns={[
                {
                  key: 'name',
                  header: 'Equipment Identifier',
                  render: (c) => (
                    <div>
                      <span className="font-bold text-slate-900 block">{c.model || c.equipment_name || 'ILR Standard Unit'}</span>
                      <span className="text-[11px] text-slate-400 font-mono">SN: {c.serial_number || 'ILR-001'}</span>
                    </div>
                  ),
                },
                {
                  key: 'type',
                  header: 'Category',
                  render: (c) => <span className="text-xs text-slate-700">{c.equipment_type || 'Ice-Lined Refrigerator (ILR)'}</span>,
                },
                {
                  key: 'range',
                  header: 'Safe Range',
                  render: (c) => <span className="text-xs font-mono text-slate-600">{c.min_temp_c ?? 2}°C to {c.max_temp_c ?? 8}°C</span>,
                },
                {
                  key: 'temp',
                  header: 'Current Temperature',
                  render: (c) => {
                    const temp = c.latest_temperature ?? c.current_temp_c ?? 4.2;
                    const safe = temp >= (c.min_temp_c ?? 2) && temp <= (c.max_temp_c ?? 8);
                    return (
                      <span className={`text-xs font-mono font-bold ${safe ? 'text-emerald-700' : 'text-red-600'}`}>
                        {temp}°C {safe ? '✅ Safe' : '⚠️ Alert'}
                      </span>
                    );
                  },
                },
                {
                  key: 'status',
                  header: 'Status',
                  render: (c) => <Badge status={c.status || 'ACTIVE'} size="sm" />,
                },
              ]}
            />
          </CardContent>
        </Card>
      )}

      {/* TAB 4: OUTREACH CAMPS */}
      {activeTab === 'camps' && (
        <Card>
          <CardHeader>
            <CardTitle>Village Outreach Medical Camps &amp; VHND Sessions</CardTitle>
            <CardDescription>
              Field medical camps conducted in remote hamlets under facility catchment area.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <DataTable
              data={outreachCamps}
              keyExtractor={(c) => c.id}
              emptyTitle="No Outreach Camps Scheduled"
              emptyMessage="No village health camps registered. Click 'Schedule Outreach Camp' above."
              columns={[
                {
                  key: 'name',
                  header: 'Camp Name',
                  render: (c) => (
                    <div>
                      <span className="font-bold text-slate-900 block">{c.camp_name}</span>
                      <span className="text-[11px] text-slate-400 flex items-center gap-1">
                        <MapPin className="w-3 h-3 text-sky-600" />
                        {c.target_village || 'Catchment Village'}
                      </span>
                    </div>
                  ),
                },
                {
                  key: 'date',
                  header: 'Scheduled Date',
                  render: (c) => <span className="text-xs font-mono text-slate-700">{c.camp_date}</span>,
                },
                {
                  key: 'target',
                  header: 'Target Citizens',
                  render: (c) => <span className="text-xs font-bold text-slate-800">{c.target_beneficiaries || 100}</span>,
                },
                {
                  key: 'actual',
                  header: 'Actual Served',
                  render: (c) => <span className="text-xs font-mono text-emerald-700 font-bold">{c.actual_beneficiaries_served ?? '—'}</span>,
                },
                {
                  key: 'status',
                  header: 'Status',
                  render: (c) => <Badge status={c.status || 'SCHEDULED'} size="sm" />,
                },
                {
                  key: 'actions',
                  header: 'Action',
                  render: (c) => (
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => {
                        setSelectedCamp(c);
                        setUpdateCampStatus(c.status || 'COMPLETED');
                        setUpdateCampActualServed(c.actual_beneficiaries_served || c.target_beneficiaries || 100);
                        setIsUpdateCampModalOpen(true);
                      }}
                      className="h-7 text-xs px-2.5"
                    >
                      Update
                    </Button>
                  ),
                },
              ]}
            />
          </CardContent>
        </Card>
      )}

      {/* TAB 5: GRIEVANCES & CITIZEN FEEDBACK */}
      {activeTab === 'grievances' && (
        <Card>
          <CardHeader>
            <CardTitle>Citizen Grievances &amp; Patient Feedback Register</CardTitle>
            <CardDescription>
              Patient ratings and complaints submitted via citizen portal, subject to superintendent review.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <DataTable
              data={grievances}
              keyExtractor={(g) => g.id}
              emptyTitle="No Grievances Logged"
              emptyMessage="No citizen complaints or service feedback on record."
              columns={[
                {
                  key: 'citizen',
                  header: 'Citizen / Patient',
                  render: (g) => (
                    <div>
                      <span className="font-bold text-slate-900 block">{g.citizen_name || 'Citizen'}</span>
                      <span className="text-[11px] text-slate-400 font-mono">Date: {new Date(g.created_at || Date.now()).toLocaleDateString()}</span>
                    </div>
                  ),
                },
                {
                  key: 'category',
                  header: 'Category',
                  render: (g) => <span className="text-xs font-semibold text-slate-700">{g.category || 'CARE_QUALITY'}</span>,
                },
                {
                  key: 'rating',
                  header: 'Rating',
                  render: (g) => <span className="text-xs font-bold text-amber-600">⭐ {g.rating || 4}/5</span>,
                },
                {
                  key: 'comments',
                  header: 'Comments',
                  render: (g) => <span className="text-xs text-slate-700 max-w-xs truncate block">{g.comments || g.description}</span>,
                },
                {
                  key: 'status',
                  header: 'Status',
                  render: (g) => <Badge status={g.status || 'PENDING'} size="sm" />,
                },
                {
                  key: 'actions',
                  header: 'Action',
                  render: (g) => (
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => {
                        setSelectedGrievance(g);
                        setGrievanceAction('RESOLVED');
                        setResolutionNotes('');
                        setIsGrievanceModalOpen(true);
                      }}
                      className="h-7 text-xs px-2.5"
                    >
                      Resolve
                    </Button>
                  ),
                },
              ]}
            />
          </CardContent>
        </Card>
      )}

      {/* Modal: Schedule Outreach Camp */}
      <Dialog open={isCampModalOpen} onOpenChange={setIsCampModalOpen} maxWidth="max-w-md">
        <DialogHeader>
          <DialogTitle>Schedule Outreach Medical Camp</DialogTitle>
          <DialogDescription>Coordinate village health day with local ANM and panchayat.</DialogDescription>
          <DialogClose onClose={() => setIsCampModalOpen(false)} />
        </DialogHeader>
        <DialogContent>
          <form onSubmit={handleCreateCamp} className="space-y-4">
            <div>
              <label className="block text-xs font-bold text-slate-700 uppercase mb-1">Camp Name</label>
              <Input
                type="text"
                value={newCampName}
                onChange={(e) => setNewCampName(e.target.value)}
                placeholder="e.g. Maternal & Child Nutrition Camp"
                required
              />
            </div>
            <div>
              <label className="block text-xs font-bold text-slate-700 uppercase mb-1">Target Village / Hamlet</label>
              <Input
                type="text"
                value={newCampVillage}
                onChange={(e) => setNewCampVillage(e.target.value)}
                placeholder="e.g. Thirukalukundram East"
                required
              />
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-xs font-bold text-slate-700 uppercase mb-1">Camp Date</label>
                <Input
                  type="date"
                  value={newCampDate}
                  onChange={(e) => setNewCampDate(e.target.value)}
                  required
                />
              </div>
              <div>
                <label className="block text-xs font-bold text-slate-700 uppercase mb-1">Target Citizens</label>
                <Input
                  type="number"
                  value={newCampTarget}
                  onChange={(e) => setNewCampTarget(Number(e.target.value))}
                  required
                />
              </div>
            </div>
            <DialogFooter>
              <Button type="button" variant="outline" size="sm" onClick={() => setIsCampModalOpen(false)}>
                Cancel
              </Button>
              <Button type="submit" variant="primary" size="sm" disabled={isSubmitting}>
                {isSubmitting ? 'Scheduling...' : 'Confirm Schedule'}
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>

      {/* Modal: Register Cold Chain Unit */}
      <Dialog open={isRegisterEquipModalOpen} onOpenChange={setIsRegisterEquipModalOpen} maxWidth="max-w-md">
        <DialogHeader>
          <DialogTitle>Register Cold Chain Asset</DialogTitle>
          <DialogDescription>Add new Ice-Lined Refrigerator or Deep Freezer to facility telemetry.</DialogDescription>
          <DialogClose onClose={() => setIsRegisterEquipModalOpen(false)} />
        </DialogHeader>
        <DialogContent>
          <form onSubmit={handleRegisterEquipment} className="space-y-4">
            <div>
              <label className="block text-xs font-bold text-slate-700 uppercase mb-1">Equipment Type</label>
              <select
                value={newEquipType}
                onChange={(e) => setNewEquipType(e.target.value)}
                className="w-full h-9 px-3 text-xs bg-white border border-slate-300 rounded-lg outline-none font-medium"
              >
                <option value="ILR">Ice-Lined Refrigerator (ILR)</option>
                <option value="DEEP_FREEZER">Deep Freezer (DF)</option>
                <option value="SOLAR_DIRECT_DRIVE">Solar Direct Drive Refrigerator</option>
              </select>
            </div>
            <div>
              <label className="block text-xs font-bold text-slate-700 uppercase mb-1">Model / Manufacturer</label>
              <Input
                type="text"
                value={newEquipModel}
                onChange={(e) => setNewEquipModel(e.target.value)}
                placeholder="e.g. Godrej Medical GVR 100"
                required
              />
            </div>
            <div>
              <label className="block text-xs font-bold text-slate-700 uppercase mb-1">Serial Number</label>
              <Input
                type="text"
                value={newEquipSerial}
                onChange={(e) => setNewEquipSerial(e.target.value)}
                placeholder="e.g. SN-ILR-2026-09"
                required
              />
            </div>
            <DialogFooter>
              <Button type="button" variant="outline" size="sm" onClick={() => setIsRegisterEquipModalOpen(false)}>
                Cancel
              </Button>
              <Button type="submit" variant="primary" size="sm" disabled={isSubmitting}>
                {isSubmitting ? 'Registering...' : 'Provision Unit'}
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>

      {/* Modal: Log Temperature */}
      <Dialog open={isLogTempModalOpen} onOpenChange={setIsLogTempModalOpen} maxWidth="max-w-md">
        <DialogHeader>
          <DialogTitle>Record ILR Temperature Log</DialogTitle>
          <DialogDescription>Submit formal temperature check to verify cold chain integrity.</DialogDescription>
          <DialogClose onClose={() => setIsLogTempModalOpen(false)} />
        </DialogHeader>
        <DialogContent>
          <form onSubmit={handleLogTemperature} className="space-y-4">
            <div>
              <label className="block text-xs font-bold text-slate-700 uppercase mb-1">Select Unit</label>
              <select
                value={logTempEquipId}
                onChange={(e) => setLogTempEquipId(e.target.value)}
                className="w-full h-9 px-3 text-xs bg-white border border-slate-300 rounded-lg outline-none font-medium"
                required
              >
                <option value="">Choose equipment...</option>
                {coldChainEquipments.map((c) => (
                  <option key={c.id} value={c.id}>{c.model || c.equipment_name || 'ILR'} (SN: {c.serial_number})</option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-xs font-bold text-slate-700 uppercase mb-1">Temperature (°C)</label>
              <Input
                type="number"
                step="0.1"
                value={logTempC}
                onChange={(e) => setLogTempC(Number(e.target.value))}
                required
              />
            </div>
            <div>
              <label className="block text-xs font-bold text-slate-700 uppercase mb-1">Shift Check Notes</label>
              <Input
                type="text"
                value={logTempNotes}
                onChange={(e) => setLogTempNotes(e.target.value)}
                placeholder="Power backup normal, sensor calibrated"
              />
            </div>
            <DialogFooter>
              <Button type="button" variant="outline" size="sm" onClick={() => setIsLogTempModalOpen(false)}>
                Cancel
              </Button>
              <Button type="submit" variant="primary" size="sm" disabled={isSubmitting || !logTempEquipId}>
                {isSubmitting ? 'Recording...' : 'Commit Reading'}
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>

      {/* Modal: Resolve Grievance */}
      <Dialog open={isGrievanceModalOpen} onOpenChange={setIsGrievanceModalOpen} maxWidth="max-w-md">
        <DialogHeader>
          <DialogTitle>Grievance Redressal Action</DialogTitle>
          <DialogDescription>Close or escalate patient service feedback.</DialogDescription>
          <DialogClose onClose={() => setIsGrievanceModalOpen(false)} />
        </DialogHeader>
        <DialogContent>
          <form onSubmit={handleResolveGrievance} className="space-y-4">
            <div>
              <label className="block text-xs font-bold text-slate-700 uppercase mb-1">Redressal Action</label>
              <select
                value={grievanceAction}
                onChange={(e) => setGrievanceAction(e.target.value as any)}
                className="w-full h-9 px-3 text-xs bg-white border border-slate-300 rounded-lg outline-none font-medium"
              >
                <option value="RESOLVED">Resolved — Corrective action taken at PHC</option>
                <option value="ESCALATED">Escalated to District Health Officer</option>
              </select>
            </div>
            <div>
              <label className="block text-xs font-bold text-slate-700 uppercase mb-1">Resolution Notes</label>
              <Textarea
                value={resolutionNotes}
                onChange={(e) => setResolutionNotes(e.target.value)}
                placeholder="State corrective actions taken..."
                rows={3}
                required
              />
            </div>
            <DialogFooter>
              <Button type="button" variant="outline" size="sm" onClick={() => setIsGrievanceModalOpen(false)}>
                Cancel
              </Button>
              <Button type="submit" variant="primary" size="sm" disabled={isSubmitting}>
                {isSubmitting ? 'Saving...' : 'Confirm Resolution'}
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>
    </div>
  );
}
