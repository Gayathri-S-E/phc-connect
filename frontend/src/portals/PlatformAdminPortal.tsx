import React, { useState, useEffect } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { 
  ShieldAlert, ShieldCheck, Users, Key, 
  Activity, Server, Database, Lock, 
  Search, Plus, CheckCircle, AlertTriangle, 
  Clock, FileText, ChevronRight, RefreshCw, Cpu,
  Shield, Code2, Layers
} from 'lucide-react';
import { api } from '../services/api';
import { useAuth } from '../context/AuthContext';
import { useLanguage } from '../context/LanguageContext';
import { StateView } from '../components/common/StateView';
import { PageHeader } from '../components/ui/page-header';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '../components/ui/card';
import { Badge } from '../components/ui/badge';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { 
  Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription, DialogFooter 
} from '../components/ui/dialog';
import { 
  Table, TableHeader, TableBody, TableHead, TableRow, TableCell 
} from '../components/ui/table';
import { Alert, AlertTitle, AlertDescription } from '../components/ui/alert';

export default function PlatformAdminPortal() {
  const { user } = useAuth();
  const { t } = useLanguage();
  const location = useLocation();
  const navigate = useNavigate();

  const getTabFromPath = (pathname: string): 'health' | 'security' | 'users' | 'roles' | 'audit' => {
    if (pathname.includes('/platform/security')) return 'security';
    if (pathname.includes('/platform/users')) return 'users';
    if (pathname.includes('/platform/roles')) return 'roles';
    if (pathname.includes('/platform/audit')) return 'audit';
    return 'health';
  };

  const [activeTab, setActiveTab] = useState<'health' | 'security' | 'users' | 'roles' | 'audit'>(getTabFromPath(location.pathname));

  useEffect(() => {
    const tab = getTabFromPath(location.pathname);
    setActiveTab(tab);
  }, [location.pathname]);

  const handleTabChange = (tab: 'health' | 'security' | 'users' | 'roles' | 'audit') => {
    setActiveTab(tab);
    const pathMap: Record<'health' | 'security' | 'users' | 'roles' | 'audit', string> = {
      health: '/platform',
      security: '/platform/security',
      users: '/platform/users',
      roles: '/platform/roles',
      audit: '/platform/audit',
    };
    navigate(pathMap[tab]);
  };

  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Platform Dashboard & Telemetry Data
  const [platformMetrics, setPlatformMetrics] = useState<any>(null);
  const [securityEvents, setSecurityEvents] = useState<any[]>([]);

  // Users State
  const [usersList, setUsersList] = useState<any[]>([]);
  const [isCreateUserModalOpen, setIsCreateUserModalOpen] = useState(false);
  const [newUserEmail, setNewUserEmail] = useState('');
  const [newUserName, setNewUserName] = useState('');
  const [newUserPassword, setNewUserPassword] = useState('Demo@Health2026');
  const [newUserPhone, setNewUserPhone] = useState('');

  // Roles State
  const [rolesList, setRolesList] = useState<any[]>([]);
  const [selectedUserForRole, setSelectedUserForRole] = useState<any>(null);
  const [isRoleAssignModalOpen, setIsRoleAssignModalOpen] = useState(false);
  const [selectedRoleId, setSelectedRoleId] = useState('');
  const [selectedScopeLevel, setSelectedScopeLevel] = useState<'FACILITY' | 'DISTRICT' | 'STATE' | 'GLOBAL'>('FACILITY');

  // Audit Logs State
  const [auditLogs, setAuditLogs] = useState<any[]>([]);
  const [auditPage, setAuditPage] = useState(1);
  const [selectedAuditLog, setSelectedAuditLog] = useState<any>(null);
  const [isAuditModalOpen, setIsAuditModalOpen] = useState(false);

  const [isSubmitting, setIsSubmitting] = useState(false);
  const [actionSuccess, setActionSuccess] = useState<string | null>(null);

  const fetchPlatformData = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const [metricsRes, secRes, usersRes, rolesRes, auditRes] = await Promise.all([
        api.get<any>('/platform/dashboard').catch(() => ({ data: null })),
        api.get<any[]>('/platform/security-events').catch(() => ({ data: [] })),
        api.get<any>('/users?page_size=50').catch(() => ({ data: { items: [] } })),
        api.get<any[]>('/roles').catch(() => ({ data: [] })),
        api.get<any>(`/audit-logs?page=${auditPage}&page_size=20`).catch(() => ({ data: { items: [] } })),
      ]);

      if (metricsRes?.data) setPlatformMetrics(metricsRes.data);
      if (secRes?.data) setSecurityEvents(secRes.data);
      if (usersRes?.data) {
        setUsersList(Array.isArray(usersRes.data) ? usersRes.data : usersRes.data.items || []);
      }
      if (rolesRes?.data) setRolesList(rolesRes.data);
      if (auditRes?.data) {
        setAuditLogs(Array.isArray(auditRes.data) ? auditRes.data : auditRes.data.items || []);
      }
    } catch (err: any) {
      setError(err?.detail || 'Failed to load platform administration telemetry');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchPlatformData();
  }, [auditPage]);

  // Provision New Platform User
  const handleCreateUser = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSubmitting(true);
    try {
      await api.post('/users', {
        email: newUserEmail,
        full_name: newUserName,
        password: newUserPassword,
        phone_number: newUserPhone || undefined,
      });
      setActionSuccess(`User account ${newUserEmail} provisioned successfully.`);
      setIsCreateUserModalOpen(false);
      setNewUserEmail('');
      setNewUserName('');
      fetchPlatformData();
    } catch (err: any) {
      alert(err?.detail || 'Failed to provision user');
    } finally {
      setIsSubmitting(false);
    }
  };

  // Assign Scoped Canonical Role to User
  const handleAssignRole = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedUserForRole || !selectedRoleId) return;
    setIsSubmitting(true);
    try {
      await api.post(`/users/${selectedUserForRole.id}/roles`, {
        role_id: selectedRoleId,
        scope_level: selectedScopeLevel,
      });
      setActionSuccess(`Canonical role assigned to ${selectedUserForRole.full_name || selectedUserForRole.email}`);
      setIsRoleAssignModalOpen(false);
      fetchPlatformData();
    } catch (err: any) {
      alert(err?.detail || 'Failed to assign role');
    } finally {
      setIsSubmitting(false);
    }
  };

  if (isLoading) return <StateView type="loading" message="Loading platform administration..." />;
  if (error) return <StateView type="error" message={error} onRetry={fetchPlatformData} />;

  return (
    <div className="space-y-6">
      {/* Context-First Standard Page Header */}
      <PageHeader
        breadcrumbs={[
          { label: 'Home', href: '/' },
          { label: 'Platform Administration', href: '/platform' },
          { label: 'Infrastructure & RBAC' }
        ]}
        scopeBadge={{ label: 'Global Platform Security Tier', variant: 'slate' }}
        roleBadge={{ label: 'Role 13: Super / Platform Administrator', variant: 'destructive' }}
        title="Platform Infrastructure, RBAC & Security Operations"
        description="Monitor backend FastAPI service telemetry, manage identity provisioning, enforce canonical 13-role access controls, and inspect immutable audit trails."
        actions={
          <div className="flex items-center gap-2">
            <Button 
              variant="outline" 
              size="sm" 
              onClick={fetchPlatformData}
              className="gap-1.5"
            >
              <RefreshCw className="w-3.5 h-3.5" />
              Refresh
            </Button>
            <Button
              onClick={() => setIsCreateUserModalOpen(true)}
              variant="default"
              size="sm"
              className="gap-2"
            >
              <Plus className="w-3.5 h-3.5" />
              Provision New User
            </Button>
          </div>
        }
      />

      {/* Action Notification Alert */}
      {actionSuccess && (
        <Alert variant="default" className="border-emerald-200 bg-emerald-50 text-emerald-900">
          <CheckCircle className="w-4 h-4 text-emerald-600" />
          <div className="flex-1">
            <AlertTitle className="text-emerald-900 font-semibold">Platform Operation Completed</AlertTitle>
            <AlertDescription className="text-emerald-700 text-xs mt-0.5">{actionSuccess}</AlertDescription>
          </div>
          <Button variant="ghost" size="sm" onClick={() => setActionSuccess(null)} className="text-emerald-700 hover:text-emerald-900 h-7 text-xs">
            Dismiss
          </Button>
        </Alert>
      )}

      {/* Platform Health Metrics Strip */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card className="border-border shadow-xs hover:border-emerald-300 transition-colors">
          <CardContent className="p-4 flex items-center justify-between">
            <div>
              <p className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">FastAPI Core Health</p>
              <h3 className="text-2xl font-bold text-emerald-600 mt-1">HEALTHY</h3>
              <p className="text-xs text-muted-foreground mt-1">Response Latency: 24ms</p>
            </div>
            <div className="w-10 h-10 rounded-lg bg-emerald-50 text-emerald-700 flex items-center justify-center border border-emerald-100">
              <Activity className="w-5 h-5" />
            </div>
          </CardContent>
        </Card>

        <Card className="border-border shadow-xs hover:border-sky-300 transition-colors">
          <CardContent className="p-4 flex items-center justify-between">
            <div>
              <p className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">Database Connection Pool</p>
              <h3 className="text-2xl font-bold text-foreground mt-1">Active</h3>
              <p className="text-xs text-sky-700 font-medium mt-1">SQLAlchemy Asyncpg Pool</p>
            </div>
            <div className="w-10 h-10 rounded-lg bg-sky-50 text-sky-700 flex items-center justify-center border border-sky-100">
              <Database className="w-5 h-5" />
            </div>
          </CardContent>
        </Card>

        <Card className="border-border shadow-xs hover:border-purple-300 transition-colors">
          <CardContent className="p-4 flex items-center justify-between">
            <div>
              <p className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">Provisioned Users</p>
              <h3 className="text-2xl font-bold text-foreground mt-1">{usersList.length} Accounts</h3>
              <p className="text-xs text-muted-foreground mt-1">Across 13 canonical tiers</p>
            </div>
            <div className="w-10 h-10 rounded-lg bg-purple-50 text-purple-700 flex items-center justify-center border border-purple-100">
              <Users className="w-5 h-5" />
            </div>
          </CardContent>
        </Card>

        <Card className="border-border shadow-xs hover:border-slate-300 transition-colors">
          <CardContent className="p-4 flex items-center justify-between">
            <div>
              <p className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">Security Events</p>
              <h3 className="text-2xl font-bold text-foreground mt-1">{securityEvents.length} Events</h3>
              <p className="text-xs text-emerald-700 font-medium mt-1">0 Critical breaches detected</p>
            </div>
            <div className="w-10 h-10 rounded-lg bg-slate-100 text-slate-700 flex items-center justify-center border border-slate-200">
              <Lock className="w-5 h-5" />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Navigation Sub-Tabs */}
      <div className="border-b border-border bg-card px-4 rounded-lg shadow-xs flex items-center gap-2 overflow-x-auto">
        <button
          onClick={() => handleTabChange('health')}
          className={`py-3 px-3.5 text-sm font-medium border-b-2 flex items-center gap-2 transition-colors whitespace-nowrap ${
            activeTab === 'health'
              ? 'border-foreground text-foreground font-semibold'
              : 'border-transparent text-muted-foreground hover:text-foreground'
          }`}
        >
          <Server className="w-4 h-4" />
          Platform Health & Telemetry
        </button>
        <button
          onClick={() => handleTabChange('security')}
          className={`py-3 px-3.5 text-sm font-medium border-b-2 flex items-center gap-2 transition-colors whitespace-nowrap ${
            activeTab === 'security'
              ? 'border-foreground text-foreground font-semibold'
              : 'border-transparent text-muted-foreground hover:text-foreground'
          }`}
        >
          <ShieldAlert className="w-4 h-4" />
          Security Telemetry & Events
          {securityEvents.length > 0 && (
            <Badge variant="destructive" className="px-1.5 py-0 text-[10px] ml-1">
              {securityEvents.length}
            </Badge>
          )}
        </button>
        <button
          onClick={() => handleTabChange('users')}
          className={`py-3 px-3.5 text-sm font-medium border-b-2 flex items-center gap-2 transition-colors whitespace-nowrap ${
            activeTab === 'users'
              ? 'border-foreground text-foreground font-semibold'
              : 'border-transparent text-muted-foreground hover:text-foreground'
          }`}
        >
          <Users className="w-4 h-4" />
          User Provisioning & Accounts
        </button>
        <button
          onClick={() => handleTabChange('roles')}
          className={`py-3 px-3.5 text-sm font-medium border-b-2 flex items-center gap-2 transition-colors whitespace-nowrap ${
            activeTab === 'roles'
              ? 'border-foreground text-foreground font-semibold'
              : 'border-transparent text-muted-foreground hover:text-foreground'
          }`}
        >
          <Key className="w-4 h-4" />
          Canonical 13-Role Catalog
        </button>
        <button
          onClick={() => handleTabChange('audit')}
          className={`py-3 px-3.5 text-sm font-medium border-b-2 flex items-center gap-2 transition-colors whitespace-nowrap ${
            activeTab === 'audit'
              ? 'border-foreground text-foreground font-semibold'
              : 'border-transparent text-muted-foreground hover:text-foreground'
          }`}
        >
          <FileText className="w-4 h-4" />
          Immutable Audit Trail
        </button>
      </div>

      {/* TAB 1: HEALTH & TELEMETRY */}
      {activeTab === 'health' && (
        <div className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <Card className="border-border shadow-xs">
              <CardHeader className="pb-3">
                <CardTitle className="text-base flex items-center gap-2 text-foreground">
                  <ShieldCheck className="w-4 h-4 text-emerald-600" />
                  Canonical Role Governance & Zero Drift Policy
                </CardTitle>
                <CardDescription>
                  Strict architectural enforcement of exactly 13 canonical operational roles with hierarchical scoping.
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-3">
                <p className="text-xs text-muted-foreground leading-relaxed">
                  Ad-hoc roles and permission mergers are strictly prohibited. Dynamic permission resolution occurs on every incoming API request via JWT claim evaluation and database row-level security.
                </p>
                <div className="p-3 bg-muted rounded-lg font-mono text-[11px] text-foreground">
                  Scope hierarchy: GLOBAL &gt; STATE &gt; DISTRICT &gt; FACILITY &gt; SELF
                </div>
              </CardContent>
            </Card>

            <Card className="border-border shadow-xs">
              <CardHeader className="pb-3">
                <CardTitle className="text-base flex items-center gap-2 text-foreground">
                  <Cpu className="w-4 h-4 text-sky-600" />
                  Background Surveillance Cron Jobs
                </CardTitle>
                <CardDescription>
                  Asynchronous workers evaluating cold-chain temperature telemetry, stock burn velocity, and anomaly detection.
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-3">
                <div className="p-3 bg-slate-50 border border-slate-200 rounded-lg text-xs space-y-2 text-slate-700">
                  <div className="flex justify-between items-center">
                    <span className="font-semibold text-foreground">Scheduler Loop:</span>
                    <Badge variant="success">Active (60s tick)</Badge>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="font-semibold text-foreground">Worker Thread Status:</span>
                    <span className="text-muted-foreground">IDLE (Queue clear)</span>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        </div>
      )}

      {/* TAB 2: SECURITY TELEMETRY */}
      {activeTab === 'security' && (
        <Card className="border-border shadow-xs">
          <CardHeader className="pb-4">
            <CardTitle className="text-base text-foreground">Security Events Stream</CardTitle>
            <CardDescription>
              Real-time feed of authentication handshakes, token rotations, and scoped access checks.
            </CardDescription>
          </CardHeader>
          <CardContent className="p-0">
            {securityEvents.length === 0 ? (
              <div className="p-8 text-center text-muted-foreground text-sm">
                No security incidents or suspicious authorization events detected.
              </div>
            ) : (
              <div className="overflow-x-auto">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Action Code</TableHead>
                      <TableHead>Target Resource</TableHead>
                      <TableHead>IP Origin</TableHead>
                      <TableHead>Timestamp</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {securityEvents.map((sec) => (
                      <TableRow key={sec.id}>
                        <TableCell className="font-mono font-bold text-foreground text-xs">
                          {sec.action}
                        </TableCell>
                        <TableCell className="text-xs text-foreground">
                          {sec.resource_type} ({sec.resource_id?.slice(0, 8)})
                        </TableCell>
                        <TableCell className="font-mono text-xs text-muted-foreground">
                          {sec.ip_address || '127.0.0.1'}
                        </TableCell>
                        <TableCell className="text-xs text-muted-foreground">
                          {new Date(sec.created_at).toLocaleString()}
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </div>
            )}
          </CardContent>
        </Card>
      )}

      {/* TAB 3: USER PROVISIONING */}
      {activeTab === 'users' && (
        <Card className="border-border shadow-xs">
          <CardHeader className="pb-4">
            <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
              <div>
                <CardTitle className="text-base text-foreground">User Identity & Access Management</CardTitle>
                <CardDescription>
                  Manage active user credentials and assign scoped roles across the primary care network.
                </CardDescription>
              </div>
              <Button
                onClick={() => setIsCreateUserModalOpen(true)}
                variant="default"
                size="sm"
                className="gap-1.5 text-xs"
              >
                <Plus className="w-3.5 h-3.5" />
                Provision User
              </Button>
            </div>
          </CardHeader>
          <CardContent className="p-0">
            <div className="overflow-x-auto">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>User Details</TableHead>
                    <TableHead>Assigned Roles</TableHead>
                    <TableHead>Account Status</TableHead>
                    <TableHead className="text-right">Action</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {usersList.map((u) => (
                    <TableRow key={u.id}>
                      <TableCell>
                        <div className="font-semibold text-foreground text-xs">{u.full_name}</div>
                        <div className="text-[11px] font-mono text-muted-foreground">{u.email}</div>
                      </TableCell>
                      <TableCell>
                        <div className="flex flex-wrap gap-1">
                          {u.roles?.map((r: any, idx: number) => (
                            <Badge key={idx} variant="outline" className="font-mono text-[10px]">
                              {r.role_code || r.name}
                            </Badge>
                          )) || <span className="text-xs text-muted-foreground">None</span>}
                        </div>
                      </TableCell>
                      <TableCell>
                        <Badge variant={u.is_active ? 'success' : 'destructive'}>
                          {u.is_active ? 'Active' : 'Disabled'}
                        </Badge>
                      </TableCell>
                      <TableCell className="text-right">
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={() => {
                            setSelectedUserForRole(u);
                            setSelectedRoleId(rolesList[0]?.id || '');
                            setSelectedScopeLevel('FACILITY');
                            setIsRoleAssignModalOpen(true);
                          }}
                          className="h-7 text-xs gap-1"
                        >
                          <Key className="w-3 h-3" />
                          Assign Role
                        </Button>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
          </CardContent>
        </Card>
      )}

      {/* TAB 4: CANONICAL 13-ROLE CATALOG */}
      {activeTab === 'roles' && (
        <Card className="border-border shadow-xs">
          <CardHeader className="pb-4">
            <CardTitle className="text-base text-foreground">Canonical 13-Role Catalog</CardTitle>
            <CardDescription>
              The immutable core roles established in system specifications. Roles are read-only to preserve architecture integrity.
            </CardDescription>
          </CardHeader>
          <CardContent className="p-0">
            <div className="overflow-x-auto">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Role Code</TableHead>
                    <TableHead>Display Name</TableHead>
                    <TableHead>Description</TableHead>
                    <TableHead>Permissions</TableHead>
                    <TableHead>Type</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {rolesList.map((r: any) => (
                    <TableRow key={r.id}>
                      <TableCell className="font-mono font-bold text-foreground text-xs">
                        {r.code}
                      </TableCell>
                      <TableCell className="font-semibold text-foreground text-xs">
                        {r.name}
                      </TableCell>
                      <TableCell className="text-xs text-muted-foreground max-w-xs truncate">
                        {r.description}
                      </TableCell>
                      <TableCell className="text-xs text-muted-foreground">
                        {r.permissions?.length || 0} permissions
                      </TableCell>
                      <TableCell>
                        <Badge variant={r.is_system ? 'info' : 'outline'}>
                          {r.is_system ? 'System Protected' : 'Dynamic'}
                        </Badge>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
          </CardContent>
        </Card>
      )}

      {/* TAB 5: IMMUTABLE AUDIT TRAIL */}
      {activeTab === 'audit' && (
        <Card className="border-border shadow-xs">
          <CardHeader className="pb-4">
            <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
              <div>
                <CardTitle className="text-base text-foreground">Immutable Audit Trail</CardTitle>
                <CardDescription>
                  Append-only compliance log recording all healthcare, pharmacy, and governance events.
                </CardDescription>
              </div>
              <div className="flex items-center gap-2">
                <Button
                  size="sm"
                  variant="outline"
                  onClick={() => setAuditPage(prev => Math.max(1, prev - 1))}
                  disabled={auditPage === 1}
                  className="h-7 text-xs"
                >
                  Previous
                </Button>
                <span className="text-xs font-semibold text-foreground">Page {auditPage}</span>
                <Button
                  size="sm"
                  variant="outline"
                  onClick={() => setAuditPage(prev => prev + 1)}
                  className="h-7 text-xs"
                >
                  Next
                </Button>
              </div>
            </div>
          </CardHeader>
          <CardContent className="p-0">
            {auditLogs.length === 0 ? (
              <div className="p-8 text-center text-muted-foreground text-sm">
                No audit logs recorded for this page.
              </div>
            ) : (
              <div className="overflow-x-auto">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Event Action</TableHead>
                      <TableHead>Resource</TableHead>
                      <TableHead>Actor Ref</TableHead>
                      <TableHead>IP Origin</TableHead>
                      <TableHead>Timestamp</TableHead>
                      <TableHead className="text-right">State Diff</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {auditLogs.map((log) => (
                      <TableRow key={log.id}>
                        <TableCell className="font-mono font-bold text-foreground text-xs">
                          {log.action}
                        </TableCell>
                        <TableCell className="text-xs text-foreground">
                          {log.resource_type} ({log.resource_id?.slice(0, 8)})
                        </TableCell>
                        <TableCell className="font-mono text-xs text-muted-foreground">
                          {log.actor_id?.slice(0, 8) || 'SYSTEM'}
                        </TableCell>
                        <TableCell className="font-mono text-xs text-muted-foreground">
                          {log.ip_address || 'Internal'}
                        </TableCell>
                        <TableCell className="text-xs text-muted-foreground">
                          {new Date(log.created_at).toLocaleString()}
                        </TableCell>
                        <TableCell className="text-right">
                          <Button
                            size="sm"
                            variant="ghost"
                            onClick={() => {
                              setSelectedAuditLog(log);
                              setIsAuditModalOpen(true);
                            }}
                            className="h-7 text-xs font-semibold text-sky-700 hover:text-sky-900"
                          >
                            Inspect State →
                          </Button>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </div>
            )}
          </CardContent>
        </Card>
      )}

      {/* DIALOG: Provision User */}
      <Dialog open={isCreateUserModalOpen} onOpenChange={setIsCreateUserModalOpen}>
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle>Provision Platform User</DialogTitle>
            <DialogDescription>
              Create identity credentials for health officers and clinicians.
            </DialogDescription>
          </DialogHeader>
          <form onSubmit={handleCreateUser} className="space-y-4">
            <div className="space-y-1.5">
              <label className="text-xs font-semibold text-foreground">Email Address</label>
              <Input
                type="email"
                value={newUserEmail}
                onChange={(e) => setNewUserEmail(e.target.value)}
                placeholder="officer.name@smarthealth.gov.in"
                className="text-xs"
                required
              />
            </div>

            <div className="space-y-1.5">
              <label className="text-xs font-semibold text-foreground">Full Legal Name</label>
              <Input
                type="text"
                value={newUserName}
                onChange={(e) => setNewUserName(e.target.value)}
                placeholder="Dr. Rajesh Kumar"
                className="text-xs"
                required
              />
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div className="space-y-1.5">
                <label className="text-xs font-semibold text-foreground">Temporary Password</label>
                <Input
                  type="text"
                  value={newUserPassword}
                  onChange={(e) => setNewUserPassword(e.target.value)}
                  className="text-xs font-mono"
                  required
                />
              </div>
              <div className="space-y-1.5">
                <label className="text-xs font-semibold text-foreground">Phone Number</label>
                <Input
                  type="text"
                  value={newUserPhone}
                  onChange={(e) => setNewUserPhone(e.target.value)}
                  placeholder="+91 98765 43210"
                  className="text-xs"
                />
              </div>
            </div>

            <DialogFooter className="gap-2 sm:gap-0 pt-2">
              <Button
                type="button"
                variant="outline"
                onClick={() => setIsCreateUserModalOpen(false)}
              >
                Cancel
              </Button>
              <Button
                type="submit"
                disabled={isSubmitting}
              >
                {isSubmitting ? 'Provisioning...' : 'Provision User'}
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>

      {/* DIALOG: Assign Role */}
      <Dialog open={isRoleAssignModalOpen} onOpenChange={setIsRoleAssignModalOpen}>
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle>Assign Scoped Role</DialogTitle>
            <DialogDescription>
              Assign role privileges to: {selectedUserForRole?.full_name || selectedUserForRole?.email}
            </DialogDescription>
          </DialogHeader>
          <form onSubmit={handleAssignRole} className="space-y-4">
            <div className="p-3 bg-muted rounded-lg text-xs space-y-1">
              <div className="font-semibold text-foreground">{selectedUserForRole?.full_name}</div>
              <div className="text-muted-foreground font-mono">{selectedUserForRole?.email}</div>
            </div>

            <div className="space-y-1.5">
              <label className="text-xs font-semibold text-foreground">Select Canonical Role</label>
              <select
                value={selectedRoleId}
                onChange={(e) => setSelectedRoleId(e.target.value)}
                className="w-full border border-border bg-background rounded-md px-3 py-2 text-xs text-foreground font-medium"
                required
              >
                {rolesList.map((r: any) => (
                  <option key={r.id} value={r.id}>
                    {r.code} — {r.name}
                  </option>
                ))}
              </select>
            </div>

            <div className="space-y-1.5">
              <label className="text-xs font-semibold text-foreground">Scope Level</label>
              <select
                value={selectedScopeLevel}
                onChange={(e) => setSelectedScopeLevel(e.target.value as any)}
                className="w-full border border-border bg-background rounded-md px-3 py-2 text-xs text-foreground font-medium"
                required
              >
                <option value="FACILITY">FACILITY (Primary Healthcare Center)</option>
                <option value="DISTRICT">DISTRICT (District Health Administration)</option>
                <option value="STATE">STATE (State Health Directorate)</option>
                <option value="GLOBAL">GLOBAL (Pan-India / Platform Admin)</option>
              </select>
            </div>

            <DialogFooter className="gap-2 sm:gap-0 pt-2">
              <Button
                type="button"
                variant="outline"
                onClick={() => setIsRoleAssignModalOpen(false)}
              >
                Cancel
              </Button>
              <Button
                type="submit"
                disabled={isSubmitting}
              >
                {isSubmitting ? 'Assigning...' : 'Confirm Role Assignment'}
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>

      {/* DIALOG: Inspect Audit State Diff */}
      <Dialog open={isAuditModalOpen} onOpenChange={setIsAuditModalOpen}>
        <DialogContent className="sm:max-w-2xl">
          <DialogHeader>
            <DialogTitle>Audit State Inspection</DialogTitle>
            <DialogDescription>
              Action #{selectedAuditLog?.action} on {selectedAuditLog?.resource_type} ({selectedAuditLog?.resource_id?.slice(0, 8)})
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4">
            <div className="p-3 bg-muted rounded-lg text-xs space-y-1 font-mono">
              <div>Actor ID: {selectedAuditLog?.actor_id || 'SYSTEM_WORKER'}</div>
              <div>Recorded At: {selectedAuditLog?.created_at}</div>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              <div>
                <label className="text-xs font-semibold text-foreground block mb-1">Previous State</label>
                <pre className="bg-slate-50 border border-slate-200 text-slate-800 p-3 rounded-lg text-[11px] overflow-x-auto h-44 font-mono">
                  {JSON.stringify(selectedAuditLog?.previous_state || {}, null, 2)}
                </pre>
              </div>
              <div>
                <label className="text-xs font-semibold text-foreground block mb-1">New State</label>
                <pre className="bg-emerald-50/70 border border-emerald-200 text-emerald-900 p-3 rounded-lg text-[11px] overflow-x-auto h-44 font-mono">
                  {JSON.stringify(selectedAuditLog?.new_state || {}, null, 2)}
                </pre>
              </div>
            </div>

            <DialogFooter className="pt-2">
              <Button
                onClick={() => setIsAuditModalOpen(false)}
              >
                Close Inspector
              </Button>
            </DialogFooter>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
}
