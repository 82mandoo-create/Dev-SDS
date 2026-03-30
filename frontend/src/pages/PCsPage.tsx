import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { pcApi } from '../api/client';
import {
  Monitor, Shield, AlertTriangle, CheckCircle, Wifi, WifiOff,
  Search, RefreshCw, Activity, Bot, ChevronRight, Lock,
  Eye, Package, X
} from 'lucide-react';
import toast from 'react-hot-toast';
import { format } from 'date-fns';

function SecurityScore({ score }: { score: number }) {
  const color = score >= 80 ? 'text-green-600 bg-green-50' : score >= 60 ? 'text-yellow-600 bg-yellow-50' : score >= 40 ? 'text-orange-600 bg-orange-50' : 'text-red-600 bg-red-50';
  return (
    <div className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-bold ${color}`}>
      <Shield size={12} />
      {score}점
    </div>
  );
}

function PCDetailModal({ pc, onClose }: { pc: any; onClose: () => void }) {
  const [tab, setTab] = useState<'info' | 'activities' | 'apps' | 'security' | 'ai'>('info');
  const qc = useQueryClient();

  const { data: activities } = useQuery({
    queryKey: ['pc-activities', pc.id],
    queryFn: () => pcApi.getActivities(pc.id, { limit: 20 }),
    enabled: tab === 'activities',
  });

  const { data: apps } = useQuery({
    queryKey: ['pc-apps', pc.id],
    queryFn: () => pcApi.getApplications(pc.id, { limit: 50 }),
    enabled: tab === 'apps',
  });

  const { data: secEvents } = useQuery({
    queryKey: ['pc-security', pc.id],
    queryFn: () => pcApi.getSecurityEvents(pc.id, { resolved: false }),
    enabled: tab === 'security',
  });

  const { data: aiAnalysis } = useQuery({
    queryKey: ['pc-ai', pc.id],
    queryFn: () => pcApi.getAIAnalysis(pc.id),
    enabled: tab === 'ai',
  });

  const resolveMutation = useMutation({
    mutationFn: ({ eventId }: any) => pcApi.resolveEvent(pc.id, eventId),
    onSuccess: () => { toast.success('해결 처리되었습니다.'); qc.invalidateQueries({ queryKey: ['pc-security', pc.id] }); },
  });

  const tabs = [
    { id: 'info', label: '상세정보' },
    { id: 'activities', label: '활동 내역' },
    { id: 'apps', label: '설치 앱' },
    { id: 'security', label: '보안 이벤트' },
    { id: 'ai', label: 'AI 분석' },
  ];

  return (
    <div className="fixed inset-0 bg-black/50 flex items-end sm:items-center justify-center z-50 p-0 sm:p-4">
      <div className="bg-white rounded-t-2xl sm:rounded-2xl shadow-2xl w-full sm:max-w-3xl max-h-[90vh] flex flex-col">
        <div className="p-4 border-b border-gray-100 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className={`w-3 h-3 rounded-full ${pc.is_online ? 'bg-green-500' : 'bg-gray-300'}`}></div>
            <div>
              <h2 className="font-semibold text-gray-900">{pc.computer_name || pc.hostname}</h2>
              <p className="text-xs text-gray-500">{pc.asset_tag} · {pc.ip_address || 'IP 없음'}</p>
            </div>
          </div>
          <button onClick={onClose} className="p-2 hover:bg-gray-100 rounded-lg"><X size={18} /></button>
        </div>
        <div className="flex gap-0 border-b border-gray-100 overflow-x-auto px-4">
          {tabs.map((t) => (
            <button
              key={t.id}
              onClick={() => setTab(t.id as any)}
              className={`px-4 py-3 text-sm font-medium whitespace-nowrap border-b-2 transition-colors ${tab === t.id ? 'border-blue-600 text-blue-600' : 'border-transparent text-gray-500 hover:text-gray-700'}`}
            >
              {t.label}
            </button>
          ))}
        </div>
        <div className="flex-1 overflow-y-auto p-4">
          {tab === 'info' && (
            <div className="grid grid-cols-2 gap-4">
              {[
                { label: 'OS', value: `${pc.os_name} ${pc.os_version || ''}` },
                { label: 'CPU', value: pc.cpu_info || '-' },
                { label: 'RAM', value: pc.ram_gb ? `${pc.ram_gb} GB` : '-' },
                { label: '제조사', value: pc.manufacturer || '-' },
                { label: '모델', value: pc.model || '-' },
                { label: 'MAC', value: pc.mac_address || '-' },
                { label: '에이전트', value: pc.agent_version || '-' },
                { label: '마지막 접속', value: pc.last_heartbeat ? format(new Date(pc.last_heartbeat), 'yyyy.MM.dd HH:mm') : '-' },
              ].map((item) => (
                <div key={item.label} className="bg-gray-50 rounded-lg p-3">
                  <p className="text-xs text-gray-500 mb-1">{item.label}</p>
                  <p className="text-sm font-medium text-gray-900 truncate">{item.value}</p>
                </div>
              ))}
              <div className="col-span-2 bg-gray-50 rounded-lg p-3">
                <p className="text-xs text-gray-500 mb-2">보안 현황</p>
                <div className="grid grid-cols-4 gap-2">
                  {[
                    { label: '안티바이러스', active: pc.antivirus_installed },
                    { label: '방화벽', active: pc.firewall_enabled },
                    { label: '디스크 암호화', active: pc.disk_encrypted },
                    { label: 'Windows Defender', active: pc.windows_defender },
                  ].map((item) => (
                    <div key={item.label} className={`flex items-center gap-1.5 p-2 rounded ${item.active ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'}`}>
                      {item.active ? <CheckCircle size={12} /> : <AlertTriangle size={12} />}
                      <span className="text-xs">{item.label}</span>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}

          {tab === 'activities' && (
            <div className="space-y-2">
              {(activities?.data?.items || []).map((act: any) => (
                <div key={act.id} className="flex items-center gap-3 p-3 bg-gray-50 rounded-lg">
                  <div className={`w-8 h-8 rounded-full flex items-center justify-center text-xs font-bold ${
                    act.activity_type === 'login' ? 'bg-blue-100 text-blue-700' :
                    act.activity_type === 'logout' ? 'bg-gray-200 text-gray-600' :
                    act.activity_type === 'sleep' ? 'bg-yellow-100 text-yellow-700' :
                    'bg-purple-100 text-purple-700'
                  }`}>
                    {act.activity_type === 'login' ? '입' : act.activity_type === 'logout' ? '출' : act.activity_type === 'sleep' ? '절' : '기'}
                  </div>
                  <div className="flex-1">
                    <p className="text-sm font-medium text-gray-900">
                      {act.activity_type === 'login' ? '로그인' : act.activity_type === 'logout' ? '로그아웃' : act.activity_type === 'sleep' ? '절전 시작' : act.activity_type === 'wake' ? '절전 해제' : act.activity_type}
                    </p>
                    <p className="text-xs text-gray-500">{act.user_account || '-'}</p>
                  </div>
                  <div className="text-right">
                    <p className="text-xs text-gray-500">{act.started_at ? format(new Date(act.started_at), 'MM/dd HH:mm') : '-'}</p>
                    {act.duration_seconds && <p className="text-xs text-gray-400">{Math.round(act.duration_seconds / 60)}분</p>}
                  </div>
                </div>
              ))}
            </div>
          )}

          {tab === 'apps' && (
            <div className="space-y-1">
              {(apps?.data?.items || []).map((app: any) => (
                <div key={app.id} className="flex items-center gap-3 p-3 hover:bg-gray-50 rounded-lg">
                  <Package size={16} className="text-gray-400 flex-shrink-0" />
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium text-gray-900 truncate">{app.app_name}</p>
                    <p className="text-xs text-gray-400">{app.publisher || '-'} · {app.app_version || '-'}</p>
                  </div>
                  {app.is_running && <span className="badge-green">실행중</span>}
                </div>
              ))}
            </div>
          )}

          {tab === 'security' && (
            <div className="space-y-3">
              {(secEvents?.data?.items || []).length === 0 ? (
                <div className="text-center py-8 text-green-600 flex items-center justify-center gap-2">
                  <CheckCircle size={18} />미해결 보안 이벤트 없음
                </div>
              ) : (
                (secEvents?.data?.items || []).map((event: any) => (
                  <div key={event.id} className={`p-4 rounded-xl border ${
                    event.severity === 'critical' ? 'border-red-200 bg-red-50' :
                    event.severity === 'high' ? 'border-orange-200 bg-orange-50' : 'border-yellow-200 bg-yellow-50'
                  }`}>
                    <div className="flex items-start justify-between">
                      <div>
                        <p className="font-medium text-gray-900">{event.title}</p>
                        <p className="text-sm text-gray-500 mt-1">{event.description}</p>
                      </div>
                      <button
                        onClick={() => resolveMutation.mutate({ eventId: event.id })}
                        className="btn-secondary text-xs px-2 py-1 ml-2 flex-shrink-0"
                      >
                        해결
                      </button>
                    </div>
                  </div>
                ))
              )}
            </div>
          )}

          {tab === 'ai' && (
            <div className="space-y-4">
              {aiAnalysis?.data ? (
                <>
                  <div className="flex items-center justify-between p-4 bg-gradient-to-r from-blue-50 to-purple-50 rounded-xl">
                    <div>
                      <p className="text-sm font-medium text-gray-700">AI 보안 점수</p>
                      <p className="text-3xl font-bold gradient-text">{aiAnalysis.data.security_analysis?.security_score}점</p>
                    </div>
                    <div className={`px-3 py-1.5 rounded-lg text-sm font-medium ${
                      aiAnalysis.data.security_analysis?.risk_level === 'critical' ? 'bg-red-100 text-red-700' :
                      aiAnalysis.data.security_analysis?.risk_level === 'high' ? 'bg-orange-100 text-orange-700' :
                      aiAnalysis.data.security_analysis?.risk_level === 'medium' ? 'bg-yellow-100 text-yellow-700' : 'bg-green-100 text-green-700'
                    }`}>
                      위험도: {aiAnalysis.data.security_analysis?.risk_level}
                    </div>
                  </div>
                  {aiAnalysis.data.security_analysis?.issues?.length > 0 && (
                    <div>
                      <h4 className="text-sm font-medium text-gray-700 mb-2">발견된 문제</h4>
                      <div className="space-y-1">
                        {aiAnalysis.data.security_analysis.issues.map((issue: string, i: number) => (
                          <div key={i} className="flex items-center gap-2 text-sm text-red-600 bg-red-50 px-3 py-2 rounded-lg">
                            <AlertTriangle size={14} />{issue}
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                  {aiAnalysis.data.security_analysis?.recommendations?.length > 0 && (
                    <div>
                      <h4 className="text-sm font-medium text-gray-700 mb-2">권장 조치</h4>
                      <div className="space-y-1">
                        {aiAnalysis.data.security_analysis.recommendations.map((rec: string, i: number) => (
                          <div key={i} className="flex items-start gap-2 text-sm text-blue-600 bg-blue-50 px-3 py-2 rounded-lg">
                            <CheckCircle size={14} className="mt-0.5 flex-shrink-0" />{rec}
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                  {aiAnalysis.data.anomalies?.length > 0 && (
                    <div>
                      <h4 className="text-sm font-medium text-gray-700 mb-2">이상 행동 감지</h4>
                      <div className="space-y-1">
                        {aiAnalysis.data.anomalies.map((anomaly: any, i: number) => (
                          <div key={i} className="text-sm text-yellow-700 bg-yellow-50 px-3 py-2 rounded-lg">
                            {anomaly.message}
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </>
              ) : (
                <div className="flex items-center justify-center h-32"><RefreshCw className="animate-spin" /></div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default function PCsPage() {
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState('');
  const [onlineFilter, setOnlineFilter] = useState<string>('');
  const [selectedPC, setSelectedPC] = useState<any>(null);

  const { data, isLoading, refetch } = useQuery({
    queryKey: ['pcs', page, search, onlineFilter],
    queryFn: () => pcApi.getList({
      page, limit: 20,
      search: search || undefined,
      is_online: onlineFilter === '' ? undefined : onlineFilter === 'true'
    }),
    refetchInterval: 30000,
  });

  const { data: stats } = useQuery({
    queryKey: ['pc-stats'],
    queryFn: () => pcApi.getStats(),
    refetchInterval: 30000,
  });

  const s = stats?.data;
  const pcs = data?.data?.items || [];
  const total = data?.data?.total || 0;

  return (
    <div className="space-y-6">
      {/* Stats */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
        {[
          { label: '전체 PC', value: s?.total || 0, icon: Monitor, color: 'bg-blue-500', text: `활성 ${s?.active || 0}대` },
          { label: '온라인', value: s?.online || 0, icon: Wifi, color: 'bg-green-500', text: `오프라인 ${s?.offline || 0}대` },
          { label: '보안 이벤트', value: s?.unresolved_security_events || 0, icon: AlertTriangle, color: s?.unresolved_security_events > 0 ? 'bg-red-500' : 'bg-teal-500', text: '미해결' },
          { label: '평균 보안점수', value: `${s?.avg_security_score || 0}점`, icon: Shield, color: (s?.avg_security_score || 0) >= 70 ? 'bg-indigo-500' : 'bg-orange-500', text: `안티바이러스 미설치 ${s?.no_antivirus || 0}대` },
        ].map((stat) => {
          const Icon = stat.icon;
          return (
            <div key={stat.label} className="card flex items-start gap-3">
              <div className={`w-10 h-10 rounded-xl ${stat.color} flex items-center justify-center flex-shrink-0`}>
                <Icon size={18} className="text-white" />
              </div>
              <div>
                <p className="text-sm text-gray-500">{stat.label}</p>
                <p className="text-2xl font-bold text-gray-900">{stat.value}</p>
                <p className="text-xs text-gray-400">{stat.text}</p>
              </div>
            </div>
          );
        })}
      </div>

      <div className="card">
        <div className="flex flex-wrap gap-3 items-center justify-between mb-4">
          <div className="flex flex-wrap gap-3 flex-1">
            <div className="relative">
              <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
              <input className="input pl-9 w-64" placeholder="호스트명, 자산태그, IP 검색..." value={search} onChange={(e) => { setSearch(e.target.value); setPage(1); }} />
            </div>
            <select className="input w-32" value={onlineFilter} onChange={(e) => { setOnlineFilter(e.target.value); setPage(1); }}>
              <option value="">전체</option>
              <option value="true">온라인</option>
              <option value="false">오프라인</option>
            </select>
          </div>
          <button onClick={() => refetch()} className="btn-secondary flex items-center gap-2">
            <RefreshCw size={14} />새로고침
          </button>
        </div>

        {isLoading ? (
          <div className="flex items-center justify-center h-40"><RefreshCw className="animate-spin text-blue-600" size={24} /></div>
        ) : (
          <div className="table-container">
            <table className="table">
              <thead>
                <tr>
                  <th>상태</th><th>자산 태그</th><th>컴퓨터명</th><th>OS</th>
                  <th>IP 주소</th><th>보안점수</th><th>에이전트</th><th>마지막 접속</th><th>상세</th>
                </tr>
              </thead>
              <tbody>
                {pcs.map((pc: any) => (
                  <tr key={pc.id}>
                    <td>
                      <div className="flex items-center gap-1.5">
                        <div className={`w-2 h-2 rounded-full ${pc.is_online ? 'bg-green-500 animate-pulse' : 'bg-gray-300'}`}></div>
                        <span className={`text-xs ${pc.is_online ? 'text-green-600' : 'text-gray-400'}`}>
                          {pc.is_online ? '온라인' : '오프라인'}
                        </span>
                      </div>
                    </td>
                    <td className="font-mono text-xs text-gray-500">{pc.asset_tag}</td>
                    <td className="font-medium text-gray-900">{pc.computer_name || pc.hostname || '-'}</td>
                    <td className="text-sm text-gray-500">{pc.os_name || '-'}</td>
                    <td className="font-mono text-xs text-gray-500">{pc.ip_address || '-'}</td>
                    <td><SecurityScore score={pc.security_score || 0} /></td>
                    <td>{pc.agent_version ? <span className="badge-green">{pc.agent_version}</span> : <span className="badge-gray">미설치</span>}</td>
                    <td className="text-xs text-gray-400">
                      {pc.last_heartbeat ? format(new Date(pc.last_heartbeat), 'MM/dd HH:mm') : '-'}
                    </td>
                    <td>
                      <button onClick={() => setSelectedPC(pc)} className="p-1.5 hover:bg-blue-50 rounded-lg text-blue-600">
                        <ChevronRight size={14} />
                      </button>
                    </td>
                  </tr>
                ))}
                {pcs.length === 0 && (
                  <tr><td colSpan={9} className="text-center text-gray-400 py-8">PC 데이터가 없습니다.</td></tr>
                )}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {selectedPC && <PCDetailModal pc={selectedPC} onClose={() => setSelectedPC(null)} />}
    </div>
  );
}
