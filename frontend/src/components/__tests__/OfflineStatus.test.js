import React from 'react';
import { render, screen, act } from '@testing-library/react';
import '@testing-library/jest-dom';
import OfflineStatus from '../OfflineStatus';

describe('OfflineStatus', () => {
  test('renders without crashing', () => {
    const { container } = render(<OfflineStatus />);
    expect(container).toBeTruthy();
  });

  test('does not show offline banner when online', () => {
    // jsdom defaults to navigator.onLine = true
    Object.defineProperty(navigator, 'onLine', { value: true, writable: true });
    render(<OfflineStatus />);
    // Should not display an offline warning when online
    expect(screen.queryByText(/offline/i)).not.toBeInTheDocument();
  });
});
