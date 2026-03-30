import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { notificationApi } from '../api/client';
import { Bell, Check, CheckCheck, Trash2, AlertTriangle, Shield, Monitor, Info, Bot, RefreshCw } from 'lucide-react';
import toast from 'react-hot-toast';
import { format } from 'date-fns';
import { ko } from 'date-fns/locale';

const typeIcon: Record<string, React.ReactNode> = {
  certificate_expiry: <AlertTriangle size={16} className="text-yellow-500" />,
  security_alert: <Shield size={16} className="text-red-500" />,
  pc_offline: <Monitor size={16} className="text-gray-500" />,
  unauthorized_app: <AlertTriangle size={16} className="text-orange-500" />,
  ai_insight: <Bot size={16} className="text-purple-500" />,
  general: <Info size={16} className="text-blue-500" />,
};

const priorityClass: Record<string, string> = {
  critical: 'border-l-red-500',
  high: 'border-l-orange-400',
  medium: 'border-l-yellow-400',
  low: 'border-l-blue-300',
};

export default function NotificationsPage() {
  const [filter, setFilter] = useState<'all' | 'unread'>('all');
  const qc = useQueryClient();

  const { data, isLoading } = useQuery({
    queryKey: ['notifications', filter],
    queryFn: () => notificationApi.getList({ is_read: filter === 'unread' ? false : undefined, limit: 50 }),
    refetchInterval: 30000,
  });

  const markReadMutation = useMutation({
    mutationFn: (id: number) => notificationApi.markRead(id),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['notifications'] }); qc.invalidateQueries({ queryKey: ['notifications-count'] }); },
  });

  const markAllMutation = useMutation({
    mutationFn: () => notificationApi.markAllRead(),
    onSuccess: () => {
      toast.success('모든 알림이 읽음 처리되었습니다.');
      qc.invalidateQueries({ queryKey: ['notifications'] });
      qc.invalidateQueries({ queryKey: ['notifications-count'] });
    },
  });

  const deleteMutation = useMutation({
    mutationFn: (id: number) => notificationApi.delete(id),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['notifications'] }); },
  });

  const notifications = data?.data?.items || [];
  const unreadCount = data?.data?.unread_count || 0;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="card flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center">
            <Bell size={18} className="text-white" />
          </div>
          <div>
            <h2 className="font-semibold text-gray-900">알림 센터</h2>
            <p className="text-sm text-gray-500">미읽음 {unreadCount}건</p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <div className="flex rounded-lg border border-gray-200 overflow-hidden">
            <button
              onClick={() => setFilter('all')}
              className={`px-3 py-1.5 text-sm ${filter === 'all' ? 'bg-blue-600 text-white' : 'bg-white text-gray-600 hover:bg-gray-50'}`}
            >
              전체
            </button>
            <button
              onClick={() => setFilter('unread')}
              className={`px-3 py-1.5 text-sm ${filter === 'unread' ? 'bg-blue-600 text-white' : 'bg-white text-gray-600 hover:bg-gray-50'}`}
            >
              미읽음
            </button>
          </div>
          {unreadCount > 0 && (
            <button onClick={() => markAllMutation.mutate()} className="btn-secondary flex items-center gap-2 text-sm">
              <CheckCheck size={14} />모두 읽음
            </button>
          )}
        </div>
      </div>

      {/* Notifications List */}
      <div className="space-y-2">
        {isLoading ? (
          <div className="flex items-center justify-center h-40"><RefreshCw className="animate-spin text-blue-600" size={24} /></div>
        ) : notifications.length === 0 ? (
          <div className="card text-center py-12">
            <Bell size={40} className="text-gray-300 mx-auto mb-3" />
            <p className="text-gray-400">알림이 없습니다.</p>
          </div>
        ) : (
          notifications.map((notif: any) => (
            <div
              key={notif.id}
              className={`bg-white border-l-4 ${priorityClass[notif.priority] || 'border-l-gray-300'} rounded-r-xl shadow-sm p-4 ${!notif.is_read ? 'bg-blue-50/30' : ''} transition-colors`}
            >
              <div className="flex items-start gap-3">
                <div className="mt-0.5 flex-shrink-0">
                  {typeIcon[notif.type] || <Info size={16} />}
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-start justify-between gap-2">
                    <p className={`text-sm font-medium ${!notif.is_read ? 'text-gray-900' : 'text-gray-600'}`}>
                      {notif.title}
                    </p>
                    <div className="flex items-center gap-1 flex-shrink-0">
                      {!notif.is_read && (
                        <span className="w-2 h-2 bg-blue-600 rounded-full flex-shrink-0"></span>
                      )}
                      <span className={`badge text-xs ${
                        notif.priority === 'critical' ? 'badge-red' :
                        notif.priority === 'high' ? 'badge-yellow' :
                        notif.priority === 'medium' ? 'badge-blue' : 'badge-gray'
                      }`}>
                        {notif.priority === 'critical' ? '긴급' : notif.priority === 'high' ? '높음' : notif.priority === 'medium' ? '보통' : '낮음'}
                      </span>
                    </div>
                  </div>
                  <p className="text-sm text-gray-500 mt-0.5">{notif.message}</p>
                  <p className="text-xs text-gray-400 mt-2">
                    {format(new Date(notif.created_at), 'yyyy년 MM월 dd일 HH:mm', { locale: ko })}
                  </p>
                </div>
                <div className="flex items-center gap-1 flex-shrink-0">
                  {!notif.is_read && (
                    <button
                      onClick={() => markReadMutation.mutate(notif.id)}
                      className="p-1.5 hover:bg-green-50 rounded-lg text-green-600 transition-colors"
                      title="읽음 처리"
                    >
                      <Check size={14} />
                    </button>
                  )}
                  <button
                    onClick={() => deleteMutation.mutate(notif.id)}
                    className="p-1.5 hover:bg-red-50 rounded-lg text-red-400 transition-colors"
                    title="삭제"
                  >
                    <Trash2 size={14} />
                  </button>
                </div>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
}
