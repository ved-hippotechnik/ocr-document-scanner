import React, { useEffect, useState, useCallback } from 'react';
import Box from '@mui/material/Box';
import Typography from '@mui/material/Typography';
import Paper from '@mui/material/Paper';
import Button from '@mui/material/Button';
import IconButton from '@mui/material/IconButton';
import TextField from '@mui/material/TextField';
import Dialog from '@mui/material/Dialog';
import DialogTitle from '@mui/material/DialogTitle';
import DialogContent from '@mui/material/DialogContent';
import DialogActions from '@mui/material/DialogActions';
import Table from '@mui/material/Table';
import TableBody from '@mui/material/TableBody';
import TableCell from '@mui/material/TableCell';
import TableContainer from '@mui/material/TableContainer';
import TableHead from '@mui/material/TableHead';
import TableRow from '@mui/material/TableRow';
import Chip from '@mui/material/Chip';
import Alert from '@mui/material/Alert';
import Snackbar from '@mui/material/Snackbar';
import Collapse from '@mui/material/Collapse';
import FormGroup from '@mui/material/FormGroup';
import FormControlLabel from '@mui/material/FormControlLabel';
import Checkbox from '@mui/material/Checkbox';
import AddIcon from '@mui/icons-material/Add';
import DeleteIcon from '@mui/icons-material/Delete';
import SendIcon from '@mui/icons-material/Send';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import ExpandLessIcon from '@mui/icons-material/ExpandLess';
import ContentCopyIcon from '@mui/icons-material/ContentCopy';
import { useDeveloperApi } from '../../hooks/useDeveloperApi';

const ALL_EVENTS = ['scan.complete', 'scan.error', 'batch.complete', 'batch.error'];

export default function Webhooks() {
  const { listWebhooks, createWebhook, deleteWebhook, testWebhook, listDeliveries, loading, error } = useDeveloperApi();
  const [webhooks, setWebhooks] = useState([]);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [newUrl, setNewUrl] = useState('');
  const [selectedEvents, setSelectedEvents] = useState(['scan.complete']);
  const [expandedId, setExpandedId] = useState(null);
  const [deliveries, setDeliveries] = useState([]);
  const [secret, setSecret] = useState(null);
  const [snackbar, setSnackbar] = useState({ open: false, message: '' });

  const fetchWebhooks = useCallback(async () => {
    try {
      const data = await listWebhooks();
      setWebhooks(data.webhooks || []);
    } catch (_) {}
  }, [listWebhooks]);

  useEffect(() => { fetchWebhooks(); }, [fetchWebhooks]);

  const handleCreate = async () => {
    try {
      const data = await createWebhook({ url: newUrl, events: selectedEvents });
      setSecret(data.secret);
      setNewUrl('');
      setSelectedEvents(['scan.complete']);
      setDialogOpen(false);
      fetchWebhooks();
    } catch (_) {}
  };

  const handleDelete = async (id) => {
    if (!window.confirm('Delete this webhook?')) return;
    try {
      await deleteWebhook(id);
      fetchWebhooks();
      setSnackbar({ open: true, message: 'Webhook deleted' });
    } catch (_) {}
  };

  const handleTest = async (id) => {
    try {
      await testWebhook(id);
      setSnackbar({ open: true, message: 'Test event sent' });
    } catch (_) {}
  };

  const handleExpand = async (id) => {
    if (expandedId === id) {
      setExpandedId(null);
      return;
    }
    setExpandedId(id);
    try {
      const data = await listDeliveries(id);
      setDeliveries(data.deliveries || []);
    } catch (_) {}
  };

  const toggleEvent = (ev) => {
    setSelectedEvents((prev) =>
      prev.includes(ev) ? prev.filter((e) => e !== ev) : [...prev, ev],
    );
  };

  const copyToClipboard = (text) => {
    navigator.clipboard.writeText(text);
    setSnackbar({ open: true, message: 'Copied to clipboard' });
  };

  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4" fontWeight={600}>Webhooks</Typography>
        <Button variant="contained" startIcon={<AddIcon />} onClick={() => setDialogOpen(true)}>
          Add Webhook
        </Button>
      </Box>

      {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}

      {secret && (
        <Alert severity="success" sx={{ mb: 2 }} onClose={() => setSecret(null)}
          action={
            <IconButton size="small" onClick={() => copyToClipboard(secret)} aria-label="Copy secret">
              <ContentCopyIcon fontSize="small" />
            </IconButton>
          }>
          <strong>Signing secret (save it now):</strong><br />
          <code style={{ wordBreak: 'break-all' }}>{secret}</code>
        </Alert>
      )}

      <TableContainer component={Paper}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>URL</TableCell>
              <TableCell>Events</TableCell>
              <TableCell>Status</TableCell>
              <TableCell align="right">Actions</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {webhooks.length === 0 && !loading && (
              <TableRow>
                <TableCell colSpan={4} align="center">
                  <Typography color="text.secondary" sx={{ py: 3 }}>No webhooks configured.</Typography>
                </TableCell>
              </TableRow>
            )}
            {webhooks.map((wh) => (
              <React.Fragment key={wh.id}>
                <TableRow>
                  <TableCell sx={{ maxWidth: 300, overflow: 'hidden', textOverflow: 'ellipsis' }}>
                    <code>{wh.url}</code>
                  </TableCell>
                  <TableCell>
                    {(wh.events || []).map((ev) => <Chip key={ev} label={ev} size="small" sx={{ mr: 0.5, mb: 0.5 }} />)}
                  </TableCell>
                  <TableCell>
                    <Chip label={wh.is_active ? 'Active' : 'Inactive'} size="small"
                      color={wh.is_active ? 'success' : 'default'} />
                  </TableCell>
                  <TableCell align="right">
                    <IconButton size="small" onClick={() => handleTest(wh.id)} aria-label="Send test event">
                      <SendIcon fontSize="small" />
                    </IconButton>
                    <IconButton size="small" onClick={() => handleExpand(wh.id)} aria-label="Toggle deliveries">
                      {expandedId === wh.id ? <ExpandLessIcon fontSize="small" /> : <ExpandMoreIcon fontSize="small" />}
                    </IconButton>
                    <IconButton size="small" color="error" onClick={() => handleDelete(wh.id)} aria-label="Delete webhook">
                      <DeleteIcon fontSize="small" />
                    </IconButton>
                  </TableCell>
                </TableRow>
                <TableRow>
                  <TableCell colSpan={4} sx={{ p: 0, borderBottom: expandedId === wh.id ? undefined : 'none' }}>
                    <Collapse in={expandedId === wh.id}>
                      <Box sx={{ p: 2, bgcolor: 'background.default' }}>
                        <Typography variant="subtitle2" gutterBottom>Recent Deliveries</Typography>
                        {deliveries.length === 0 ? (
                          <Typography variant="body2" color="text.secondary">No deliveries yet.</Typography>
                        ) : (
                          <Table size="small">
                            <TableHead>
                              <TableRow>
                                <TableCell>Event</TableCell>
                                <TableCell>Status</TableCell>
                                <TableCell>Attempts</TableCell>
                                <TableCell>Delivered At</TableCell>
                              </TableRow>
                            </TableHead>
                            <TableBody>
                              {deliveries.map((d) => (
                                <TableRow key={d.id}>
                                  <TableCell>{d.event_type}</TableCell>
                                  <TableCell>
                                    <Chip size="small"
                                      label={d.delivered_at ? `${d.response_status}` : 'Pending'}
                                      color={d.delivered_at ? 'success' : 'warning'} />
                                  </TableCell>
                                  <TableCell>{d.attempts}/{d.max_attempts}</TableCell>
                                  <TableCell>{d.delivered_at ? new Date(d.delivered_at).toLocaleString() : '-'}</TableCell>
                                </TableRow>
                              ))}
                            </TableBody>
                          </Table>
                        )}
                      </Box>
                    </Collapse>
                  </TableCell>
                </TableRow>
              </React.Fragment>
            ))}
          </TableBody>
        </Table>
      </TableContainer>

      {/* Create Dialog */}
      <Dialog open={dialogOpen} onClose={() => setDialogOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Add Webhook</DialogTitle>
        <DialogContent>
          <TextField autoFocus fullWidth label="Webhook URL" variant="outlined" sx={{ mt: 1, mb: 2 }}
            value={newUrl} onChange={(e) => setNewUrl(e.target.value)}
            placeholder="https://your-server.com/webhook" />
          <Typography variant="subtitle2" gutterBottom>Subscribe to Events</Typography>
          <FormGroup row>
            {ALL_EVENTS.map((ev) => (
              <FormControlLabel key={ev}
                control={<Checkbox checked={selectedEvents.includes(ev)} onChange={() => toggleEvent(ev)} />}
                label={ev} />
            ))}
          </FormGroup>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDialogOpen(false)}>Cancel</Button>
          <Button variant="contained" onClick={handleCreate} disabled={!newUrl || loading}>Create</Button>
        </DialogActions>
      </Dialog>

      <Snackbar open={snackbar.open} autoHideDuration={3000}
        onClose={() => setSnackbar({ open: false, message: '' })} message={snackbar.message} />
    </Box>
  );
}
