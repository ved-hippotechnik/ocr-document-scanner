import React from 'react';
import {
  Box,
  Button,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  Grid,
  IconButton,
  List,
  ListItem,
  ListItemText,
  Menu,
  MenuItem,
  Paper,
  Tab,
  Tabs,
  TextField,
  Tooltip,
  Typography,
} from '@mui/material';
import CloseIcon from '@mui/icons-material/Close';
import EditIcon from '@mui/icons-material/Edit';
import PrintIcon from '@mui/icons-material/Print';
import MoreVertIcon from '@mui/icons-material/MoreVert';
import FileDownloadIcon from '@mui/icons-material/FileDownload';
import ContentCopyIcon from '@mui/icons-material/ContentCopy';
import DescriptionIcon from '@mui/icons-material/Description';
import BadgeIcon from '@mui/icons-material/Badge';
import PassportIcon from '@mui/icons-material/ArticleOutlined';
import CreditCardIcon from '@mui/icons-material/CreditCard';
import PersonIcon from '@mui/icons-material/Person';
import FingerprintIcon from '@mui/icons-material/Fingerprint';
import CalendarTodayIcon from '@mui/icons-material/CalendarToday';
import LocationOnIcon from '@mui/icons-material/LocationOn';

const DialogDocTypeIcon = ({ documentType, size }) => {
  const fontSize = size || { xs: '1.25rem', sm: '1.5rem' };
  if (documentType === 'passport') {
    return <PassportIcon sx={{ mr: 1, color: 'info.main', fontSize }} />;
  }
  if (documentType === 'us_green_card') {
    return <CreditCardIcon sx={{ mr: 1, color: 'success.main', fontSize }} />;
  }
  if (documentType === 'id_card' || documentType === 'ID Card') {
    return <BadgeIcon sx={{ mr: 1, color: 'success.main', fontSize }} />;
  }
  return <DescriptionIcon sx={{ mr: 1, color: 'warning.main', fontSize }} />;
};

const ScanDetailDialog = ({
  open,
  selectedScan,
  editMode,
  editedScan,
  tabValue,
  menuAnchorEl,
  menuOpen,
  onClose,
  onTabChange,
  onEditClick,
  onCancelEdit,
  onSaveEdit,
  onEditFieldChange,
  onPrintScan,
  onExportJSON,
  onCopyToClipboard,
  onMenuOpen,
  onMenuClose,
}) => {
  const dialogTitle = selectedScan?.document_type === 'us_green_card'
    ? 'US Green Card Details'
    : `${selectedScan?.document_type?.charAt(0).toUpperCase() + selectedScan?.document_type?.slice(1).replace('_', ' ')} Details`;

  return (
    <Dialog
      open={open}
      onClose={onClose}
      fullWidth
      maxWidth="md"
      sx={{
        '& .MuiDialog-paper': {
          width: '100%',
          margin: { xs: '16px', sm: '24px', md: '32px' },
          maxHeight: { xs: 'calc(100% - 32px)', sm: 'calc(100% - 48px)', md: 'calc(100% - 64px)' },
        },
      }}
    >
      <DialogTitle
        sx={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          pb: 1,
          px: { xs: 2, sm: 3 },
        }}
      >
        <Box sx={{ display: 'flex', alignItems: 'center', overflow: 'hidden' }}>
          <DialogDocTypeIcon documentType={selectedScan?.document_type} />
          <Typography
            variant="h6"
            sx={{
              fontSize: { xs: '1rem', sm: '1.25rem' },
              whiteSpace: 'nowrap',
              overflow: 'hidden',
              textOverflow: 'ellipsis',
            }}
          >
            {dialogTitle}
          </Typography>
        </Box>
        <Box sx={{ display: 'flex', ml: 1, flexShrink: 0 }}>
          {!editMode && (
            <>
              <Tooltip title="Print">
                <IconButton
                  onClick={onPrintScan}
                  size="small"
                  sx={{ mr: { xs: 0.5, sm: 1 }, p: { xs: 0.5, sm: 1 } }}
                >
                  <PrintIcon sx={{ fontSize: { xs: '1.1rem', sm: '1.25rem' } }} />
                </IconButton>
              </Tooltip>
              <Tooltip title="More options">
                <IconButton
                  onClick={onMenuOpen}
                  size="small"
                  sx={{ mr: { xs: 0.5, sm: 1 }, p: { xs: 0.5, sm: 1 } }}
                  aria-controls={menuOpen ? 'scan-menu' : undefined}
                  aria-haspopup="true"
                  aria-expanded={menuOpen ? 'true' : undefined}
                >
                  <MoreVertIcon sx={{ fontSize: { xs: '1.1rem', sm: '1.25rem' } }} />
                </IconButton>
              </Tooltip>
            </>
          )}
          <IconButton onClick={onClose} size="small">
            <CloseIcon />
          </IconButton>
        </Box>

        <Menu
          id="scan-menu"
          anchorEl={menuAnchorEl}
          open={menuOpen}
          onClose={onMenuClose}
          MenuListProps={{ 'aria-labelledby': 'more-options-button' }}
        >
          <MenuItem onClick={onEditClick}>
            <EditIcon fontSize="small" sx={{ mr: 1 }} />
            Edit Details
          </MenuItem>
          <MenuItem onClick={onExportJSON}>
            <FileDownloadIcon fontSize="small" sx={{ mr: 1 }} />
            Export as JSON
          </MenuItem>
          <MenuItem onClick={onCopyToClipboard}>
            <ContentCopyIcon fontSize="small" sx={{ mr: 1 }} />
            Copy to Clipboard
          </MenuItem>
        </Menu>
      </DialogTitle>

      <Box sx={{ borderBottom: 1, borderColor: 'divider', px: { xs: 1, sm: 2 } }}>
        <Tabs
          value={tabValue}
          onChange={onTabChange}
          aria-label="scan details tabs"
          variant={window.innerWidth < 600 ? 'scrollable' : 'standard'}
          scrollButtons={window.innerWidth < 600 ? 'auto' : false}
          allowScrollButtonsMobile
          sx={{
            minHeight: { xs: 40, sm: 48 },
            '& .MuiTab-root': {
              minHeight: { xs: 40, sm: 48 },
              fontSize: { xs: '0.8rem', sm: '0.9rem' },
              px: { xs: 1, sm: 2 },
              py: { xs: 0.5, sm: 1 },
            },
          }}
        >
          <Tab label="Details" />
          <Tab label="Raw Text" />
          {selectedScan?.image_data && <Tab label="Image" />}
        </Tabs>
      </Box>

      <DialogContent dividers sx={{ px: { xs: 2, sm: 3 }, py: { xs: 2, sm: 2.5 } }}>
        {selectedScan && (
          <>
            {/* Tab Panel 0: Details */}
            {tabValue === 0 && (
              <Grid container spacing={{ xs: 2, sm: 3 }}>
                {/* Document Information */}
                <Grid item xs={12} sm={6}>
                  <Typography
                    variant="subtitle1"
                    color="primary"
                    gutterBottom
                    sx={{ fontSize: { xs: '0.9rem', sm: '1rem', md: '1.1rem' } }}
                  >
                    Document Information
                  </Typography>
                  {editMode ? (
                    <Box sx={{ mt: { xs: 1, sm: 2 } }}>
                      <TextField
                        label="Document Type"
                        value={editedScan.document_type || ''}
                        onChange={(e) => onEditFieldChange('document_type', e.target.value)}
                        fullWidth
                        margin="dense"
                        size="small"
                        select
                        sx={{
                          mb: { xs: 1, sm: 1.5 },
                          '& .MuiInputLabel-root': { fontSize: { xs: '0.8rem', sm: '0.875rem' } },
                          '& .MuiInputBase-input': { fontSize: { xs: '0.8rem', sm: '0.875rem' } },
                          '& .MuiMenuItem-root': { fontSize: { xs: '0.8rem', sm: '0.875rem' } },
                        }}
                      >
                        <MenuItem value="passport">Passport</MenuItem>
                        <MenuItem value="id_card">ID Card</MenuItem>
                        <MenuItem value="driving_license">Driving License</MenuItem>
                        <MenuItem value="us_green_card">US Green Card</MenuItem>
                        <MenuItem value="other">Other</MenuItem>
                      </TextField>
                      <TextField
                        label="Nationality"
                        value={editedScan.nationality || ''}
                        onChange={(e) => onEditFieldChange('nationality', e.target.value)}
                        fullWidth
                        margin="dense"
                        size="small"
                        sx={{
                          mb: { xs: 1, sm: 1.5 },
                          '& .MuiInputLabel-root': { fontSize: { xs: '0.8rem', sm: '0.875rem' } },
                          '& .MuiInputBase-input': { fontSize: { xs: '0.8rem', sm: '0.875rem' } },
                        }}
                      />
                      <TextField
                        label="Scan Date"
                        value={new Date(editedScan.timestamp).toISOString().split('T')[0]}
                        type="date"
                        fullWidth
                        margin="dense"
                        size="small"
                        InputLabelProps={{ shrink: true }}
                        onChange={(e) => {
                          const newDate = new Date(e.target.value);
                          const currentDate = new Date(editedScan.timestamp);
                          currentDate.setFullYear(newDate.getFullYear());
                          currentDate.setMonth(newDate.getMonth());
                          currentDate.setDate(newDate.getDate());
                          onEditFieldChange('timestamp', currentDate.toISOString());
                        }}
                        sx={{
                          '& .MuiInputLabel-root': { fontSize: { xs: '0.8rem', sm: '0.875rem' } },
                          '& .MuiInputBase-input': { fontSize: { xs: '0.8rem', sm: '0.875rem' } },
                        }}
                      />
                    </Box>
                  ) : (
                    <List dense>
                      <ListItem>
                        <ListItemText
                          primary="Document Type"
                          secondary={
                            selectedScan.document_type?.charAt(0).toUpperCase() +
                            selectedScan.document_type?.slice(1).replace('_', ' ')
                          }
                        />
                      </ListItem>
                      <ListItem>
                        <ListItemText primary="Nationality" secondary={selectedScan.nationality || 'Unknown'} />
                      </ListItem>
                      <ListItem>
                        <ListItemText
                          primary="Scan Date"
                          secondary={new Date(selectedScan.timestamp).toLocaleString()}
                        />
                      </ListItem>
                    </List>
                  )}
                </Grid>

                {/* Extracted Information */}
                <Grid item xs={12} sm={6}>
                  <Typography
                    variant="subtitle1"
                    color="primary"
                    gutterBottom
                    sx={{ fontSize: { xs: '0.9rem', sm: '1rem', md: '1.1rem' } }}
                  >
                    Extracted Information
                  </Typography>
                  {editMode ? (
                    <Box sx={{ mt: { xs: 1, sm: 2 } }}>
                      {[
                        { label: 'Full Name', field: 'extracted_info.full_name', value: editedScan.extracted_info?.full_name },
                        { label: 'Document Number', field: 'extracted_info.document_number', value: editedScan.extracted_info?.document_number },
                        { label: 'Date of Birth', field: 'extracted_info.birth_date', value: editedScan.extracted_info?.birth_date },
                        { label: 'Expiry Date', field: 'extracted_info.expiry_date', value: editedScan.extracted_info?.expiry_date },
                        { label: 'Place of Issue', field: 'extracted_info.place_of_issue', value: editedScan.extracted_info?.place_of_issue },
                        { label: 'Issue Date', field: 'extracted_info.issue_date', value: editedScan.extracted_info?.issue_date },
                      ].map(({ label, field, value }) => (
                        <TextField
                          key={field}
                          label={label}
                          value={value || ''}
                          onChange={(e) => onEditFieldChange(field, e.target.value)}
                          fullWidth
                          margin="dense"
                          size="small"
                          sx={{
                            mb: { xs: 1, sm: 1.5 },
                            '& .MuiInputLabel-root': { fontSize: { xs: '0.8rem', sm: '0.875rem' } },
                            '& .MuiInputBase-input': { fontSize: { xs: '0.8rem', sm: '0.875rem' } },
                          }}
                        />
                      ))}
                      <TextField
                        label="Gender"
                        value={editedScan.extracted_info?.gender || ''}
                        onChange={(e) => onEditFieldChange('extracted_info.gender', e.target.value)}
                        select
                        fullWidth
                        margin="dense"
                        size="small"
                        sx={{
                          '& .MuiInputLabel-root': { fontSize: { xs: '0.8rem', sm: '0.875rem' } },
                          '& .MuiInputBase-input': { fontSize: { xs: '0.8rem', sm: '0.875rem' } },
                          '& .MuiMenuItem-root': { fontSize: { xs: '0.8rem', sm: '0.875rem' } },
                        }}
                      >
                        <MenuItem value="M">Male</MenuItem>
                        <MenuItem value="F">Female</MenuItem>
                        <MenuItem value="X">Other</MenuItem>
                      </TextField>
                    </Box>
                  ) : (
                    <List
                      dense
                      sx={{
                        '& .MuiListItemText-primary': { fontSize: { xs: '0.8rem', sm: '0.875rem' } },
                        '& .MuiListItemText-secondary': { fontSize: { xs: '0.75rem', sm: '0.8rem' } },
                        '& .MuiSvgIcon-root': { fontSize: { xs: '1rem', sm: '1.25rem' } },
                      }}
                    >
                      {selectedScan.extracted_info?.full_name && (
                        <ListItem>
                          <PersonIcon fontSize="small" sx={{ mr: 1, color: 'text.secondary' }} />
                          <ListItemText primary="Full Name" secondary={selectedScan.extracted_info.full_name} />
                        </ListItem>
                      )}
                      {selectedScan.extracted_info?.document_number && (
                        <ListItem>
                          <FingerprintIcon fontSize="small" sx={{ mr: 1, color: 'text.secondary' }} />
                          <ListItemText
                            primary="Document Number"
                            secondary={selectedScan.extracted_info.document_number}
                          />
                        </ListItem>
                      )}
                      {selectedScan.extracted_info?.birth_date && (
                        <ListItem>
                          <CalendarTodayIcon fontSize="small" sx={{ mr: 1, color: 'text.secondary' }} />
                          <ListItemText primary="Date of Birth" secondary={selectedScan.extracted_info.birth_date} />
                        </ListItem>
                      )}
                      {selectedScan.extracted_info?.expiry_date && (
                        <ListItem>
                          <CalendarTodayIcon fontSize="small" sx={{ mr: 1, color: 'text.secondary' }} />
                          <ListItemText primary="Expiry Date" secondary={selectedScan.extracted_info.expiry_date} />
                        </ListItem>
                      )}
                      {selectedScan.extracted_info?.place_of_issue && (
                        <ListItem>
                          <LocationOnIcon fontSize="small" sx={{ mr: 1, color: 'text.secondary' }} />
                          <ListItemText
                            primary="Place of Issue"
                            secondary={selectedScan.extracted_info.place_of_issue}
                          />
                        </ListItem>
                      )}
                      {selectedScan.extracted_info?.issue_date && (
                        <ListItem>
                          <CalendarTodayIcon fontSize="small" sx={{ mr: 1, color: 'text.secondary' }} />
                          <ListItemText primary="Issue Date" secondary={selectedScan.extracted_info.issue_date} />
                        </ListItem>
                      )}
                      {selectedScan.extracted_info?.gender && (
                        <ListItem>
                          <PersonIcon fontSize="small" sx={{ mr: 1, color: 'text.secondary' }} />
                          <ListItemText primary="Gender" secondary={selectedScan.extracted_info.gender} />
                        </ListItem>
                      )}
                    </List>
                  )}
                </Grid>
              </Grid>
            )}

            {/* Tab Panel 1: Raw Text */}
            {tabValue === 1 && (
              <Box sx={{ px: { xs: 0, sm: 1 } }}>
                <Typography
                  variant="subtitle1"
                  color="primary"
                  gutterBottom
                  sx={{ fontSize: { xs: '0.9rem', sm: '1rem', md: '1.1rem' } }}
                >
                  Raw Extracted Text
                </Typography>
                {editMode ? (
                  <TextField
                    multiline
                    rows={10}
                    value={editedScan.extracted_text || ''}
                    onChange={(e) => onEditFieldChange('extracted_text', e.target.value)}
                    fullWidth
                    variant="outlined"
                    sx={{
                      '& .MuiInputBase-input': {
                        fontSize: { xs: '0.75rem', sm: '0.85rem' },
                        fontFamily: 'monospace',
                      },
                    }}
                  />
                ) : (
                  <Paper
                    elevation={0}
                    variant="outlined"
                    sx={{
                      p: { xs: 1.5, sm: 2 },
                      maxHeight: { xs: 300, sm: 350, md: 400 },
                      overflow: 'auto',
                      fontSize: { xs: '0.75rem', sm: '0.85rem', md: '0.9rem' },
                      lineHeight: { xs: 1.4, sm: 1.5 },
                      fontFamily: 'monospace',
                    }}
                  >
                    {selectedScan.extracted_text}
                  </Paper>
                )}
              </Box>
            )}

            {/* Tab Panel 2: Image */}
            {tabValue === 2 && selectedScan.image_data && (
              <Box sx={{ textAlign: 'center', px: { xs: 0, sm: 1 } }}>
                <Typography
                  variant="subtitle1"
                  color="primary"
                  gutterBottom
                  sx={{ fontSize: { xs: '0.9rem', sm: '1rem', md: '1.1rem' } }}
                >
                  Document Image
                </Typography>
                <Box
                  component="img"
                  src={selectedScan.image_data}
                  alt="Scanned document"
                  sx={{
                    maxWidth: '100%',
                    maxHeight: { xs: 300, sm: 400, md: 500 },
                    boxShadow: 1,
                    border: '1px solid #ddd',
                  }}
                />
              </Box>
            )}
          </>
        )}
      </DialogContent>

      <DialogActions sx={{ px: { xs: 2, sm: 3 }, py: { xs: 1.5, sm: 2 } }}>
        {editMode ? (
          <>
            <Button
              onClick={onCancelEdit}
              color="inherit"
              size={window.innerWidth < 600 ? 'small' : 'medium'}
              sx={{
                fontSize: { xs: '0.75rem', sm: '0.875rem' },
                px: { xs: 1.5, sm: 2 },
                py: { xs: 0.5, sm: 0.75 },
              }}
            >
              Cancel
            </Button>
            <Button
              onClick={onSaveEdit}
              color="primary"
              variant="contained"
              size={window.innerWidth < 600 ? 'small' : 'medium'}
              sx={{
                fontSize: { xs: '0.75rem', sm: '0.875rem' },
                px: { xs: 1.5, sm: 2 },
                py: { xs: 0.5, sm: 0.75 },
              }}
            >
              Save Changes
            </Button>
          </>
        ) : (
          <Button
            onClick={onClose}
            color="primary"
            size={window.innerWidth < 600 ? 'small' : 'medium'}
            sx={{
              fontSize: { xs: '0.75rem', sm: '0.875rem' },
              px: { xs: 1.5, sm: 2 },
              py: { xs: 0.5, sm: 0.75 },
            }}
          >
            Close
          </Button>
        )}
      </DialogActions>
    </Dialog>
  );
};

export default ScanDetailDialog;
