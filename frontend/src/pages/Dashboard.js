import React, { useState, useEffect } from 'react';
import { 
  BriefcaseIcon, 
  DocumentTextIcon, 
  CheckCircleIcon,
  ClockIcon,
  ChartBarIcon,
  EyeIcon
} from '@heroicons/react/24/outline';
import { statsAPI, jobsAPI, applicationsAPI } from '../services/api';

const StatCard = ({ title, value, icon: Icon, color = "blue", change = null }) => (
  <div className="bg-white overflow-hidden shadow rounded-lg">
    <div className="p-5">
      <div className="flex items-center">
        <div className="flex-shrink-0">
          <Icon className={`h-6 w-6 text-${color}-600`} />
        </div>
        <div className="ml-5 w-0 flex-1">
          <dl>
            <dt className="text-sm font-medium text-gray-500 truncate">
              {title}
            </dt>
            <dd className="text-lg font-medium text-gray-900">
              {value}
              {change && (
                <span className={`ml-2 text-sm ${change > 0 ? 'text-green-600' : 'text-red-600'}`}>
                  {change > 0 ? '+' : ''}{change}%
                </span>
              )}
            </dd>
          </dl>
        </div>
      </div>
    </div>
  </div>
);

const RecentActivity = ({ activities }) => (
  <div className="bg-white shadow rounded-lg">
    <div className="px-4 py-5 sm:p-6">
      <h3 className="text-lg leading-6 font-medium text-gray-900 mb-4">
        Actividad Reciente
      </h3>
      
      {activities.length === 0 ? (
        <p className="text-gray-500 text-center py-4">
          No hay actividad reciente
        </p>
      ) : (
        <div className="flow-root">
          <ul className="-mb-8">
            {activities.map((activity, activityIdx) => (
              <li key={activity.id}>
                <div className="relative pb-8">
                  {activityIdx !== activities.length - 1 ? (
                    <span
                      className="absolute top-4 left-4 -ml-px h-full w-0.5 bg-gray-200"
                      aria-hidden="true"
                    />
                  ) : null}
                  <div className="relative flex space-x-3">
                    <div>
                      <span className={`h-8 w-8 rounded-full bg-${activity.color}-500 flex items-center justify-center ring-8 ring-white`}>
                        <activity.icon className="h-4 w-4 text-white" />
                      </span>
                    </div>
                    <div className="min-w-0 flex-1 pt-1.5">
                      <div>
                        <p className="text-sm text-gray-500">
                          {activity.content}{' '}
                          <span className="font-medium text-gray-900">
                            {activity.target}
                          </span>
                        </p>
                        <p className="mt-0.5 text-xs text-gray-400">
                          {activity.date}
                        </p>
                      </div>
                    </div>
                  </div>
                </div>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  </div>
);

export default function Dashboard() {
  const [stats, setStats] = useState(null);
  const [recentJobs, setRecentJobs] = useState([]);
  const [recentApplications, setRecentApplications] = useState([]);
  const [loading, setLoading] = useState(true);

  // Usuario dummy para desarrollo
  const userId = "user-demo-123";

  useEffect(() => {
    loadDashboardData();
  }, []);

  const loadDashboardData = async () => {
    try {
      setLoading(true);
      
      // Cargar estadísticas
      const statsResponse = await statsAPI.get(userId);
      setStats(statsResponse.data);
      
      // Cargar trabajos recientes
      const jobsResponse = await jobsAPI.getAll(userId, { limit: 5 });
      setRecentJobs(jobsResponse.data);
      
      // Cargar postulaciones recientes
      const appsResponse = await applicationsAPI.getAll(userId, { limit: 5 });
      setRecentApplications(appsResponse.data);
      
    } catch (error) {
      console.error('Error loading dashboard:', error);
      // Datos mock para desarrollo
      setStats({
        total_applications: 0,
        total_jobs_found: 0,
        applications_by_status: {},
        applications_by_portal: {},
        success_rate: 0
      });
      setRecentJobs([]);
      setRecentApplications([]);
    } finally {
      setLoading(false);
    }
  };

  // Generar actividades recientes basadas en datos
  const generateRecentActivities = () => {
    const activities = [];
    
    recentApplications.slice(0, 3).forEach((app, index) => {
      activities.push({
        id: `app-${app.id}`,
        content: 'Postulación enviada a',
        target: app.job_id, // Sería mejor tener el nombre de la empresa
        date: new Date(app.created_at).toLocaleDateString('es-CL'),
        icon: DocumentTextIcon,
        color: 'blue'
      });
    });
    
    recentJobs.slice(0, 2).forEach((job, index) => {
      activities.push({
        id: `job-${job.id}`,
        content: 'Nuevo trabajo encontrado en',
        target: job.company,
        date: new Date(job.scraped_at).toLocaleDateString('es-CL'),
        icon: BriefcaseIcon,
        color: 'green'
      });
    });
    
    return activities.sort((a, b) => new Date(b.date) - new Date(a.date));
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  const activities = generateRecentActivities();

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Dashboard</h1>
        <p className="mt-1 text-sm text-gray-500">
          Resumen de tu búsqueda laboral automatizada
        </p>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-4">
        <StatCard
          title="Trabajos Encontrados"
          value={stats.total_jobs_found}
          icon={BriefcaseIcon}
          color="blue"
        />
        <StatCard
          title="Postulaciones Enviadas"
          value={stats.total_applications}
          icon={DocumentTextIcon}
          color="green"
        />
        <StatCard
          title="Tasa de Éxito"
          value={`${stats.success_rate.toFixed(1)}%`}
          icon={ChartBarIcon}
          color="purple"
        />
        <StatCard
          title="Pendientes"
          value={stats.applications_by_status?.pending || 0}
          icon={ClockIcon}
          color="yellow"
        />
      </div>

      {/* Portales Stats */}
      <div className="bg-white shadow rounded-lg">
        <div className="px-4 py-5 sm:p-6">
          <h3 className="text-lg leading-6 font-medium text-gray-900 mb-4">
            Postulaciones por Portal
          </h3>
          
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
            {Object.entries(stats.applications_by_portal || {}).map(([portal, count]) => (
              <div key={portal} className="text-center">
                <div className="text-2xl font-bold text-gray-900">{count}</div>
                <div className="text-sm text-gray-500 capitalize">{portal}</div>
              </div>
            ))}
          </div>
          
          {Object.keys(stats.applications_by_portal || {}).length === 0 && (
            <p className="text-center text-gray-500 py-4">
              Aún no hay postulaciones registradas
            </p>
          )}
        </div>
      </div>

      {/* Recent Activity */}
      <RecentActivity activities={activities} />

      {/* Quick Actions */}
      <div className="bg-white shadow rounded-lg">
        <div className="px-4 py-5 sm:p-6">
          <h3 className="text-lg leading-6 font-medium text-gray-900 mb-4">
            Acciones Rápidas
          </h3>
          
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            <button 
              className="bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700 transition-colors"
              onClick={() => window.location.href = '/cv'}
            >
              Actualizar CV
            </button>
            <button 
              className="bg-green-600 text-white px-4 py-2 rounded-md hover:bg-green-700 transition-colors"
              onClick={() => window.location.href = '/settings'}
            >
              Configurar IA
            </button>
            <button 
              className="bg-purple-600 text-white px-4 py-2 rounded-md hover:bg-purple-700 transition-colors"
              onClick={() => window.location.href = '/jobs'}
            >
              Ver Trabajos
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}