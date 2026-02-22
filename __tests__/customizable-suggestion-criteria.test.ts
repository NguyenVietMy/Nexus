// __tests__/customizable-suggestion-criteria.test.ts

import { render, screen, fireEvent } from '@testing-library/react';
import AddFeatureFlow from '../frontend/src/components/modals/AddFeatureFlow';
import SuggestionPanel from '../frontend/src/components/panels/SuggestionPanel';

// Test UI for setting custom suggestion criteria
it('renders input fields for custom criteria and updates state correctly', () => {
    render(<AddFeatureFlow />);
    const inputElement = screen.getByPlaceholderText(/enter criteria/i);
    fireEvent.change(inputElement, { target: { value: 'test criteria' } });
    expect(inputElement.value).toBe('test criteria');
});

// Test backend processing of customized criteria
it('fetches suggestions using custom criteria', async () => {
    render(<SuggestionPanel />);
    const criteriaInput = screen.getByPlaceholderText(/enter criteria/i);
    fireEvent.change(criteriaInput, { target: { value: 'custom criteria' } });

    const fetchButton = screen.getByRole('button', { name: /fetch suggestions/i });
    fireEvent.click(fetchButton);

    const suggestionItems = await screen.findAllByRole('listitem');
    expect(suggestionItems.length).toBeGreaterThan(0);
    expect(suggestionItems[0]).toHaveTextContent(/suggestion/i);
});