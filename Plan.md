## Implementation Plan for Customizable Suggestion Criteria

### Feature Overview
The feature "Customizable Suggestion Criteria" allows users to define and customize the criteria used for generating suggestions. This feature will be implemented in both the backend and frontend to ensure criteria can be set, processed, and applied consistently.

### Source Files to Modify or Create
1. **Modify**: `backend/app/services/suggestion_service.py`
2. **Modify**: `frontend/src/components/modals/AddFeatureFlow.tsx`
3. **Modify**: `frontend/src/components/panels/SuggestionPanel.tsx`

### Backend Implementation

#### File: `backend/app/services/suggestion_service.py`
- **Import Statement**: No additional imports required.
- **Modifications**:
  - Update the `generate_suggestions` function to accept an additional parameter `criteria` and apply these criteria during suggestion generation.
  
  ```python
  def generate_suggestions(self, criteria=None):
      # Existing logic...
      if criteria:
          # Apply criteria to modify suggestion generation
          pass  # Implement criteria-based logic here
  
  # Example usage of criteria
  def apply_criteria(self, suggestions, criteria):
      # Logic to filter or modify suggestions based on criteria
      return suggestions
  ```

### Frontend Implementation

#### File: `frontend/src/components/modals/AddFeatureFlow.tsx`
- **Import Statement**: No additional imports required.
- **Modifications**:
  - Add UI components to allow users to input custom suggestion criteria.
  
  ```tsx
  // Inside the component render method
  <div>
      <label htmlFor="criteria">Custom Criteria:</label>
      <input type="text" id="criteria" value={criteria} onChange={(e) => setCriteria(e.target.value)} />
  </div>
  ```

#### File: `frontend/src/components/panels/SuggestionPanel.tsx`
- **Import Statement**: No additional imports required.
- **Modifications**:
  - Modify the logic to pass the custom criteria from the UI to the backend service when generating suggestions.
  
  ```tsx
  // Assuming generateSuggestions is a method that triggers the backend call
  const handleGenerateSuggestions = () => {
      suggestionService.generateSuggestions({ criteria });
  };
  ```

### Verification Step
Run the test file to verify the implementation:
```bash
npm test -- __tests__/customizable-suggestion-criteria.test.ts
```

### Constraints
- Do NOT modify `.env`, CI configs, or deployment configs.
- Maximum of 25 files changed.