import { useState, useEffect, createContext, useContext } from "react";
import { BrowserRouter, Routes, Route, Navigate, useNavigate } from "react-router-dom";
import axios from "axios";
import { Toaster, toast } from "sonner";
import Login from "./pages/Login";
import Register from "./pages/Register";
import Dashboard from "./pages/Dashboard";
import NewDeployment from "./pages/NewDeployment";
import DeploymentDetails from "./pages/DeploymentDetails";
import VPSManagement from "./pages/VPSManagement";
import AdminUsers from "./pages/AdminUsers";
import "./App.css";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
export const API = `${BACKEND_URL}/api`;

// Auth Context
const AuthContext = createContext(null);

export const useAuth = () => useContext(AuthContext);

const api = axios.create({ baseURL: API });

api.interceptors.request.use((config) => {
  const token = localStorage.getItem("token");
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem("token");
      localStorage.removeItem("user");
      window.location.href = "/login";
    }
    return Promise.reject(error);
  }
);

export { api };

function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const token = localStorage.getItem("token");
    const savedUser = localStorage.getItem("user");
    if (token && savedUser) {
      setUser(JSON.parse(savedUser));
    }
    setLoading(false);
  }, []);

  const login = async (email, password) => {
    const response = await api.post("/auth/login", { email, password });
    const { access_token, user } = response.data;
    localStorage.setItem("token", access_token);
    localStorage.setItem("user", JSON.stringify(user));
    setUser(user);
    return user;
  };

  const register = async (name, email, password) => {
    const response = await api.post("/auth/register", { name, email, password });
    const { access_token, user } = response.data;
    localStorage.setItem("token", access_token);
    localStorage.setItem("user", JSON.stringify(user));
    setUser(user);
    return user;
  };

  const logout = () => {
    localStorage.removeItem("token");
    localStorage.removeItem("user");
    setUser(null);
  };

  return (
    <AuthContext.Provider value={{ user, login, register, logout, loading }}>
      {children}
    </AuthContext.Provider>
  );
}

function PrivateRoute({ children }) {
  const { user, loading } = useAuth();
  
  if (loading) {
    return (
      <div className="min-h-screen bg-[#09090b] flex items-center justify-center">
        <div className="w-8 h-8 border-2 border-green-500 border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }
  
  return user ? children : <Navigate to="/login" />;
}

function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Toaster 
          theme="dark" 
          position="top-right"
          toastOptions={{
            style: { background: '#18181b', border: '1px solid #27272a', color: '#fafafa' }
          }}
        />
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route path="/register" element={<Register />} />
          <Route path="/" element={<PrivateRoute><Dashboard /></PrivateRoute>} />
          <Route path="/deploy/new" element={<PrivateRoute><NewDeployment /></PrivateRoute>} />
          <Route path="/deploy/:id" element={<PrivateRoute><DeploymentDetails /></PrivateRoute>} />
          <Route path="/vps" element={<PrivateRoute><VPSManagement /></PrivateRoute>} />
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  );
}

export default App;
