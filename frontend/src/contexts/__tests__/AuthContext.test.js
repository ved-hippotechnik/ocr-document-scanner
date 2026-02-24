import React from 'react';
import { render, screen, act, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';

// ---------------------------------------------------------------------------
// Module mocks
// ---------------------------------------------------------------------------

jest.mock('axios');
import axios from 'axios';

jest.mock('../../config', () => ({
  API_URL: 'http://localhost:5001',
  __esModule: true,
  default: { API_URL: 'http://localhost:5001' },
}));

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

/**
 * A simple consumer component that displays selected values from useAuth
 * so we can assert on them via the rendered DOM.
 */
const AuthConsumer = () => {
  const { useAuth } = require('../AuthContext');
  const { user, loading, isAuthenticated } = useAuth();

  return (
    <div>
      <span data-testid="loading">{String(loading)}</span>
      <span data-testid="isAuthenticated">{String(isAuthenticated)}</span>
      <span data-testid="user">{user ? JSON.stringify(user) : 'null'}</span>
    </div>
  );
};

/**
 * Render the AuthProvider wrapping a consumer that exposes auth state.
 * Optionally wraps an additional child component.
 */
const renderWithAuth = async (ui = <AuthConsumer />) => {
  // Import after mocks are in place
  const { AuthProvider } = require('../AuthContext');

  let result;
  await act(async () => {
    result = render(<AuthProvider>{ui}</AuthProvider>);
  });
  return result;
};

// Shortcut to get the exposed auth actions from a test component
const AuthActionsConsumer = ({ onRender }) => {
  const { useAuth } = require('../AuthContext');
  const auth = useAuth();
  onRender(auth);
  return <div data-testid="actions-ready">ready</div>;
};

// ---------------------------------------------------------------------------
// Setup / teardown
// ---------------------------------------------------------------------------

beforeEach(() => {
  jest.clearAllMocks();
  localStorage.clear();

  // Suppress console.error for expected async errors in tests
  jest.spyOn(console, 'error').mockImplementation(() => {});

  // Default axios mocks so interceptors attach cleanly
  axios.interceptors = {
    request: { use: jest.fn(() => 1), eject: jest.fn() },
    response: { use: jest.fn(() => 2), eject: jest.fn() },
  };
});

afterEach(() => {
  console.error.mockRestore?.();
});

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------

describe('AuthContext', () => {
  // -------------------------------------------------------------------------
  // Provider rendering
  // -------------------------------------------------------------------------
  describe('AuthProvider', () => {
    test('renders children without crashing', async () => {
      // When no token is stored, checkAuth will set loading=false immediately
      axios.get.mockRejectedValue({ response: { status: 401 } });

      await renderWithAuth(<div data-testid="child">child content</div>);
      expect(screen.getByTestId('child')).toBeInTheDocument();
    });

    test('sets loading to false after the initial auth check completes', async () => {
      axios.get.mockRejectedValue(new Error('no token'));

      await renderWithAuth();

      await waitFor(() => {
        expect(screen.getByTestId('loading').textContent).toBe('false');
      });
    });

    test('sets isAuthenticated to false when no token is present', async () => {
      // No token in localStorage — checkAuth short-circuits without calling axios
      await renderWithAuth();

      await waitFor(() => {
        expect(screen.getByTestId('isAuthenticated').textContent).toBe('false');
      });
    });

    test('sets isAuthenticated to true when a valid token is stored', async () => {
      localStorage.setItem('access_token', 'valid-token');
      localStorage.setItem('user', JSON.stringify({ id: 1, email: 'user@test.com' }));

      axios.get.mockResolvedValue({
        data: { user: { id: 1, email: 'user@test.com', name: 'Test User' } },
      });

      await renderWithAuth();

      await waitFor(() => {
        expect(screen.getByTestId('isAuthenticated').textContent).toBe('true');
      });
    });

    test('sets user data when a valid token is found', async () => {
      const mockUser = { id: 1, email: 'user@test.com', name: 'Test User' };
      localStorage.setItem('access_token', 'valid-token');
      localStorage.setItem('user', JSON.stringify(mockUser));
      axios.get.mockResolvedValue({ data: { user: mockUser } });

      await renderWithAuth();

      await waitFor(() => {
        const userEl = screen.getByTestId('user');
        expect(JSON.parse(userEl.textContent)).toMatchObject({ email: 'user@test.com' });
      });
    });

    test('clears tokens and sets isAuthenticated=false when the profile request fails', async () => {
      localStorage.setItem('access_token', 'expired-token');
      localStorage.setItem('user', JSON.stringify({ id: 1 }));
      localStorage.setItem('refresh_token', 'refresh');

      axios.get.mockRejectedValue({ response: { status: 401 } });

      await renderWithAuth();

      await waitFor(() => {
        expect(screen.getByTestId('isAuthenticated').textContent).toBe('false');
        expect(localStorage.getItem('access_token')).toBeNull();
        expect(localStorage.getItem('refresh_token')).toBeNull();
      });
    });
  });

  // -------------------------------------------------------------------------
  // useAuth hook
  // -------------------------------------------------------------------------
  describe('useAuth hook', () => {
    test('throws when used outside an AuthProvider', () => {
      const { useAuth } = require('../AuthContext');

      const BadConsumer = () => {
        useAuth(); // should throw
        return null;
      };

      // Suppress the React error boundary noise
      const spy = jest.spyOn(console, 'error').mockImplementation(() => {});
      expect(() => render(<BadConsumer />)).toThrow(
        'useAuth must be used within an AuthProvider'
      );
      spy.mockRestore();
    });

    test('returns all expected values from the context', async () => {
      axios.get.mockRejectedValue(new Error('no session'));

      let capturedAuth;
      const { AuthProvider } = require('../AuthContext');

      await act(async () => {
        render(
          <AuthProvider>
            <AuthActionsConsumer onRender={(auth) => { capturedAuth = auth; }} />
          </AuthProvider>
        );
      });

      await waitFor(() =>
        expect(screen.getByTestId('actions-ready')).toBeInTheDocument()
      );

      expect(typeof capturedAuth.login).toBe('function');
      expect(typeof capturedAuth.logout).toBe('function');
      expect(typeof capturedAuth.register).toBe('function');
      expect(typeof capturedAuth.updateProfile).toBe('function');
      expect(typeof capturedAuth.changePassword).toBe('function');
      expect(typeof capturedAuth.checkAuth).toBe('function');
    });
  });

  // -------------------------------------------------------------------------
  // login()
  // -------------------------------------------------------------------------
  describe('login()', () => {
    test('returns { success: true } on valid credentials', async () => {
      const mockResponse = {
        access_token: 'tok_access',
        refresh_token: 'tok_refresh',
        user: { id: 1, email: 'a@b.com' },
      };
      axios.get.mockRejectedValue(new Error('no prior session'));
      axios.post.mockResolvedValue({ data: mockResponse });

      let auth;
      const { AuthProvider } = require('../AuthContext');

      await act(async () => {
        render(
          <AuthProvider>
            <AuthActionsConsumer onRender={(a) => { auth = a; }} />
          </AuthProvider>
        );
      });

      await waitFor(() => expect(screen.getByTestId('actions-ready')).toBeInTheDocument());

      let result;
      await act(async () => {
        result = await auth.login('a@b.com', 'password123');
      });

      expect(result.success).toBe(true);
    });

    test('stores tokens in localStorage on successful login', async () => {
      const mockResponse = {
        access_token: 'tok_access',
        refresh_token: 'tok_refresh',
        user: { id: 1, email: 'a@b.com' },
      };
      axios.get.mockRejectedValue(new Error('no prior session'));
      axios.post.mockResolvedValue({ data: mockResponse });

      let auth;
      const { AuthProvider } = require('../AuthContext');

      await act(async () => {
        render(
          <AuthProvider>
            <AuthActionsConsumer onRender={(a) => { auth = a; }} />
          </AuthProvider>
        );
      });

      await waitFor(() => expect(screen.getByTestId('actions-ready')).toBeInTheDocument());

      await act(async () => {
        await auth.login('a@b.com', 'password123');
      });

      expect(localStorage.getItem('access_token')).toBe('tok_access');
      expect(localStorage.getItem('refresh_token')).toBe('tok_refresh');
    });

    test('returns { success: false, error } when the API rejects', async () => {
      axios.get.mockRejectedValue(new Error('no prior session'));
      axios.post.mockRejectedValue({
        response: { data: { error: 'Invalid credentials' } },
      });

      let auth;
      const { AuthProvider } = require('../AuthContext');

      await act(async () => {
        render(
          <AuthProvider>
            <AuthActionsConsumer onRender={(a) => { auth = a; }} />
          </AuthProvider>
        );
      });

      await waitFor(() => expect(screen.getByTestId('actions-ready')).toBeInTheDocument());

      let result;
      await act(async () => {
        result = await auth.login('bad@email.com', 'wrongpw');
      });

      expect(result.success).toBe(false);
      expect(result.error).toBe('Invalid credentials');
    });

    test('falls back to "Login failed" when no error detail is provided', async () => {
      axios.get.mockRejectedValue(new Error('no prior session'));
      axios.post.mockRejectedValue({ response: {} });

      let auth;
      const { AuthProvider } = require('../AuthContext');

      await act(async () => {
        render(
          <AuthProvider>
            <AuthActionsConsumer onRender={(a) => { auth = a; }} />
          </AuthProvider>
        );
      });

      await waitFor(() => expect(screen.getByTestId('actions-ready')).toBeInTheDocument());

      let result;
      await act(async () => {
        result = await auth.login('a@b.com', 'pw');
      });

      expect(result.success).toBe(false);
      expect(result.error).toBe('Login failed');
    });
  });

  // -------------------------------------------------------------------------
  // logout()
  // -------------------------------------------------------------------------
  describe('logout()', () => {
    test('clears localStorage tokens on logout', async () => {
      localStorage.setItem('access_token', 'tok');
      localStorage.setItem('refresh_token', 'ref');
      localStorage.setItem('user', JSON.stringify({ id: 1 }));

      axios.get.mockRejectedValue(new Error('not authenticated'));

      let auth;
      const { AuthProvider } = require('../AuthContext');

      await act(async () => {
        render(
          <AuthProvider>
            <AuthActionsConsumer onRender={(a) => { auth = a; }} />
          </AuthProvider>
        );
      });

      await waitFor(() => expect(screen.getByTestId('actions-ready')).toBeInTheDocument());

      act(() => {
        auth.logout();
      });

      expect(localStorage.getItem('access_token')).toBeNull();
      expect(localStorage.getItem('refresh_token')).toBeNull();
      expect(localStorage.getItem('user')).toBeNull();
    });

    test('sets isAuthenticated to false after logout', async () => {
      const mockUser = { id: 1, email: 'u@test.com' };
      localStorage.setItem('access_token', 'tok');
      localStorage.setItem('user', JSON.stringify(mockUser));
      axios.get.mockResolvedValue({ data: { user: mockUser } });

      let auth;
      const { AuthProvider } = require('../AuthContext');

      await act(async () => {
        render(
          <AuthProvider>
            <AuthActionsConsumer onRender={(a) => { auth = a; }} />
            <AuthConsumer />
          </AuthProvider>
        );
      });

      await waitFor(() =>
        expect(screen.getByTestId('isAuthenticated').textContent).toBe('true')
      );

      act(() => {
        auth.logout();
      });

      await waitFor(() => {
        expect(screen.getByTestId('isAuthenticated').textContent).toBe('false');
      });
    });

    test('sets user to null after logout', async () => {
      const mockUser = { id: 1, email: 'u@test.com' };
      localStorage.setItem('access_token', 'tok');
      localStorage.setItem('user', JSON.stringify(mockUser));
      axios.get.mockResolvedValue({ data: { user: mockUser } });

      let auth;
      const { AuthProvider } = require('../AuthContext');

      await act(async () => {
        render(
          <AuthProvider>
            <AuthActionsConsumer onRender={(a) => { auth = a; }} />
            <AuthConsumer />
          </AuthProvider>
        );
      });

      await waitFor(() =>
        expect(screen.getByTestId('user').textContent).not.toBe('null')
      );

      act(() => {
        auth.logout();
      });

      await waitFor(() => {
        expect(screen.getByTestId('user').textContent).toBe('null');
      });
    });
  });

  // -------------------------------------------------------------------------
  // register()
  // -------------------------------------------------------------------------
  describe('register()', () => {
    test('returns { success: true } with valid registration data', async () => {
      const mockResponse = {
        access_token: 'tok_access',
        refresh_token: 'tok_refresh',
        user: { id: 2, email: 'new@test.com' },
      };
      axios.get.mockRejectedValue(new Error('no prior session'));
      axios.post.mockResolvedValue({ data: mockResponse });

      let auth;
      const { AuthProvider } = require('../AuthContext');

      await act(async () => {
        render(
          <AuthProvider>
            <AuthActionsConsumer onRender={(a) => { auth = a; }} />
          </AuthProvider>
        );
      });

      await waitFor(() => expect(screen.getByTestId('actions-ready')).toBeInTheDocument());

      let result;
      await act(async () => {
        result = await auth.register({
          email: 'new@test.com',
          password: 'secure123',
          name: 'New User',
        });
      });

      expect(result.success).toBe(true);
    });

    test('stores tokens in localStorage after successful registration', async () => {
      const mockResponse = {
        access_token: 'reg_access',
        refresh_token: 'reg_refresh',
        user: { id: 2, email: 'new@test.com' },
      };
      axios.get.mockRejectedValue(new Error('no prior session'));
      axios.post.mockResolvedValue({ data: mockResponse });

      let auth;
      const { AuthProvider } = require('../AuthContext');

      await act(async () => {
        render(
          <AuthProvider>
            <AuthActionsConsumer onRender={(a) => { auth = a; }} />
          </AuthProvider>
        );
      });

      await waitFor(() => expect(screen.getByTestId('actions-ready')).toBeInTheDocument());

      await act(async () => {
        await auth.register({ email: 'new@test.com', password: 'pw', name: 'User' });
      });

      expect(localStorage.getItem('access_token')).toBe('reg_access');
    });

    test('returns { success: false, error } when registration fails', async () => {
      axios.get.mockRejectedValue(new Error('no prior session'));
      axios.post.mockRejectedValue({
        response: { data: { error: 'Email already in use' } },
      });

      let auth;
      const { AuthProvider } = require('../AuthContext');

      await act(async () => {
        render(
          <AuthProvider>
            <AuthActionsConsumer onRender={(a) => { auth = a; }} />
          </AuthProvider>
        );
      });

      await waitFor(() => expect(screen.getByTestId('actions-ready')).toBeInTheDocument());

      let result;
      await act(async () => {
        result = await auth.register({ email: 'dup@test.com', password: 'pw', name: 'User' });
      });

      expect(result.success).toBe(false);
      expect(result.error).toBe('Email already in use');
    });
  });

  // -------------------------------------------------------------------------
  // updateProfile()
  // -------------------------------------------------------------------------
  describe('updateProfile()', () => {
    test('returns { success: true } when the update succeeds', async () => {
      const updatedUser = { id: 1, email: 'u@test.com', name: 'Updated Name' };
      axios.get.mockRejectedValue(new Error('no prior session'));
      axios.put.mockResolvedValue({ data: { user: updatedUser } });

      let auth;
      const { AuthProvider } = require('../AuthContext');

      await act(async () => {
        render(
          <AuthProvider>
            <AuthActionsConsumer onRender={(a) => { auth = a; }} />
          </AuthProvider>
        );
      });

      await waitFor(() => expect(screen.getByTestId('actions-ready')).toBeInTheDocument());

      let result;
      await act(async () => {
        result = await auth.updateProfile({ name: 'Updated Name' });
      });

      expect(result.success).toBe(true);
    });

    test('updates user in localStorage after successful profile update', async () => {
      const updatedUser = { id: 1, email: 'u@test.com', name: 'Updated Name' };
      axios.get.mockRejectedValue(new Error('no prior session'));
      axios.put.mockResolvedValue({ data: { user: updatedUser } });

      let auth;
      const { AuthProvider } = require('../AuthContext');

      await act(async () => {
        render(
          <AuthProvider>
            <AuthActionsConsumer onRender={(a) => { auth = a; }} />
          </AuthProvider>
        );
      });

      await waitFor(() => expect(screen.getByTestId('actions-ready')).toBeInTheDocument());

      await act(async () => {
        await auth.updateProfile({ name: 'Updated Name' });
      });

      const stored = JSON.parse(localStorage.getItem('user'));
      expect(stored.name).toBe('Updated Name');
    });

    test('returns { success: false, error } when the update fails', async () => {
      axios.get.mockRejectedValue(new Error('no prior session'));
      axios.put.mockRejectedValue({
        response: { data: { error: 'Validation error' } },
      });

      let auth;
      const { AuthProvider } = require('../AuthContext');

      await act(async () => {
        render(
          <AuthProvider>
            <AuthActionsConsumer onRender={(a) => { auth = a; }} />
          </AuthProvider>
        );
      });

      await waitFor(() => expect(screen.getByTestId('actions-ready')).toBeInTheDocument());

      let result;
      await act(async () => {
        result = await auth.updateProfile({ name: '' });
      });

      expect(result.success).toBe(false);
    });
  });

  // -------------------------------------------------------------------------
  // changePassword()
  // -------------------------------------------------------------------------
  describe('changePassword()', () => {
    test('returns { success: true } when the password change succeeds', async () => {
      axios.get.mockRejectedValue(new Error('no prior session'));
      axios.post.mockResolvedValue({ data: { message: 'Password changed successfully' } });

      let auth;
      const { AuthProvider } = require('../AuthContext');

      await act(async () => {
        render(
          <AuthProvider>
            <AuthActionsConsumer onRender={(a) => { auth = a; }} />
          </AuthProvider>
        );
      });

      await waitFor(() => expect(screen.getByTestId('actions-ready')).toBeInTheDocument());

      let result;
      await act(async () => {
        result = await auth.changePassword('oldPw', 'newPw');
      });

      expect(result.success).toBe(true);
      expect(result.message).toBe('Password changed successfully');
    });

    test('returns { success: false, error } when the password change fails', async () => {
      axios.get.mockRejectedValue(new Error('no prior session'));
      axios.post.mockRejectedValue({
        response: { data: { error: 'Current password is incorrect' } },
      });

      let auth;
      const { AuthProvider } = require('../AuthContext');

      await act(async () => {
        render(
          <AuthProvider>
            <AuthActionsConsumer onRender={(a) => { auth = a; }} />
          </AuthProvider>
        );
      });

      await waitFor(() => expect(screen.getByTestId('actions-ready')).toBeInTheDocument());

      let result;
      await act(async () => {
        result = await auth.changePassword('wrong', 'new');
      });

      expect(result.success).toBe(false);
      expect(result.error).toBe('Current password is incorrect');
    });
  });

  // -------------------------------------------------------------------------
  // Axios interceptors
  // -------------------------------------------------------------------------
  describe('axios interceptors', () => {
    test('attaches request and response interceptors on mount', async () => {
      axios.get.mockRejectedValue(new Error('no session'));
      await renderWithAuth();
      expect(axios.interceptors.request.use).toHaveBeenCalled();
      expect(axios.interceptors.response.use).toHaveBeenCalled();
    });

    test('ejects interceptors on unmount', async () => {
      axios.get.mockRejectedValue(new Error('no session'));
      const { unmount } = await renderWithAuth();

      act(() => {
        unmount();
      });

      expect(axios.interceptors.request.eject).toHaveBeenCalled();
      expect(axios.interceptors.response.eject).toHaveBeenCalled();
    });
  });
});
