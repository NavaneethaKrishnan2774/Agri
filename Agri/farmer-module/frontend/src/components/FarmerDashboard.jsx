// frontend/src/components/FarmerDashboard.jsx
import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import {
  Card,
  Grid,
  Typography,
  Button,
  Chip,
  Alert,
  CircularProgress,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper
} from '@mui/material';
import {
  LocalShipping,
  Security,
  People,
  AttachMoney,
  Notifications,
  Forum
} from '@mui/icons-material';

const FarmerDashboard = () => {
  const { farmer, token } = useAuth();
  const [dashboardData, setDashboardData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [securityAlert, setSecurityAlert] = useState(null);

  useEffect(() => {
    fetchDashboardData();
    checkSecurityStatus();
  }, []);

  const fetchDashboardData = async () => {
    try {
      const response = await fetch('/api/farmer/dashboard', {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      const data = await response.json();
      setDashboardData(data);
    } catch (error) {
      console.error('Failed to fetch dashboard data:', error);
    } finally {
      setLoading(false);
    }
  };

  const checkSecurityStatus = async () => {
    try {
      const response = await fetch('/api/farmer/security/check', {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      const data = await response.json();
      
      if (data.risk_analysis.risk_level === 'high' || 
          data.risk_analysis.risk_level === 'critical') {
        setSecurityAlert({
          severity: 'warning',
          message: 'Security check recommended',
          details: data.risk_analysis.recommendations
        });
      }
    } catch (error) {
      console.error('Security check failed:', error);
    }
  };

  const handleUploadProduct = () => {
    // Navigate to product upload page
    window.location.href = '/farmer/products/upload';
  };

  const handleViewMatches = () => {
    // Navigate to buyer matches page
    window.location.href = '/farmer/buyers/matches';
  };

  const handleCommunityConnect = () => {
    // Navigate to community page
    window.location.href = '/farmer/community';
  };

  if (loading) {
    return <CircularProgress />;
  }

  return (
    <div className="farmer-dashboard">
      {/* Security Alert */}
      {securityAlert && (
        <Alert severity={securityAlert.severity} sx={{ mb: 3 }}>
          <Typography variant="subtitle2">
            {securityAlert.message}
          </Typography>
          <ul>
            {securityAlert.details?.map((rec, idx) => (
              <li key={idx}>{rec}</li>
            ))}
          </ul>
        </Alert>
      )}

      {/* Welcome Header */}
      <Card sx={{ p: 3, mb: 3 }}>
        <Grid container alignItems="center" spacing={2}>
          <Grid item xs={12} md={8}>
            <Typography variant="h4" gutterBottom>
              Welcome, {farmer?.name}!
            </Typography>
            <Typography variant="body1" color="textSecondary">
              {farmer?.isVerified && (
                <Chip 
                  icon={<Security />} 
                  label="Verified Farmer" 
                  color="success" 
                  size="small"
                  sx={{ mr: 1 }}
                />
              )}
              Trust Score: {farmer?.trustScore}/10
            </Typography>
          </Grid>
          <Grid item xs={12} md={4} container justifyContent="flex-end">
            <Button 
              variant="contained" 
              color="primary"
              onClick={handleUploadProduct}
            >
              + Upload Product
            </Button>
          </Grid>
        </Grid>
      </Card>

      {/* Quick Stats */}
      <Grid container spacing={3} sx={{ mb: 3 }}>
        <Grid item xs={12} sm={6} md={3}>
          <Card sx={{ p: 2, textAlign: 'center' }}>
            <AttachMoney fontSize="large" color="primary" />
            <Typography variant="h6">{dashboardData?.activeProducts || 0}</Typography>
            <Typography variant="body2" color="textSecondary">
              Active Products
            </Typography>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Card sx={{ p: 2, textAlign: 'center' }}>
            <People fontSize="large" color="secondary" />
            <Typography variant="h6">{dashboardData?.buyerMatches || 0}</Typography>
            <Typography variant="body2" color="textSecondary">
              Buyer Matches
            </Typography>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Card sx={{ p: 2, textAlign: 'center' }}>
            <LocalShipping fontSize="large" color="action" />
            <Typography variant="h6">{dashboardData?.pendingOrders || 0}</Typography>
            <Typography variant="body2" color="textSecondary">
              Pending Orders
            </Typography>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Card sx={{ p: 2, textAlign: 'center' }}>
            <Forum fontSize="large" color="success" />
            <Typography variant="h6">{dashboardData?.communityConnections || 0}</Typography>
            <Typography variant="body2" color="textSecondary">
              Community Connections
            </Typography>
          </Card>
        </Grid>
      </Grid>

      {/* Recent Activity */}
      <Grid container spacing={3}>
        <Grid item xs={12} md={6}>
          <Card sx={{ p: 2 }}>
            <Typography variant="h6" gutterBottom>
              Recent Orders
            </Typography>
            <TableContainer component={Paper} variant="outlined">
              <Table size="small">
                <TableHead>
                  <TableRow>
                    <TableCell>Product</TableCell>
                    <TableCell>Buyer</TableCell>
                    <TableCell>Status</TableCell>
                    <TableCell align="right">Amount</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {dashboardData?.recentOrders?.map((order) => (
                    <TableRow key={order.id}>
                      <TableCell>{order.productName}</TableCell>
                      <TableCell>{order.buyerName}</TableCell>
                      <TableCell>
                        <Chip 
                          label={order.status} 
                          size="small"
                          color={
                            order.status === 'completed' ? 'success' :
                            order.status === 'pending' ? 'warning' : 'default'
                          }
                        />
                      </TableCell>
                      <TableCell align="right">₹{order.amount}</TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>
          </Card>
        </Grid>

        <Grid item xs={12} md={6}>
          <Card sx={{ p: 2 }}>
            <Typography variant="h6" gutterBottom>
              Quick Actions
            </Typography>
            <Grid container spacing={2}>
              <Grid item xs={6}>
                <Button
                  fullWidth
                  variant="outlined"
                  startIcon={<People />}
                  onClick={handleViewMatches}
                >
                  View Buyer Matches
                </Button>
              </Grid>
              <Grid item xs={6}>
                <Button
                  fullWidth
                  variant="outlined"
                  startIcon={<Forum />}
                  onClick={handleCommunityConnect}
                >
                  Connect Community
                </Button>
              </Grid>
              <Grid item xs={6}>
                <Button
                  fullWidth
                  variant="outlined"
                  startIcon={<Notifications />}
                  onClick={() => window.location.href = '/farmer/notifications'}
                >
                  View Notifications
                </Button>
              </Grid>
              <Grid item xs={6}>
                <Button
                  fullWidth
                  variant="outlined"
                  startIcon={<Security />}
                  onClick={() => window.location.href = '/farmer/security'}
                >
                  Security Check
                </Button>
              </Grid>
            </Grid>

            {/* Market Prices */}
            <Typography variant="h6" sx={{ mt: 3, mb: 2 }}>
              Current Market Prices
            </Typography>
            {dashboardData?.marketPrices?.map((price) => (
              <div key={price.crop} style={{ marginBottom: '8px' }}>
                <Grid container justifyContent="space-between">
                  <Typography variant="body2">{price.crop}</Typography>
                  <Typography variant="body2">
                    ₹{price.min} - ₹{price.max} / {price.unit}
                  </Typography>
                </Grid>
              </div>
            ))}
          </Card>
        </Grid>
      </Grid>
    </div>
  );
};

export default FarmerDashboard;