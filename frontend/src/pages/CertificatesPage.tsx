import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { certificateApi } from '../api/client';
import { FileCheck, Plus, Search, Edit2, Trash2, AlertTriangle, CheckCircle, Bot, RefreshCw, Calendar } from 'lucide-react';
import toast from 'react-hot-toast';
import { format, differenceInDays } from 'date-fns';

const typeLabel: Record<string, string> = {
  ssl_tls: 'SSL/TLS', code_signing: '코드서명', email: '이메일',
  wildcard: '와일드카드', ev: 'EV', ov: 'OV', dv: 'DV', custom: '기타'
};

function getDaysColor(days: number) {
  if (days < 0) return 'badge-red';
  if (days <= 7) return 'badge-red';
  if (days <= 30) return 'badge-yellow';
  return 'badge-green';
}

function CertModal({ cert, vendors, onClose, onSave }: any) {
  const [form, setForm] = useState(cert || {
    name: '', cert_type: 'ssl_tls', domain: '', issuer: '',
    expiry_date: '', issued_date: '', renewal_reminder_days: 30,
    vendor_id: '', responsible_employee_id: null,
    purchase_price: '', notes: '', auto_renewal: false
  });

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-2xl shadow-2xl w-full max-w-2xl max-h-[90vh] overflow-y-auto">
        <div className="p-6 border-b border-gray-100">
          <h2 className="text-lg font-semibold">{cert ? '인증서 수정' : '인증서 등록'}</h2>
        </div>
        <div className="p-6 grid grid-cols-2 gap-4">
          <div className="col-span-2">
            <label className="block text-sm font-medium text-gray-700 mb-1">인증서 이름 *</label>
            <input className="input" value={form.name} onChange={e => setForm({ ...form, name: e.target.value })} placeholder="예: www.company.com SSL 인증서" />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">종류</label>
            <select className="input" value={form.cert_type} onChange={e => setForm({ ...form, cert_type: e.target.value })}>
              {Object.entries(typeLabel).map(([k, v]) => <option key={k} value={k}>{v}</option>)}
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">도메인</label>
            <input className="input" value={form.domain || ''} onChange={e => setForm({ ...form, domain: e.target.value })} placeholder="www.example.com" />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">발급 기관</label>
            <input className="input" value={form.issuer || ''} onChange={e => setForm({ ...form, issuer: e.target.value })} placeholder="DigiCert" />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">업체</label>
            <select className="input" value={form.vendor_id || ''} onChange={e => setForm({ ...form, vendor_id: e.target.value ? Number(e.target.value) : null })}>
              <option value="">선택없음</option>
              {vendors?.map((v: any) => <option key={v.id} value={v.id}>{v.name}</option>)}
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">발급일</label>
            <input className="input" type="date" value={form.issued_date || ''} onChange={e => setForm({ ...form, issued_date: e.target.value })} />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">만료일 *</label>
            <input className="input" type="date" value={form.expiry_date || ''} onChange={e => setForm({ ...form, expiry_date: e.target.value })} />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">갱신 알림 (일 전)</label>
            <input className="input" type="number" value={form.renewal_reminder_days} onChange={e => setForm({ ...form, renewal_reminder_days: Number(e.target.value) })} min={1} max={365} />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">구매금액</label>
            <input className="input" type="number" value={form.purchase_price || ''} onChange={e => setForm({ ...form, purchase_price: e.target.value })} placeholder="0" />
          </div>
          <div className="col-span-2 flex items-center gap-2">
            <input type="checkbox" id="auto_renewal" checked={form.auto_renewal} onChange={e => setForm({ ...form, auto_renewal: e.target.checked })} className="w-4 h-4 text-blue-600" />
            <label htmlFor="auto_renewal" className="text-sm text-gray-700">자동 갱신</label>
          </div>
          <div className="col-span-2">
            <label className="block text-sm font-medium text-gray-700 mb-1">메모</label>
            <textarea className="input" rows={2} value={form.notes || ''} onChange={e => setForm({ ...form, notes: e.target.value })} />
          </div>
        </div>
        <div className="p-6 border-t border-gray-100 flex justify-end gap-3">
          <button onClick={onClose} className="btn-secondary">취소</button>
          <button onClick={() => onSave(form)} className="btn-primary">{cert ? '수정' : '등록'}</button>
        </div>
      </div>
    </div>
  );
}

export default function CertificatesPage() {
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [showModal, setShowModal] = useState(false);
  const [editCert, setEditCert] = useState<any>(null);
  const [activeTab, setActiveTab] = useState<'list' | 'ai'>('list');
  const qc = useQueryClient();

  const { data, isLoading } = useQuery({
    queryKey: ['certificates', page, search, statusFilter],
    queryFn: () => certificateApi.getList({ page, limit: 20, search: search || undefined, status: statusFilter || undefined }),
  });

  const { data: stats } = useQuery({
    queryKey: ['cert-stats'],
    queryFn: () => certificateApi.getStats(),
  });

  const { data: vendors } = useQuery({
    queryKey: ['cert-vendors'],
    queryFn: () => certificateApi.getVendors(),
  });

  const { data: predictions } = useQuery({
    queryKey: ['cert-predictions'],
    queryFn: () => certificateApi.getRenewalPredictions(),
    enabled: activeTab === 'ai',
  });

  const createMutation = useMutation({
    mutationFn: (d: any) => certificateApi.create(d),
    onSuccess: () => { toast.success('인증서가 등록되었습니다.'); qc.invalidateQueries({ queryKey: ['certificates'] }); setShowModal(false); },
    onError: (e: any) => toast.error(e.response?.data?.detail || '등록 실패'),
  });

  const updateMutation = useMutation({
    mutationFn: ({ id, data }: any) => certificateApi.update(id, data),
    onSuccess: () => { toast.success('수정되었습니다.'); qc.invalidateQueries({ queryKey: ['certificates'] }); setShowModal(false); setEditCert(null); },
  });

  const deleteMutation = useMutation({
    mutationFn: (id: number) => certificateApi.delete(id),
    onSuccess: () => { toast.success('삭제되었습니다.'); qc.invalidateQueries({ queryKey: ['certificates'] }); },
  });

  const s = stats?.data;
  const certs = data?.data?.items || [];

  const handleSave = (form: any) => {
    if (editCert) updateMutation.mutate({ id: editCert.id, data: form });
    else createMutation.mutate(form);
  };

  return (
    <div className="space-y-6">
      {/* Stats */}
      <div className="grid grid-cols-2 sm:grid-cols-5 gap-4">
        {[
          { label: '전체', value: s?.total || 0, color: 'text-blue-600', bg: 'bg-blue-50' },
          { label: '정상', value: s?.active || 0, color: 'text-green-600', bg: 'bg-green-50' },
          { label: '만료됨', value: s?.expired || 0, color: 'text-red-600', bg: 'bg-red-50' },
          { label: '7일 내 만료', value: s?.expiring_7_days || 0, color: 'text-orange-600', bg: 'bg-orange-50' },
          { label: '30일 내 만료', value: s?.expiring_30_days || 0, color: 'text-yellow-600', bg: 'bg-yellow-50' },
        ].map((stat) => (
          <div key={stat.label} className="card text-center">
            <p className="text-sm text-gray-500">{stat.label}</p>
            <p className={`text-2xl font-bold mt-1 ${stat.color}`}>{stat.value}</p>
          </div>
        ))}
      </div>

      {/* Tabs */}
      <div className="flex gap-2 border-b border-gray-200">
        <button
          onClick={() => setActiveTab('list')}
          className={`px-4 py-2 text-sm font-medium border-b-2 transition-colors ${activeTab === 'list' ? 'border-blue-600 text-blue-600' : 'border-transparent text-gray-500 hover:text-gray-700'}`}
        >
          인증서 목록
        </button>
        <button
          onClick={() => setActiveTab('ai')}
          className={`px-4 py-2 text-sm font-medium border-b-2 transition-colors flex items-center gap-1 ${activeTab === 'ai' ? 'border-purple-600 text-purple-600' : 'border-transparent text-gray-500 hover:text-gray-700'}`}
        >
          <Bot size={14} />AI 갱신 예측
        </button>
      </div>

      {activeTab === 'list' ? (
        <div className="card">
          <div className="flex flex-wrap gap-3 items-center justify-between mb-4">
            <div className="flex flex-wrap gap-3 flex-1">
              <div className="relative">
                <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
                <input className="input pl-9 w-64" placeholder="이름, 도메인 검색..." value={search} onChange={(e) => { setSearch(e.target.value); setPage(1); }} />
              </div>
              <select className="input w-36" value={statusFilter} onChange={(e) => { setStatusFilter(e.target.value); setPage(1); }}>
                <option value="">전체 상태</option>
                <option value="active">정상</option>
                <option value="expiring_soon">만료 예정</option>
                <option value="expired">만료됨</option>
              </select>
            </div>
            <button onClick={() => { setEditCert(null); setShowModal(true); }} className="btn-primary flex items-center gap-2">
              <Plus size={16} />인증서 등록
            </button>
          </div>

          {isLoading ? (
            <div className="flex items-center justify-center h-40"><RefreshCw className="animate-spin text-blue-600" size={24} /></div>
          ) : (
            <div className="table-container">
              <table className="table">
                <thead>
                  <tr>
                    <th>이름</th><th>종류</th><th>도메인</th><th>만료일</th>
                    <th>잔여일</th><th>상태</th><th>자동갱신</th><th>관리</th>
                  </tr>
                </thead>
                <tbody>
                  {certs.map((cert: any) => {
                    const daysLeft = cert.expiry_date ? differenceInDays(new Date(cert.expiry_date), new Date()) : 0;
                    return (
                      <tr key={cert.id}>
                        <td className="font-medium text-gray-900">{cert.name}</td>
                        <td><span className="badge-blue">{typeLabel[cert.cert_type] || cert.cert_type}</span></td>
                        <td className="text-gray-500 text-sm font-mono">{cert.domain || '-'}</td>
                        <td className="text-sm">{cert.expiry_date ? format(new Date(cert.expiry_date), 'yyyy.MM.dd') : '-'}</td>
                        <td>
                          <span className={`badge ${getDaysColor(daysLeft)}`}>
                            {daysLeft < 0 ? `${Math.abs(daysLeft)}일 초과` : `${daysLeft}일`}
                          </span>
                        </td>
                        <td>
                          <span className={`badge ${cert.status === 'active' ? 'badge-green' : cert.status === 'expired' ? 'badge-red' : 'badge-yellow'}`}>
                            {cert.status === 'active' ? '정상' : cert.status === 'expired' ? '만료' : '만료예정'}
                          </span>
                        </td>
                        <td>
                          {cert.auto_renewal ? <span className="badge-green">자동</span> : <span className="badge-gray">수동</span>}
                        </td>
                        <td>
                          <div className="flex items-center gap-1">
                            <button onClick={() => { setEditCert(cert); setShowModal(true); }} className="p-1.5 hover:bg-blue-50 rounded-lg text-blue-600">
                              <Edit2 size={14} />
                            </button>
                            <button onClick={() => { if (confirm('삭제하시겠습니까?')) deleteMutation.mutate(cert.id); }} className="p-1.5 hover:bg-red-50 rounded-lg text-red-500">
                              <Trash2 size={14} />
                            </button>
                          </div>
                        </td>
                      </tr>
                    );
                  })}
                  {certs.length === 0 && (
                    <tr><td colSpan={8} className="text-center text-gray-400 py-8">인증서 데이터가 없습니다.</td></tr>
                  )}
                </tbody>
              </table>
            </div>
          )}
        </div>
      ) : (
        <div className="card">
          <div className="flex items-center gap-2 mb-6">
            <Bot size={20} className="text-purple-600" />
            <h3 className="font-semibold text-gray-900">AI 기반 갱신 우선순위 분석</h3>
          </div>
          <div className="space-y-3">
            {(predictions?.data?.predictions || []).map((p: any) => (
              <div key={p.cert_id} className={`p-4 rounded-xl border ${
                p.priority === 'critical' ? 'border-red-200 bg-red-50' :
                p.priority === 'high' ? 'border-orange-200 bg-orange-50' :
                p.priority === 'medium' ? 'border-yellow-200 bg-yellow-50' : 'border-gray-200 bg-gray-50'
              }`}>
                <div className="flex items-start justify-between">
                  <div>
                    <p className="font-medium text-gray-900">{p.cert_name}</p>
                    <p className="text-sm text-gray-500 mt-0.5">권장 조치: {p.recommended_action}</p>
                  </div>
                  <div className="text-right">
                    <span className={`badge ${
                      p.priority === 'critical' ? 'badge-red' :
                      p.priority === 'high' ? 'badge-yellow' :
                      p.priority === 'medium' ? 'badge-blue' : 'badge-gray'
                    }`}>
                      {p.priority === 'critical' ? '긴급' : p.priority === 'high' ? '높음' : p.priority === 'medium' ? '보통' : '낮음'}
                    </span>
                    <p className="text-xs text-gray-400 mt-1">잔여 {p.days_left}일</p>
                  </div>
                </div>
              </div>
            ))}
            {(predictions?.data?.predictions || []).length === 0 && (
              <div className="text-center text-gray-400 py-8 flex items-center justify-center gap-2">
                <CheckCircle size={18} className="text-green-500" />
                갱신이 필요한 인증서가 없습니다.
              </div>
            )}
          </div>
        </div>
      )}

      {showModal && (
        <CertModal
          cert={editCert}
          vendors={vendors?.data || []}
          onClose={() => { setShowModal(false); setEditCert(null); }}
          onSave={handleSave}
        />
      )}
    </div>
  );
}
