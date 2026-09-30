import React, { useState, useEffect } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { 
  Building2, Users, Thermometer, MapPin, 
  AlertCircle, CheckCircle, Clock, Plus, 
  Calendar, FileText, ChevronRight, ShieldCheck,
  TrendingUp, BarChart2, ShieldAlert
} from 'lucide-react';
import { api } from '../services/api';
import { useAuth } from '../context/AuthContext';
import { useLanguage } from '../context/LanguageContext';
import { StateView } from '../components/common/StateView';
import { Badge } from '../components/common/Badge';
import { Modal } from '../components/common/Modal';
import { DataTable } from '../components/common/DataTable';

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

  // Facility ID from context or fallback
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

  // Fetch initial dashboard data
  const fetchPortalData = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const [reportRes, equipRes, campsRes, complaintsRes, summaryRes] = await Promise.all([
        api.get<any>(`/facility-admin/reports/monthly?facility_id=${facilityId}&month=${selectedMonth}&year=${selectedYear}`).catch(() => ({ data: null })),
        api.get<any[]>(`/facility-admin/cold-chain/equipment?facility_id=${facilityId}`).catch(() => ({ data: [] })),
        api.get<any[]>(`/facility-admin/outreach-camps?facility_id=${facilityId}`).catch(() => ({ data: [] })),
        api.get<any[]>(`/facility-admin/complaints?facility_id=${facilityId}`).catch(() => ({ data: [] })),
        api.get<any[]>(`/facility-admin/staff-attendance/summary?facility_id=${facilityId}&month=${selectedMonth}&year=${selectedYear}`).catch(() => ({ data: [] })),
      ]);

      if (reportRes?.data) setMonthlyReport(reportRes.data);
      if (equipRes?.data) setColdChainEquipments(equipRes.data);
      if (campsRes?.data) setOutreachCamps(campsRes.data);
      if (complaintsRes?.data) setGrievances(complaintsRes.data);
      if (summaryRes?.data) setAttendanceSummary(summaryRes.data);
    } catch (err: any) {
      setError(err?.detail || 'Failed to load facility administration data');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchPortalData();
  }, [facilityId, selectedMonth, selectedYear]);

  // Handle Cold Chain Temp Log
  const handleLogTemperature = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!logTempEquipId) return;
    setIsSubmitting(true);
    try {
      await api.post(`/facility-admin/cold-chain/equipment/${logTempEquipId}/log`, {
        temperature_c: Number(logTempC),
        notes: logTempNotes || 'Routine check',
        excursion_reason: excursionReason || undefined,
      });
      setActionSuccess('Temperature reading successfully recorded');
      setIsLogTempModalOpen(false);
      setLogTempNotes('');
      setExcursionReason('');
      fetchPortalData();
    } catch (err: any) {
      alert(err?.detail || 'Failed to log temperature');
    } finally {
      setIsSubmitting(false);
    }
  };

  // Handle Equipment Registration
  const handleRegisterEquipment = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSubmitting(true);
    try {
      await api.post(`/facility-admin/cold-chain/equipment?facility_id=${facilityId}`, {
        equipment_type: newEquipType,
        serial_number: newEquipSerial,
        model_name: newEquipModel,
        min_temp_c: Number(newEquipMinTemp),
        max_temp_c: Number(newEquipMaxTemp),
      });
      setActionSuccess('Cold chain equipment registered successfully');
      setIsRegisterEquipModalOpen(false);
      setNewEquipSerial('');
      setNewEquipModel('');
      fetchPortalData();
    } catch (err: any) {
      alert(err?.detail || 'Failed to register equipment');
    } finally {
      setIsSubmitting(false);
    }
  };

  // View Log History
  const handleViewEquipmentLogs = async (equip: any) => {
    setSelectedEquipForLogs(equip);
    try {
      const res = await api.get<any[]>(`/facility-admin/cold-chain/equipment/${equip.id}/logs`);
      if (res.data) setSelectedEquipmentLogs(res.data);
    } catch (err) {
      console.error(err);
    }
  };

  // Handle Outreach Camp Creation
  const handleCreateCamp = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSubmitting(true);
    try {
      await api.post(`/facility-admin/outreach-camps?facility_id=${facilityId}`, {
        camp_name: newCampName,
        target_village: newCampVillage,
        scheduled_date: newCampDate,
        target_beneficiaries: Number(newCampTarget),
        notes: newCampNotes,
      });
      setActionSuccess('Outreach camp scheduled successfully');
      setIsCampModalOpen(false);
      setNewCampName('');
      setNewCampVillage('');
      fetchPortalData();
    } catch (err: any) {
      alert(err?.detail || 'Failed to schedule camp');
    } finally {
      setIsSubmitting(false);
    }
  };

  // Handle Outreach Camp Update
  const handleUpdateCamp = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedCamp) return;
    setIsSubmitting(true);
    try {
      await api.patch(`/facility-admin/outreach-camps/${selectedCamp.id}`, {
        status: updateCampStatus,
        actual_beneficiaries_served: Number(updateCampActualServed),
        notes: 'Status updated by PHC In-Charge',
      });
      setActionSuccess('Camp status and beneficiary count updated');
      setIsUpdateCampModalOpen(false);
      fetchPortalData();
    } catch (err: any) {
      alert(err?.detail || 'Failed to update camp');
    } finally {
      setIsSubmitting(false);
    }
  };

  // Handle Grievance Status Update
  const handleResolveGrievance = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedGrievance) return;
    setIsSubmitting(true);
    try {
      await api.patch(`/facility-admin/complaints/${selectedGrievance.id}`, {
        status: grievanceAction,
        resolution_notes: resolutionNotes,
      });
      setActionSuccess(`Grievance marked as ${grievanceAction}`);
      setIsGrievanceModalOpen(false);
      setResolutionNotes('');
      fetchPortalData();
    } catch (err: any) {
      alert(err?.detail || 'Failed to update grievance');
    } finally {
      setIsSubmitting(false);
    }
  };

  if (isLoading) return <StateView type="loading" message="Loading facility administration portal..." />;
  if (error) return <StateView type="error" message={error} onRetry={fetchPortalData} />;

  return (
    <div className="space-y-6">
      {/* Header Banner */}
      <div className="bg-gradient-to-r from-emerald-800 to-teal-900 text-white rounded-xl p-6 shadow-md">
        <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
          <div>
            <div className="flex items-center gap-2 text-emerald-200 text-sm font-semibold tracking-wide uppercase">
              <Building2 className="w-4 h-4" />
              <span>Role 04: PHC Medical Officer In-Charge</span>
            </div>
            <h1 className="text-2xl font-bold mt-1">
              {monthlyReport?.facility_name || user?.facility_name || 'Primary Health Centre Administration'}
            </h1>
            <p className="text-emerald-100 text-sm mt-1">
              OPD throughput, HMIS monthly KPIs, cold chain compliance, staff attendance & village outreach monitoring.
            </p>
          </div>
          <div className="flex items-center gap-3 bg-white/10 backdrop-blur-md px-4 py-3 rounded-lg border border-white/20">
            <Calendar className="w-5 h-5 text-emerald-200" />
            <div>
              <div className="text-xs text-emerald-200 uppercase font-bold">Reporting Period</div>
              <div className="text-sm font-semibold">
                {new Date(selectedYear, selectedMonth - 1).toLocaleString('default', { month: 'long', year: 'numeric' })}
              </div>
            </div>
          </div>
        </div>

        {actionSuccess && (
          <div className="mt-4 bg-emerald-500/20 border border-emerald-400 text-emerald-100 px-4 py-2.5 rounded-lg flex items-center justify-between text-sm animate-fade-in">
            <span className="flex items-center gap-2">
              <CheckCircle className="w-4 h-4 text-emerald-300" />
              {actionSuccess}
            </span>
            <button onClick={() => setActionSuccess(null)} className="text-emerald-200 hover:text-white text-xs font-bold uppercase">
              Dismiss
            </button>
          </div>
        )}
      </div>

      {/* Navigation Tabs */}
      <div className="flex border-b border-gray-200 bg-white px-4 rounded-lg shadow-sm overflow-x-auto">
        <button
          onClick={() => handleTabChange('overview')}
          className={`py-3.5 px-4 font-medium text-sm border-b-2 flex items-center gap-2 transition-colors whitespace-nowrap ${
            activeTab === 'overview'
              ? 'border-emerald-600 text-emerald-700 font-semibold'
              : 'border-transparent text-gray-500 hover:text-gray-700'
          }`}
        >
          <BarChart2 className="w-4 h-4" />
          HMIS Performance Overview
        </button>
        <button
          onClick={() => handleTabChange('attendance')}
          className={`py-3.5 px-4 font-medium text-sm border-b-2 flex items-center gap-2 transition-colors whitespace-nowrap ${
            activeTab === 'attendance'
              ? 'border-emerald-600 text-emerald-700 font-semibold'
              : 'border-transparent text-gray-500 hover:text-gray-700'
          }`}
        >
          <Users className="w-4 h-4" />
          Staff Attendance
        </button>
        <button
          onClick={() => handleTabChange('coldchain')}
          className={`py-3.5 px-4 font-medium text-sm border-b-2 flex items-center gap-2 transition-colors whitespace-nowrap ${
            activeTab === 'coldchain'
              ? 'border-emerald-600 text-emerald-700 font-semibold'
              : 'border-transparent text-gray-500 hover:text-gray-700'
          }`}
        >
          <Thermometer className="w-4 h-4" />
          Cold Chain Registry
          {coldChainEquipments.some(e => !e.is_temperature_in_range) && (
            <span className="w-2 h-2 rounded-full bg-red-500 animate-pulse"></span>
          )}
        </button>
        <button
          onClick={() => handleTabChange('camps')}
          className={`py-3.5 px-4 font-medium text-sm border-b-2 flex items-center gap-2 transition-colors whitespace-nowrap ${
            activeTab === 'camps'
              ? 'border-emerald-600 text-emerald-700 font-semibold'
              : 'border-transparent text-gray-500 hover:text-gray-700'
          }`}
        >
          <MapPin className="w-4 h-4" />
          Village Outreach Camps
        </button>
        <button
          onClick={() => handleTabChange('grievances')}
          className={`py-3.5 px-4 font-medium text-sm border-b-2 flex items-center gap-2 transition-colors whitespace-nowrap ${
            activeTab === 'grievances'
              ? 'border-emerald-600 text-emerald-700 font-semibold'
              : 'border-transparent text-gray-500 hover:text-gray-700'
          }`}
        >
          <AlertCircle className="w-4 h-4" />
          Grievance Redressal
          {grievances.filter(g => g.status === 'SUBMITTED' || g.status === 'IN_REVIEW').length > 0 && (
            <span className="bg-amber-100 text-amber-800 text-xs px-2 py-0.5 rounded-full font-bold">
              {grievances.filter(g => g.status === 'SUBMITTED' || g.status === 'IN_REVIEW').length}
            </span>
          )}
        </button>
      </div>

      {/* TAB 1: HMIS PERFORMANCE OVERVIEW */}
      {activeTab === 'overview' && (
        <div className="space-y-6">
          {/* Period Selector Controls */}
          <div className="flex flex-wrap items-center justify-between gap-4 bg-white p-4 rounded-xl shadow-sm border border-gray-100">
            <div className="flex items-center gap-3">
              <span className="text-sm font-medium text-gray-700">Filter Month:</span>
              <select
                value={selectedMonth}
                onChange={(e) => setSelectedMonth(Number(e.target.value))}
                className="border border-gray-300 rounded-lg px-3 py-1.5 text-sm focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500"
              >
                {Array.from({ length: 12 }, (_, i) => i + 1).map((m) => (
                  <option key={m} value={m}>
                    {new Date(2026, m - 1).toLocaleString('default', { month: 'long' })}
                  </option>
                ))}
              </select>
              <select
                value={selectedYear}
                onChange={(e) => setSelectedYear(Number(e.target.value))}
                className="border border-gray-300 rounded-lg px-3 py-1.5 text-sm focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500"
              >
                {[2024, 2025, 2026].map((y) => (
                  <option key={y} value={y}>{y}</option>
                ))}
              </select>
            </div>
            <button
              onClick={fetchPortalData}
              className="px-4 py-1.5 bg-emerald-50 text-emerald-700 hover:bg-emerald-100 rounded-lg text-sm font-semibold transition"
            >
              Refresh Report
            </button>
          </div>

          {/* HMIS Metric Cards Grid */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            <div className="bg-white p-5 rounded-xl border border-gray-100 shadow-sm flex items-start justify-between">
              <div>
                <p className="text-xs font-semibold text-gray-500 uppercase tracking-wider">Total OPD Patients</p>
                <h3 className="text-2xl font-bold text-gray-900 mt-1">{monthlyReport?.total_opd_patients ?? 0}</h3>
                <span className="text-xs text-emerald-600 font-medium mt-1 inline-block">Consultations: {monthlyReport?.total_consultations ?? 0}</span>
              </div>
              <div className="p-3 bg-blue-50 text-blue-600 rounded-lg">
                <Users className="w-5 h-5" />
              </div>
            </div>

            <div className="bg-white p-5 rounded-xl border border-gray-100 shadow-sm flex items-start justify-between">
              <div>
                <p className="text-xs font-semibold text-gray-500 uppercase tracking-wider">Staff Attendance Rate</p>
                <h3 className="text-2xl font-bold text-gray-900 mt-1">{monthlyReport?.staff_attendance_rate_percent ?? 0}%</h3>
                <span className="text-xs text-gray-500 mt-1 inline-block">Active Duty: {monthlyReport?.total_staff ?? 0} staff</span>
              </div>
              <div className="p-3 bg-emerald-50 text-emerald-600 rounded-lg">
                <ShieldCheck className="w-5 h-5" />
              </div>
            </div>

            <div className="bg-white p-5 rounded-xl border border-gray-100 shadow-sm flex items-start justify-between">
              <div>
                <p className="text-xs font-semibold text-gray-500 uppercase tracking-wider">Cold Chain Excursions</p>
                <h3 className={`text-2xl font-bold mt-1 ${monthlyReport?.cold_chain_excursions > 0 ? 'text-red-600' : 'text-emerald-700'}`}>
                  {monthlyReport?.cold_chain_excursions ?? 0}
                </h3>
                <span className="text-xs text-gray-500 mt-1 inline-block">
                  {monthlyReport?.cold_chain_excursions > 0 ? 'Excursions flagged' : '100% in safe range'}
                </span>
              </div>
              <div className={`p-3 rounded-lg ${monthlyReport?.cold_chain_excursions > 0 ? 'bg-red-50 text-red-600' : 'bg-emerald-50 text-emerald-600'}`}>
                <Thermometer className="w-5 h-5" />
              </div>
            </div>

            <div className="bg-white p-5 rounded-xl border border-gray-100 shadow-sm flex items-start justify-between">
              <div>
                <p className="text-xs font-semibold text-gray-500 uppercase tracking-wider">Outreach Camps Done</p>
                <h3 className="text-2xl font-bold text-gray-900 mt-1">
                  {monthlyReport?.outreach_camps_completed ?? 0} / {monthlyReport?.outreach_camps_scheduled ?? 0}
                </h3>
                <span className="text-xs text-gray-500 mt-1 inline-block">Beneficiaries: {monthlyReport?.beneficiaries_served ?? 0}</span>
              </div>
              <div className="p-3 bg-purple-50 text-purple-600 rounded-lg">
                <MapPin className="w-5 h-5" />
              </div>
            </div>
          </div>

          {/* Secondary Details Row */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="bg-white p-5 rounded-xl border border-gray-100 shadow-sm">
              <h4 className="text-sm font-bold text-gray-900 mb-3 flex items-center gap-2">
                <FileText className="w-4 h-4 text-emerald-600" />
                Clinical Services Throughput
              </h4>
              <ul className="space-y-3 text-sm">
                <li className="flex justify-between py-1.5 border-b border-gray-100">
                  <span className="text-gray-600">Prescriptions Issued</span>
                  <span className="font-semibold text-gray-900">{monthlyReport?.total_prescriptions_issued ?? 0}</span>
                </li>
                <li className="flex justify-between py-1.5 border-b border-gray-100">
                  <span className="text-gray-600">Lab Tests Ordered</span>
                  <span className="font-semibold text-gray-900">{monthlyReport?.total_lab_tests_ordered ?? 0}</span>
                </li>
                <li className="flex justify-between py-1.5 border-b border-gray-100">
                  <span className="text-gray-600">Lab Tests Completed</span>
                  <span className="font-semibold text-emerald-700">{monthlyReport?.total_lab_tests_completed ?? 0}</span>
                </li>
                <li className="flex justify-between py-1.5">
                  <span className="text-gray-600">Referrals to Higher Facilities</span>
                  <span className="font-semibold text-amber-700">{monthlyReport?.total_referrals ?? 0}</span>
                </li>
              </ul>
            </div>

            <div className="bg-white p-5 rounded-xl border border-gray-100 shadow-sm">
              <h4 className="text-sm font-bold text-gray-900 mb-3 flex items-center gap-2">
                <AlertCircle className="w-4 h-4 text-amber-600" />
                Citizen Grievances & Redressal
              </h4>
              <ul className="space-y-3 text-sm">
                <li className="flex justify-between py-1.5 border-b border-gray-100">
                  <span className="text-gray-600">Grievances Received</span>
                  <span className="font-semibold text-gray-900">{monthlyReport?.grievances_received ?? 0}</span>
                </li>
                <li className="flex justify-between py-1.5 border-b border-gray-100">
                  <span className="text-gray-600">Grievances Resolved</span>
                  <span className="font-semibold text-emerald-700">{monthlyReport?.grievances_resolved ?? 0}</span>
                </li>
                <li className="flex justify-between py-1.5">
                  <span className="text-gray-600">Resolution Rate</span>
                  <span className="font-bold text-emerald-600">{monthlyReport?.grievance_resolution_rate_percent ?? 0}%</span>
                </li>
              </ul>
            </div>

            <div className="bg-white p-5 rounded-xl border border-gray-100 shadow-sm">
              <h4 className="text-sm font-bold text-gray-900 mb-3 flex items-center gap-2">
                <ShieldCheck className="w-4 h-4 text-teal-600" />
                HMIS Compliance Status
              </h4>
              <div className="space-y-3">
                <div className="p-3 bg-emerald-50 text-emerald-800 rounded-lg text-xs leading-relaxed">
                  ✓ Ready for submission to District Health Officer (DHO). All data reconciled from primary clinic registers.
                </div>
                <div className="text-xs text-gray-500">
                  Primary registers reconciled: Daily OPD Register, Staff Muster, Cold Chain Logbook, ASHA Village Camp Register.
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* TAB 2: STAFF ATTENDANCE */}
      {activeTab === 'attendance' && (
        <div className="bg-white p-6 rounded-xl border border-gray-100 shadow-sm space-y-4">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
            <div>
              <h3 className="text-base font-bold text-gray-900">Staff Attendance Summary</h3>
              <p className="text-xs text-gray-500">Monthly aggregated attendance by healthcare worker at this facility.</p>
            </div>
            <div className="text-xs font-semibold text-emerald-700 bg-emerald-50 px-3 py-1.5 rounded-lg border border-emerald-200">
              Month: {new Date(selectedYear, selectedMonth - 1).toLocaleString('default', { month: 'long', year: 'numeric' })}
            </div>
          </div>

          <DataTable
            data={attendanceSummary}
            keyField="user_id"
            emptyMessage="No staff attendance records logged for this month"
            columns={[
              {
                header: 'Staff Member',
                accessor: (item) => (
                  <div>
                    <div className="font-medium text-gray-900">{item.full_name}</div>
                    <div className="text-xs text-gray-400 font-mono">{item.role_code}</div>
                  </div>
                ),
              },
              {
                header: 'Present',
                accessor: (item) => (
                  <span className="font-semibold text-emerald-700">{item.present_days} days</span>
                ),
              },
              {
                header: 'Half Days',
                accessor: 'half_days',
              },
              {
                header: 'On Leave',
                accessor: (item) => (
                  <span className={item.on_leave_days > 0 ? 'text-amber-600 font-medium' : 'text-gray-500'}>
                    {item.on_leave_days} days
                  </span>
                ),
              },
              {
                header: 'Camp Duty',
                accessor: (item) => `${item.on_duty_camp_days} days`,
              },
              {
                header: 'Attendance %',
                accessor: (item) => (
                  <div className="flex items-center gap-2">
                    <span className="font-bold text-gray-900">{item.attendance_rate_percent}%</span>
                    <div className="w-16 bg-gray-200 rounded-full h-1.5">
                      <div
                        className={`h-1.5 rounded-full ${item.attendance_rate_percent >= 80 ? 'bg-emerald-600' : 'bg-amber-500'}`}
                        style={{ width: `${Math.min(item.attendance_rate_percent, 100)}%` }}
                      ></div>
                    </div>
                  </div>
                ),
              },
            ]}
          />
        </div>
      )}

      {/* TAB 3: COLD CHAIN REGISTRY */}
      {activeTab === 'coldchain' && (
        <div className="space-y-6">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 bg-white p-5 rounded-xl border border-gray-100 shadow-sm">
            <div>
              <h3 className="text-base font-bold text-gray-900">Cold Chain Equipment & Temperature Monitor</h3>
              <p className="text-xs text-gray-500">Continuous monitoring of Ice-Lined Refrigerators (ILR), Deep Freezers, and Cold Boxes.</p>
            </div>
            <div className="flex items-center gap-2">
              <button
                onClick={() => {
                  if (coldChainEquipments.length > 0) {
                    setLogTempEquipId(coldChainEquipments[0].id);
                    setIsLogTempModalOpen(true);
                  }
                }}
                disabled={coldChainEquipments.length === 0}
                className="px-3.5 py-2 bg-emerald-600 hover:bg-emerald-700 text-white rounded-lg text-sm font-semibold flex items-center gap-1.5 transition disabled:opacity-50"
              >
                <Thermometer className="w-4 h-4" />
                Record Temp Log
              </button>
              <button
                onClick={() => setIsRegisterEquipModalOpen(true)}
                className="px-3.5 py-2 border border-gray-300 hover:bg-gray-50 text-gray-700 rounded-lg text-sm font-semibold flex items-center gap-1.5 transition"
              >
                <Plus className="w-4 h-4" />
                Add Equipment
              </button>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
            {coldChainEquipments.map((equip) => (
              <div key={equip.id} className="bg-white rounded-xl border border-gray-200 shadow-sm p-5 space-y-4">
                <div className="flex items-start justify-between">
                  <div>
                    <span className="text-xs font-bold px-2 py-0.5 rounded bg-gray-100 text-gray-700 uppercase">
                      {equip.equipment_type}
                    </span>
                    <h4 className="text-base font-bold text-gray-900 mt-1">{equip.model_name || 'Standard Unit'}</h4>
                    <p className="text-xs text-gray-500 font-mono">SN: {equip.serial_number}</p>
                  </div>
                  <Badge 
                    label={equip.is_temperature_in_range ? 'Normal Range' : 'Excursion!'} 
                    status={equip.is_temperature_in_range ? 'success' : 'danger'} 
                  />
                </div>

                <div className="bg-gray-50 p-4 rounded-lg flex items-center justify-between">
                  <div>
                    <div className="text-xs text-gray-500 uppercase">Current Reading</div>
                    <div className="text-2xl font-black text-gray-900">
                      {equip.current_temp_c !== null ? `${equip.current_temp_c}°C` : 'N/A'}
                    </div>
                  </div>
                  <div className="text-right">
                    <div className="text-xs text-gray-500 uppercase">Safe Limits</div>
                    <div className="text-sm font-semibold text-gray-700">
                      {equip.min_temp_c}°C to {equip.max_temp_c}°C
                    </div>
                  </div>
                </div>

                <div className="flex items-center justify-between text-xs text-gray-500 pt-2 border-t border-gray-100">
                  <span>Last logged: {equip.last_logged_at ? new Date(equip.last_logged_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) : 'Never'}</span>
                  <button
                    onClick={() => handleViewEquipmentLogs(equip)}
                    className="text-emerald-700 hover:text-emerald-800 font-semibold"
                  >
                    View History →
                  </button>
                </div>
              </div>
            ))}
          </div>

          {/* Temperature Log History Drawer/Modal */}
          {selectedEquipForLogs && (
            <div className="bg-white p-5 rounded-xl border border-gray-200 shadow-sm">
              <div className="flex items-center justify-between mb-4">
                <div>
                  <h4 className="text-base font-bold text-gray-900">
                    Temperature Log History — {selectedEquipForLogs.equipment_type} ({selectedEquipForLogs.serial_number})
                  </h4>
                  <p className="text-xs text-gray-500">Twice-daily temperature compliance record</p>
                </div>
                <button
                  onClick={() => setSelectedEquipForLogs(null)}
                  className="text-xs text-gray-500 hover:text-gray-800 font-bold"
                >
                  Close History
                </button>
              </div>

              <DataTable
                data={selectedEquipmentLogs}
                keyField="id"
                emptyMessage="No historical logs found for this equipment"
                columns={[
                  {
                    header: 'Recorded At',
                    accessor: (log) => new Date(log.recorded_at).toLocaleString(),
                  },
                  {
                    header: 'Temperature',
                    accessor: (log) => (
                      <span className={`font-bold ${log.is_excursion ? 'text-red-600' : 'text-emerald-700'}`}>
                        {log.temperature_c}°C
                      </span>
                    ),
                  },
                  {
                    header: 'Status',
                    accessor: (log) => (
                      <Badge 
                        label={log.is_excursion ? 'Excursion Alert' : 'Compliant'} 
                        status={log.is_excursion ? 'danger' : 'success'} 
                      />
                    ),
                  },
                  {
                    header: 'Notes / Reason',
                    accessor: (log) => log.excursion_reason || log.notes || 'Routine check',
                  },
                ]}
              />
            </div>
          )}
        </div>
      )}

      {/* TAB 4: VILLAGE OUTREACH CAMPS */}
      {activeTab === 'camps' && (
        <div className="bg-white p-6 rounded-xl border border-gray-100 shadow-sm space-y-4">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
            <div>
              <h3 className="text-base font-bold text-gray-900">Village Outreach Camps (ANC & Immunization)</h3>
              <p className="text-xs text-gray-500">Schedule and monitor healthcare camps conducted in remote habitations.</p>
            </div>
            <button
              onClick={() => setIsCampModalOpen(true)}
              className="px-3.5 py-2 bg-emerald-600 hover:bg-emerald-700 text-white rounded-lg text-sm font-semibold flex items-center gap-1.5 transition self-start sm:self-auto"
            >
              <Plus className="w-4 h-4" />
              Schedule Outreach Camp
            </button>
          </div>

          <DataTable
            data={outreachCamps}
            keyField="id"
            emptyMessage="No outreach camps scheduled for this facility"
            columns={[
              {
                header: 'Camp Details',
                accessor: (c) => (
                  <div>
                    <div className="font-semibold text-gray-900">{c.camp_name}</div>
                    <div className="text-xs text-gray-500 flex items-center gap-1">
                      <MapPin className="w-3 h-3 text-emerald-600" />
                      {c.target_village}
                    </div>
                  </div>
                ),
              },
              {
                header: 'Scheduled Date',
                accessor: (c) => c.scheduled_date,
              },
              {
                header: 'Target vs Served',
                accessor: (c) => (
                  <div>
                    <span className="font-bold text-gray-900">{c.actual_beneficiaries_served}</span>
                    <span className="text-xs text-gray-500"> / {c.target_beneficiaries} beneficiaries</span>
                  </div>
                ),
              },
              {
                header: 'Status',
                accessor: (c) => (
                  <Badge 
                    label={c.status} 
                    status={c.status === 'COMPLETED' ? 'success' : c.status === 'IN_PROGRESS' ? 'info' : 'warning'} 
                  />
                ),
              },
              {
                header: 'Actions',
                accessor: (c) => (
                  <button
                    onClick={() => {
                      setSelectedCamp(c);
                      setUpdateCampStatus(c.status);
                      setUpdateCampActualServed(c.actual_beneficiaries_served);
                      setIsUpdateCampModalOpen(true);
                    }}
                    className="text-xs font-semibold text-emerald-700 hover:text-emerald-800 px-2.5 py-1 rounded bg-emerald-50 border border-emerald-200"
                  >
                    Update Progress
                  </button>
                ),
              },
            ]}
          />
        </div>
      )}

      {/* TAB 5: GRIEVANCE REDRESSAL */}
      {activeTab === 'grievances' && (
        <div className="bg-white p-6 rounded-xl border border-gray-100 shadow-sm space-y-4">
          <div>
            <h3 className="text-base font-bold text-gray-900">Citizen Complaints & Grievance Redressal</h3>
            <p className="text-xs text-gray-500">Patient feedback, waiting time complaints, and medicine availability grievances.</p>
          </div>

          <DataTable
            data={grievances}
            keyField="id"
            emptyMessage="No grievances or feedback submitted for this facility"
            columns={[
              {
                header: 'Complaint',
                accessor: (g) => (
                  <div>
                    <div className="font-semibold text-gray-900">{g.subject || g.category || 'Feedback'}</div>
                    <div className="text-xs text-gray-600 line-clamp-1">{g.description}</div>
                  </div>
                ),
              },
              {
                header: 'Date',
                accessor: (g) => new Date(g.created_at).toLocaleDateString(),
              },
              {
                header: 'Status',
                accessor: (g) => (
                  <Badge 
                    label={g.status} 
                    status={g.status === 'RESOLVED' ? 'success' : g.status === 'ESCALATED' ? 'danger' : 'warning'} 
                  />
                ),
              },
              {
                header: 'Action',
                accessor: (g) => (
                  <button
                    onClick={() => {
                      setSelectedGrievance(g);
                      setResolutionNotes(g.resolution_notes || '');
                      setIsGrievanceModalOpen(true);
                    }}
                    className="text-xs font-semibold text-emerald-700 hover:text-emerald-800 px-3 py-1 bg-emerald-50 rounded border border-emerald-200"
                  >
                    Redress Grievance
                  </button>
                ),
              },
            ]}
          />
        </div>
      )}

      {/* MODAL: Record Temperature Log */}
      <Modal
        isOpen={isLogTempModalOpen}
        onClose={() => setIsLogTempModalOpen(false)}
        title="Record Cold Chain Temperature Reading"
      >
        <form onSubmit={handleLogTemperature} className="space-y-4">
          <div>
            <label className="block text-xs font-bold text-gray-700 uppercase mb-1">Select Equipment</label>
            <select
              value={logTempEquipId}
              onChange={(e) => setLogTempEquipId(e.target.value)}
              className="w-full border border-gray-300 rounded-lg p-2.5 text-sm"
              required
            >
              {coldChainEquipments.map((e) => (
                <option key={e.id} value={e.id}>
                  {e.equipment_type} - {e.model_name || e.serial_number} (Range: {e.min_temp_c}°C to {e.max_temp_c}°C)
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-xs font-bold text-gray-700 uppercase mb-1">Temperature (°C)</label>
            <input
              type="number"
              step="0.1"
              value={logTempC}
              onChange={(e) => setLogTempC(Number(e.target.value))}
              className="w-full border border-gray-300 rounded-lg p-2.5 text-sm font-mono font-bold"
              required
            />
          </div>

          <div>
            <label className="block text-xs font-bold text-gray-700 uppercase mb-1">Notes / Observations</label>
            <input
              type="text"
              value={logTempNotes}
              onChange={(e) => setLogTempNotes(e.target.value)}
              placeholder="e.g. Morning routine inspection, power OK"
              className="w-full border border-gray-300 rounded-lg p-2.5 text-sm"
            />
          </div>

          <div>
            <label className="block text-xs font-bold text-gray-700 uppercase mb-1">Excursion Reason (If out of safe range)</label>
            <input
              type="text"
              value={excursionReason}
              onChange={(e) => setExcursionReason(e.target.value)}
              placeholder="e.g. Power outage, compressor failure"
              className="w-full border border-gray-300 rounded-lg p-2.5 text-sm"
            />
          </div>

          <div className="flex justify-end gap-2 pt-3 border-t">
            <button
              type="button"
              onClick={() => setIsLogTempModalOpen(false)}
              className="px-4 py-2 border border-gray-300 rounded-lg text-sm text-gray-700 hover:bg-gray-50"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={isSubmitting}
              className="px-4 py-2 bg-emerald-600 hover:bg-emerald-700 text-white rounded-lg text-sm font-semibold"
            >
              {isSubmitting ? 'Logging...' : 'Confirm Temperature Log'}
            </button>
          </div>
        </form>
      </Modal>

      {/* MODAL: Register New Equipment */}
      <Modal
        isOpen={isRegisterEquipModalOpen}
        onClose={() => setIsRegisterEquipModalOpen(false)}
        title="Register Cold Chain Equipment"
      >
        <form onSubmit={handleRegisterEquipment} className="space-y-4">
          <div>
            <label className="block text-xs font-bold text-gray-700 uppercase mb-1">Equipment Type</label>
            <select
              value={newEquipType}
              onChange={(e) => setNewEquipType(e.target.value)}
              className="w-full border border-gray-300 rounded-lg p-2.5 text-sm"
            >
              <option value="ILR">ILR (Ice-Lined Refrigerator)</option>
              <option value="DEEP_FREEZER">Deep Freezer (-20°C)</option>
              <option value="COLD_BOX">Cold Box</option>
              <option value="VACCINE_CARRIER">Vaccine Carrier</option>
            </select>
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-bold text-gray-700 uppercase mb-1">Serial Number</label>
              <input
                type="text"
                value={newEquipSerial}
                onChange={(e) => setNewEquipSerial(e.target.value)}
                placeholder="SN-998811"
                className="w-full border border-gray-300 rounded-lg p-2.5 text-sm"
                required
              />
            </div>
            <div>
              <label className="block text-xs font-bold text-gray-700 uppercase mb-1">Model Name</label>
              <input
                type="text"
                value={newEquipModel}
                onChange={(e) => setNewEquipModel(e.target.value)}
                placeholder="Vestfrost VLS 024"
                className="w-full border border-gray-300 rounded-lg p-2.5 text-sm"
                required
              />
            </div>
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-bold text-gray-700 uppercase mb-1">Min Temp (°C)</label>
              <input
                type="number"
                step="0.5"
                value={newEquipMinTemp}
                onChange={(e) => setNewEquipMinTemp(Number(e.target.value))}
                className="w-full border border-gray-300 rounded-lg p-2.5 text-sm"
                required
              />
            </div>
            <div>
              <label className="block text-xs font-bold text-gray-700 uppercase mb-1">Max Temp (°C)</label>
              <input
                type="number"
                step="0.5"
                value={newEquipMaxTemp}
                onChange={(e) => setNewEquipMaxTemp(Number(e.target.value))}
                className="w-full border border-gray-300 rounded-lg p-2.5 text-sm"
                required
              />
            </div>
          </div>

          <div className="flex justify-end gap-2 pt-3 border-t">
            <button
              type="button"
              onClick={() => setIsRegisterEquipModalOpen(false)}
              className="px-4 py-2 border border-gray-300 rounded-lg text-sm text-gray-700 hover:bg-gray-50"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={isSubmitting}
              className="px-4 py-2 bg-emerald-600 hover:bg-emerald-700 text-white rounded-lg text-sm font-semibold"
            >
              {isSubmitting ? 'Registering...' : 'Register Equipment'}
            </button>
          </div>
        </form>
      </Modal>

      {/* MODAL: Schedule Outreach Camp */}
      <Modal
        isOpen={isCampModalOpen}
        onClose={() => setIsCampModalOpen(false)}
        title="Schedule Village Outreach Health Camp"
      >
        <form onSubmit={handleCreateCamp} className="space-y-4">
          <div>
            <label className="block text-xs font-bold text-gray-700 uppercase mb-1">Camp Title</label>
            <input
              type="text"
              value={newCampName}
              onChange={(e) => setNewCampName(e.target.value)}
              placeholder="e.g. Village Immunization & NCD Screening Drive"
              className="w-full border border-gray-300 rounded-lg p-2.5 text-sm"
              required
            />
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-bold text-gray-700 uppercase mb-1">Target Village / Habitation</label>
              <input
                type="text"
                value={newCampVillage}
                onChange={(e) => setNewCampVillage(e.target.value)}
                placeholder="e.g. Melmaruvathur West"
                className="w-full border border-gray-300 rounded-lg p-2.5 text-sm"
                required
              />
            </div>
            <div>
              <label className="block text-xs font-bold text-gray-700 uppercase mb-1">Scheduled Date</label>
              <input
                type="date"
                value={newCampDate}
                onChange={(e) => setNewCampDate(e.target.value)}
                className="w-full border border-gray-300 rounded-lg p-2.5 text-sm"
                required
              />
            </div>
          </div>

          <div>
            <label className="block text-xs font-bold text-gray-700 uppercase mb-1">Target Beneficiaries</label>
            <input
              type="number"
              value={newCampTarget}
              onChange={(e) => setNewCampTarget(Number(e.target.value))}
              className="w-full border border-gray-300 rounded-lg p-2.5 text-sm"
              required
            />
          </div>

          <div>
            <label className="block text-xs font-bold text-gray-700 uppercase mb-1">Field Notes</label>
            <textarea
              value={newCampNotes}
              onChange={(e) => setNewCampNotes(e.target.value)}
              placeholder="Specify vaccines, BP/Sugar kits, and ASHA mobilizing team"
              className="w-full border border-gray-300 rounded-lg p-2.5 text-sm h-20"
            />
          </div>

          <div className="flex justify-end gap-2 pt-3 border-t">
            <button
              type="button"
              onClick={() => setIsCampModalOpen(false)}
              className="px-4 py-2 border border-gray-300 rounded-lg text-sm text-gray-700 hover:bg-gray-50"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={isSubmitting}
              className="px-4 py-2 bg-emerald-600 hover:bg-emerald-700 text-white rounded-lg text-sm font-semibold"
            >
              {isSubmitting ? 'Scheduling...' : 'Schedule Camp'}
            </button>
          </div>
        </form>
      </Modal>

      {/* MODAL: Update Outreach Camp Progress */}
      <Modal
        isOpen={isUpdateCampModalOpen}
        onClose={() => setIsUpdateCampModalOpen(false)}
        title="Update Outreach Camp Progress"
      >
        <form onSubmit={handleUpdateCamp} className="space-y-4">
          <div>
            <label className="block text-xs font-bold text-gray-700 uppercase mb-1">Camp Status</label>
            <select
              value={updateCampStatus}
              onChange={(e) => setUpdateCampStatus(e.target.value)}
              className="w-full border border-gray-300 rounded-lg p-2.5 text-sm"
            >
              <option value="SCHEDULED">SCHEDULED</option>
              <option value="IN_PROGRESS">IN_PROGRESS</option>
              <option value="COMPLETED">COMPLETED</option>
              <option value="POSTPONED">POSTPONED</option>
              <option value="CANCELLED">CANCELLED</option>
            </select>
          </div>

          <div>
            <label className="block text-xs font-bold text-gray-700 uppercase mb-1">Actual Beneficiaries Served</label>
            <input
              type="number"
              value={updateCampActualServed}
              onChange={(e) => setUpdateCampActualServed(Number(e.target.value))}
              className="w-full border border-gray-300 rounded-lg p-2.5 text-sm font-bold"
              required
            />
          </div>

          <div className="flex justify-end gap-2 pt-3 border-t">
            <button
              type="button"
              onClick={() => setIsUpdateCampModalOpen(false)}
              className="px-4 py-2 border border-gray-300 rounded-lg text-sm text-gray-700 hover:bg-gray-50"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={isSubmitting}
              className="px-4 py-2 bg-emerald-600 hover:bg-emerald-700 text-white rounded-lg text-sm font-semibold"
            >
              {isSubmitting ? 'Updating...' : 'Save Progress'}
            </button>
          </div>
        </form>
      </Modal>

      {/* MODAL: Redress Grievance */}
      <Modal
        isOpen={isGrievanceModalOpen}
        onClose={() => setIsGrievanceModalOpen(false)}
        title="Grievance Action & Redressal"
      >
        <form onSubmit={handleResolveGrievance} className="space-y-4">
          <div className="bg-gray-50 p-3 rounded-lg text-sm">
            <div className="font-semibold text-gray-900">{selectedGrievance?.subject || 'Feedback'}</div>
            <p className="text-gray-600 mt-1">{selectedGrievance?.description}</p>
          </div>

          <div>
            <label className="block text-xs font-bold text-gray-700 uppercase mb-1">Action Determination</label>
            <select
              value={grievanceAction}
              onChange={(e) => setGrievanceAction(e.target.value as any)}
              className="w-full border border-gray-300 rounded-lg p-2.5 text-sm"
            >
              <option value="RESOLVED">Resolve at Facility Level</option>
              <option value="ESCALATED">Escalate to District Health Officer</option>
            </select>
          </div>

          <div>
            <label className="block text-xs font-bold text-gray-700 uppercase mb-1">Resolution Summary / Action Notes</label>
            <textarea
              value={resolutionNotes}
              onChange={(e) => setResolutionNotes(e.target.value)}
              placeholder="Detail actions taken (e.g. Counseled pharmacy staff, fast-tracked OPD queue for elderly)"
              className="w-full border border-gray-300 rounded-lg p-2.5 text-sm h-24"
              required
            />
          </div>

          <div className="flex justify-end gap-2 pt-3 border-t">
            <button
              type="button"
              onClick={() => setIsGrievanceModalOpen(false)}
              className="px-4 py-2 border border-gray-300 rounded-lg text-sm text-gray-700 hover:bg-gray-50"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={isSubmitting}
              className="px-4 py-2 bg-emerald-600 hover:bg-emerald-700 text-white rounded-lg text-sm font-semibold"
            >
              {isSubmitting ? 'Saving...' : 'Submit Resolution'}
            </button>
          </div>
        </form>
      </Modal>
    </div>
  );
}
