import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { pcApi } from '../api/client';
import { Shield, AlertTriangle, CheckCircle, RefreshCw, Filter } from 'lucide-react';
import toast from 'react-hot-toast';
import { format } from 'date-fns';

const severityLabel: Record<string, string> = { critical: '심각', high: '높음', medium: '보통', low: '낮음' };
const severityClass: Record<string, string> = { critical: 'badge-red', high: 'badge-yellow', medium: 'badge-blue', low: 'badge-gray' };

export default function SecurityPage() {
  const [filter, setFilter] = useState<'all' | 'unresolved'>('unresolved');
  const [pcFilter, setPcFilter] = useState('');
  const qc = useQueryClient();

  const { data: pcs } = useQuery({
    queryKey: ['pcs-simple'],
    queryFn: () => pcApi.getList({ limit: 100 }),
  });

  const { data: stats } = useQuery({
    queryKey: ['pc-stats'],
    queryFn: () => pcApi.getStats(),
    refetchInterval: 30000,
  });

  const { data: eventsData, isLoading } = useQuery({
    queryKey: ['all-security-events', pcFilter],
    queryFn: async () => {
      const pcList = pcs?.data?.items || [];
      const target = pcFilter ? pcList.filter((p: any) => p.id === Number(pcFilter)) : pcList;
      const all: any[] = [];
      for (const pc of target.slice(0, 20)) {
        const res = await pcApi.getSecurityEvents(pc.id, { resolved: filter === 'unresolved' ? false : undefined });
        (res.data?.items || []).forEach((e: any) => {
          all.push({ ...e, pc_name: pc.hostname || pc.computer_name || pc.asset_tag });
        });
      }
      return all.sort((a, b) => new Date(b.occurred_at).getTime() - new Date(a.occurred_at).getTime());
    },
    enabled: !!pcs,
  });

  const resolveMutation = useMutation({
    mutationFn: ({ pcId, eventId }: any) => pcApi.resolveEvent(pcId, eventId),
    onSuccess: () => {
      toast.success('해결 처리되었습니다.');
      qc.invalidateQueries({ queryKey: ['all-security-events'] });
      qc.invalidateQueries({ queryKey: ['pc-stats'] });
    },
  });

  const s = stats?.data;
  const events = eventsData || [];

  return (
    <div className="space-y-6">
      {/* Stats */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
        {[
          { label: '미해결 이벤트', value: s?.unresolved_security_events || 0, color: s?.unresolved_security_events > 0 ? 'text-red-600' : 'text-green-600', bg: s?.unresolved_security_events > 0 ? 'bg-red-50' : 'bg-green-50' },
          { label: '안티바이러스 미설치', value: s?.no_antivirus || 0, color: 'text-orange-600', bg: 'bg-orange-50' },
          { label: '방화벽 미설정', value: s?.no_firewall || 0, color: 'text-yellow-600', bg: 'bg-yellow-50' },
          { label: '평균 보안점수', value: `${s?.avg_security_score || 0}점`, color: (s?.avg_security_score || 0) >= 70 ? 'text-green-600' : 'text-red-600', bg: 'bg-gray-50' },
        ].map((stat) => (
          <div key={stat.label} className={`card flex items-center gap-3`}>
            <div className={`${stat.bg} ${stat.color} rounded-lg p-3`}>
              <Shield size={20} />
            </div>
            <div>
              <p className="text-sm text-gray-500">{stat.label}</p>
              <p className={`text-2xl font-bold ${stat.color}`}>{stat.value}</p>
            </div>
          </div>
        ))}
      </div>

      {/* Events */}
      <div className="card">
        <div className="flex flex-wrap gap-3 items-center justify-between mb-4">
          <h3 className="font-semibold text-gray-900 flex items-center gap-2">
            <AlertTriangle size={18} className="text-red-500" />
            보안 이벤트 목록
          </h3>
          <div className="flex gap-2">
            <div className="flex rounded-lg border border-gray-200 overflow-hidden">
              <button onClick={() => setFilter('unresolved')} className={`px-3 py-1.5 text-sm ${filter === 'unresolved' ? 'bg-red-600 text-white' : 'bg-white text-gray-600 hover:bg-gray-50'}`}>미해결</button>
              <button onClick={() => setFilter('all')} className={`px-3 py-1.5 text-sm ${filter === 'all' ? 'bg-blue-600 text-white' : 'bg-white text-gray-600 hover:bg-gray-50'}`}>전체</button>
            </div>
            <select className="input w-44" value={pcFilter} onChange={e => setPcFilter(e.target.value)}>
              <option value="">전체 PC</option>
              {(pcs?.data?.items || []).map((p: any) => (
                <option key={p.id} value={p.id}>{p.hostname || p.computer_name}</option>
              ))}
            </select>
          </div>
        </div>

        {isLoading ? (
          <div className="flex items-center justify-center h-40"><RefreshCw className="animate-spin text-blue-600" size={24} /></div>
        ) : events.length === 0 ? (
          <div className="text-center py-12 text-green-600 flex items-center justify-center gap-2">
            <CheckCircle size={20} />
            <p className="font-medium">보안 이벤트가 없습니다.</p>
          </div>
        ) : (
          <div className="space-y-3">
            {events.map((event: any) => (
              <div key={`${event.pc_asset_id}-${event.id}`} className={`p-4 rounded-xl border-l-4 ${
                event.severity === 'critical' ? 'border-l-red-500 bg-red-50' :
                event.severity === 'high' ? 'border-l-orange-400 bg-orange-50' :
                event.severity === 'medium' ? 'border-l-yellow-400 bg-yellow-50' : 'border-l-blue-300 bg-blue-50'
              }`}>
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center gap-2 flex-wrap">
                      <span className={`badge ${severityClass[event.severity] || 'badge-gray'}`}>{severityLabel[event.severity]}</span>
                      <span className="badge-gray">{event.pc_name}</span>
                      <span className="text-xs text-gray-400">{format(new Date(event.occurred_at), 'yyyy.MM.dd HH:mm')}</span>
                    </div>
                    <p className="font-medium text-gray-900 mt-1">{event.title}</p>
                    {event.description && <p className="text-sm text-gray-600 mt-0.5">{event.description}</p>}
                  </div>
                  <button
                    onClick={() => resolveMutation.mutate({ pcId: event.pc_asset_id, eventId: event.id })}
                    className="btn-secondary text-xs px-3 py-1.5 ml-3 flex-shrink-0"
                    disabled={resolveMutation.isPending}
                  >
                    해결처리
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
