import React from 'react';
import { render, screen, fireEvent, waitFor, act } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import '@testing-library/jest-dom';

// ---------------------------------------------------------------------------
// Module mocks — declared before any dynamic imports
// ---------------------------------------------------------------------------

jest.mock('axios');
import axios from 'axios';

// react-router-dom — capture navigation calls for assertion
const mockNavigate = jest.fn();
jest.mock('react-router-dom', () => ({
  ...jest.requireActual('react-router-dom'),
  useNavigate: () => mockNavigate,
}));

jest.mock('../../config', () => ({
  API_URL: 'http://localhost:5001',
  __esModule: true,
  default: { API_URL: 'http://localhost:5001' },
}));

// Responsive hook — return stable desktop values
jest.mock('../../utils/responsive', () => ({
  useScreenSize: jest.fn(() => ({
    isMobile: false,
    isTablet: false,
    isDesktop: true,
    isLargeDesktop: true,
    isSmallScreen: false,
    isMediumScreen: false,
    isLargeScreen: true,
    isPortrait: false,
    isLandscape: true,
  })),
  getResponsiveSpacing: jest.fn(() => ({ padding: 4, margin: 3, gap: 3 })),
  getResponsiveDimensions: jest.fn(() => ({ height: 250, padding: 4 })),
  getResponsiveIconSize: jest.fn(() => 56),
  getResponsiveButtonSize: jest.fn(() => 'large'),
}));

// Dynamic import so all mocks are applied before the module is evaluated
let LoginForm;
beforeAll(async () => {
  const mod = await import('../Auth/LoginForm');
  LoginForm = mod.default;
});

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

const renderLoginForm = (props = {}) => render(<LoginForm {...props} />);

const fillEmail = (email) => {
  const input = screen.getByRole('textbox', { name: /email address/i });
  fireEvent.change(input, { target: { name: 'email', value: email } });
  return input;
};

const fillPassword = (password) => {
  // Password inputs don't appear under "textbox" role — query by label text
  const input = screen.getByLabelText(/^password$/i);
  fireEvent.change(input, { target: { name: 'password', value: password } });
  return input;
};

const submitForm = () => {
  const btn = screen.getByRole('button', { name: /sign in/i });
  fireEvent.click(btn);
};

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------
describe('LoginForm', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    localStorage.clear();
  });

  // -------------------------------------------------------------------------
  // Rendering
  // -------------------------------------------------------------------------
  describe('initial render', () => {
    test('renders without crashing', () => {
      const { container } = renderLoginForm();
      expect(container).toBeTruthy();
    });

    test('renders the "Welcome Back" heading', () => {
      renderLoginForm();
      expect(screen.getByRole('heading', { name: /welcome back/i })).toBeInTheDocument();
    });

    test('renders the email input field', () => {
      renderLoginForm();
      expect(screen.getByRole('textbox', { name: /email address/i })).toBeInTheDocument();
    });

    test('renders the password input field', () => {
      renderLoginForm();
      expect(screen.getByLabelText(/^password$/i)).toBeInTheDocument();
    });

    test('renders the Sign In submit button', () => {
      renderLoginForm();
      expect(screen.getByRole('button', { name: /sign in/i })).toBeInTheDocument();
    });

    test('Sign In button is enabled on initial render', () => {
      renderLoginForm();
      expect(screen.getByRole('button', { name: /sign in/i })).not.toBeDisabled();
    });

    test('renders the "Forgot password?" link', () => {
      renderLoginForm();
      expect(screen.getByRole('button', { name: /forgot password/i })).toBeInTheDocument();
    });

    test('renders the "Sign up" link', () => {
      renderLoginForm();
      expect(screen.getByRole('button', { name: /sign up/i })).toBeInTheDocument();
    });

    test('renders the password visibility toggle button', () => {
      renderLoginForm();
      // aria-label alternates between "Show password" / "Hide password"
      expect(screen.getByRole('button', { name: /show password/i })).toBeInTheDocument();
    });

    test('does not show an error alert initially', () => {
      renderLoginForm();
      expect(screen.queryByRole('alert')).not.toBeInTheDocument();
    });

    test('password field is of type "password" by default', () => {
      renderLoginForm();
      const passwordInput = screen.getByLabelText(/^password$/i);
      expect(passwordInput).toHaveAttribute('type', 'password');
    });
  });

  // -------------------------------------------------------------------------
  // User input
  // -------------------------------------------------------------------------
  describe('user input', () => {
    test('updates the email field value on change', () => {
      renderLoginForm();
      const input = fillEmail('user@example.com');
      expect(input.value).toBe('user@example.com');
    });

    test('updates the password field value on change', () => {
      renderLoginForm();
      const input = fillPassword('mysecretpw');
      expect(input.value).toBe('mysecretpw');
    });

    test('toggles password visibility when the eye icon button is clicked', async () => {
      renderLoginForm();
      const toggle = screen.getByRole('button', { name: /show password/i });

      await act(async () => {
        fireEvent.click(toggle);
      });

      expect(screen.getByLabelText(/^password$/i)).toHaveAttribute('type', 'text');
      expect(screen.getByRole('button', { name: /hide password/i })).toBeInTheDocument();
    });

    test('toggles password back to hidden when eye icon is clicked again', async () => {
      renderLoginForm();
      const toggle = screen.getByRole('button', { name: /show password/i });

      await act(async () => {
        fireEvent.click(toggle);
        fireEvent.click(screen.getByRole('button', { name: /hide password/i }));
      });

      expect(screen.getByLabelText(/^password$/i)).toHaveAttribute('type', 'password');
    });
  });

  // -------------------------------------------------------------------------
  // Validation
  // -------------------------------------------------------------------------
  describe('form validation', () => {
    test('shows "Email is required" error when email is empty on submit', async () => {
      renderLoginForm();
      await act(async () => { submitForm(); });
      expect(screen.getByText(/email is required/i)).toBeInTheDocument();
    });

    test('shows "Password is required" error when password is empty on submit', async () => {
      renderLoginForm();
      fillEmail('user@example.com');
      await act(async () => { submitForm(); });
      expect(screen.getByText(/password is required/i)).toBeInTheDocument();
    });

    test('shows "Invalid email format" for a malformed email address', async () => {
      renderLoginForm();
      fillEmail('not-an-email');
      fillPassword('password');
      await act(async () => { submitForm(); });
      expect(screen.getByText(/invalid email format/i)).toBeInTheDocument();
    });

    test('does not call axios.post when validation fails', async () => {
      renderLoginForm();
      await act(async () => { submitForm(); });
      expect(axios.post).not.toHaveBeenCalled();
    });

    test('clears the email error when the user starts typing in the email field', async () => {
      renderLoginForm();
      // Trigger the error first
      await act(async () => { submitForm(); });
      expect(screen.getByText(/email is required/i)).toBeInTheDocument();

      // Now type in the email field
      const emailInput = screen.getByRole('textbox', { name: /email address/i });
      fireEvent.change(emailInput, { target: { name: 'email', value: 'a' } });

      await waitFor(() => {
        expect(screen.queryByText(/email is required/i)).not.toBeInTheDocument();
      });
    });

    test('clears the password error when the user starts typing in the password field', async () => {
      renderLoginForm();
      fillEmail('user@example.com');
      await act(async () => { submitForm(); });
      expect(screen.getByText(/password is required/i)).toBeInTheDocument();

      const pwInput = screen.getByLabelText(/^password$/i);
      fireEvent.change(pwInput, { target: { name: 'password', value: 'x' } });

      await waitFor(() => {
        expect(screen.queryByText(/password is required/i)).not.toBeInTheDocument();
      });
    });
  });

  // -------------------------------------------------------------------------
  // Loading state
  // -------------------------------------------------------------------------
  describe('loading state', () => {
    test('disables the Sign In button while the API request is in-flight', async () => {
      // Never-resolving promise keeps loading=true
      axios.post.mockReturnValue(new Promise(() => {}));

      renderLoginForm();
      fillEmail('user@example.com');
      fillPassword('password123');

      await act(async () => { submitForm(); });

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /sign in/i })).toBeDisabled();
      });
    });

    test('shows a circular progress indicator while the request is in-flight', async () => {
      axios.post.mockReturnValue(new Promise(() => {}));

      renderLoginForm();
      fillEmail('user@example.com');
      fillPassword('password123');

      await act(async () => { submitForm(); });

      await waitFor(() => {
        // MUI CircularProgress renders with role="progressbar"
        expect(screen.getByRole('progressbar')).toBeInTheDocument();
      });
    });
  });

  // -------------------------------------------------------------------------
  // Successful login
  // -------------------------------------------------------------------------
  describe('successful login', () => {
    const successResponse = {
      access_token: 'tok_access',
      refresh_token: 'tok_refresh',
      user: { id: 1, email: 'user@example.com', name: 'Test User' },
    };

    test('stores access_token in localStorage on success', async () => {
      axios.post.mockResolvedValue({ data: successResponse });

      renderLoginForm();
      fillEmail('user@example.com');
      fillPassword('password123');

      await act(async () => { submitForm(); });

      await waitFor(() => {
        expect(localStorage.getItem('access_token')).toBe('tok_access');
      });
    });

    test('stores refresh_token in localStorage on success', async () => {
      axios.post.mockResolvedValue({ data: successResponse });

      renderLoginForm();
      fillEmail('user@example.com');
      fillPassword('password123');

      await act(async () => { submitForm(); });

      await waitFor(() => {
        expect(localStorage.getItem('refresh_token')).toBe('tok_refresh');
      });
    });

    test('stores user data in localStorage on success', async () => {
      axios.post.mockResolvedValue({ data: successResponse });

      renderLoginForm();
      fillEmail('user@example.com');
      fillPassword('password123');

      await act(async () => { submitForm(); });

      await waitFor(() => {
        const stored = JSON.parse(localStorage.getItem('user'));
        expect(stored.email).toBe('user@example.com');
      });
    });

    test('navigates to "/" after successful login', async () => {
      axios.post.mockResolvedValue({ data: successResponse });

      renderLoginForm();
      fillEmail('user@example.com');
      fillPassword('password123');

      await act(async () => { submitForm(); });

      await waitFor(() => {
        expect(mockNavigate).toHaveBeenCalledWith('/');
      });
    });

    test('calls the onSuccess callback prop with the response data', async () => {
      const onSuccess = jest.fn();
      axios.post.mockResolvedValue({ data: successResponse });

      renderLoginForm({ onSuccess });
      fillEmail('user@example.com');
      fillPassword('password123');

      await act(async () => { submitForm(); });

      await waitFor(() => {
        expect(onSuccess).toHaveBeenCalledWith(successResponse);
      });
    });

    test('posts to the correct auth/login endpoint', async () => {
      axios.post.mockResolvedValue({ data: successResponse });

      renderLoginForm();
      fillEmail('user@example.com');
      fillPassword('password123');

      await act(async () => { submitForm(); });

      await waitFor(() => {
        expect(axios.post).toHaveBeenCalledWith(
          expect.stringContaining('/api/auth/login'),
          expect.objectContaining({
            email: 'user@example.com',
            password: 'password123',
          })
        );
      });
    });
  });

  // -------------------------------------------------------------------------
  // Failed login
  // -------------------------------------------------------------------------
  describe('failed login', () => {
    test('shows error alert with the server error message', async () => {
      axios.post.mockRejectedValue({
        response: { status: 401, data: { error: 'Invalid credentials' } },
      });

      renderLoginForm();
      fillEmail('user@example.com');
      fillPassword('wrongpassword');

      await act(async () => { submitForm(); });

      await waitFor(() => {
        expect(screen.getByRole('alert')).toBeInTheDocument();
        expect(screen.getByText(/invalid credentials/i)).toBeInTheDocument();
      });
    });

    test('falls back to "Login failed. Please try again." when no error detail is provided', async () => {
      axios.post.mockRejectedValue({ response: { status: 500, data: {} } });

      renderLoginForm();
      fillEmail('user@example.com');
      fillPassword('password');

      await act(async () => { submitForm(); });

      await waitFor(() => {
        expect(screen.getByText(/login failed. please try again/i)).toBeInTheDocument();
      });
    });

    test('shows account-locked message when status 423 is returned', async () => {
      axios.post.mockRejectedValue({
        response: { status: 423, data: {} },
      });

      renderLoginForm();
      fillEmail('locked@example.com');
      fillPassword('password');

      await act(async () => { submitForm(); });

      await waitFor(() => {
        expect(
          screen.getByText(/account temporarily locked/i)
        ).toBeInTheDocument();
      });
    });

    test('does not navigate on login failure', async () => {
      axios.post.mockRejectedValue({
        response: { status: 401, data: { error: 'Bad credentials' } },
      });

      renderLoginForm();
      fillEmail('user@example.com');
      fillPassword('wrong');

      await act(async () => { submitForm(); });

      await waitFor(() => {
        expect(mockNavigate).not.toHaveBeenCalled();
      });
    });

    test('re-enables the Sign In button after a failed request', async () => {
      axios.post.mockRejectedValue({
        response: { status: 401, data: { error: 'Bad credentials' } },
      });

      renderLoginForm();
      fillEmail('user@example.com');
      fillPassword('wrong');

      await act(async () => { submitForm(); });

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /sign in/i })).not.toBeDisabled();
      });
    });

    test('dismisses the error alert when its close button is clicked', async () => {
      axios.post.mockRejectedValue({
        response: { status: 401, data: { error: 'Invalid credentials' } },
      });

      renderLoginForm();
      fillEmail('user@example.com');
      fillPassword('wrong');

      await act(async () => { submitForm(); });

      await waitFor(() => expect(screen.getByRole('alert')).toBeInTheDocument());

      // MUI Alert has an onClose button — click it
      const closeAlertBtn = screen.getByTitle(/close/i);
      await act(async () => {
        fireEvent.click(closeAlertBtn);
      });

      await waitFor(() => {
        expect(screen.queryByRole('alert')).not.toBeInTheDocument();
      });
    });
  });

  // -------------------------------------------------------------------------
  // Navigation links
  // -------------------------------------------------------------------------
  describe('navigation links', () => {
    test('navigates to /auth/forgot-password when "Forgot password?" is clicked', async () => {
      renderLoginForm();
      const forgotBtn = screen.getByRole('button', { name: /forgot password/i });

      await act(async () => {
        fireEvent.click(forgotBtn);
      });

      expect(mockNavigate).toHaveBeenCalledWith('/auth/forgot-password');
    });

    test('navigates to /auth/register when "Sign up" is clicked', async () => {
      renderLoginForm();
      const signUpBtn = screen.getByRole('button', { name: /sign up/i });

      await act(async () => {
        fireEvent.click(signUpBtn);
      });

      expect(mockNavigate).toHaveBeenCalledWith('/auth/register');
    });
  });

  // -------------------------------------------------------------------------
  // Accessibility
  // -------------------------------------------------------------------------
  describe('accessibility', () => {
    test('email input has the correct autocomplete attribute', () => {
      renderLoginForm();
      expect(screen.getByRole('textbox', { name: /email address/i })).toHaveAttribute(
        'autocomplete',
        'email'
      );
    });

    test('password input has the correct autocomplete attribute', () => {
      renderLoginForm();
      expect(screen.getByLabelText(/^password$/i)).toHaveAttribute(
        'autocomplete',
        'current-password'
      );
    });

    test('password visibility button has a descriptive aria-label', () => {
      renderLoginForm();
      const btn = screen.getByRole('button', { name: /show password/i });
      expect(btn).toBeInTheDocument();
    });
  });
});
