import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { Shield, Mail, Lock, Eye, EyeOff, Loader2, KeyRound } from 'lucide-react';
import { authApi } from '../api/client';
import { useAuthStore } from '../stores/authStore';
import toast from 'react-hot-toast';

export default function LoginPage() {
  const [form, setForm] = useState({ email: '', password: '', totp_code: '' });
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [needsTOTP, setNeedsTOTP] = useState(false);
  const [verifyEmail, setVerifyEmail] = useState(false);
  const [verifyCode, setVerifyCode] = useState('');
  const navigate = useNavigate();
  const { setAuth } = useAuthStore();

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    try {
      const res = await authApi.login(form.email, form.password, form.totp_code || undefined);
      setAuth(res.data.user, res.data.access_token, res.data.refresh_token);
      toast.success(`환영합니다, ${res.data.user.full_name}님!`);
      navigate('/dashboard');
    } catch (err: any) {
      const msg = err.response?.data?.detail || '로그인에 실패했습니다.';
      if (msg.includes('2단계 인증')) {
        setNeedsTOTP(true);
        toast('2단계 인증 코드를 입력해주세요.', { icon: '🔐' });
      } else if (msg.includes('이메일 인증')) {
        setVerifyEmail(true);
        toast('이메일 인증이 필요합니다.', { icon: '📧' });
      } else {
        toast.error(msg);
      }
    } finally {
      setLoading(false);
    }
  };

  const handleVerifyEmail = async () => {
    setLoading(true);
    try {
      await authApi.verifyEmail(form.email, verifyCode);
      toast.success('이메일 인증 완료! 다시 로그인해주세요.');
      setVerifyEmail(false);
    } catch (err: any) {
      toast.error(err.response?.data?.detail || '인증 실패');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-blue-950 to-purple-950 flex items-center justify-center p-4">
      {/* Background decoration */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <div className="absolute -top-40 -right-40 w-80 h-80 bg-blue-500/10 rounded-full blur-3xl"></div>
        <div className="absolute -bottom-40 -left-40 w-80 h-80 bg-purple-500/10 rounded-full blur-3xl"></div>
      </div>

      <div className="w-full max-w-md relative">
        {/* Logo */}
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-gradient-to-br from-blue-500 to-purple-600 shadow-2xl mb-4">
            <Shield size={32} className="text-white" />
          </div>
          <h1 className="text-3xl font-bold text-white">AssetGuard</h1>
          <p className="text-blue-200/70 mt-1">기업 자산 관리 시스템</p>
        </div>

        {/* Card */}
        <div className="bg-white/10 backdrop-blur-xl border border-white/20 rounded-2xl p-8 shadow-2xl">
          {verifyEmail ? (
            <div>
              <h2 className="text-xl font-semibold text-white mb-2">이메일 인증</h2>
              <p className="text-blue-200/70 text-sm mb-6">{form.email}로 발송된 인증 코드를 입력해주세요.</p>
              <input
                type="text"
                placeholder="인증 코드 6자리"
                value={verifyCode}
                onChange={(e) => setVerifyCode(e.target.value)}
                className="w-full px-4 py-3 bg-white/10 border border-white/20 rounded-xl text-white placeholder-white/40 focus:outline-none focus:border-blue-400 text-center text-2xl tracking-widest mb-4"
                maxLength={6}
              />
              <button
                onClick={handleVerifyEmail}
                disabled={loading || verifyCode.length !== 6}
                className="w-full py-3 bg-gradient-to-r from-blue-500 to-purple-600 text-white rounded-xl font-medium hover:from-blue-600 hover:to-purple-700 transition-all disabled:opacity-50"
              >
                {loading ? <Loader2 className="animate-spin mx-auto" size={20} /> : '인증 확인'}
              </button>
            </div>
          ) : (
            <form onSubmit={handleLogin} className="space-y-5">
              <div>
                <h2 className="text-xl font-semibold text-white mb-1">로그인</h2>
                <p className="text-blue-200/60 text-sm">계정에 로그인하세요</p>
              </div>

              <div className="space-y-3">
                <div className="relative">
                  <Mail size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-white/40" />
                  <input
                    type="email"
                    placeholder="이메일 주소"
                    value={form.email}
                    onChange={(e) => setForm({ ...form, email: e.target.value })}
                    className="w-full pl-10 pr-4 py-3 bg-white/10 border border-white/20 rounded-xl text-white placeholder-white/40 focus:outline-none focus:border-blue-400"
                    required
                  />
                </div>

                <div className="relative">
                  <Lock size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-white/40" />
                  <input
                    type={showPassword ? 'text' : 'password'}
                    placeholder="비밀번호"
                    value={form.password}
                    onChange={(e) => setForm({ ...form, password: e.target.value })}
                    className="w-full pl-10 pr-12 py-3 bg-white/10 border border-white/20 rounded-xl text-white placeholder-white/40 focus:outline-none focus:border-blue-400"
                    required
                  />
                  <button
                    type="button"
                    onClick={() => setShowPassword(!showPassword)}
                    className="absolute right-3 top-1/2 -translate-y-1/2 text-white/40 hover:text-white/70"
                  >
                    {showPassword ? <EyeOff size={16} /> : <Eye size={16} />}
                  </button>
                </div>

                {needsTOTP && (
                  <div className="relative">
                    <KeyRound size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-white/40" />
                    <input
                      type="text"
                      placeholder="2단계 인증 코드 (6자리)"
                      value={form.totp_code}
                      onChange={(e) => setForm({ ...form, totp_code: e.target.value })}
                      className="w-full pl-10 pr-4 py-3 bg-white/10 border border-white/20 rounded-xl text-white placeholder-white/40 focus:outline-none focus:border-blue-400 tracking-widest text-center"
                      maxLength={6}
                    />
                  </div>
                )}
              </div>

              <div className="text-right">
                <Link to="/forgot-password" className="text-sm text-blue-300/70 hover:text-blue-300">
                  비밀번호를 잊으셨나요?
                </Link>
              </div>

              <button
                type="submit"
                disabled={loading}
                className="w-full py-3 bg-gradient-to-r from-blue-500 to-purple-600 text-white rounded-xl font-medium hover:from-blue-600 hover:to-purple-700 transition-all shadow-lg hover:shadow-blue-500/25 disabled:opacity-50 flex items-center justify-center gap-2"
              >
                {loading ? <Loader2 className="animate-spin" size={20} /> : '로그인'}
              </button>

              {/* Demo credentials */}
              <div className="mt-4 p-3 bg-white/5 rounded-lg border border-white/10">
                <p className="text-xs text-white/50 mb-2 font-medium">데모 계정</p>
                <div className="space-y-1 text-xs text-white/40">
                  <p>관리자: admin@company.com / Admin@123456</p>
                  <p>매니저: manager@company.com / Manager@123</p>
                  <p>사용자: user@company.com / User@123456</p>
                </div>
              </div>
            </form>
          )}
        </div>
      </div>
    </div>
  );
}
