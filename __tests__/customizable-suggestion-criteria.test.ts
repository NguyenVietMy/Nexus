import { render, screen, fireEvent } from '@testing-library/react';
import AddFeatureFlow from '../frontend/src/components/modals/AddFeatureFlow';
import SuggestionPanel from '../frontend/src/components/panels/SuggestionPanel';
import suggestionService from '../frontend/src/services/api';

jest.mock('../frontend/src/services/api');

// Test UI for setting custom suggestion criteria
it('renders the criteria input field and allows input', () => {
  render(<AddFeatureFlow />);
  const input = screen.getByLabelText(/custom criteria/i);
  fireEvent.change(input, { target: { value: 'New Criteria' } });
  expect(input.value).toBe('New Criteria');
});

// Test backend processing of customized criteria
it('calls suggestion service with custom criteria', () => {
  const criteria = 'Test Criteria';
  suggestionService.generateSuggestions = jest.fn();

  render(<SuggestionPanel criteria={criteria} />);
  fireEvent.click(screen.getByText('Generate Suggestions'));

  expect(suggestionService.generateSuggestions).toHaveBeenCalledWith(
    expect.objectContaining({ criteria })
  );
});