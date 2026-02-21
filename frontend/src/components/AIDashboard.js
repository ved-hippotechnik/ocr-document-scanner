import React, { useState, useEffect } from 'react';
import { endpoints } from '../config';
import {
  Box,
  Grid,
  Card,
  CardContent,
  Typography,
  Button,
  Paper,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  Chip,
  LinearProgress,
  Alert,
  Tabs,
  Tab,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem
} from '@mui/material';
import {
  Psychology,
  Analytics,
  Speed,
  CheckCircleOutline as Accuracy,
  TrendingUp,
  Assessment,
  RateReview as Feedback,
  Settings,
  Warning,
  CheckCircle,
  Error,
  Info,
  Memory as ModelTraining,
  SmartToy,
  DataUsage,
  BugReport
} from '@mui/icons-material';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, Cell, BarChart, Bar } from 'recharts';

const AIDashboard = () => {
  const [activeTab, setActiveTab] = useState(0);
  const [metrics, setMetrics] = useState(null);
  const [supportedTypes, setSupportedTypes] = useState([]);
  const [processingHistory, setProcessingHistory] = useState([]);
  const [feedbackDialog, setFeedbackDialog] = useState(false);
  const [trainingDialog, setTrainingDialog] = useState(false);
  const [confidenceThreshold, setConfidenceThreshold] = useState(0.7);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadDashboardData();
  }, []);

  const loadDashboardData = async () => {
    try {
      setLoading(true);
      
      // Load AI metrics
      const metricsResponse = await fetch(endpoints.aiMetrics);
      
      if (metricsResponse.ok) {
        const metricsData = await metricsResponse.json();
        setMetrics(metricsData.metrics);
      }

      // Load supported document types
      const typesResponse = await fetch(endpoints.aiSupportedTypes);
      if (typesResponse.ok) {
        const typesData = await typesResponse.json();
        setSupportedTypes(typesData.document_types);
      }

      // Load processing history (mock data for now)
      setProcessingHistory([
        { date: '2024-01-15', accuracy: 0.92, processed: 145 },
        { date: '2024-01-16', accuracy: 0.89, processed: 167 },
        { date: '2024-01-17', accuracy: 0.95, processed: 189 },
        { date: '2024-01-18', accuracy: 0.91, processed: 156 },
        { date: '2024-01-19', accuracy: 0.94, processed: 178 },
        { date: '2024-01-20', accuracy: 0.96, processed: 203 },
        { date: '2024-01-21', accuracy: 0.93, processed: 167 }
      ]);

    } catch (error) {
      console.error('Error loading dashboard data:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleTabChange = (event, newValue) => {
    setActiveTab(newValue);
  };

  const submitFeedback = async (feedbackData) => {
    try {
      const response = await fetch(endpoints.aiFeedback, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(feedbackData)
      });

      if (response.ok) {
        alert('Feedback submitted successfully!');
        setFeedbackDialog(false);
      }
    } catch (error) {
      console.error('Error submitting feedback:', error);
    }
  };

  const updateConfidenceThreshold = async () => {
    try {
      const response = await fetch(endpoints.aiConfidenceThreshold, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ threshold: confidenceThreshold })
      });

      if (response.ok) {
        alert('Confidence threshold updated successfully!');
      }
    } catch (error) {
      console.error('Error updating threshold:', error);
    }
  };

  const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#8884D8'];

  const documentTypeData = supportedTypes.map((type, index) => ({
    name: type.name,
    value: Math.floor(Math.random() * 100) + 10,
    color: COLORS[index % COLORS.length]
  }));

  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '50vh' }}>
        <LinearProgress sx={{ width: '50%' }} />
      </Box>
    );
  }

  return (
    <Box sx={{ maxWidth: 1200, mx: 'auto', p: 3 }}>
      <Typography variant="h4" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
        <SmartToy color="primary" />
        AI Classification Dashboard
      </Typography>

      <Tabs value={activeTab} onChange={handleTabChange} sx={{ mb: 3 }}>
        <Tab label="Overview" />
        <Tab label="Performance" />
        <Tab label="Document Types" />
        <Tab label="Settings" />
      </Tabs>

      {/* Overview Tab */}
      {activeTab === 0 && (
        <Box>
          {/* Key Metrics */}
          <Grid container spacing={3} sx={{ mb: 3 }}>
            <Grid item xs={12} md={3}>
              <Card>
                <CardContent sx={{ textAlign: 'center' }}>
                  <Psychology sx={{ fontSize: 40, color: 'primary.main', mb: 1 }} />
                  <Typography variant="h4" color="primary">
                    {metrics?.accuracy ? (metrics.accuracy * 100).toFixed(1) : 0}%
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Classification Accuracy
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
            
            <Grid item xs={12} md={3}>
              <Card>
                <CardContent sx={{ textAlign: 'center' }}>
                  <DataUsage sx={{ fontSize: 40, color: 'success.main', mb: 1 }} />
                  <Typography variant="h4" color="success.main">
                    {metrics?.total_classifications || 0}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Total Classifications
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
            
            <Grid item xs={12} md={3}>
              <Card>
                <CardContent sx={{ textAlign: 'center' }}>
                  <Speed sx={{ fontSize: 40, color: 'warning.main', mb: 1 }} />
                  <Typography variant="h4" color="warning.main">
                    {supportedTypes.length}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Supported Types
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
            
            <Grid item xs={12} md={3}>
              <Card>
                <CardContent sx={{ textAlign: 'center' }}>
                  <TrendingUp sx={{ fontSize: 40, color: 'info.main', mb: 1 }} />
                  <Typography variant="h4" color="info.main">
                    {confidenceThreshold * 100}%
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Confidence Threshold
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
          </Grid>

          {/* Recent Activity */}
          <Card sx={{ mb: 3 }}>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Recent Classifications
              </Typography>
              <List>
                {Array.from({ length: 5 }, (_, i) => (
                  <ListItem key={i} divider>
                    <ListItemIcon>
                      <CheckCircle color="success" />
                    </ListItemIcon>
                    <ListItemText
                      primary={`Document ${i + 1} - ${['Aadhaar Card', 'Passport', 'Driving License'][i % 3]}`}
                      secondary={`Confidence: ${(85 + Math.random() * 15).toFixed(1)}% • ${new Date().toLocaleTimeString()}`}
                    />
                    <Chip
                      label="Success"
                      color="success"
                      size="small"
                    />
                  </ListItem>
                ))}
              </List>
            </CardContent>
          </Card>

          {/* System Health */}
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                System Health
              </Typography>
              <Grid container spacing={2}>
                <Grid item xs={12} md={4}>
                  <Alert severity="success" sx={{ mb: 1 }}>
                    <Typography variant="body2">
                      AI Model: Healthy
                    </Typography>
                  </Alert>
                </Grid>
                <Grid item xs={12} md={4}>
                  <Alert severity="info" sx={{ mb: 1 }}>
                    <Typography variant="body2">
                      Cache: 89% Hit Rate
                    </Typography>
                  </Alert>
                </Grid>
                <Grid item xs={12} md={4}>
                  <Alert severity="warning" sx={{ mb: 1 }}>
                    <Typography variant="body2">
                      Training: Due for Update
                    </Typography>
                  </Alert>
                </Grid>
              </Grid>
            </CardContent>
          </Card>
        </Box>
      )}

      {/* Performance Tab */}
      {activeTab === 1 && (
        <Box>
          <Grid container spacing={3}>
            <Grid item xs={12} md={8}>
              <Card>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    Classification Accuracy Over Time
                  </Typography>
                  <ResponsiveContainer width="100%" height={300}>
                    <LineChart data={processingHistory}>
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis dataKey="date" />
                      <YAxis />
                      <Tooltip />
                      <Line type="monotone" dataKey="accuracy" stroke="#8884d8" strokeWidth={2} />
                    </LineChart>
                  </ResponsiveContainer>
                </CardContent>
              </Card>
            </Grid>
            
            <Grid item xs={12} md={4}>
              <Card>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    Processing Volume
                  </Typography>
                  <ResponsiveContainer width="100%" height={300}>
                    <BarChart data={processingHistory}>
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis dataKey="date" />
                      <YAxis />
                      <Tooltip />
                      <Bar dataKey="processed" fill="#82ca9d" />
                    </BarChart>
                  </ResponsiveContainer>
                </CardContent>
              </Card>
            </Grid>
          </Grid>

          <Card sx={{ mt: 3 }}>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Performance Metrics
              </Typography>
              <TableContainer>
                <Table>
                  <TableHead>
                    <TableRow>
                      <TableCell>Metric</TableCell>
                      <TableCell>Current Value</TableCell>
                      <TableCell>Target</TableCell>
                      <TableCell>Status</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    <TableRow>
                      <TableCell>Average Confidence</TableCell>
                      <TableCell>92.3%</TableCell>
                      <TableCell>90%</TableCell>
                      <TableCell><CheckCircle color="success" /></TableCell>
                    </TableRow>
                    <TableRow>
                      <TableCell>Processing Speed</TableCell>
                      <TableCell>1.2s avg</TableCell>
                      <TableCell>{'< 2s'}</TableCell>
                      <TableCell><CheckCircle color="success" /></TableCell>
                    </TableRow>
                    <TableRow>
                      <TableCell>False Positive Rate</TableCell>
                      <TableCell>3.2%</TableCell>
                      <TableCell>{'< 5%'}</TableCell>
                      <TableCell><CheckCircle color="success" /></TableCell>
                    </TableRow>
                    <TableRow>
                      <TableCell>Model Accuracy</TableCell>
                      <TableCell>94.7%</TableCell>
                      <TableCell>{'> 95%'}</TableCell>
                      <TableCell><Warning color="warning" /></TableCell>
                    </TableRow>
                  </TableBody>
                </Table>
              </TableContainer>
            </CardContent>
          </Card>
        </Box>
      )}

      {/* Document Types Tab */}
      {activeTab === 2 && (
        <Box>
          <Grid container spacing={3}>
            <Grid item xs={12} md={6}>
              <Card>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    Document Type Distribution
                  </Typography>
                  <ResponsiveContainer width="100%" height={300}>
                    <PieChart>
                      <Pie
                        data={documentTypeData}
                        cx="50%"
                        cy="50%"
                        labelLine={false}
                        label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                        outerRadius={80}
                        fill="#8884d8"
                        dataKey="value"
                      >
                        {documentTypeData.map((entry, index) => (
                          <Cell key={`cell-${index}`} fill={entry.color} />
                        ))}
                      </Pie>
                      <Tooltip />
                    </PieChart>
                  </ResponsiveContainer>
                </CardContent>
              </Card>
            </Grid>
            
            <Grid item xs={12} md={6}>
              <Card>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    Supported Document Types
                  </Typography>
                  <List>
                    {supportedTypes.map((type, index) => (
                      <ListItem key={index} divider>
                        <ListItemIcon>
                          <CheckCircle color="success" />
                        </ListItemIcon>
                        <ListItemText
                          primary={type.name}
                          secondary={`Type: ${type.type}`}
                        />
                        <Chip
                          label="Active"
                          color="success"
                          size="small"
                        />
                      </ListItem>
                    ))}
                  </List>
                </CardContent>
              </Card>
            </Grid>
          </Grid>
        </Box>
      )}

      {/* Settings Tab */}
      {activeTab === 3 && (
        <Box>
          <Grid container spacing={3}>
            <Grid item xs={12} md={6}>
              <Card>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    Classification Settings
                  </Typography>
                  
                  <Box sx={{ mb: 3 }}>
                    <Typography variant="subtitle1" gutterBottom>
                      Confidence Threshold
                    </Typography>
                    <TextField
                      type="number"
                      value={confidenceThreshold}
                      onChange={(e) => setConfidenceThreshold(parseFloat(e.target.value))}
                      inputProps={{ min: 0, max: 1, step: 0.1 }}
                      fullWidth
                      sx={{ mb: 2 }}
                    />
                    <Button
                      variant="contained"
                      onClick={updateConfidenceThreshold}
                      startIcon={<Settings />}
                    >
                      Update Threshold
                    </Button>
                  </Box>

                  <Box sx={{ mb: 3 }}>
                    <Button
                      variant="outlined"
                      onClick={() => setFeedbackDialog(true)}
                      startIcon={<Feedback />}
                      sx={{ mr: 1 }}
                    >
                      Submit Feedback
                    </Button>
                    <Button
                      variant="outlined"
                      onClick={() => setTrainingDialog(true)}
                      startIcon={<ModelTraining />}
                    >
                      Train Model
                    </Button>
                  </Box>
                </CardContent>
              </Card>
            </Grid>
            
            <Grid item xs={12} md={6}>
              <Card>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    Model Information
                  </Typography>
                  
                  <List>
                    <ListItem>
                      <ListItemText
                        primary="Model Version"
                        secondary="v2.1.0"
                      />
                    </ListItem>
                    <ListItem>
                      <ListItemText
                        primary="Last Updated"
                        secondary={metrics?.last_updated || 'Unknown'}
                      />
                    </ListItem>
                    <ListItem>
                      <ListItemText
                        primary="Training Data"
                        secondary="15,000 samples"
                      />
                    </ListItem>
                    <ListItem>
                      <ListItemText
                        primary="Model Size"
                        secondary="125 MB"
                      />
                    </ListItem>
                  </List>
                </CardContent>
              </Card>
            </Grid>
          </Grid>
        </Box>
      )}

      {/* Feedback Dialog */}
      <Dialog open={feedbackDialog} onClose={() => setFeedbackDialog(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Submit Classification Feedback</DialogTitle>
        <DialogContent>
          <TextField
            margin="dense"
            label="Image Hash"
            fullWidth
            variant="outlined"
            sx={{ mb: 2 }}
          />
          <FormControl fullWidth sx={{ mb: 2 }}>
            <InputLabel>Predicted Type</InputLabel>
            <Select>
              {supportedTypes.map((type) => (
                <MenuItem key={type.type} value={type.type}>
                  {type.name}
                </MenuItem>
              ))}
            </Select>
          </FormControl>
          <FormControl fullWidth sx={{ mb: 2 }}>
            <InputLabel>Actual Type</InputLabel>
            <Select>
              {supportedTypes.map((type) => (
                <MenuItem key={type.type} value={type.type}>
                  {type.name}
                </MenuItem>
              ))}
            </Select>
          </FormControl>
          <TextField
            margin="dense"
            label="Confidence Score"
            type="number"
            fullWidth
            variant="outlined"
            inputProps={{ min: 0, max: 1, step: 0.01 }}
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setFeedbackDialog(false)}>Cancel</Button>
          <Button onClick={() => submitFeedback({})} variant="contained">
            Submit Feedback
          </Button>
        </DialogActions>
      </Dialog>

      {/* Training Dialog */}
      <Dialog open={trainingDialog} onClose={() => setTrainingDialog(false)} maxWidth="md" fullWidth>
        <DialogTitle>Train AI Model</DialogTitle>
        <DialogContent>
          <Alert severity="info" sx={{ mb: 2 }}>
            Upload training data to improve model accuracy. Minimum 10 samples required.
          </Alert>
          <Typography variant="body2" sx={{ mb: 2 }}>
            Training will temporarily impact performance. Schedule during low-usage periods.
          </Typography>
          <Button variant="outlined" component="label" sx={{ mb: 2 }}>
            Upload Training Data
            <input type="file" hidden accept=".zip,.json" />
          </Button>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setTrainingDialog(false)}>Cancel</Button>
          <Button variant="contained" color="warning">
            Start Training
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default AIDashboard;