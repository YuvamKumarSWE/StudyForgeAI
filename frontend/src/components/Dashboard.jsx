import { useState, useRef, useEffect } from 'react';
import { Box, Container, Typography, Paper, Tabs, Tab, Button, Divider, Alert, CircularProgress } from '@mui/material';
import Navbar from './Navbar';
import FileUpload from './FileUpload';
import WebPageInput from './WebPageInput';
import TextInput from './TextInput';
import CollectedItems from './CollectedItems';
import OutputDisplay from './OutputDisplay';
import apiService from '../services/api';

// Icons
import UploadFileIcon from '@mui/icons-material/UploadFile';
import LinkIcon from '@mui/icons-material/Link';
import TextFieldsIcon from '@mui/icons-material/TextFields';
import AutoAwesomeIcon from '@mui/icons-material/AutoAwesome';

function TabPanel(props) {
  const { children, value, index, ...other } = props;

  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`simple-tabpanel-${index}`}
      aria-labelledby={`simple-tab-${index}`}
      {...other}
    >
      {value === index && (
        <Box sx={{ py: 3 }}>
          {children}
        </Box>
      )}
    </div>
  );
}

function Dashboard() {
  const [items, setItems] = useState([]);
  const [output, setOutput] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [videoOverlayClosed, setVideoOverlayClosed] = useState(false);
  const [tabValue, setTabValue] = useState(0);

  const outputRef = useRef(null);

  const handleTabChange = (event, newValue) => {
    setTabValue(newValue);
  };

  const handleAddItem = (item) => {
    setItems([...items, item]);
  };

  const handleRemoveItem = (index) => {
    setItems(items.filter((_, i) => i !== index));
  };

  const handleSubmit = async () => {
    if (items.length === 0) {
      setError('Please add at least one source before generating.');
      return;
    }

    setLoading(true);
    setError('');
    setOutput('');
    setVideoOverlayClosed(false);

    try {
      const formData = new FormData();

      const pdfItems = items.filter(item => item.type === 'pdf');
      pdfItems.forEach((item) => {
        if (item.file) {
          formData.append('pdfs', item.file);
        }
      });

      const otherSources = {
        urls: items.filter(item => item.type === 'webpage').map(item => item.name),
        videos: items.filter(item => item.type === 'video').map(item => item.name),
        text: items.filter(item => item.type === 'text').map(item => item.name)
      };

      formData.append('sources', JSON.stringify(otherSources));


      const response = await apiService.getOutput(formData);

      if (response && response.study_guide) {
        setOutput(response.study_guide);
      } else if (typeof response === 'string') {
        setOutput(response);
      } else {
        setOutput(JSON.stringify(response, null, 2));
      }
    } catch (err) {
      console.error('Error:', err);
      let errorMessage = 'Failed to generate study guide. Please try again.';

      if (err.response?.data?.detail) {
        errorMessage = err.response.data.detail;
      } else if (err.message) {
        errorMessage = err.message;
      }

      if (errorMessage.includes('rate limit') || errorMessage.includes('quota')) {
        errorMessage = '⚠️ API rate limit reached. Please wait 1-2 minutes and try again.';
      }

      setError(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (!loading && (output || error) && outputRef.current) {
      setTimeout(() => {
        outputRef.current.scrollIntoView({
          behavior: 'smooth',
          block: 'start'
        });
      }, 100);
    }
  }, [loading, output, error]);

  const handleCloseVideoOverlay = () => {
    setVideoOverlayClosed(true);
  };

  return (
    <Box sx={{ minHeight: '100vh', pt: 12, pb: 8 }}>
      <Navbar />

      <Container maxWidth="lg">
        <Box sx={{ mb: 6, display: 'flex', justifyContent: 'space-between', alignItems: 'flex-end' }}>
          <Box>
            <Typography variant="h4" sx={{ fontWeight: 600, color: '#EDEDED', mb: 1 }}>
              Dashboard
            </Typography>
            <Typography variant="body1" sx={{ color: '#A1A1A1' }}>
              Manage your sources and generate study guides.
            </Typography>
          </Box>
        </Box>

        <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', lg: '2fr 1fr' }, gap: 4 }}>
          {/* Main Input Area */}
          <Box>
            <Paper sx={{ mb: 4, overflow: 'hidden' }}>
              <Tabs
                value={tabValue}
                onChange={handleTabChange}
                aria-label="source tabs"
                sx={{
                  borderBottom: 1,
                  borderColor: 'divider',
                  '& .MuiTab-root': { textTransform: 'none', fontWeight: 500, minHeight: 48 }
                }}
              >
                <Tab icon={<UploadFileIcon sx={{ fontSize: 20 }} />} iconPosition="start" label="Upload Files" />
                <Tab icon={<LinkIcon sx={{ fontSize: 20 }} />} iconPosition="start" label="Web & Video" />
                <Tab icon={<TextFieldsIcon sx={{ fontSize: 20 }} />} iconPosition="start" label="Text Input" />
              </Tabs>

              <Box sx={{ p: 3 }}>
                <TabPanel value={tabValue} index={0}>
                  <FileUpload onAdd={handleAddItem} />
                </TabPanel>
                <TabPanel value={tabValue} index={1}>
                  <WebPageInput onAdd={handleAddItem} />
                </TabPanel>
                <TabPanel value={tabValue} index={2}>
                  <TextInput onAdd={handleAddItem} />
                </TabPanel>
              </Box>
            </Paper>

            {/* Output Section */}
            {(output || loading || error) && (
              <Box ref={outputRef}>
                <Typography variant="h5" sx={{ mb: 2, fontWeight: 600 }}>
                  Generated Guide
                </Typography>
                <OutputDisplay
                  output={output}
                  loading={loading}
                  error={error}
                  showVideoOverlay={!videoOverlayClosed}
                  onCloseVideoOverlay={handleCloseVideoOverlay}
                />
              </Box>
            )}
          </Box>

          {/* Sidebar: Collected Items */}
          <Box>
            <Paper sx={{ p: 3, position: 'sticky', top: 100 }}>
              <Typography variant="h6" sx={{ mb: 2, fontWeight: 600 }}>
                Sources ({items.length})
              </Typography>
              <Divider sx={{ mb: 2 }} />

              <CollectedItems
                items={items}
                onRemove={handleRemoveItem}
                onSubmit={handleSubmit}
                compact={true} // Pass a prop to make it look cleaner in sidebar
              />

              <Button
                fullWidth
                variant="contained"
                color="primary"
                size="large"
                startIcon={loading ? <CircularProgress size={20} color="inherit" /> : <AutoAwesomeIcon />}
                onClick={handleSubmit}
                disabled={loading || items.length === 0}
                sx={{ mt: 3 }}
              >
                {loading ? 'Generating...' : 'Generate Guide'}
              </Button>

              {error && (
                <Alert severity="error" sx={{ mt: 2, fontSize: '0.875rem' }}>
                  {error}
                </Alert>
              )}
            </Paper>
          </Box>
        </Box>
      </Container>
    </Box>
  );
}

export default Dashboard;