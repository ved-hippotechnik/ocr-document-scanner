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
import FormGroup from '@mui/material/FormGroup';
import FormControlLabel from '@mui/material/FormControlLabel';
import Checkbox from '@mui/material/Checkbox';
import ContentCopyIcon from '@mui/icons-material/ContentCopy';
import DeleteIcon from '@mui/icons-material/Delete';
import AddIcon from '@mui/icons-material/Add';
import { useDeveloperApi } from '../../hooks/useDeveloperApi';

const ALL_SCOPES = ['scan', 'batch', 'ai', 'analytics'];

export default function ApiKeys() {
  const { listKeys, createKey, revokeKey, loading, error } = useDeveloperApi();
  const [keys, setKeys] = useState([]);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [newKeyName, setNewKeyName] = useState('');
  const [selectedScopes, setSelectedScopes] = useState(['scan']);
  const [rawKey, setRawKey] = useState(null);
  const [snackbar, setSnackbar] = useState({ open: false, message: '' });

  const fetchKeys = useCallback(async () => {
    try {
      const data = await listKeys();
      setKeys(data.keys || []);
    } catch (_) {}
  }, [listKeys]);

  useEffect(() => { fetchKeys(); }, [fetchKeys]);

  const handleCreate = async () => {
    try {
      const data = await createKey({ name: newKeyName || 'Default Key', scopes: selectedScopes });
      setRawKey(data.raw_key);
      setNewKeyName('');
      setSelectedScopes(['scan']);
      fetchKeys();
    } catch (_) {}
  };

  const handleRevoke = async (id) => {
    if (!window.confirm('Are you sure you want to revoke this API key? This cannot be undone.')) return;
    try {
      await revokeKey(id);
      fetchKeys();
      setSnackbar({ open: true, message: 'API key revoked' });
    } catch (_) {}
  };

  const copyToClipboard = (text) => {
    navigator.clipboard.writeText(text);
    setSnackbar({ open: true, message: 'Copied to clipboard' });
  };

  const toggleScope = (scope) => {
    setSelectedScopes((prev) =>
      prev.includes(scope) ? prev.filter((s) => s !== scope) : [...prev, scope],
    );
  };

  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4" fontWeight={600}>API Keys</Typography>
        <Button variant="contained" startIcon={<AddIcon />} onClick={() => setDialogOpen(true)}>
          Create Key
        </Button>
      </Box>

      {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}

      {rawKey && (
        <Alert severity="success" sx={{ mb: 2 }} onClose={() => setRawKey(null)}
          action={
            <IconButton size="small" onClick={() => copyToClipboard(rawKey)} aria-label="Copy key">
              <ContentCopyIcon fontSize="small" />
            </IconButton>
          }>
          <strong>Save this key — it won't be shown again:</strong>
          <br />
          <code style={{ wordBreak: 'break-all' }}>{rawKey}</code>
        </Alert>
      )}

      <TableContainer component={Paper}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>Name</TableCell>
              <TableCell>Key Prefix</TableCell>
              <TableCell>Scopes</TableCell>
              <TableCell>Rate Limit</TableCell>
              <TableCell>Last Used</TableCell>
              <TableCell>Status</TableCell>
              <TableCell align="right">Actions</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {keys.length === 0 && !loading && (
              <TableRow>
                <TableCell colSpan={7} align="center">
                  <Typography color="text.secondary" sx={{ py: 3 }}>
                    No API keys yet. Create one to get started.
                  </Typography>
                </TableCell>
              </TableRow>
            )}
            {keys.map((k) => (
              <TableRow key={k.id}>
                <TableCell>{k.name}</TableCell>
                <TableCell><code>{k.key_prefix}</code></TableCell>
                <TableCell>
                  {(k.scopes || []).map((s) => (
                    <Chip key={s} label={s} size="small" sx={{ mr: 0.5 }} />
                  ))}
                </TableCell>
                <TableCell>{k.rate_limit}/min</TableCell>
                <TableCell>{k.last_used_at ? new Date(k.last_used_at).toLocaleDateString() : 'Never'}</TableCell>
                <TableCell>
                  <Chip label={k.is_active ? 'Active' : 'Revoked'} size="small"
                    color={k.is_active ? 'success' : 'default'} />
                </TableCell>
                <TableCell align="right">
                  {k.is_active && (
                    <IconButton size="small" color="error" onClick={() => handleRevoke(k.id)} aria-label="Revoke key">
                      <DeleteIcon fontSize="small" />
                    </IconButton>
                  )}
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>

      {/* Create Key Dialog */}
      <Dialog open={dialogOpen} onClose={() => setDialogOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Create API Key</DialogTitle>
        <DialogContent>
          <TextField
            autoFocus fullWidth label="Key Name" variant="outlined" sx={{ mt: 1, mb: 2 }}
            value={newKeyName} onChange={(e) => setNewKeyName(e.target.value)}
            placeholder="e.g. Production Backend"
          />
          <Typography variant="subtitle2" gutterBottom>Scopes</Typography>
          <FormGroup row>
            {ALL_SCOPES.map((scope) => (
              <FormControlLabel key={scope}
                control={<Checkbox checked={selectedScopes.includes(scope)} onChange={() => toggleScope(scope)} />}
                label={scope}
              />
            ))}
          </FormGroup>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDialogOpen(false)}>Cancel</Button>
          <Button variant="contained" onClick={handleCreate} disabled={loading}>Create</Button>
        </DialogActions>
      </Dialog>

      <Snackbar open={snackbar.open} autoHideDuration={3000}
        onClose={() => setSnackbar({ open: false, message: '' })}
        message={snackbar.message} />
    </Box>
  );
}
