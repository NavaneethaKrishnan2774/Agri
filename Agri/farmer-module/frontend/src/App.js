// frontend/src/App.js
import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import CssBaseline from '@mui/material/CssBaseline';
import { AuthProvider } from './context/AuthContext';
import FarmerDashboard from './components/FarmerDashboard';

// Create theme
const theme = createTheme({
  palette: {
    primary: {
      main: '#2e7d32', // Green for agriculture
    },
    secondary: {
      main: '#ff9800', // Orange
    },
  },
});

function App() {
  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <AuthProvider>
        <Router>
          <div className="App">
            <Routes>
              <Route path="/" element={<Navigate to="/farmer/dashboard" />} />
              <Route path="/farmer/dashboard" element={<FarmerDashboard />} />
              <Route path="/farmer/products/upload" element={<div>Product Upload Page</div>} />
              <Route path="/farmer/buyers/matches" element={<div>Buyer Matches Page</div>} />
              <Route path="/farmer/community" element={<div>Community Page</div>} />
              <Route path="/farmer/notifications" element={<div>Notifications Page</div>} />
              <Route path="/farmer/security" element={<div>Security Page</div>} />
            </Routes>
          </div>
        </Router>
      </AuthProvider>
    </ThemeProvider>
  );
}

export default App;
