# Implementation Plan for Customizable Suggestion Criteria

## Feature Description
The feature "Customizable Suggestion Criteria" allows users to set and customize criteria that will be used during suggestion generation. This enhances the adaptability of the tool to different project needs and user preferences.

## Source Files to Modify
1. `backend/app/services/suggestion_service.py`
2. `frontend/src/components/modals/AddFeatureFlow.tsx`
3. `frontend/src/components/panels/SuggestionPanel.tsx`

## Detailed Steps

### 1. Update Backend Suggestion Service

**File:** `backend/app/services/suggestion_service.py`

- **Add a new method** to process custom criteria:
  
  ```python
  def apply_custom_criteria(self, suggestions, criteria):
      # Example logic to filter suggestions based on criteria
      filtered_suggestions = [s for s in suggestions if self._matches_criteria(s, criteria)]
      return filtered_suggestions

  def _matches_criteria(self, suggestion, criteria):
      # Define logic to match suggestion with criteria
      return all(getattr(suggestion, key, None) == value for key, value in criteria.items())
  ```

- **Modify existing suggestion generation method** to incorporate the new criteria:

  ```python
  def generate_suggestions(self, base_criteria, custom_criteria=None):
      suggestions = self._generate_base_suggestions(base_criteria)
      if custom_criteria:
          suggestions = self.apply_custom_criteria(suggestions, custom_criteria)
      return suggestions
  ```

### 2. Update AddFeatureFlow UI Component

**File:** `frontend/src/components/modals/AddFeatureFlow.tsx`

- **Import necessary hooks and components**:

  ```typescript
  import { useState } from 'react';
  import { CriteriaForm } from '../forms/CriteriaForm';
  ```

- **Add state to manage custom criteria**:

  ```typescript
  const [customCriteria, setCustomCriteria] = useState({});
  ```

- **Render a new form component** for setting criteria:

  ```typescript
  <CriteriaForm criteria={customCriteria} setCriteria={setCustomCriteria} />
  ```

### 3. Update SuggestionPanel to Use Custom Criteria

**File:** `frontend/src/components/panels/SuggestionPanel.tsx`

- **Import necessary hooks**:

  ```typescript
  import { useEffect, useState } from 'react';
  import { api } from '../../services/api';
  ```

- **Add logic to fetch suggestions with custom criteria**:

  ```typescript
  const [suggestions, setSuggestions] = useState([]);
  const [customCriteria, setCustomCriteria] = useState({});

  useEffect(() => {
      api.fetchSuggestions(customCriteria).then(setSuggestions);
  }, [customCriteria]);
  ```

## Final Verification
Run the test file to confirm the implementation:

```
# Test the functionality by running the following command
npm test -- __tests__/customizable-suggestion-criteria.test.ts
```

## Constraints
- Do not modify any environment files or deployment configurations.

