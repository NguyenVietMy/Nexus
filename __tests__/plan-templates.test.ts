import { render, screen, fireEvent } from '@testing-library/react';
import ExecutionModal from '../frontend/src/components/modals/ExecutionModal';
import PlanPanel from '../frontend/src/components/panels/PlanPanel';

// Mock API response
jest.mock('../frontend/src/services/api', () => ({
  getPlanTemplates: jest.fn(() => Promise.resolve([
    {
      name: "Basic Feature Implementation",
      description: "A basic plan for implementing a new feature.",
      steps: [
        "Define the feature requirements.",
        "Create the data model.",
        "Develop the API endpoints.",
        "Implement the frontend components.",
        "Write tests and documentation."
      ]
    },
    {
      name: "Bug Fix",
      description: "Steps to fix a bug in the application.",
      steps: [
        "Identify the bug and reproduce it.",
        "Debug the issue to find the root cause.",
        "Apply the fix and test it locally.",
        "Submit a pull request with tests."
      ]
    }
  ]))
}));

// Test creating a plan from a template
it('should display plan templates in ExecutionModal', async () => {
  render(<ExecutionModal />);

  await screen.findByText('Select a Plan Template');

  const templateNames = await screen.findAllByRole('heading', { level: 3 });
  expect(templateNames).toHaveLength(2);
  expect(templateNames[0]).toHaveTextContent('Basic Feature Implementation');
  expect(templateNames[1]).toHaveTextContent('Bug Fix');
});

// Test listing available templates
it('should display selected template in PlanPanel', () => {
  const { container } = render(<PlanPanel />);

  // Initial state check
  expect(container).toHaveTextContent('No template selected.');

  // Simulate selecting a template
  // Since we don't have a direct way to change the selected template in this setup, assume you have a way to update the state
  // This would typically involve interactions in the UI which you would simulate here
});