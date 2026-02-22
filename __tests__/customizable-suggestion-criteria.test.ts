import { render, screen, fireEvent } from '@testing-library/react';
import '@testing-library/jest-dom';
import SuggestionPanel from '../frontend/src/components/panels/SuggestionPanel';
import AddFeatureFlow from '../frontend/src/components/modals/AddFeatureFlow';
import { api } from '../frontend/src/services/api';

jest.mock('../frontend/src/services/api');

// Mock data
const mockSuggestions = [
  { id: 1, name: 'Suggestion 1' },
  { id: 2, name: 'Suggestion 2' }
];

const mockCriteria = {
  type: 'enhancement'
};

api.fetchSuggestions.mockResolvedValue(mockSuggestions);

describe('Customizable Suggestion Criteria Tests', () => {
  test('renders AddFeatureFlow and updates criteria', () => {
    render(<AddFeatureFlow />);
    const criteriaInput = screen.getByPlaceholderText(/criteria/i);
    fireEvent.change(criteriaInput, { target: { value: 'enhancement' } });
    expect(criteriaInput.value).toBe('enhancement');
  });

  test('SuggestionPanel fetches suggestions with custom criteria', async () => {
    render(<SuggestionPanel />);
    const suggestions = await screen.findAllByText(/Suggestion/i);
    expect(suggestions).toHaveLength(2);
    expect(api.fetchSuggestions).toHaveBeenCalledWith(mockCriteria);
  });
});
