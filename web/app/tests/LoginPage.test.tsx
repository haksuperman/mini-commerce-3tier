import { describe, expect, it } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter } from 'react-router-dom';
import LoginPage from '../src/pages/LoginPage';

function renderLogin() {
  return render(
    <MemoryRouter initialEntries={['/login']}>
      <LoginPage />
    </MemoryRouter>,
  );
}

describe('LoginPage', () => {
  it('shows a validation error when submitting empty fields', async () => {
    renderLogin();
    await userEvent.click(screen.getByRole('button', { name: /^login$/i }));
    expect(await screen.findByRole('alert')).toHaveTextContent(/required/i);
  });

  it('renders username and password inputs', () => {
    renderLogin();
    expect(screen.getByLabelText(/username or email/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/password/i)).toBeInTheDocument();
  });
});
