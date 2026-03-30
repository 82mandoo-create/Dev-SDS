import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { userApi } from '../api/client';
import { User, Plus, Search, Edit2, Lock, Unlock, Trash2, RefreshCw, Shield } from 'lucide-react';
import toast from 'react-hot-toast';
import { format } from 'date-fns';

const roleLabel: Record<string, string> = { admin: '관리자', manager: '매니저', user: '사용자' };
const roleClass: Record<string, string> = { admin: 'badge-purple', manager: 'badge-blue', user: 'badge-gray' };
const statusClass: Record<string, string> = { active: 'badge-green', inactive: 'badge-red', pending: 'badge-yellow', locked: 'badge-red' };
const statusLabel: Record<string, string> = { active: '활성', inactive: '비활성', pending: '대기', locked: '잠금' };

function UserModal({ user, onClose, onSave }: any) {
  const [form, setForm] = useState(user || { email: '', full_name: '', role: 'user', password: '', status: 'active' });
  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-2xl shadow-2xl w-full max-w-md">
        <div className="p-6 border-b border-gray-100">
          <h2 className="text-lg font-semibold">{user ? '사용자 수정' : '사용자 생성'}</h2>
        </div>
        <div className="p-6 space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">이메일 *</label>
            <input className="input" type="email" value={form.email} onChange={e => setForm({ ...form, email: e.target.value })} />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">이름 *</label>
            <input className="input" value={form.full_name} onChange={e => setForm({ ...form, full_name: e.target.value })} />
          </div>
          {!user && (
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">비밀번호 *</label>
              <input className="input" type="password" value={form.password} onChange={e => setForm({ ...form, password: e.target.value })} />
            </div>
          )}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">권한</label>
            <select className="input" value={form.role} onChange={e => setForm({ ...form, role: e.target.value })}>
              <option value="user">사용자</option>
              <option value="manager">매니저</option>
              <option value="admin">관리자</option>
            </select>
          </div>
          {user && (
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">상태</label>
              <select className="input" value={form.status} onChange={e => setForm({ ...form, status: e.target.value })}>
                <option value="active">활성</option>
                <option value="inactive">비활성</option>
                <option value="pending">대기</option>
              </select>
            </div>
          )}
        </div>
        <div className="p-6 border-t border-gray-100 flex justify-end gap-3">
          <button onClick={onClose} className="btn-secondary">취소</button>
          <button onClick={() => onSave(form)} className="btn-primary">{user ? '수정' : '생성'}</button>
        </div>
      </div>
    </div>
  );
}

export default function UsersPage() {
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState('');
  const [showModal, setShowModal] = useState(false);
  const [editUser, setEditUser] = useState<any>(null);
  const qc = useQueryClient();

  const { data, isLoading } = useQuery({
    queryKey: ['users', page, search],
    queryFn: () => userApi.getList({ page, limit: 20, search: search || undefined }),
  });

  const createMutation = useMutation({
    mutationFn: (d: any) => userApi.create(d),
    onSuccess: () => { toast.success('사용자가 생성되었습니다.'); qc.invalidateQueries({ queryKey: ['users'] }); setShowModal(false); },
    onError: (e: any) => toast.error(e.response?.data?.detail || '생성 실패'),
  });

  const updateMutation = useMutation({
    mutationFn: ({ id, data }: any) => userApi.update(id, data),
    onSuccess: () => { toast.success('수정되었습니다.'); qc.invalidateQueries({ queryKey: ['users'] }); setShowModal(false); setEditUser(null); },
  });

  const unlockMutation = useMutation({
    mutationFn: (id: number) => userApi.unlock(id),
    onSuccess: () => { toast.success('잠금 해제되었습니다.'); qc.invalidateQueries({ queryKey: ['users'] }); },
  });

  const deleteMutation = useMutation({
    mutationFn: (id: number) => userApi.delete(id),
    onSuccess: () => { toast.success('비활성화되었습니다.'); qc.invalidateQueries({ queryKey: ['users'] }); },
  });

  const users = data?.data?.items || [];
  const total = data?.data?.total || 0;

  const handleSave = (form: any) => {
    if (editUser) updateMutation.mutate({ id: editUser.id, data: form });
    else createMutation.mutate(form);
  };

  return (
    <div className="space-y-6">
      <div className="card">
        <div className="flex flex-wrap gap-3 items-center justify-between mb-4">
          <div className="flex flex-wrap gap-3 flex-1">
            <div className="relative">
              <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
              <input className="input pl-9 w-64" placeholder="이름, 이메일 검색..." value={search} onChange={(e) => { setSearch(e.target.value); setPage(1); }} />
            </div>
          </div>
          <button onClick={() => { setEditUser(null); setShowModal(true); }} className="btn-primary flex items-center gap-2">
            <Plus size={16} />사용자 생성
          </button>
        </div>

        {isLoading ? (
          <div className="flex items-center justify-center h-40"><RefreshCw className="animate-spin text-blue-600" size={24} /></div>
        ) : (
          <div className="table-container">
            <table className="table">
              <thead>
                <tr>
                  <th>이름</th><th>이메일</th><th>권한</th><th>상태</th>
                  <th>이메일 인증</th><th>2FA</th><th>마지막 로그인</th><th>관리</th>
                </tr>
              </thead>
              <tbody>
                {users.map((u: any) => (
                  <tr key={u.id}>
                    <td>
                      <div className="flex items-center gap-2">
                        <div className="w-7 h-7 rounded-full bg-gradient-to-br from-blue-400 to-purple-500 flex items-center justify-center text-white text-xs font-medium">
                          {u.full_name?.charAt(0)}
                        </div>
                        <span className="font-medium text-gray-900">{u.full_name}</span>
                      </div>
                    </td>
                    <td className="text-gray-500">{u.email}</td>
                    <td><span className={`badge ${roleClass[u.role] || 'badge-gray'}`}>{roleLabel[u.role]}</span></td>
                    <td><span className={`badge ${statusClass[u.status] || 'badge-gray'}`}>{statusLabel[u.status]}</span></td>
                    <td>{u.email_verified ? <span className="badge-green">인증됨</span> : <span className="badge-red">미인증</span>}</td>
                    <td>{u.totp_enabled ? <span className="badge-green">활성</span> : <span className="badge-gray">비활성</span>}</td>
                    <td className="text-xs text-gray-400">{u.last_login ? format(new Date(u.last_login), 'MM/dd HH:mm') : '없음'}</td>
                    <td>
                      <div className="flex items-center gap-1">
                        <button onClick={() => { setEditUser(u); setShowModal(true); }} className="p-1.5 hover:bg-blue-50 rounded-lg text-blue-600">
                          <Edit2 size={14} />
                        </button>
                        {u.status === 'locked' && (
                          <button onClick={() => unlockMutation.mutate(u.id)} className="p-1.5 hover:bg-green-50 rounded-lg text-green-600">
                            <Unlock size={14} />
                          </button>
                        )}
                        <button onClick={() => { if (confirm('비활성화하시겠습니까?')) deleteMutation.mutate(u.id); }} className="p-1.5 hover:bg-red-50 rounded-lg text-red-500">
                          <Trash2 size={14} />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
                {users.length === 0 && (
                  <tr><td colSpan={8} className="text-center text-gray-400 py-8">사용자 데이터가 없습니다.</td></tr>
                )}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {showModal && (
        <UserModal user={editUser} onClose={() => { setShowModal(false); setEditUser(null); }} onSave={handleSave} />
      )}
    </div>
  );
}
