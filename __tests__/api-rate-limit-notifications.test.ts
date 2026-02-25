import { render, screen } from '@testing-library/react';
import '@testing-library/jest-dom/extend-expect';
import { RepoInput } from '../frontend/src/components/modals/RepoInput';
import { setupRateLimitInterceptor } from '../frontend/src/services/api';
import axios from 'axios';

jest.mock('axios');

describe('API Rate Limit Notifications', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  test('should display notification when approaching rate limits', async () => {
    const mockResponse = {
      headers: {
        'x-rate-limit-remaining': '5',
        'x-rate-limit-reset': (Math.floor(Date.now() / 1000) + 60).toString(),
      },
    };
    (axios.create as jest.Mock).mockReturnValue({
      interceptors: {
        response: {
          use: (onFulfilled: any) => onFulfilled(mockResponse),
        },
      },
    });

    render(<RepoInput />);

    const notificationElement = await screen.findByText(/Only 5 requests remaining/);
    expect(notificationElement).toBeInTheDocument();
  });
});
