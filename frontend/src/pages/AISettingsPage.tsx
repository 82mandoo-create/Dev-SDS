import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { aiSettingsApi } from '../api/client';
import {
  Bot, Plus, Trash2, Edit2, CheckCircle, XCircle, Loader2,
  Eye, EyeOff, Zap, Star, StarOff, RefreshCw, AlertTriangle,
  ChevronDown, ChevronUp, ExternalLink, Server, Key, Settings,
  Activity, Clock, TrendingUp, Info, Check
} from 'lucide-react';
import toast from 'react-hot-toast';

// ─────────────────── 타입 ───────────────────
interface AIConfig {
  id: number;
  name: string;
  provider: string;
  model_name: string;
  api_key: string | null;
  api_key_set: boolean;
  api_base_url: string | null;
  api_version: string | null;
  deployment_name: string | null;
  is_active: boolean;
  is_default: boolean;
  status: 'active' | 'inactive' | 'error' | 'testing';
  max_tokens: number;
  temperature: number;
  use_for_pc_analysis: boolean;
  use_for_cert_prediction: boolean;
  use_for_security_insights: boolean;
  use_for_anomaly_detection: boolean;
  last_test_at: string | null;
  last_test_result: string | null;
  last_test_success: boolean | null;
  total_requests: number;
  failed_requests: number;
  last_used_at: string | null;
  description: string | null;
  created_at: string;
}

interface Provider {
  key: string;
  label: string;
  icon: string;
  color: string;
  description: string;
  requires_api_key: boolean;
  requires_base_url: boolean;
  models: { id: string; label: string }[];
  api_key_placeholder: string | null;
  base_url_placeholder: string | null;
  docs_url: string | null;
}

// ─────────────────── 상수 ───────────────────
const STATUS_MAP: Record<string, { label: string; cls: string }> = {
  active:   { label: '연결됨',   cls: 'badge-green' },
  inactive: { label: '미테스트', cls: 'badge-gray' },
  error:    { label: '오류',     cls: 'badge-red' },
  testing:  { label: '테스트중', cls: 'badge-blue' },
};

const USAGE_LABELS: Record<string, string> = {
  use_for_pc_analysis:       'PC 보안 분석',
  use_for_cert_prediction:   '인증서 갱신 예측',
  use_for_security_insights: '보안 인사이트',
  use_for_anomaly_detection: '이상행동 탐지',
};

// ─────────────────── 모달 ───────────────────
function AIConfigModal({
  providers,
  existing,
  onClose,
}: {
  providers: Provider[];
  existing: AIConfig | null;
  onClose: () => void;
}) {
  const qc = useQueryClient();
  const isEdit = !!existing;

  const defaultProvider = providers[0]?.key || 'openai';
  const [provider, setProvider] = useState<string>(existing?.provider || defaultProvider);
  const [showKey, setShowKey] = useState(false);
  const [customModelInput, setCustomModelInput] = useState(false);

  const providerInfo = providers.find(p => p.key === provider);

  const [form, setForm] = useState({
    name: existing?.name || '',
    provider: existing?.provider || defaultProvider,
    model_name: existing?.model_name || providerInfo?.models[0]?.id || '',
    api_key: '',
    api_base_url: existing?.api_base_url || providerInfo?.base_url_placeholder || '',
    api_version: existing?.api_version || '',
    deployment_name: existing?.deployment_name || '',
    is_active: existing?.is_active ?? true,
    is_default: existing?.is_default ?? false,
    max_tokens: existing?.max_tokens ?? 2000,
    temperature: existing?.temperature ?? 0.3,
    use_for_pc_analysis: existing?.use_for_pc_analysis ?? true,
    use_for_cert_prediction: existing?.use_for_cert_prediction ?? true,
    use_for_security_insights: existing?.use_for_security_insights ?? true,
    use_for_anomaly_detection: existing?.use_for_anomaly_detection ?? true,
    description: existing?.description || '',
  });

  const handleProviderChange = (pKey: string) => {
    const p = providers.find(x => x.key === pKey);
    setProvider(pKey);
    setCustomModelInput(false);
    setForm(f => ({
      ...f,
      provider: pKey,
      model_name: p?.models[0]?.id || '',
      api_base_url: p?.base_url_placeholder || '',
      api_key: '',
    }));
  };

  const mutation = useMutation({
    mutationFn: (data: any) =>
      isEdit ? aiSettingsApi.update(existing!.id, data) : aiSettingsApi.create(data),
    onSuccess: () => {
      toast.success(isEdit ? '설정이 수정되었습니다.' : 'AI 설정이 등록되었습니다.');
      qc.invalidateQueries({ queryKey: ['ai-configs'] });
      qc.invalidateQueries({ queryKey: ['ai-stats'] });
      onClose();
    },
    onError: (e: any) => toast.error(e.response?.data?.detail || '저장 실패'),
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const payload: any = { ...form };
    // api_key 미입력 시 제외 (수정 시 빈칸이면 유지)
    if (!payload.api_key) delete payload.api_key;
    mutation.mutate(payload);
  };

  const currentModels = providerInfo?.models || [];
  const isCustomModel = customModelInput || form.model_name === 'custom';

  return (
    <div className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-4">
      <div className="bg-white rounded-2xl shadow-2xl w-full max-w-2xl max-h-[90vh] overflow-y-auto">
        {/* 헤더 */}
        <div className="flex items-center justify-between p-6 border-b border-gray-100">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center">
              <Bot size={20} className="text-white" />
            </div>
            <div>
              <h2 className="text-lg font-bold text-gray-900">
                {isEdit ? 'AI 설정 수정' : '새 AI 설정 등록'}
              </h2>
              <p className="text-xs text-gray-500">API 키와 모델을 등록하여 AI 기능을 활성화하세요</p>
            </div>
          </div>
          <button onClick={onClose} className="p-2 rounded-lg hover:bg-gray-100 text-gray-400">✕</button>
        </div>

        <form onSubmit={handleSubmit} className="p-6 space-y-6">
          {/* 제공자 선택 */}
          <div>
            <label className="block text-sm font-semibold text-gray-700 mb-3">AI 제공자 선택</label>
            <div className="grid grid-cols-3 gap-2">
              {providers.map(p => (
                <button
                  key={p.key}
                  type="button"
                  onClick={() => handleProviderChange(p.key)}
                  className={`flex flex-col items-center gap-1.5 p-3 rounded-xl border-2 transition-all text-sm ${
                    provider === p.key
                      ? 'border-blue-500 bg-blue-50'
                      : 'border-gray-200 hover:border-gray-300 hover:bg-gray-50'
                  }`}
                >
                  <span className="text-2xl">{p.icon}</span>
                  <span className={`font-medium text-xs ${provider === p.key ? 'text-blue-700' : 'text-gray-700'}`}>
                    {p.label}
                  </span>
                </button>
              ))}
            </div>
            {providerInfo && (
              <div className="mt-2 flex items-start gap-2 p-2.5 bg-gray-50 rounded-lg">
                <Info size={14} className="text-gray-400 mt-0.5 flex-shrink-0" />
                <p className="text-xs text-gray-500">{providerInfo.description}</p>
                {providerInfo.docs_url && (
                  <a href={providerInfo.docs_url} target="_blank" rel="noopener noreferrer"
                    className="flex-shrink-0 text-xs text-blue-600 hover:underline flex items-center gap-1">
                    키 발급 <ExternalLink size={10} />
                  </a>
                )}
              </div>
            )}
          </div>

          {/* 기본 정보 */}
          <div className="grid grid-cols-2 gap-4">
            <div className="col-span-2">
              <label className="block text-sm font-medium text-gray-700 mb-1">설정 이름 <span className="text-red-500">*</span></label>
              <input className="input" placeholder="예: GPT-4o 운영용" required
                value={form.name} onChange={e => setForm(f => ({ ...f, name: e.target.value }))} />
            </div>

            {/* 모델 선택 */}
            <div className="col-span-2">
              <label className="block text-sm font-medium text-gray-700 mb-1">모델 <span className="text-red-500">*</span></label>
              {isCustomModel ? (
                <div className="flex gap-2">
                  <input className="input flex-1" placeholder="모델명 직접 입력 (예: llama3.2:latest)"
                    value={form.model_name === 'custom' ? '' : form.model_name}
                    onChange={e => setForm(f => ({ ...f, model_name: e.target.value }))} />
                  <button type="button" onClick={() => { setCustomModelInput(false); setForm(f => ({ ...f, model_name: currentModels[0]?.id || '' })); }}
                    className="btn-secondary text-xs px-3">목록으로</button>
                </div>
              ) : (
                <select className="input"
                  value={form.model_name}
                  onChange={e => {
                    if (e.target.value === 'custom') { setCustomModelInput(true); setForm(f => ({ ...f, model_name: '' })); }
                    else setForm(f => ({ ...f, model_name: e.target.value }));
                  }}>
                  {currentModels.map(m => (
                    <option key={m.id} value={m.id}>{m.label}</option>
                  ))}
                </select>
              )}
            </div>
          </div>

          {/* API 키 */}
          {providerInfo?.requires_api_key && (
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                API 키 {!isEdit && <span className="text-red-500">*</span>}
                {isEdit && existing?.api_key_set && (
                  <span className="ml-2 text-xs text-green-600 font-normal">(현재 키 등록됨 - 변경 시에만 입력)</span>
                )}
              </label>
              <div className="relative">
                <input
                  className="input pr-10"
                  type={showKey ? 'text' : 'password'}
                  placeholder={providerInfo.api_key_placeholder || 'API Key를 입력하세요'}
                  value={form.api_key}
                  onChange={e => setForm(f => ({ ...f, api_key: e.target.value }))}
                  required={!isEdit}
                />
                <button type="button" onClick={() => setShowKey(!showKey)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600">
                  {showKey ? <EyeOff size={16} /> : <Eye size={16} />}
                </button>
              </div>
            </div>
          )}

          {/* Base URL (Ollama, Azure, Custom) */}
          {providerInfo?.requires_base_url && (
            <div className="grid grid-cols-1 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  {provider === 'azure_openai' ? 'Azure Endpoint URL' : 'Base URL'} <span className="text-red-500">*</span>
                </label>
                <input className="input" type="url"
                  placeholder={providerInfo.base_url_placeholder || 'http://...'}
                  value={form.api_base_url}
                  onChange={e => setForm(f => ({ ...f, api_base_url: e.target.value }))}
                  required={providerInfo.requires_base_url} />
              </div>
              {provider === 'azure_openai' && (
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">API 버전</label>
                    <input className="input" placeholder="2024-02-01"
                      value={form.api_version} onChange={e => setForm(f => ({ ...f, api_version: e.target.value }))} />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">배포 이름 (Deployment)</label>
                    <input className="input" placeholder="my-gpt4-deployment"
                      value={form.deployment_name} onChange={e => setForm(f => ({ ...f, deployment_name: e.target.value }))} />
                  </div>
                </div>
              )}
            </div>
          )}

          {/* 파라미터 */}
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Max Tokens <span className="text-xs text-gray-400">(100~32000)</span>
              </label>
              <input className="input" type="number" min={100} max={32000}
                value={form.max_tokens} onChange={e => setForm(f => ({ ...f, max_tokens: Number(e.target.value) }))} />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Temperature <span className="text-xs text-gray-400">(0.0~2.0)</span>
              </label>
              <input className="input" type="number" step={0.1} min={0} max={2}
                value={form.temperature} onChange={e => setForm(f => ({ ...f, temperature: Number(e.target.value) }))} />
            </div>
          </div>

          {/* 사용 범위 */}
          <div>
            <label className="block text-sm font-semibold text-gray-700 mb-2">사용 범위</label>
            <div className="grid grid-cols-2 gap-2">
              {Object.entries(USAGE_LABELS).map(([key, label]) => (
                <label key={key} className="flex items-center gap-2 p-2.5 rounded-lg border border-gray-200 cursor-pointer hover:bg-gray-50">
                  <input type="checkbox" className="rounded"
                    checked={(form as any)[key]}
                    onChange={e => setForm(f => ({ ...f, [key]: e.target.checked }))} />
                  <span className="text-sm text-gray-700">{label}</span>
                </label>
              ))}
            </div>
          </div>

          {/* 옵션 */}
          <div className="flex gap-4">
            <label className="flex items-center gap-2 cursor-pointer">
              <input type="checkbox" className="rounded"
                checked={form.is_active} onChange={e => setForm(f => ({ ...f, is_active: e.target.checked }))} />
              <span className="text-sm text-gray-700">활성화</span>
            </label>
            <label className="flex items-center gap-2 cursor-pointer">
              <input type="checkbox" className="rounded"
                checked={form.is_default} onChange={e => setForm(f => ({ ...f, is_default: e.target.checked }))} />
              <span className="text-sm text-gray-700">기본 AI로 설정</span>
            </label>
          </div>

          {/* 메모 */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">메모 (선택)</label>
            <textarea className="input resize-none" rows={2} placeholder="이 설정에 대한 메모를 입력하세요"
              value={form.description} onChange={e => setForm(f => ({ ...f, description: e.target.value }))} />
          </div>

          {/* 버튼 */}
          <div className="flex gap-3 pt-2">
            <button type="button" onClick={onClose} className="btn-secondary flex-1">취소</button>
            <button type="submit" className="btn-primary flex-1" disabled={mutation.isPending}>
              {mutation.isPending ? <Loader2 size={16} className="animate-spin inline mr-1" /> : null}
              {isEdit ? '저장' : '등록'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

// ─────────────────── 카드 컴포넌트 ───────────────────
function AIConfigCard({
  config,
  provider,
  onEdit,
  onDelete,
  onTest,
  onSetDefault,
}: {
  config: AIConfig;
  provider?: Provider;
  onEdit: () => void;
  onDelete: () => void;
  onTest: () => void;
  onSetDefault: () => void;
}) {
  const [expanded, setExpanded] = useState(false);
  const s = STATUS_MAP[config.status] || STATUS_MAP.inactive;

  return (
    <div className={`bg-white rounded-2xl border-2 shadow-sm transition-all ${
      config.is_default ? 'border-blue-400 ring-2 ring-blue-100' : 'border-gray-100 hover:border-gray-200'
    }`}>
      {/* 상단 헤더 */}
      <div className="p-5">
        <div className="flex items-start justify-between gap-3">
          <div className="flex items-center gap-3">
            <div className="text-3xl">{provider?.icon || '🤖'}</div>
            <div>
              <div className="flex items-center gap-2 flex-wrap">
                <h3 className="font-bold text-gray-900">{config.name}</h3>
                {config.is_default && (
                  <span className="inline-flex items-center gap-1 px-2 py-0.5 bg-blue-100 text-blue-700 text-xs rounded-full font-medium">
                    <Star size={10} fill="currentColor" /> 기본 AI
                  </span>
                )}
                {!config.is_active && (
                  <span className="badge badge-gray">비활성</span>
                )}
              </div>
              <div className="flex items-center gap-2 mt-1 flex-wrap">
                <span className="text-xs text-gray-500">{provider?.label || config.provider}</span>
                <span className="text-gray-300">·</span>
                <span className="text-xs font-mono text-gray-600 bg-gray-100 px-1.5 py-0.5 rounded">{config.model_name}</span>
                <span className={`badge ${s.cls}`}>{s.label}</span>
              </div>
            </div>
          </div>

          {/* 액션 버튼 */}
          <div className="flex items-center gap-1 flex-shrink-0">
            <button onClick={onTest}
              className="p-2 rounded-lg hover:bg-blue-50 text-blue-500 transition-colors"
              title="연결 테스트">
              <Zap size={15} />
            </button>
            {!config.is_default && config.is_active && (
              <button onClick={onSetDefault}
                className="p-2 rounded-lg hover:bg-yellow-50 text-yellow-500 transition-colors"
                title="기본 AI로 설정">
                <Star size={15} />
              </button>
            )}
            <button onClick={onEdit}
              className="p-2 rounded-lg hover:bg-gray-100 text-gray-500 transition-colors"
              title="수정">
              <Edit2 size={15} />
            </button>
            <button onClick={onDelete}
              className="p-2 rounded-lg hover:bg-red-50 text-red-400 transition-colors"
              title="삭제">
              <Trash2 size={15} />
            </button>
          </div>
        </div>

        {/* 사용 범위 태그 */}
        <div className="flex gap-1.5 mt-3 flex-wrap">
          {config.use_for_pc_analysis && <span className="badge badge-blue text-xs">PC 분석</span>}
          {config.use_for_cert_prediction && <span className="badge badge-green text-xs">인증서</span>}
          {config.use_for_security_insights && <span className="badge badge-purple text-xs">보안 인사이트</span>}
          {config.use_for_anomaly_detection && <span className="badge badge-yellow text-xs">이상탐지</span>}
        </div>

        {/* 마지막 테스트 결과 */}
        {config.last_test_result && (
          <div className={`mt-3 p-2.5 rounded-lg text-xs flex items-start gap-2 ${
            config.last_test_success ? 'bg-green-50 text-green-700' : 'bg-red-50 text-red-700'
          }`}>
            {config.last_test_success ? <CheckCircle size={13} className="mt-0.5 flex-shrink-0" /> : <XCircle size={13} className="mt-0.5 flex-shrink-0" />}
            <span>{config.last_test_result}</span>
          </div>
        )}
      </div>

      {/* 상세 정보 토글 */}
      <div className="border-t border-gray-50">
        <button
          onClick={() => setExpanded(!expanded)}
          className="w-full flex items-center justify-between px-5 py-2.5 text-xs text-gray-400 hover:text-gray-600 hover:bg-gray-50 transition-colors"
        >
          <span>상세 정보</span>
          {expanded ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
        </button>

        {expanded && (
          <div className="px-5 pb-5 space-y-3">
            <div className="grid grid-cols-2 gap-3 text-sm">
              <div className="bg-gray-50 rounded-lg p-3">
                <p className="text-xs text-gray-400 mb-0.5">Max Tokens</p>
                <p className="font-semibold text-gray-800">{config.max_tokens.toLocaleString()}</p>
              </div>
              <div className="bg-gray-50 rounded-lg p-3">
                <p className="text-xs text-gray-400 mb-0.5">Temperature</p>
                <p className="font-semibold text-gray-800">{config.temperature}</p>
              </div>
              <div className="bg-gray-50 rounded-lg p-3">
                <p className="text-xs text-gray-400 mb-0.5">총 요청</p>
                <p className="font-semibold text-gray-800">{config.total_requests.toLocaleString()}</p>
              </div>
              <div className="bg-gray-50 rounded-lg p-3">
                <p className="text-xs text-gray-400 mb-0.5">실패</p>
                <p className="font-semibold text-gray-800">{config.failed_requests.toLocaleString()}</p>
              </div>
            </div>
            {config.api_base_url && (
              <div className="bg-gray-50 rounded-lg p-3 text-sm">
                <p className="text-xs text-gray-400 mb-0.5">Base URL</p>
                <p className="font-mono text-gray-700 text-xs break-all">{config.api_base_url}</p>
              </div>
            )}
            {config.last_test_at && (
              <div className="flex items-center gap-1.5 text-xs text-gray-400">
                <Clock size={12} />
                마지막 테스트: {new Date(config.last_test_at).toLocaleString('ko-KR')}
              </div>
            )}
            {config.last_used_at && (
              <div className="flex items-center gap-1.5 text-xs text-gray-400">
                <Activity size={12} />
                마지막 사용: {new Date(config.last_used_at).toLocaleString('ko-KR')}
              </div>
            )}
            {config.description && (
              <p className="text-xs text-gray-500 italic">{config.description}</p>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

// ─────────────────── 메인 페이지 ───────────────────
export default function AISettingsPage() {
  const qc = useQueryClient();
  const [modalOpen, setModalOpen] = useState(false);
  const [editTarget, setEditTarget] = useState<AIConfig | null>(null);
  const [testingId, setTestingId] = useState<number | null>(null);
  const [testResult, setTestResult] = useState<{ id: number; success: boolean; message: string; preview?: string; latency_ms?: number } | null>(null);
  const [filterProvider, setFilterProvider] = useState<string>('all');

  const { data: configsData, isLoading } = useQuery({
    queryKey: ['ai-configs'],
    queryFn: () => aiSettingsApi.getList(),
  });

  const { data: providersData } = useQuery({
    queryKey: ['ai-providers'],
    queryFn: () => aiSettingsApi.getProviders(),
  });

  const { data: statsData } = useQuery({
    queryKey: ['ai-stats'],
    queryFn: () => aiSettingsApi.getStats(),
  });

  const configs: AIConfig[] = configsData?.data?.data || [];
  const providers: Provider[] = providersData?.data?.providers || [];
  const stats = statsData?.data || {};

  const deleteMutation = useMutation({
    mutationFn: (id: number) => aiSettingsApi.delete(id),
    onSuccess: () => {
      toast.success('삭제되었습니다.');
      qc.invalidateQueries({ queryKey: ['ai-configs'] });
      qc.invalidateQueries({ queryKey: ['ai-stats'] });
    },
    onError: () => toast.error('삭제 실패'),
  });

  const setDefaultMutation = useMutation({
    mutationFn: (id: number) => aiSettingsApi.setDefault(id),
    onSuccess: (res) => {
      toast.success(res.data.message);
      qc.invalidateQueries({ queryKey: ['ai-configs'] });
    },
    onError: (e: any) => toast.error(e.response?.data?.detail || '설정 실패'),
  });

  const handleTest = async (id: number) => {
    setTestingId(id);
    setTestResult(null);
    try {
      const res = await aiSettingsApi.test(id);
      const r = res.data;
      setTestResult({ id, success: r.success, message: r.message, preview: r.response_preview, latency_ms: r.latency_ms });
      if (r.success) toast.success(`연결 성공! (${r.latency_ms}ms)`);
      else toast.error('연결 실패: ' + r.message);
    } catch (e: any) {
      toast.error('테스트 중 오류 발생');
    } finally {
      setTestingId(null);
      qc.invalidateQueries({ queryKey: ['ai-configs'] });
    }
  };

  const handleDelete = (id: number, name: string) => {
    if (confirm(`"${name}" 설정을 삭제하시겠습니까?`)) {
      deleteMutation.mutate(id);
    }
  };

  const filteredConfigs = filterProvider === 'all'
    ? configs
    : configs.filter(c => c.provider === filterProvider);

  const providerMap = Object.fromEntries(providers.map(p => [p.key, p]));

  // 제공자별 집계
  const providerCounts = configs.reduce<Record<string, number>>((acc, c) => {
    acc[c.provider] = (acc[c.provider] || 0) + 1;
    return acc;
  }, {});

  return (
    <div className="space-y-6">
      {/* 헤더 */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-bold text-gray-900">AI API 설정 관리</h2>
          <p className="text-sm text-gray-500 mt-0.5">다양한 AI 제공자의 API 키를 등록하고 관리합니다</p>
        </div>
        <button
          onClick={() => { setEditTarget(null); setModalOpen(true); }}
          className="btn-primary flex items-center gap-2"
        >
          <Plus size={16} /> AI 설정 추가
        </button>
      </div>

      {/* 통계 카드 */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="card text-center">
          <p className="text-3xl font-bold text-gray-900">{stats.total ?? 0}</p>
          <p className="text-xs text-gray-500 mt-1">전체 설정</p>
        </div>
        <div className="card text-center">
          <p className="text-3xl font-bold text-green-600">{stats.active ?? 0}</p>
          <p className="text-xs text-gray-500 mt-1">활성 설정</p>
        </div>
        <div className="card text-center">
          <div className="flex justify-center">
            {stats.default ? (
              <span className="text-2xl">{providerMap[stats.default.provider]?.icon || '🤖'}</span>
            ) : (
              <span className="text-2xl text-gray-300">—</span>
            )}
          </div>
          <p className="text-xs text-gray-500 mt-1">
            {stats.default ? stats.default.name : '기본 AI 없음'}
          </p>
          <p className="text-xs text-blue-500 font-medium">기본 AI</p>
        </div>
        <div className="card text-center">
          <p className="text-3xl font-bold text-purple-600">
            {Object.keys(providerCounts).length}
          </p>
          <p className="text-xs text-gray-500 mt-1">등록된 제공자</p>
        </div>
      </div>

      {/* 테스트 결과 알림 */}
      {testResult && (
        <div className={`p-4 rounded-xl border flex items-start gap-3 ${
          testResult.success ? 'bg-green-50 border-green-200' : 'bg-red-50 border-red-200'
        }`}>
          {testResult.success
            ? <CheckCircle size={20} className="text-green-600 flex-shrink-0 mt-0.5" />
            : <XCircle size={20} className="text-red-600 flex-shrink-0 mt-0.5" />}
          <div className="flex-1">
            <p className={`font-medium text-sm ${testResult.success ? 'text-green-800' : 'text-red-800'}`}>
              {testResult.message}
              {testResult.latency_ms && <span className="ml-2 font-normal text-xs opacity-70">({testResult.latency_ms}ms)</span>}
            </p>
            {testResult.preview && (
              <p className="text-xs text-gray-600 mt-1 bg-white/60 px-2 py-1 rounded">
                AI 응답: "{testResult.preview}"
              </p>
            )}
          </div>
          <button onClick={() => setTestResult(null)} className="text-gray-400 hover:text-gray-600">✕</button>
        </div>
      )}

      {/* 필터 탭 */}
      <div className="flex gap-2 flex-wrap">
        <button
          onClick={() => setFilterProvider('all')}
          className={`px-3 py-1.5 rounded-lg text-sm font-medium transition-all ${
            filterProvider === 'all' ? 'bg-blue-600 text-white' : 'bg-white text-gray-600 border border-gray-200 hover:bg-gray-50'
          }`}
        >
          전체 ({configs.length})
        </button>
        {providers.filter(p => providerCounts[p.key]).map(p => (
          <button
            key={p.key}
            onClick={() => setFilterProvider(p.key)}
            className={`px-3 py-1.5 rounded-lg text-sm font-medium transition-all flex items-center gap-1.5 ${
              filterProvider === p.key ? 'bg-blue-600 text-white' : 'bg-white text-gray-600 border border-gray-200 hover:bg-gray-50'
            }`}
          >
            <span>{p.icon}</span> {p.label} ({providerCounts[p.key]})
          </button>
        ))}
      </div>

      {/* 설정 목록 */}
      {isLoading ? (
        <div className="flex justify-center py-16">
          <Loader2 size={32} className="animate-spin text-blue-500" />
        </div>
      ) : filteredConfigs.length === 0 ? (
        <div className="card text-center py-16">
          <Bot size={48} className="text-gray-200 mx-auto mb-4" />
          <p className="text-gray-500 font-medium">등록된 AI 설정이 없습니다</p>
          <p className="text-gray-400 text-sm mt-1">
            {filterProvider !== 'all' ? '다른 제공자를 선택하거나 ' : ''}
            AI 설정 추가 버튼으로 첫 번째 AI를 등록하세요
          </p>
          <button
            onClick={() => { setEditTarget(null); setModalOpen(true); }}
            className="btn-primary mt-4 inline-flex items-center gap-2"
          >
            <Plus size={16} /> AI 설정 추가
          </button>
        </div>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          {filteredConfigs.map(cfg => (
            <AIConfigCard
              key={cfg.id}
              config={cfg}
              provider={providerMap[cfg.provider]}
              onEdit={() => { setEditTarget(cfg); setModalOpen(true); }}
              onDelete={() => handleDelete(cfg.id, cfg.name)}
              onTest={() => handleTest(cfg.id)}
              onSetDefault={() => setDefaultMutation.mutate(cfg.id)}
            />
          ))}
        </div>
      )}

      {/* 지원 제공자 안내 (설정이 없을 때만) */}
      {configs.length === 0 && !isLoading && (
        <div className="card">
          <h3 className="font-semibold text-gray-900 mb-4 flex items-center gap-2">
            <Info size={18} className="text-blue-500" /> 지원 AI 제공자
          </h3>
          <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
            {providers.map(p => (
              <div key={p.key}
                className="flex items-start gap-3 p-3 rounded-xl border border-gray-100 hover:bg-gray-50 cursor-pointer transition-colors"
                onClick={() => { setEditTarget(null); setModalOpen(true); }}
              >
                <span className="text-2xl">{p.icon}</span>
                <div>
                  <p className="font-medium text-sm text-gray-900">{p.label}</p>
                  <p className="text-xs text-gray-400 mt-0.5 line-clamp-2">{p.description}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* 도움말 */}
      <div className="card bg-gradient-to-r from-blue-50 to-purple-50 border-blue-100">
        <div className="flex items-start gap-3">
          <div className="w-8 h-8 rounded-lg bg-blue-100 flex items-center justify-center flex-shrink-0">
            <Key size={16} className="text-blue-600" />
          </div>
          <div>
            <p className="font-semibold text-gray-900 text-sm">API 키 보안 안내</p>
            <ul className="text-xs text-gray-500 mt-1.5 space-y-1">
              <li>• API 키는 DB에 저장되며 화면에서는 마스킹(***)되어 표시됩니다</li>
              <li>• 기본 AI로 설정된 설정이 PC 보안 분석, 인증서 예측 등 모든 AI 기능에 사용됩니다</li>
              <li>• 연결 테스트로 API 키 유효성을 사전에 확인하세요</li>
              <li>• Ollama는 별도의 서버 구축이 필요합니다 (자체 서버 실행 후 Base URL 입력)</li>
            </ul>
          </div>
        </div>
      </div>

      {/* 모달 */}
      {modalOpen && (
        <AIConfigModal
          providers={providers}
          existing={editTarget}
          onClose={() => { setModalOpen(false); setEditTarget(null); }}
        />
      )}
    </div>
  );
}
