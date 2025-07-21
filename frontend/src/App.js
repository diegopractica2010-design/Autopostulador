import React, { useState, useEffect } from "react";
import "./App.css";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import Layout from "./components/Layout";
import Dashboard from "./pages/Dashboard";
import { applicationsAPI, healthAPI } from "./services/api";
import toast from 'react-hot-toast';

// Páginas placeholder
const JobsPage = () => (
  <div className="bg-white shadow rounded-lg p-6">
    <h1 className="text-2xl font-bold text-gray-900 mb-4">Trabajos Encontrados</h1>
    <p className="text-gray-500">Lista de trabajos será mostrada aquí...</p>
  </div>
);

const ApplicationsPage = () => (
  <div className="bg-white shadow rounded-lg p-6">
    <h1 className="text-2xl font-bold text-gray-900 mb-4">Mis Postulaciones</h1>
    <p className="text-gray-500">Lista de postulaciones será mostrada aquí...</p>
  </div>
);

const CVPage = () => (
  <div className="bg-white shadow rounded-lg p-6">
    <h1 className="text-2xl font-bold text-gray-900 mb-4">Gestión de CV</h1>
    <p className="text-gray-500">Gestión de CVs será mostrada aquí...</p>
  </div>
);

const SettingsPage = () => (
  <div className="bg-white shadow rounded-lg p-6">
    <h1 className="text-2xl font-bold text-gray-900 mb-4">Configuración</h1>
    <p className="text-gray-500">Configuraciones del sistema será mostrada aquí...</p>
  </div>
);

const StatsPage = () => (
  <div className="bg-white shadow rounded-lg p-6">
    <h1 className="text-2xl font-bold text-gray-900 mb-4">Estadísticas</h1>
    <p className="text-gray-500">Estadísticas detalladas serán mostradas aquí...</p>
  </div>
);

function App() {
  const [isSearching, setIsSearching] = useState(false);
  const [isConnected, setIsConnected] = useState(false);
  const userId = "user-demo-123"; // Usuario demo para desarrollo

  useEffect(() => {
    // Verificar conexión con el backend
    checkConnection();
  }, []);

  const checkConnection = async () => {
    try {
      await healthAPI.root();
      setIsConnected(true);
      console.log('✅ Conectado al backend correctamente');
    } catch (error) {
      setIsConnected(false);
      console.error('❌ Error conectando al backend:', error);
    }
  };

  const handleToggleSearch = async () => {
    try {
      if (isSearching) {
        await applicationsAPI.stopSearch(userId);
        setIsSearching(false);
        toast.success('Búsqueda automática detenida');
      } else {
        await applicationsAPI.startSearch(userId);
        setIsSearching(true);
        toast.success('Búsqueda automática iniciada');
      }
    } catch (error) {
      console.error('Error toggling search:', error);
      toast.error('Error al cambiar estado de búsqueda');
    }
  };

  return (
    <div className="App">
      <BrowserRouter>
        <Routes>
          <Route 
            path="/" 
            element={
              <Layout 
                isSearching={isSearching}
                onToggleSearch={handleToggleSearch}
              />
            }
          >
            <Route index element={<Dashboard />} />
            <Route path="jobs" element={<JobsPage />} />
            <Route path="applications" element={<ApplicationsPage />} />
            <Route path="cv" element={<CVPage />} />
            <Route path="settings" element={<SettingsPage />} />
            <Route path="stats" element={<StatsPage />} />
          </Route>
        </Routes>
      </BrowserRouter>
      
      {/* Connection Status Indicator */}
      <div className={`fixed top-4 right-4 z-50 px-3 py-1 rounded-full text-sm font-medium ${
        isConnected 
          ? 'bg-green-100 text-green-800' 
          : 'bg-red-100 text-red-800'
      }`}>
        {isConnected ? '🟢 Conectado' : '🔴 Desconectado'}
      </div>
    </div>
  );
}

export default App;