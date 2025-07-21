import React from 'react';
import { NavLink, Outlet } from 'react-router-dom';
import { 
  HomeIcon, 
  BriefcaseIcon, 
  DocumentTextIcon, 
  CogIcon,
  ChartBarIcon,
  PlayIcon,
  PauseIcon,
  UserIcon
} from '@heroicons/react/24/outline';
import { Toaster } from 'react-hot-toast';

const navigation = [
  { name: 'Dashboard', href: '/', icon: HomeIcon },
  { name: 'Trabajos', href: '/jobs', icon: BriefcaseIcon },
  { name: 'Postulaciones', href: '/applications', icon: DocumentTextIcon },
  { name: 'Mi CV', href: '/cv', icon: UserIcon },
  { name: 'Configuración', href: '/settings', icon: CogIcon },
  { name: 'Estadísticas', href: '/stats', icon: ChartBarIcon },
];

export default function Layout({ isSearching, onToggleSearch }) {
  return (
    <div className="min-h-screen bg-gray-50">
      <Toaster position="top-right" />
      
      {/* Sidebar */}
      <div className="fixed inset-y-0 left-0 z-50 w-64 bg-white shadow-lg">
        <div className="flex h-16 shrink-0 items-center px-6 border-b border-gray-200">
          <h1 className="text-xl font-bold text-gray-900">AutoPostulador</h1>
          <span className="ml-2 inline-flex items-center px-2 py-1 text-xs font-medium bg-blue-100 text-blue-800 rounded-full">
            Chile
          </span>
        </div>
        
        <nav className="flex flex-1 flex-col p-4">
          <ul role="list" className="flex flex-1 flex-col gap-y-2">
            {navigation.map((item) => (
              <li key={item.name}>
                <NavLink
                  to={item.href}
                  className={({ isActive }) =>
                    `group flex gap-x-3 rounded-md p-3 text-sm leading-6 font-semibold transition-colors ${
                      isActive
                        ? 'bg-blue-50 text-blue-700'
                        : 'text-gray-700 hover:text-blue-700 hover:bg-gray-50'
                    }`
                  }
                >
                  <item.icon className="h-5 w-5 shrink-0" />
                  {item.name}
                </NavLink>
              </li>
            ))}
          </ul>
          
          {/* Control de búsqueda */}
          <div className="mt-8 p-4 bg-gray-50 rounded-lg">
            <div className="flex items-center justify-between mb-3">
              <span className="text-sm font-medium text-gray-700">
                Búsqueda Automática
              </span>
              <div className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${
                isSearching 
                  ? 'bg-green-100 text-green-800' 
                  : 'bg-gray-100 text-gray-800'
              }`}>
                {isSearching ? 'Activa' : 'Inactiva'}
              </div>
            </div>
            
            <button
              onClick={onToggleSearch}
              className={`w-full flex items-center justify-center gap-2 px-3 py-2 text-sm font-medium rounded-md transition-colors ${
                isSearching
                  ? 'bg-red-600 text-white hover:bg-red-700'
                  : 'bg-blue-600 text-white hover:bg-blue-700'
              }`}
            >
              {isSearching ? (
                <>
                  <PauseIcon className="h-4 w-4" />
                  Detener
                </>
              ) : (
                <>
                  <PlayIcon className="h-4 w-4" />
                  Iniciar
                </>
              )}
            </button>
          </div>
        </nav>
      </div>

      {/* Main content */}
      <div className="pl-64">
        <div className="px-6 py-8">
          <Outlet />
        </div>
      </div>
    </div>
  );
}