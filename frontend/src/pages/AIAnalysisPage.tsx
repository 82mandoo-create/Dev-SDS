import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { dashboardApi, certificateApi, pcApi } from '../api/client';
import { Bot, Brain, Shield, TrendingUp, AlertTriangle, CheckCircle, RefreshCw, Lightbulb, BarChart2 } from 'lucide-react';
import { RadarChart, PolarGrid, PolarAngleAxis, Radar, ResponsiveContainer, AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip } from 'recharts';

export default function AIAnalysisPage() {
  const { data: insights, isLoading: insightsLoading } = useQuery({
    queryKey: ['ai-insights'],
    queryFn: () => dashboardApi.getAIInsights(),
  });

  const { data: predictions } = useQuery({
    queryKey: ['cert-predictions'],
    queryFn: () => certificateApi.getRenewalPredictions(),
  });

  const { data: pcStats } = useQuery({
    queryKey: ['pc-stats'],
    queryFn: () => pcApi.getStats(),
  });

  const { data: scoreDistribution } = useQuery({
    queryKey: ['score-distribution'],
    queryFn: () => dashboardApi.getSecurityScoreDistribution(),
  });

  const s = pcStats?.data;
  const insightData = insights?.data;

  const radarData = [
    { subject: '안티바이러스', A: s ? Math.round(((s.total - (s.no_antivirus || 0)) / Math.max(s.total, 1)) * 100) : 0 },
    { subject: '방화벽', A: s ? Math.round(((s.total - (s.no_firewall || 0)) / Math.max(s.total, 1)) * 100) : 0 },
    { subject: '온라인율', A: s?.total ? Math.round((s.online / s.total) * 100) : 0 },
    { subject: '보안점수', A: s?.avg_security_score || 0 },
    { subject: '이벤트 해결', A: s?.unresolved_security_events === 0 ? 100 : s?.total ? Math.max(0, 100 - (s.unresolved_security_events * 10)) : 0 },
  ];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="card bg-gradient-to-r from-blue-600 to-purple-700 text-white">
        <div className="flex items-center gap-4">
          <div className="w-14 h-14 rounded-2xl bg-white/20 flex items-center justify-center">
            <Brain size={28} className="text-white" />
          </div>
          <div>
            <h2 className="text-xl font-bold">AI 보안 분석 센터</h2>
            <p className="text-blue-100 text-sm mt-1">머신러닝 기반 위협 분석 및 예측 서비스</p>
          </div>
        </div>
      </div>

      {/* Alerts */}
      {insightData?.alerts?.length > 0 && (
        <div className="space-y-2">
          <h3 className="font-semibold text-gray-700 flex items-center gap-2"><AlertTriangle size={16} className="text-red-500" />실시간 경보</h3>
          {insightData.alerts.map((alert: any, i: number) => (
            <div key={i} className={`flex items-center gap-3 p-4 rounded-xl border ${
              alert.type === 'critical' ? 'bg-red-50 border-red-200 text-red-700' : 'bg-yellow-50 border-yellow-200 text-yellow-700'
            }`}>
              <AlertTriangle size={18} className="flex-shrink-0" />
              <p className="font-medium">{alert.message}</p>
            </div>
          ))}
        </div>
      )}

      {/* Charts Row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Radar Chart */}
        <div className="card">
          <h3 className="font-semibold text-gray-900 mb-4 flex items-center gap-2">
            <Shield size={18} className="text-blue-600" />전체 보안 현황 레이더
          </h3>
          <ResponsiveContainer width="100%" height={260}>
            <RadarChart data={radarData}>
              <PolarGrid />
              <PolarAngleAxis dataKey="subject" tick={{ fontSize: 12 }} />
              <Radar name="보안" dataKey="A" stroke="#3b82f6" fill="#3b82f6" fillOpacity={0.3} />
            </RadarChart>
          </ResponsiveContainer>
        </div>

        {/* Security Score Distribution */}
        <div className="card">
          <h3 className="font-semibold text-gray-900 mb-4 flex items-center gap-2">
            <BarChart2 size={18} className="text-purple-600" />보안 점수 분포
          </h3>
          <div className="space-y-3 mt-2">
            {(scoreDistribution?.data || []).map((item: any) => {
              const total = (scoreDistribution?.data || []).reduce((sum: number, d: any) => sum + d.count, 0);
              const pct = total > 0 ? Math.round((item.count / total) * 100) : 0;
              const color = item.range === '81-100' ? 'bg-green-500' : item.range === '61-80' ? 'bg-blue-500' : item.range === '41-60' ? 'bg-yellow-500' : item.range === '21-40' ? 'bg-orange-500' : 'bg-red-500';
              return (
                <div key={item.range}>
                  <div className="flex justify-between text-sm mb-1">
                    <span className="text-gray-600">점수 {item.range}</span>
                    <span className="font-medium">{item.count}대 ({pct}%)</span>
                  </div>
                  <div className="w-full bg-gray-100 rounded-full h-2">
                    <div className={`h-2 rounded-full ${color} transition-all`} style={{ width: `${pct}%` }}></div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </div>

      {/* Insights */}
      <div className="card">
        <h3 className="font-semibold text-gray-900 mb-4 flex items-center gap-2">
          <Lightbulb size={18} className="text-yellow-500" />AI 인사이트 및 권장사항
        </h3>
        {insightsLoading ? (
          <div className="flex items-center justify-center h-32"><RefreshCw className="animate-spin text-blue-600" /></div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {insightData?.insights?.length > 0 ? (
              insightData.insights.map((insight: any, i: number) => (
                <div key={i} className="p-4 rounded-xl bg-gradient-to-br from-purple-50 to-blue-50 border border-purple-100">
                  <div className="flex items-start gap-3">
                    <div className="w-8 h-8 rounded-lg bg-purple-100 flex items-center justify-center flex-shrink-0">
                      <Brain size={16} className="text-purple-600" />
                    </div>
                    <div>
                      <p className="text-sm font-medium text-purple-700">{insight.category}</p>
                      <p className="text-sm text-gray-600 mt-1">{insight.message}</p>
                    </div>
                  </div>
                </div>
              ))
            ) : (
              <div className="col-span-2 flex items-center justify-center gap-2 text-green-600 py-8">
                <CheckCircle size={20} />
                <p className="font-medium">현재 모든 보안 지표가 양호합니다.</p>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Certificate Predictions */}
      <div className="card">
        <h3 className="font-semibold text-gray-900 mb-4 flex items-center gap-2">
          <TrendingUp size={18} className="text-green-600" />AI 인증서 갱신 예측 (우선순위 분석)
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
          {(predictions?.data?.predictions || []).slice(0, 6).map((p: any) => (
            <div key={p.cert_id} className={`p-4 rounded-xl border-2 ${
              p.priority === 'critical' ? 'border-red-300 bg-red-50' :
              p.priority === 'high' ? 'border-orange-300 bg-orange-50' :
              p.priority === 'medium' ? 'border-yellow-300 bg-yellow-50' : 'border-gray-200 bg-gray-50'
            }`}>
              <div className="flex items-start justify-between mb-2">
                <p className="font-medium text-gray-900 text-sm">{p.cert_name}</p>
                <span className={`badge text-xs ${
                  p.priority === 'critical' ? 'badge-red' :
                  p.priority === 'high' ? 'badge-yellow' :
                  p.priority === 'medium' ? 'badge-blue' : 'badge-gray'
                }`}>
                  잔여 {p.days_left}일
                </span>
              </div>
              <p className="text-xs text-gray-500">{p.recommended_action}</p>
            </div>
          ))}
          {(predictions?.data?.predictions || []).length === 0 && (
            <div className="col-span-2 text-center text-green-600 py-6 flex items-center justify-center gap-2">
              <CheckCircle size={18} />갱신이 필요한 인증서가 없습니다.
            </div>
          )}
        </div>
      </div>

      {/* Summary */}
      {insightData?.summary && (
        <div className="card border border-blue-100 bg-blue-50/50">
          <div className="flex items-center gap-3">
            <Bot size={18} className="text-blue-600" />
            <p className="text-sm text-blue-700">{insightData.summary}</p>
            <span className="ml-auto text-xs text-blue-400">자동 분석</span>
          </div>
        </div>
      )}
    </div>
  );
}
