import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { employeeApi } from '../api/client';
import { Users, Plus, Search, Edit2, Trash2, Building2, UserCheck, UserX, RefreshCw } from 'lucide-react';
import toast from 'react-hot-toast';
import { format } from 'date-fns';

const statusLabel: Record<string, string> = {
  active: '재직중', on_leave: '휴직', resigned: '퇴직', retired: '은퇴'
};
const statusClass: Record<string, string> = {
  active: 'badge-green', on_leave: 'badge-yellow', resigned: 'badge-red', retired: 'badge-gray'
};

function EmployeeModal({ employee, departments, onClose, onSave }: any) {
  const [form, setForm] = useState(employee || {
    employee_number: '', full_name: '', email: '', phone: '',
    department_id: '', position: '', job_title: '', hire_date: '',
    employment_status: 'active', notes: '', create_user_account: false
  });

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-2xl shadow-2xl w-full max-w-2xl max-h-[90vh] overflow-y-auto">
        <div className="p-6 border-b border-gray-100">
          <h2 className="text-lg font-semibold text-gray-900">
            {employee ? '직원 정보 수정' : '직원 등록'}
          </h2>
        </div>
        <div className="p-6 grid grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">사번 *</label>
            <input className="input" value={form.employee_number} onChange={e => setForm({ ...form, employee_number: e.target.value })} placeholder="EMP001" />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">이름 *</label>
            <input className="input" value={form.full_name} onChange={e => setForm({ ...form, full_name: e.target.value })} placeholder="홍길동" />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">이메일 *</label>
            <input className="input" type="email" value={form.email} onChange={e => setForm({ ...form, email: e.target.value })} placeholder="user@company.com" />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">연락처</label>
            <input className="input" value={form.phone || ''} onChange={e => setForm({ ...form, phone: e.target.value })} placeholder="010-0000-0000" />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">부서</label>
            <select className="input" value={form.department_id || ''} onChange={e => setForm({ ...form, department_id: e.target.value ? Number(e.target.value) : null })}>
              <option value="">선택없음</option>
              {departments?.map((d: any) => <option key={d.id} value={d.id}>{d.name}</option>)}
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">직위</label>
            <input className="input" value={form.position || ''} onChange={e => setForm({ ...form, position: e.target.value })} placeholder="시니어 개발자" />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">직함</label>
            <input className="input" value={form.job_title || ''} onChange={e => setForm({ ...form, job_title: e.target.value })} placeholder="Software Engineer" />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">입사일</label>
            <input className="input" type="date" value={form.hire_date || ''} onChange={e => setForm({ ...form, hire_date: e.target.value })} />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">재직 상태</label>
            <select className="input" value={form.employment_status} onChange={e => setForm({ ...form, employment_status: e.target.value })}>
              <option value="active">재직중</option>
              <option value="on_leave">휴직</option>
              <option value="resigned">퇴직</option>
              <option value="retired">은퇴</option>
            </select>
          </div>
          {!employee && (
            <div className="col-span-2 flex items-center gap-2">
              <input type="checkbox" id="create_account" checked={form.create_user_account} onChange={e => setForm({ ...form, create_user_account: e.target.checked })} className="w-4 h-4 text-blue-600" />
              <label htmlFor="create_account" className="text-sm text-gray-700">시스템 계정 자동 생성 (임시 비밀번호 이메일 발송)</label>
            </div>
          )}
          <div className="col-span-2">
            <label className="block text-sm font-medium text-gray-700 mb-1">메모</label>
            <textarea className="input" rows={2} value={form.notes || ''} onChange={e => setForm({ ...form, notes: e.target.value })} />
          </div>
        </div>
        <div className="p-6 border-t border-gray-100 flex justify-end gap-3">
          <button onClick={onClose} className="btn-secondary">취소</button>
          <button onClick={() => onSave(form)} className="btn-primary">
            {employee ? '수정' : '등록'}
          </button>
        </div>
      </div>
    </div>
  );
}

export default function EmployeesPage() {
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [deptFilter, setDeptFilter] = useState('');
  const [showModal, setShowModal] = useState(false);
  const [editEmployee, setEditEmployee] = useState<any>(null);
  const qc = useQueryClient();

  const { data, isLoading } = useQuery({
    queryKey: ['employees', page, search, statusFilter, deptFilter],
    queryFn: () => employeeApi.getList({ page, limit: 20, search: search || undefined, status: statusFilter || undefined, department_id: deptFilter || undefined }),
  });

  const { data: stats } = useQuery({
    queryKey: ['employee-stats'],
    queryFn: () => employeeApi.getStats(),
  });

  const { data: depts } = useQuery({
    queryKey: ['departments'],
    queryFn: () => employeeApi.getDepartments(),
  });

  const createMutation = useMutation({
    mutationFn: (d: any) => employeeApi.create(d),
    onSuccess: () => { toast.success('직원이 등록되었습니다.'); qc.invalidateQueries({ queryKey: ['employees'] }); setShowModal(false); },
    onError: (e: any) => toast.error(e.response?.data?.detail || '등록 실패'),
  });

  const updateMutation = useMutation({
    mutationFn: ({ id, data }: any) => employeeApi.update(id, data),
    onSuccess: () => { toast.success('수정되었습니다.'); qc.invalidateQueries({ queryKey: ['employees'] }); setShowModal(false); setEditEmployee(null); },
    onError: (e: any) => toast.error(e.response?.data?.detail || '수정 실패'),
  });

  const s = stats?.data;
  const employees = data?.data?.items || [];
  const total = data?.data?.total || 0;
  const departments = depts?.data || [];

  const handleSave = (form: any) => {
    if (editEmployee) {
      updateMutation.mutate({ id: editEmployee.id, data: form });
    } else {
      createMutation.mutate(form);
    }
  };

  return (
    <div className="space-y-6">
      {/* Stats */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
        {[
          { label: '전체 직원', value: s?.total || 0, color: 'text-blue-600', bg: 'bg-blue-50' },
          { label: '재직중', value: s?.active || 0, color: 'text-green-600', bg: 'bg-green-50' },
          { label: '휴직', value: s?.on_leave || 0, color: 'text-yellow-600', bg: 'bg-yellow-50' },
          { label: '퇴직', value: s?.resigned || 0, color: 'text-red-600', bg: 'bg-red-50' },
        ].map((stat) => (
          <div key={stat.label} className={`card flex items-center gap-4`}>
            <div className={`${stat.bg} ${stat.color} rounded-lg p-3`}>
              <Users size={20} />
            </div>
            <div>
              <p className="text-sm text-gray-500">{stat.label}</p>
              <p className="text-2xl font-bold text-gray-900">{stat.value}</p>
            </div>
          </div>
        ))}
      </div>

      {/* Toolbar */}
      <div className="card">
        <div className="flex flex-wrap gap-3 items-center justify-between mb-4">
          <div className="flex flex-wrap gap-3 flex-1">
            <div className="relative">
              <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
              <input
                className="input pl-9 w-64"
                placeholder="이름, 이메일, 사번 검색..."
                value={search}
                onChange={(e) => { setSearch(e.target.value); setPage(1); }}
              />
            </div>
            <select className="input w-36" value={statusFilter} onChange={(e) => { setStatusFilter(e.target.value); setPage(1); }}>
              <option value="">전체 상태</option>
              <option value="active">재직중</option>
              <option value="on_leave">휴직</option>
              <option value="resigned">퇴직</option>
            </select>
            <select className="input w-36" value={deptFilter} onChange={(e) => { setDeptFilter(e.target.value); setPage(1); }}>
              <option value="">전체 부서</option>
              {departments.map((d: any) => <option key={d.id} value={d.id}>{d.name}</option>)}
            </select>
          </div>
          <button onClick={() => { setEditEmployee(null); setShowModal(true); }} className="btn-primary flex items-center gap-2">
            <Plus size={16} />직원 등록
          </button>
        </div>

        {/* Table */}
        {isLoading ? (
          <div className="flex items-center justify-center h-40"><RefreshCw className="animate-spin text-blue-600" size={24} /></div>
        ) : (
          <div className="table-container">
            <table className="table">
              <thead>
                <tr>
                  <th>사번</th><th>이름</th><th>이메일</th><th>부서</th><th>직위</th>
                  <th>상태</th><th>입사일</th><th>관리</th>
                </tr>
              </thead>
              <tbody>
                {employees.map((emp: any) => (
                  <tr key={emp.id}>
                    <td className="font-mono text-xs text-gray-500">{emp.employee_number}</td>
                    <td className="font-medium text-gray-900">{emp.full_name}</td>
                    <td className="text-gray-500 text-sm">{emp.email}</td>
                    <td className="text-gray-500">{emp.department?.name || '-'}</td>
                    <td className="text-gray-500">{emp.position || '-'}</td>
                    <td><span className={`badge ${statusClass[emp.employment_status] || 'badge-gray'}`}>{statusLabel[emp.employment_status]}</span></td>
                    <td className="text-gray-400 text-xs">{emp.hire_date ? format(new Date(emp.hire_date), 'yyyy.MM.dd') : '-'}</td>
                    <td>
                      <div className="flex items-center gap-1">
                        <button onClick={() => { setEditEmployee(emp); setShowModal(true); }} className="p-1.5 hover:bg-blue-50 rounded-lg text-blue-600 transition-colors">
                          <Edit2 size={14} />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
                {employees.length === 0 && (
                  <tr><td colSpan={8} className="text-center text-gray-400 py-8">직원 데이터가 없습니다.</td></tr>
                )}
              </tbody>
            </table>
          </div>
        )}

        {/* Pagination */}
        {total > 20 && (
          <div className="flex items-center justify-between mt-4 pt-4 border-t border-gray-100">
            <p className="text-sm text-gray-500">총 {total}명</p>
            <div className="flex gap-2">
              <button onClick={() => setPage(p => Math.max(1, p - 1))} disabled={page === 1} className="btn-secondary text-sm px-3 py-1">이전</button>
              <span className="px-3 py-1 text-sm text-gray-700">{page} / {Math.ceil(total / 20)}</span>
              <button onClick={() => setPage(p => p + 1)} disabled={page >= Math.ceil(total / 20)} className="btn-secondary text-sm px-3 py-1">다음</button>
            </div>
          </div>
        )}
      </div>

      {showModal && (
        <EmployeeModal
          employee={editEmployee}
          departments={departments}
          onClose={() => { setShowModal(false); setEditEmployee(null); }}
          onSave={handleSave}
        />
      )}
    </div>
  );
}
