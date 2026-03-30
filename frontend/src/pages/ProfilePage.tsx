import React, { useState } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { authApi } from '../api/client';
import { useAuthStore } from '../stores/authStore';
import { User, Lock, Shield, KeyRound, Check, Loader2 } from 'lucide-react';
import toast from 'react-hot-toast';

export default function ProfilePage() {
  const { user, updateUser } = useAuthStore();
  const [activeTab, setActiveTab] = useState<'profile' | 'password' | 'totp'>('profile');
  const [profileForm, setProfileForm] = useState({ full_name: user?.full_name || '', phone: user?.phone || '' });
  const [pwForm, setPwForm] = useState({ current_password: '', new_password: '', confirm: '' });
  const [totpCode, setTotpCode] = useState('');
  const [totpSetup, setTotpSetup] = useState<any>(null);
  const qc = useQueryClient();

  const updateProfileMutation = useMutation({
    mutationFn: (d: any) => authApi.updateMe(d),
    onSuccess: (res) => {
      updateUser(res.data);
      toast.success('프로필이 업데이트되었습니다.');
    },
    onError: () => toast.error('업데이트 실패'),
  });

  const changePwMutation = useMutation({
    mutationFn: (d: any) => authApi.changePassword(d.current_password, d.new_password),
    onSuccess: () => { toast.success('비밀번호가 변경되었습니다.'); setPwForm({ current_password: '', new_password: '', confirm: '' }); },
    onError: (e: any) => toast.error(e.response?.data?.detail || '변경 실패'),
  });

  const setupTotpMutation = useMutation({
    mutationFn: () => authApi.setupTOTP(),
    onSuccess: (res) => setTotpSetup(res.data),
    onError: () => toast.error('TOTP 설정 실패'),
  });

  const verifyTotpMutation = useMutation({
    mutationFn: (code: string) => authApi.verifyTOTP(code),
    onSuccess: () => {
      toast.success('2단계 인증이 활성화되었습니다.');
      updateUser({ totp_enabled: true });
      setTotpSetup(null);
    },
    onError: (e: any) => toast.error(e.response?.data?.detail || '인증 실패'),
  });

  const disableTotpMutation = useMutation({
    mutationFn: (code: string) => authApi.disableTOTP(code),
    onSuccess: () => {
      toast.success('2단계 인증이 비활성화되었습니다.');
      updateUser({ totp_enabled: false });
    },
    onError: (e: any) => toast.error(e.response?.data?.detail || '비활성화 실패'),
  });

  const handlePasswordChange = () => {
    if (pwForm.new_password !== pwForm.confirm) {
      toast.error('새 비밀번호가 일치하지 않습니다.');
      return;
    }
    changePwMutation.mutate(pwForm);
  };

  return (
    <div className="max-w-2xl mx-auto space-y-6">
      {/* User Header */}
      <div className="card flex items-center gap-4">
        <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-blue-400 to-purple-500 flex items-center justify-center text-white text-2xl font-bold">
          {user?.full_name?.charAt(0)}
        </div>
        <div>
          <h2 className="text-xl font-bold text-gray-900">{user?.full_name}</h2>
          <p className="text-gray-500">{user?.email}</p>
          <div className="flex items-center gap-2 mt-1">
            <span className={`badge ${user?.role === 'admin' ? 'badge-purple' : user?.role === 'manager' ? 'badge-blue' : 'badge-gray'}`}>
              {user?.role === 'admin' ? '관리자' : user?.role === 'manager' ? '매니저' : '사용자'}
            </span>
            {user?.totp_enabled && <span className="badge-green"><Shield size={10} />2FA 활성</span>}
          </div>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex gap-0 border-b border-gray-200">
        {[
          { id: 'profile', label: '프로필', icon: User },
          { id: 'password', label: '비밀번호', icon: Lock },
          { id: 'totp', label: '2단계 인증', icon: Shield },
        ].map((tab) => {
          const Icon = tab.icon;
          return (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id as any)}
              className={`flex items-center gap-2 px-4 py-3 text-sm font-medium border-b-2 transition-colors ${activeTab === tab.id ? 'border-blue-600 text-blue-600' : 'border-transparent text-gray-500 hover:text-gray-700'}`}
            >
              <Icon size={15} />{tab.label}
            </button>
          );
        })}
      </div>

      {activeTab === 'profile' && (
        <div className="card space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">이름</label>
            <input className="input" value={profileForm.full_name} onChange={e => setProfileForm({ ...profileForm, full_name: e.target.value })} />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">연락처</label>
            <input className="input" value={profileForm.phone} onChange={e => setProfileForm({ ...profileForm, phone: e.target.value })} placeholder="010-0000-0000" />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">이메일</label>
            <input className="input bg-gray-50" value={user?.email || ''} disabled />
          </div>
          <button
            onClick={() => updateProfileMutation.mutate(profileForm)}
            disabled={updateProfileMutation.isPending}
            className="btn-primary flex items-center gap-2"
          >
            {updateProfileMutation.isPending ? <Loader2 size={16} className="animate-spin" /> : <Check size={16} />}
            저장
          </button>
        </div>
      )}

      {activeTab === 'password' && (
        <div className="card space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">현재 비밀번호</label>
            <input className="input" type="password" value={pwForm.current_password} onChange={e => setPwForm({ ...pwForm, current_password: e.target.value })} />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">새 비밀번호</label>
            <input className="input" type="password" value={pwForm.new_password} onChange={e => setPwForm({ ...pwForm, new_password: e.target.value })} />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">새 비밀번호 확인</label>
            <input className="input" type="password" value={pwForm.confirm} onChange={e => setPwForm({ ...pwForm, confirm: e.target.value })} />
          </div>
          <button onClick={handlePasswordChange} disabled={changePwMutation.isPending} className="btn-primary flex items-center gap-2">
            {changePwMutation.isPending ? <Loader2 size={16} className="animate-spin" /> : <Lock size={16} />}
            비밀번호 변경
          </button>
        </div>
      )}

      {activeTab === 'totp' && (
        <div className="card space-y-4">
          <div className="p-4 bg-blue-50 rounded-lg">
            <p className="text-sm text-blue-700 font-medium">2단계 인증(TOTP)</p>
            <p className="text-sm text-blue-600 mt-1">Google Authenticator 또는 Authy 앱을 사용하여 추가 보안을 설정합니다.</p>
          </div>

          {user?.totp_enabled ? (
            <div className="space-y-4">
              <div className="flex items-center gap-2 text-green-600">
                <Check size={18} /><span className="font-medium">2단계 인증이 활성화되어 있습니다.</span>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">비활성화를 위한 인증 코드</label>
                <input className="input" type="text" value={totpCode} onChange={e => setTotpCode(e.target.value)} placeholder="6자리 코드" maxLength={6} />
              </div>
              <button onClick={() => disableTotpMutation.mutate(totpCode)} disabled={disableTotpMutation.isPending || totpCode.length !== 6} className="btn-danger flex items-center gap-2">
                2단계 인증 비활성화
              </button>
            </div>
          ) : totpSetup ? (
            <div className="space-y-4">
              <p className="text-sm text-gray-600">인증 앱으로 아래 QR 코드를 스캔하세요:</p>
              <img src={totpSetup.qr_code} alt="TOTP QR Code" className="w-48 h-48 mx-auto" />
              <div className="text-center">
                <p className="text-xs text-gray-500 mb-1">또는 시크릿 키 입력:</p>
                <p className="font-mono text-sm bg-gray-100 px-3 py-2 rounded">{totpSetup.secret}</p>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">인증 코드 확인</label>
                <input className="input" type="text" value={totpCode} onChange={e => setTotpCode(e.target.value)} placeholder="6자리 코드" maxLength={6} />
              </div>
              <button onClick={() => verifyTotpMutation.mutate(totpCode)} disabled={verifyTotpMutation.isPending || totpCode.length !== 6} className="btn-primary">
                인증 및 활성화
              </button>
            </div>
          ) : (
            <button onClick={() => setupTotpMutation.mutate()} disabled={setupTotpMutation.isPending} className="btn-primary flex items-center gap-2">
              {setupTotpMutation.isPending ? <Loader2 size={16} className="animate-spin" /> : <KeyRound size={16} />}
              2단계 인증 설정 시작
            </button>
          )}
        </div>
      )}
    </div>
  );
}
