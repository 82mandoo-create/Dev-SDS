import React, { useState } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import {
  LayoutDashboard, Users, Shield, Monitor, Bell, Settings,
  LogOut, Menu, X, ChevronDown, Building2, Activity, Lock,
  Cpu, AlertTriangle, FileCheck, Bot, User, KeyRound
} from 'lucide-react';
import { useAuthStore } from '../stores/authStore';
import { useQuery } from '@tanstack/react-query';
import { notificationApi } from '../api/client';

const menuItems = [
  { path: '/dashboard', icon: LayoutDashboard, label: '대시보드', roles: ['admin', 'manager', 'user'] },
  { path: '/employees', icon: Users, label: '직원 관리', roles: ['admin', 'manager'] },
  { path: '/certificates', icon: FileCheck, label: '인증서 관리', roles: ['admin', 'manager', 'user'] },
  { path: '/pcs', icon: Monitor, label: 'PC 관리', roles: ['admin', 'manager'] },
  { path: '/security', icon: Shield, label: '보안 관리', roles: ['admin', 'manager'] },
  { path: '/ai-analysis', icon: Bot, label: 'AI 분석', roles: ['admin', 'manager'] },
  { path: '/notifications', icon: Bell, label: '알림', roles: ['admin', 'manager', 'user'] },
  { path: '/users', icon: User, label: '사용자 관리', roles: ['admin'] },
  { path: '/ai-settings', icon: KeyRound, label: 'AI API 설정', roles: ['admin'] },
  { path: '/settings', icon: Settings, label: '설정', roles: ['admin'] },
];

interface LayoutProps { children: React.ReactNode; }

export default function Layout({ children }: LayoutProps) {
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [profileOpen, setProfileOpen] = useState(false);
  const location = useLocation();
  const navigate = useNavigate();
  const { user, logout } = useAuthStore();

  const { data: notifData } = useQuery({
    queryKey: ['notifications-count'],
    queryFn: () => notificationApi.getList({ is_read: false, limit: 1 }),
    refetchInterval: 30000,
  });

  const unreadCount = notifData?.data?.unread_count || 0;

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  const filteredMenu = menuItems.filter(
    item => item.roles.includes(user?.role || 'user')
  );

  return (
    <div className="flex h-screen bg-gray-50 overflow-hidden">
      {/* Sidebar */}
      <aside className={`${sidebarOpen ? 'w-64' : 'w-16'} transition-all duration-300 bg-white border-r border-gray-100 flex flex-col shadow-sm z-20`}>
        {/* Logo */}
        <div className="h-16 flex items-center px-4 border-b border-gray-100">
          <div className="flex items-center gap-3 flex-1">
            <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-blue-600 to-purple-600 flex items-center justify-center flex-shrink-0">
              <Shield size={16} className="text-white" />
            </div>
            {sidebarOpen && (
              <span className="font-bold text-gray-900 text-sm leading-tight">
                Asset<span className="gradient-text">Guard</span>
              </span>
            )}
          </div>
          <button
            onClick={() => setSidebarOpen(!sidebarOpen)}
            className="p-1 rounded hover:bg-gray-100 text-gray-400"
          >
            {sidebarOpen ? <X size={16} /> : <Menu size={16} />}
          </button>
        </div>

        {/* Navigation */}
        <nav className="flex-1 p-3 space-y-1 overflow-y-auto">
          {filteredMenu.map((item) => {
            const Icon = item.icon;
            const isActive = location.pathname.startsWith(item.path);
            return (
              <Link
                key={item.path}
                to={item.path}
                className={`sidebar-item ${isActive ? 'active' : ''} ${!sidebarOpen ? 'justify-center' : ''}`}
                title={!sidebarOpen ? item.label : undefined}
              >
                <div className="relative flex-shrink-0">
                  <Icon size={18} />
                  {item.path === '/notifications' && unreadCount > 0 && (
                    <span className="absolute -top-1 -right-1 w-4 h-4 bg-red-500 text-white text-xs rounded-full flex items-center justify-center">
                      {unreadCount > 9 ? '9+' : unreadCount}
                    </span>
                  )}
                </div>
                {sidebarOpen && <span>{item.label}</span>}
              </Link>
            );
          })}
        </nav>

        {/* User info */}
        <div className="p-3 border-t border-gray-100">
          <div
            className={`flex items-center gap-3 p-2 rounded-lg hover:bg-gray-50 cursor-pointer ${!sidebarOpen ? 'justify-center' : ''}`}
            onClick={() => setProfileOpen(!profileOpen)}
          >
            <div className="w-8 h-8 rounded-full bg-gradient-to-br from-blue-400 to-purple-500 flex items-center justify-center flex-shrink-0 text-white text-sm font-medium">
              {user?.full_name?.charAt(0) || 'U'}
            </div>
            {sidebarOpen && (
              <>
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium text-gray-900 truncate">{user?.full_name}</p>
                  <p className="text-xs text-gray-500 truncate">{user?.role === 'admin' ? '관리자' : user?.role === 'manager' ? '매니저' : '사용자'}</p>
                </div>
                <ChevronDown size={14} className="text-gray-400" />
              </>
            )}
          </div>
          {profileOpen && sidebarOpen && (
            <div className="mt-1 bg-white rounded-lg border border-gray-100 shadow-lg overflow-hidden">
              <Link to="/profile" className="flex items-center gap-2 px-3 py-2 text-sm text-gray-700 hover:bg-gray-50">
                <Settings size={14} />내 설정
              </Link>
              <button
                onClick={handleLogout}
                className="w-full flex items-center gap-2 px-3 py-2 text-sm text-red-600 hover:bg-red-50"
              >
                <LogOut size={14} />로그아웃
              </button>
            </div>
          )}
        </div>
      </aside>

      {/* Main content */}
      <main className="flex-1 flex flex-col overflow-hidden">
        {/* Header */}
        <header className="h-16 bg-white border-b border-gray-100 flex items-center justify-between px-6 flex-shrink-0">
          <div>
            <h1 className="text-lg font-semibold text-gray-900">
              {filteredMenu.find(m => location.pathname.startsWith(m.path))?.label || 'AssetGuard'}
            </h1>
          </div>
          <div className="flex items-center gap-3">
            <Link to="/notifications" className="relative p-2 rounded-lg hover:bg-gray-100 text-gray-500">
              <Bell size={18} />
              {unreadCount > 0 && (
                <span className="absolute top-1 right-1 w-2 h-2 bg-red-500 rounded-full"></span>
              )}
            </Link>
            <div className="h-6 w-px bg-gray-200"></div>
            <div className="flex items-center gap-2">
              <div className="w-8 h-8 rounded-full bg-gradient-to-br from-blue-400 to-purple-500 flex items-center justify-center text-white text-sm font-medium">
                {user?.full_name?.charAt(0) || 'U'}
              </div>
              <span className="text-sm font-medium text-gray-700">{user?.full_name}</span>
            </div>
          </div>
        </header>

        {/* Page content */}
        <div className="flex-1 overflow-y-auto p-6">
          {children}
        </div>
      </main>
    </div>
  );
}
