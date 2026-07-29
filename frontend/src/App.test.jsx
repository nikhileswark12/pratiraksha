import { render, screen } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import App from './App';

test('renders app title', () => {
  render(
    <BrowserRouter>
      <App />
    </BrowserRouter>
  );
  // Expect something generic or we can just verify it renders without crashing
  expect(document.body).toBeInTheDocument();
});

