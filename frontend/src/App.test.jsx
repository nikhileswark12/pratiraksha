import { beforeEach, expect, test } from 'vitest';
import { render, screen } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import App from './App';

beforeEach(() => {
  localStorage.clear();
});

test('renders the login screen when no access token exists', () => {
  render(
    <BrowserRouter>
      <App />
    </BrowserRouter>
  );

  expect(screen.getByRole('heading', { name: 'Pratiraksha Login' })).toBeInTheDocument();
  expect(screen.getByRole('button', { name: 'Sign In' })).toBeInTheDocument();
});
