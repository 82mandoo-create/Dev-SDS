import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { dashboardApi } from '../api/client';
import {
  Users, FileCheck, Monitor, Shield, AlertTriangle,
  Activity, Bot, RefreshCw, Clock,
  CheckCircle, XCircle, AlertCircle, WifiOff, Lock, Wifi
} from 'lucide-react';
import {
  AreaChart, Area, BarChart, Bar, Cell,
  XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend
} from 'recharts';
import { format, parseISO } from 'date-fns';
import { ko } from 'date-fns/locale';

// ─────────────────── 타입 ───────────────────
interface Summary {
  employees:    { total: number; active: number };
  certificates: { total: number; active: number; expired: number; expiring_soon: number; critical: number };
  pcs:          { total: number; online: number; offline: number; online_rate: number;
                  no_antivirus: number; no_firewall: number; not_encrypted: number };
  security:     { unresolved_events: number; avg_security_score: number };
  users:        { total: number };
  notifications:{ unread: number };
}

interface ActivityLog {
  id: number;
  action: string;
  action_label: string;
  resource_type: string | null;
  resource_label: string | null;
  description: string;
  user_name: string;
  ip_address: string | null;
  created_at: string | null;
}

interface SecurityEvent {
  id: number;
  pc_id: number;
  pc_name: string;
  asset_tag: string | null;
  event_type: string;
  severity: 'critical' | 'high' | 'medium' | 'low';
  title: string;
  description: string;
  occurred_at: string | null;
}

interface ExpiringCert {
  id: number;
  name: string;
  domain: string | null;
  cert_type: string;
  expiry_date: string;
  days_left: number;
  status: 'critical' | 'warning';
  vendor_name: string | null;
}

interface ActivityChartRow {
  date: string;
  login: number;
  sleep: number;
  wakeup: number;
}

interface ScoreRange {
  range: string;
  count: number;
  risk_level: 'critical' | 'high' | 'medium' | 'low' | 'safe';
}

interface AIInsight {
  category: string;
  message: string;
}

interface AIInsightsData {
  insights: AIInsight[];
  alerts:   { type: string; message: string }[];
  summary:  string;
  generated_at: string;
}

// ─────────────────── 상수 ───────────────────
// 보안 점수 범위별 막대 색상 (하드코딩 제거 – risk_level로 결정)
const RISK_COLOR: Record<string, string> = {
  critical: '#ef4444',
  high:     '#f97316',
  medium:   '#f59e0b',
  low:      '#60a5fa',
  safe:     '#10b981',
};

// action 별 배지 색상
const ACTION_COLOR: Record<string, string> = {
  LOGIN:           'badge-blue',
  LOGOUT:          'badge-gray',
  CREATE:          'badge-green',
  UPDATE:          'badge-yellow',
  DELETE:          'badge-red',
  REGISTER:        'badge-purple',
  RESOLVE:         'badge-green',
  LOCK:            'badge-red',
  UNLOCK:          'badge-blue',
  PASSWORD_CHANGE: 'badge-yellow',
};

const SEVERITY_BADGE: Record<string, string> = {
  critical: 'badge-red',
  high:     'badge-yellow',
  medium:   'badge-blue',
  low:      'badge-gray',
};
const SEVERITY_LABEL: Record<string, string> = {
  critical: '심각', high: '높음', medium: '보통', low: '낮음',
};

// ─────────────────── 서브 컴포넌트 ───────────────────
function StatCard({
  title, value, sub, icon: Icon, color, badge,
}: {
  title: string; value: string | number; sub?: string;
  icon: React.ElementType; color: string; badge?: React.ReactNode;
}) {
  return (
    <div className="card hover:shadow-md transition-shadow">
      <div className="flex items-start justify-between">
        <div className="flex-1 min-w-0">
          <p className="text-sm text-gray-500 font-medium">{title}</p>
          <p className="text-3xl font-bold text-gray-900 mt-1">{value}</p>
          {sub && <p className="text-xs text-gray-400 mt-1">{sub}</p>}
          {badge && <div className="mt-2">{badge}</div>}
        </div>
        <div className={`w-12 h-12 rounded-xl ${color} flex items-center justify-center flex-shrink-0 ml-3`}>
          <Icon size={22} className="text-white" />
        </div>
      </div>
    </div>
  );
}

function SeverityBadge({ severity }: { severity: string }) {
  return (
    <span className={`badge ${SEVERITY_BADGE[severity] ?? 'badge-gray'}`}>
      {SEVERITY_LABEL[severity] ?? severity}
    </span>
  );
}

function ActionBadge({ action, label }: { action: string; label: string }) {
  return (
    <span className={`badge ${ACTION_COLOR[action] ?? 'badge-gray'} whitespace-nowrap`}>
      {label || action}
    </span>
  );
}

function EmptyRow({ message }: { message: string }) {
  return (
    <div className="flex items-center justify-center gap-2 text-gray-400 text-sm py-6">
      <CheckCircle size={15} className="text-green-400" />
      {message}
    </div>
  );
}

function ChartSkeleton() {
  return <div className="h-[220px] bg-gray-100 animate-pulse rounded-lg" />;
}

// ─────────────────── 메인 페이지 ───────────────────
export default function DashboardPage() {
  const { data: summaryRes, isLoading, isError: summaryError } = useQuery({
    queryKey: ['dashboard-summary'],
    queryFn:  () => dashboardApi.getSummary(),
    refetchInterval: 30_000,
  });

  const { data: activitiesRes, isLoading: actLoading } = useQuery({
    queryKey: ['recent-activities'],
    queryFn:  () => dashboardApi.getRecentActivities(),
    refetchInterval: 60_000,
  });

  const { data: secEventsRes } = useQuery({
    queryKey: ['security-events'],
    queryFn:  () => dashboardApi.getSecurityEvents(),
    refetchInterval: 60_000,
  });

  const { data: expiringRes } = useQuery({
    queryKey: ['expiring-certs'],
    queryFn:  () => dashboardApi.getExpiringCertificates(30),
  });

  const { data: chartRes, isLoading: chartLoading } = useQuery({
    queryKey: ['activity-chart'],
    queryFn:  () => dashboardApi.getPCActivityChart(7),
  });

  const { data: scoreRes, isLoading: scoreLoading } = useQuery({
    queryKey: ['score-distribution'],
    queryFn:  () => dashboardApi.getSecurityScoreDistribution(),
  });

  const { data: insightsRes } = useQuery({
    queryKey: ['ai-insights'],
    queryFn:  () => dashboardApi.getAIInsights(),
    refetchInterval: 120_000,
  });

  // ── 데이터 추출 (타입 지정)
  const s        = summaryRes?.data     as Summary          | undefined;
  const acts     = activitiesRes?.data  as ActivityLog[]    | undefined ?? [];
  const secEvts  = secEventsRes?.data   as SecurityEvent[]  | undefined ?? [];
  const expCerts = expiringRes?.data    as ExpiringCert[]   | undefined ?? [];
  const chartData= chartRes?.data       as ActivityChartRow[]| undefined ?? [];
  const scoreDist= scoreRes?.data       as ScoreRange[]     | undefined ?? [];
  const insights = insightsRes?.data    as AIInsightsData   | undefined;

  // ── 전체 로딩 스피너
  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <RefreshCw className="animate-spin text-blue-600" size={32} />
      </div>
    );
  }

  // ── 오류 배너
  if (summaryError) {
    return (
      <div className="flex items-center gap-3 p-4 bg-red-50 border border-red-200 rounded-xl text-red-700">
        <XCircle size={20} />
        <span className="text-sm font-medium">대시보드 데이터를 불러오지 못했습니다. 잠시 후 다시 시도하세요.</span>
      </div>
    );
  }

  // ── 통계 기본값
  const emp  = s?.employees    ?? { total: 0, active: 0 };
  const cert = s?.certificates ?? { total: 0, active: 0, expired: 0, expiring_soon: 0, critical: 0 };
  const pc   = s?.pcs          ?? { total: 0, online: 0, offline: 0, online_rate: 0,
                                    no_antivirus: 0, no_firewall: 0, not_encrypted: 0 };
  const sec  = s?.security     ?? { unresolved_events: 0, avg_security_score: 0 };

  const certDanger    = cert.critical > 0;
  const secDanger     = sec.unresolved_events > 0;
  const pcSecureBadge = pc.no_antivirus > 0 || pc.no_firewall > 0 ? (
    <div className="flex gap-1 flex-wrap">
      {pc.no_antivirus > 0 && (
        <span className="badge badge-red text-xs">백신 미설치 {pc.no_antivirus}대</span>
      )}
      {pc.no_firewall > 0 && (
        <span className="badge badge-yellow text-xs">방화벽 미설정 {pc.no_firewall}대</span>
      )}
    </div>
  ) : null;

  return (
    <div className="space-y-6">

      {/* ── AI 경고 배너 */}
      {(insights?.alerts?.length ?? 0) > 0 && (
        <div className="space-y-2">
          {insights!.alerts.map((alert, i) => (
            <div
              key={i}
              className={`flex items-center gap-3 px-4 py-3 rounded-lg text-sm font-medium ${
                alert.type === 'critical'
                  ? 'bg-red-50 text-red-700 border border-red-200'
                  : 'bg-yellow-50 text-yellow-700 border border-yellow-200'
              }`}
            >
              <AlertTriangle size={16} />
              {alert.message}
            </div>
          ))}
        </div>
      )}

      {/* ── 4개 요약 카드 */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          title="활성 직원"
          value={emp.active}
          sub={`전체 ${emp.total}명`}
          icon={Users}
          color="bg-gradient-to-br from-blue-500 to-blue-600"
        />
        <StatCard
          title="인증서 현황"
          value={cert.total}
          sub={`만료예정 ${cert.expiring_soon}개 · 만료 ${cert.expired}개`}
          icon={FileCheck}
          color={certDanger
            ? 'bg-gradient-to-br from-red-500 to-red-600'
            : 'bg-gradient-to-br from-green-500 to-green-600'}
        />
        <StatCard
          title="PC 자산"
          value={pc.total}
          sub={`온라인 ${pc.online}대 (${pc.online_rate}%)`}
          icon={pc.online > 0 ? Wifi : WifiOff}
          color="bg-gradient-to-br from-purple-500 to-purple-600"
          badge={pcSecureBadge}
        />
        <StatCard
          title="보안 이벤트"
          value={sec.unresolved_events}
          sub={`평균 보안점수 ${sec.avg_security_score}점`}
          icon={secDanger ? AlertTriangle : Shield}
          color={secDanger
            ? 'bg-gradient-to-br from-orange-500 to-red-500'
            : 'bg-gradient-to-br from-teal-500 to-teal-600'}
        />
      </div>

      {/* ── 차트 행 */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">

        {/* PC 활동 영역 차트 */}
        <div className="lg:col-span-2 card">
          <h3 className="font-semibold text-gray-900 mb-4 flex items-center gap-2">
            <Activity size={18} className="text-blue-600" />
            PC 활동 현황 (최근 7일)
          </h3>
          {chartLoading ? <ChartSkeleton /> : (
            <ResponsiveContainer width="100%" height={220}>
              <AreaChart data={chartData}>
                <defs>
                  <linearGradient id="gLogin" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%"  stopColor="#3b82f6" stopOpacity={0.3} />
                    <stop offset="95%" stopColor="#3b82f6" stopOpacity={0} />
                  </linearGradient>
                  <linearGradient id="gSleep" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%"  stopColor="#8b5cf6" stopOpacity={0.2} />
                    <stop offset="95%" stopColor="#8b5cf6" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                <XAxis
                  dataKey="date"
                  tick={{ fontSize: 11 }}
                  tickFormatter={(v: string) => {
                    try { return format(parseISO(v), 'M/d', { locale: ko }); }
                    catch { return v.slice(5); }
                  }}
                />
                <YAxis tick={{ fontSize: 11 }} allowDecimals={false} />
                <Tooltip
                  formatter={(value: any, name: any) => [
                    `${value}건`,
                    name === 'login' ? '로그인' : name === 'sleep' ? '절전' : '절전해제',
                  ]}
                  labelFormatter={(label: any) => {
                    try { return format(parseISO(String(label)), 'yyyy년 M월 d일', { locale: ko }); }
                    catch { return String(label); }
                  }}
                />
                <Legend
                  formatter={(value: string) =>
                    value === 'login' ? '로그인' : value === 'sleep' ? '절전' : '절전해제'
                  }
                />
                <Area type="monotone" dataKey="login"  stroke="#3b82f6" fill="url(#gLogin)"  />
                <Area type="monotone" dataKey="sleep"  stroke="#8b5cf6" fill="url(#gSleep)"  />
                <Area type="monotone" dataKey="wakeup" stroke="#10b981" fill="transparent"   />
              </AreaChart>
            </ResponsiveContainer>
          )}
        </div>

        {/* 보안 점수 분포 막대 차트 */}
        <div className="card">
          <h3 className="font-semibold text-gray-900 mb-4 flex items-center gap-2">
            <Shield size={18} className="text-purple-600" />
            보안 점수 분포
          </h3>
          {scoreLoading ? <ChartSkeleton /> : (
            <ResponsiveContainer width="100%" height={220}>
              <BarChart data={scoreDist} layout="vertical">
                <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                <XAxis type="number" tick={{ fontSize: 11 }} allowDecimals={false} />
                <YAxis type="category" dataKey="range" tick={{ fontSize: 11 }} width={52} />
                <Tooltip
                  formatter={(value: any) => [`${value}대`, 'PC 수']}
                />
                <Bar dataKey="count" name="PC 수" radius={[0, 4, 4, 0]}>
                  {scoreDist.map((row, idx) => (
                    <Cell
                      key={`cell-${idx}`}
                      fill={RISK_COLOR[row.risk_level] ?? '#94a3b8'}
                    />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          )}
          {/* 범례 */}
          <div className="flex flex-wrap gap-2 mt-3 justify-center">
            {[
              { level: 'critical', label: '심각(0-20)' },
              { level: 'high',     label: '위험(21-40)' },
              { level: 'medium',   label: '주의(41-60)' },
              { level: 'low',      label: '양호(61-80)' },
              { level: 'safe',     label: '안전(81+)' },
            ].map(({ level, label }) => (
              <span key={level} className="flex items-center gap-1 text-xs text-gray-500">
                <span
                  className="inline-block w-2.5 h-2.5 rounded-sm"
                  style={{ backgroundColor: RISK_COLOR[level] }}
                />
                {label}
              </span>
            ))}
          </div>
        </div>
      </div>

      {/* ── 하단 3열 */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">

        {/* 만료 예정 인증서 */}
        <div className="card">
          <h3 className="font-semibold text-gray-900 mb-4 flex items-center gap-2">
            <FileCheck size={18} className="text-yellow-600" />
            만료 예정 인증서
            {expCerts.length > 0 && (
              <span className="badge badge-yellow ml-auto">{expCerts.length}</span>
            )}
          </h3>
          <div className="space-y-2">
            {expCerts.length === 0 ? (
              <EmptyRow message="만료 예정 인증서 없음" />
            ) : (
              expCerts.map((c) => (
                <div key={c.id} className="flex items-center justify-between p-2 rounded-lg hover:bg-gray-50">
                  <div className="min-w-0 flex-1 mr-2">
                    <p className="text-sm font-medium text-gray-800 truncate">{c.name}</p>
                    <p className="text-xs text-gray-400 truncate">
                      {c.domain ?? c.cert_type}
                      {c.vendor_name ? ` · ${c.vendor_name}` : ''}
                    </p>
                  </div>
                  <span className={`badge flex-shrink-0 ${
                    c.status === 'critical' ? 'badge-red' : 'badge-yellow'
                  }`}>
                    {c.days_left}일
                  </span>
                </div>
              ))
            )}
          </div>
        </div>

        {/* 보안 이벤트 */}
        <div className="card">
          <h3 className="font-semibold text-gray-900 mb-4 flex items-center gap-2">
            <AlertTriangle size={18} className="text-red-600" />
            보안 이벤트
            {sec.unresolved_events > 0 && (
              <span className="badge badge-red ml-auto">{sec.unresolved_events}</span>
            )}
          </h3>
          <div className="space-y-2">
            {secEvts.length === 0 ? (
              <EmptyRow message="미해결 보안 이벤트 없음" />
            ) : (
              secEvts.map((ev) => (
                <div key={ev.id} className="p-2 rounded-lg hover:bg-gray-50">
                  <div className="flex items-center justify-between mb-1">
                    <p className="text-sm font-medium text-gray-800 truncate max-w-[160px]">
                      {ev.title}
                    </p>
                    <SeverityBadge severity={ev.severity} />
                  </div>
                  <p className="text-xs text-gray-400">
                    {ev.pc_name}
                    {ev.asset_tag ? ` (${ev.asset_tag})` : ''}
                  </p>
                </div>
              ))
            )}
          </div>
        </div>

        {/* AI 인사이트 */}
        <div className="card">
          <h3 className="font-semibold text-gray-900 mb-4 flex items-center gap-2">
            <Bot size={18} className="text-purple-600" />
            AI 인사이트
            <span className="badge badge-purple ml-auto">자동분석</span>
          </h3>
          {(insights?.insights?.length ?? 0) > 0 ? (
            <div className="space-y-3">
              {insights!.insights.map((item, i) => (
                <div key={i} className="p-3 bg-purple-50 rounded-lg border border-purple-100">
                  <p className="text-xs font-medium text-purple-700 mb-1">{item.category}</p>
                  <p className="text-xs text-gray-600">{item.message}</p>
                </div>
              ))}
            </div>
          ) : (
            <EmptyRow message="모든 시스템이 정상입니다" />
          )}
          {insights?.summary && (
            <p className="text-xs text-gray-400 mt-3 pt-3 border-t border-gray-100">
              {insights.summary}
            </p>
          )}
          {insights?.generated_at && (
            <p className="text-xs text-gray-300 mt-1">
              분석시각:{' '}
              {(() => {
                try { return format(parseISO(insights.generated_at), 'HH:mm', { locale: ko }); }
                catch { return insights.generated_at; }
              })()}
            </p>
          )}
        </div>
      </div>

      {/* ── 최근 활동 로그 */}
      <div className="card">
        <h3 className="font-semibold text-gray-900 mb-4 flex items-center gap-2">
          <Clock size={18} className="text-gray-600" />
          최근 활동 로그
        </h3>
        {actLoading ? (
          <div className="space-y-2">
            {Array.from({ length: 5 }).map((_, i) => (
              <div key={i} className="h-8 bg-gray-100 animate-pulse rounded" />
            ))}
          </div>
        ) : acts.length === 0 ? (
          <EmptyRow message="활동 로그가 없습니다" />
        ) : (
          <div className="table-container">
            <table className="table">
              <thead>
                <tr>
                  <th>작업</th>
                  <th>리소스</th>
                  <th>설명</th>
                  <th>사용자</th>
                  <th>IP</th>
                  <th>시간</th>
                </tr>
              </thead>
              <tbody>
                {acts.slice(0, 10).map((log) => (
                  <tr key={log.id}>
                    <td>
                      <ActionBadge action={log.action} label={log.action_label} />
                    </td>
                    <td className="text-gray-500">
                      {log.resource_label ?? log.resource_type ?? '-'}
                    </td>
                    <td className="text-gray-700 max-w-xs truncate">{log.description}</td>
                    <td className="font-medium">{log.user_name}</td>
                    <td className="text-gray-400 text-xs font-mono">{log.ip_address ?? '-'}</td>
                    <td className="text-gray-400 text-xs whitespace-nowrap">
                      {log.created_at
                        ? (() => {
                            try { return format(parseISO(log.created_at), 'MM/dd HH:mm', { locale: ko }); }
                            catch { return log.created_at; }
                          })()
                        : '-'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
