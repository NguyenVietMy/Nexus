# Plan for Implementing API Rate Limit Notifications

## Feature Name
API Rate Limit Notifications

## Feature Description
This feature will notify users when they are approaching or have exceeded their API rate limits. The notifications will be displayed in the `RepoInput` modal component.

## Source Files to Modify

1. `frontend/src/services/api.ts`
   - **Objective**: Implement an interceptor to monitor API response headers for rate limit information.
   - **Modifications**:
     - Import `axios` to use interceptors.
     - Create a function to set up an interceptor.
     - Extract rate limit information from response headers and trigger notifications.

```typescript
import axios, { AxiosResponse } from 'axios';

// Existing axios instance
const api = axios.create({
  // ... existing configuration
});

// Function to set up interceptor
export function setupRateLimitInterceptor() {
  api.interceptors.response.use((response: AxiosResponse) => {
    const rateLimit = response.headers['x-rate-limit-remaining'];
    const rateLimitReset = response.headers['x-rate-limit-reset'];
    if (rateLimit !== undefined && rateLimitReset !== undefined) {
      const remaining = parseInt(rateLimit, 10);
      if (remaining < 10) { // Threshold for notification
        const resetTime = new Date(parseInt(rateLimitReset, 10) * 1000);
        // Trigger a notification (to be implemented in RepoInput.tsx)
        dispatchRateLimitNotification(remaining, resetTime);
      }
    }
    return response;
  }, (error) => {
    return Promise.reject(error);
  });
}

// Placeholder for dispatch function
function dispatchRateLimitNotification(remaining: number, resetTime: Date) {
  // This function will be implemented in the RepoInput component
}
```

2. `frontend/src/components/modals/RepoInput.tsx`
   - **Objective**: Implement a function to display notifications when the API rate limit is approaching.
   - **Modifications**:
     - Import necessary hooks and components for notifications.
     - Implement the notification dispatch function.

```typescript
import React, { useState, useEffect } from 'react';
import { setupRateLimitInterceptor } from '../../services/api';
import { Notification } from '../common/Notification';

export const RepoInput: React.FC = () => {
  const [rateLimitWarning, setRateLimitWarning] = useState<string | null>(null);

  useEffect(() => {
    setupRateLimitInterceptor();
  }, []);

  function dispatchRateLimitNotification(remaining: number, resetTime: Date) {
    setRateLimitWarning(`Warning: Only ${remaining} requests remaining. Resets at ${resetTime.toLocaleTimeString()}.`);
  }

  return (
    <div>
      {/* Existing modal content */}
      {rateLimitWarning && <Notification message={rateLimitWarning} />}
    </div>
  );
};
```

## Verification Step
To verify the implementation, run the following test file:

- `run jest __tests__/api-rate-limit-notifications.test.ts`

## Constraints
- Do not modify `.env`, CI configs, or deployment configs.
- Limit changes to a maximum of 25 files.
