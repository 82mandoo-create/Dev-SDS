import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { dashboardApi } from '../api/client';
import {
  Users, FileCheck, Monitor, Shield, AlertTriangle,
  TrendingUp, Activity, Bot, RefreshCw, Clock,
  CheckCircle, XCircle, AlertCircle
} from 'lucide-react';
import {
  AreaChart, Area, BarChart, Bar, PieChart, Pie, Cell,
  XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend
} from 'recharts';
import { format } from 'date-fns';
import { ko } from 'date-fns/locale';

const COLORS = ['#3b82f6', '#8b5cf6', '#10b981', '#f59e0b', '#ef4444'];

function StatCard({ title, value, sub, icon: Icon, color, trend }: any) {
  return (
    <div className="card hover:shadow-md transition-shadow">
      <div className="flex items-start justify-between">
        <div>
          <p className="text-sm text-gray-500 font-medium">{title}</p>
          <p className="text-3xl font-bold text-gray-900 mt-1">{value}</p>
          {sub && <p className="text-xs text-gray-400 mt-1">{sub}</p>}
        </div>
        <div className={`w-12 h-12 rounded-xl ${color} flex items-center justify-center`}>
          <Icon size={22} className="text-white" />
        </div>
      </div>
    </div>
  );
}

function SeverityBadge({ severity }: { severity: string }) {
  const map: Record<string, string> = {
    critical: 'badge-red',
    high: 'badge-yellow',
    medium: 'badge-blue',
    low: 'badge-gray'
  };
  const label: Record<string, string> = {
    critical: '심각', high: '높음', medium: '보통', low: '낮음'
  };
  return <span className={`badge ${map[severity] || 'badge-gray'}`}>{label[severity] || severity}</span>;
}

export default function DashboardPage() {
  const { data: summary, isLoading } = useQuery({
    queryKey: ['dashboard-summary'],
    queryFn: () => dashboardApi.getSummary(),
    refetchInterval: 30000,
  });

  const { data: activities } = useQuery({
    queryKey: ['recent-activities'],
    queryFn: () => dashboardApi.getRecentActivities(),
    refetchInterval: 60000,
  });

  const { data: securityEvents } = useQuery({
    queryKey: ['security-events'],
    queryFn: () => dashboardApi.getSecurityEvents(),
    refetchInterval: 60000,
  });

  const { data: expiringCerts } = useQuery({
    queryKey: ['expiring-certs'],
    queryFn: () => dashboardApi.getExpiringCertificates(30),
  });

  const { data: activityChart } = useQuery({
    queryKey: ['activity-chart'],
    queryFn: () => dashboardApi.getPCActivityChart(7),
  });

  const { data: scoreDistribution } = useQuery({
    queryKey: ['score-distribution'],
    queryFn: () => dashboardApi.getSecurityScoreDistribution(),
  });

  const { data: aiInsights } = useQuery({
    queryKey: ['ai-insights'],
    queryFn: () => dashboardApi.getAIInsights(),
    refetchInterval: 120000,
  });

  const s = summary?.data;
  const insights = aiInsights?.data;

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <RefreshCw className="animate-spin text-blue-600" size={32} />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* AI Alerts */}
      {insights?.alerts?.length > 0 && (
        <div className="space-y-2">
          {insights.alerts.map((alert: any, i: number) => (
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

      {/* Stats Grid */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          title="활성 직원"
          value={s?.employees?.total || 0}
          icon={Users}
          color="bg-gradient-to-br from-blue-500 to-blue-600"
        />
        <StatCard
          title="인증서 현황"
          value={s?.certificates?.total || 0}
          sub={`만료예정 ${s?.certificates?.expiring_soon || 0}개`}
          icon={FileCheck}
          color={s?.certificates?.critical > 0 ? 'bg-gradient-to-br from-red-500 to-red-600' : 'bg-gradient-to-br from-green-500 to-green-600'}
        />
        <StatCard
          title="PC 자산"
          value={s?.pcs?.total || 0}
          sub={`온라인 ${s?.pcs?.online || 0}대 (${s?.pcs?.online_rate || 0}%)`}
          icon={Monitor}
          color="bg-gradient-to-br from-purple-500 to-purple-600"
        />
        <StatCard
          title="보안 이벤트"
          value={s?.security?.unresolved_events || 0}
          sub={`평균 점수 ${s?.security?.avg_security_score || 0}점`}
          icon={Shield}
          color={s?.security?.unresolved_events > 0 ? 'bg-gradient-to-br from-orange-500 to-red-500' : 'bg-gradient-to-br from-teal-500 to-teal-600'}
        />
      </div>

      {/* Charts Row */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Activity Chart */}
        <div className="lg:col-span-2 card">
          <h3 className="font-semibold text-gray-900 mb-4 flex items-center gap-2">
            <Activity size={18} className="text-blue-600" />
            PC 활동 현황 (최근 7일)
          </h3>
          <ResponsiveContainer width="100%" height={220}>
            <AreaChart data={activityChart?.data || []}>
              <defs>
                <linearGradient id="colorLogin" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.3} />
                  <stop offset="95%" stopColor="#3b82f6" stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
              <XAxis dataKey="date" tick={{ fontSize: 11 }} tickFormatter={(v) => v.slice(5)} />
              <YAxis tick={{ fontSize: 11 }} />
              <Tooltip />
              <Area type="monotone" dataKey="login" stroke="#3b82f6" fill="url(#colorLogin)" name="로그인" />
              <Area type="monotone" dataKey="sleep" stroke="#8b5cf6" fill="transparent" name="절전" />
            </AreaChart>
          </ResponsiveContainer>
        </div>

        {/* Security Score Distribution */}
        <div className="card">
          <h3 className="font-semibold text-gray-900 mb-4 flex items-center gap-2">
            <Shield size={18} className="text-purple-600" />
            보안 점수 분포
          </h3>
          <ResponsiveContainer width="100%" height={220}>
            <BarChart data={scoreDistribution?.data || []} layout="vertical">
              <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
              <XAxis type="number" tick={{ fontSize: 11 }} />
              <YAxis type="category" dataKey="range" tick={{ fontSize: 11 }} width={50} />
              <Tooltip />
              <Bar dataKey="count" name="PC 수" radius={[0, 4, 4, 0]}>
                {(scoreDistribution?.data || []).map((_: any, index: number) => (
                  <Cell
                    key={`cell-${index}`}
                    fill={index < 2 ? '#ef4444' : index < 3 ? '#f59e0b' : '#10b981'}
                  />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Bottom Row */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Expiring Certificates */}
        <div className="card">
          <h3 className="font-semibold text-gray-900 mb-4 flex items-center gap-2">
            <FileCheck size={18} className="text-yellow-600" />
            만료 예정 인증서
            <span className="badge-yellow ml-auto">{expiringCerts?.data?.length || 0}</span>
          </h3>
          <div className="space-y-2">
            {(expiringCerts?.data || []).length === 0 ? (
              <p className="text-sm text-gray-400 text-center py-4">만료 예정 인증서 없음</p>
            ) : (
              (expiringCerts?.data || []).map((cert: any) => (
                <div key={cert.id} className="flex items-center justify-between p-2 rounded-lg hover:bg-gray-50">
                  <div>
                    <p className="text-sm font-medium text-gray-800 truncate max-w-[160px]">{cert.name}</p>
                    <p className="text-xs text-gray-400">{cert.domain || '-'}</p>
                  </div>
                  <div className="text-right">
                    <span className={`badge ${cert.status === 'critical' ? 'badge-red' : 'badge-yellow'}`}>
                      {cert.days_left}일
                    </span>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>

        {/* Security Events */}
        <div className="card">
          <h3 className="font-semibold text-gray-900 mb-4 flex items-center gap-2">
            <AlertTriangle size={18} className="text-red-600" />
            보안 이벤트
            {s?.security?.unresolved_events > 0 && (
              <span className="badge-red ml-auto">{s.security.unresolved_events}</span>
            )}
          </h3>
          <div className="space-y-2">
            {(securityEvents?.data || []).length === 0 ? (
              <div className="flex items-center gap-2 text-green-600 text-sm py-4 justify-center">
                <CheckCircle size={16} />미해결 보안 이벤트 없음
              </div>
            ) : (
              (securityEvents?.data || []).map((event: any) => (
                <div key={event.id} className="p-2 rounded-lg hover:bg-gray-50">
                  <div className="flex items-center justify-between mb-1">
                    <p className="text-sm font-medium text-gray-800 truncate max-w-[160px]">{event.title}</p>
                    <SeverityBadge severity={event.severity} />
                  </div>
                  <p className="text-xs text-gray-400">{event.pc_name}</p>
                </div>
              ))
            )}
          </div>
        </div>

        {/* AI Insights */}
        <div className="card">
          <h3 className="font-semibold text-gray-900 mb-4 flex items-center gap-2">
            <Bot size={18} className="text-purple-600" />
            AI 인사이트
            <span className="badge-purple ml-auto">자동분석</span>
          </h3>
          {insights?.insights?.length > 0 ? (
            <div className="space-y-3">
              {insights.insights.map((insight: any, i: number) => (
                <div key={i} className="p-3 bg-purple-50 rounded-lg border border-purple-100">
                  <p className="text-xs font-medium text-purple-700 mb-1">{insight.category}</p>
                  <p className="text-xs text-gray-600">{insight.message}</p>
                </div>
              ))}
            </div>
          ) : (
            <div className="flex items-center gap-2 text-green-600 text-sm py-4 justify-center">
              <CheckCircle size={16} />모든 시스템이 정상입니다
            </div>
          )}
          {insights?.summary && (
            <p className="text-xs text-gray-400 mt-3 pt-3 border-t border-gray-100">{insights.summary}</p>
          )}
        </div>
      </div>

      {/* Recent Activities */}
      <div className="card">
        <h3 className="font-semibold text-gray-900 mb-4 flex items-center gap-2">
          <Clock size={18} className="text-gray-600" />
          최근 활동 로그
        </h3>
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
              {(activities?.data || []).slice(0, 10).map((log: any) => (
                <tr key={log.id}>
                  <td><span className="badge-blue">{log.action}</span></td>
                  <td className="text-gray-500">{log.resource_type || '-'}</td>
                  <td className="text-gray-700 max-w-xs truncate">{log.description}</td>
                  <td className="font-medium">{log.user_name}</td>
                  <td className="text-gray-400 text-xs font-mono">{log.ip_address || '-'}</td>
                  <td className="text-gray-400 text-xs">
                    {log.created_at ? format(new Date(log.created_at), 'MM/dd HH:mm', { locale: ko }) : '-'}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
