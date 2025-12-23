// frontend/src/context/AuthContext.js
import React, { createContext, useState, useContext, useEffect } from 'react';

const AuthContext = createContext();

export const useAuth = () => {
  return useContext(AuthContext);
};

export const AuthProvider = ({ children }) => {
  const [farmer, setFarmer] = useState(null);
  const [token, setToken] = useState(localStorage.getItem('token'));
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Check if user is logged in
    if (token) {
      fetchFarmerProfile();
    } else {
      setLoading(false);
    }
  }, [token]);

  const fetchFarmerProfile = async () => {
    try {
      const response = await fetch('/api/farmer/profile', {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (response.ok) {
        const data = await response.json();
        setFarmer(data.data);
      }
    } catch (error) {
      console.error('Failed to fetch farmer profile:', error);
      logout();
    } finally {
      setLoading(false);
    }
  };

  const login = async (phone, password) => {
    try {
      const response = await fetch('/api/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ phone, password })
      });
      
      if (response.ok) {
        const data = await response.json();
        localStorage.setItem('token', data.data.access_token);
        setToken(data.data.access_token);
        setFarmer(data.data);
        return { success: true };
      }
      return { success: false, error: 'Login failed' };
    } catch (error) {
      return { success: false, error: error.message };
    }
  };

  const logout = () => {
    localStorage.removeItem('token');
    setToken(null);
    setFarmer(null);
  };

  const value = {
    farmer,
    token,
    login,
    logout,
    loading
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
};
