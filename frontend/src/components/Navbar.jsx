import React from 'react';
import { AppBar, Toolbar, Typography, Box, Button, IconButton, Avatar, Tooltip, Container } from '@mui/material';
import AutoStoriesIcon from '@mui/icons-material/AutoStories';
import { Link, useLocation, useNavigate } from 'react-router-dom';

function Navbar() {
  const location = useLocation();
  const navigate = useNavigate();
  const isDashboard = location.pathname === '/dashboard';
  const isProfile = location.pathname === '/profile';

  return (
    <AppBar
      position="fixed"
      elevation={0}
      sx={{
        zIndex: 1200,
        borderBottom: '1px solid rgba(255, 255, 255, 0.1)',
        bgcolor: 'rgba(2, 2, 5, 0.9)',
        backdropFilter: 'blur(10px)',
      }}
    >
      <Container maxWidth="xl" disableGutters>
        <Toolbar sx={{ minHeight: 80, px: { xs: 2, md: 4 } }}>
          <Box
            onClick={() => navigate('/')}
            sx={{
              display: 'flex',
              alignItems: 'center',
              cursor: 'pointer',
              mr: 8,
              borderRight: { md: '1px solid rgba(255, 255, 255, 0.1)' },
              pr: 4,
              height: 80,
            }}
          >
            <AutoStoriesIcon sx={{ mr: 2, color: 'primary.main', fontSize: 28 }} />
            <Typography
              variant="h6"
              component="div"
              sx={{
                fontWeight: 600,
                color: '#fff',
                letterSpacing: '-0.02em',
              }}
            >
              StudyForgeAI
            </Typography>
          </Box>

          <Box sx={{ flexGrow: 1 }} />

          <Box sx={{ display: 'flex', gap: 0, alignItems: 'center', height: 80 }}>
            {!isDashboard && !isProfile && (
              <>
                <Button
                  component={Link}
                  to="/login"
                  color="inherit"
                  sx={{
                    color: '#fff',
                    height: '100%',
                    px: 3,
                    borderLeft: '1px solid rgba(255, 255, 255, 0.1)',
                    borderRadius: 0,
                  }}
                >
                  Log in
                </Button>
                <Button
                  component={Link}
                  to="/signup"
                  variant="contained"
                  color="primary"
                  sx={{
                    ml: 0,
                    height: '100%',
                    px: 4,
                    borderRadius: 0,
                    boxShadow: 'none',
                  }}
                >
                  Get Started
                </Button>
              </>
            )}

            {(isDashboard || isProfile) && (
              <>
                <Button
                  component={Link}
                  to="/dashboard"
                  color="inherit"
                  sx={{
                    color: isDashboard ? 'primary.main' : 'text.secondary',
                    height: '100%',
                    px: 3,
                    borderLeft: '1px solid rgba(255, 255, 255, 0.1)',
                    borderRadius: 0,
                  }}
                >
                  Dashboard
                </Button>
                <Box sx={{ pl: 3, borderLeft: '1px solid rgba(255, 255, 255, 0.1)', height: '100%', display: 'flex', alignItems: 'center' }}>
                  <Tooltip title="User Profile">
                    <IconButton component={Link} to="/profile" sx={{ p: 0 }}>
                      <Avatar
                        sx={{
                          width: 36,
                          height: 36,
                          bgcolor: 'primary.main',
                          color: '#fff',
                          fontSize: '0.9rem',
                          borderRadius: '4px'
                        }}
                      >
                        YK
                      </Avatar>
                    </IconButton>
                  </Tooltip>
                </Box>
              </>
            )}
          </Box>
        </Toolbar>
      </Container>
    </AppBar>
  );
}

export default Navbar;
