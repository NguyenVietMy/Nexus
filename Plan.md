# Implementation Plan for Customizable Suggestion Criteria

## Feature Description

This feature allows users to customize the criteria for suggestion generation. This will enable the tool to adapt to different project requirements and user preferences by allowing users to define their own criteria for generating suggestions.

## Source Files to Modify or Create

1. **Modify `backend/app/services/suggestion_service.py`**
   - Update the `generate_suggestions` function to accept custom criteria and apply them during suggestion generation.
   
   ```python
   # Import statements
   from typing import Any, Dict

   def generate_suggestions(self, criteria: Dict[str, Any]):
       # Apply custom criteria to the suggestion generation logic
       # Existing logic...
   ```

2. **Modify `frontend/src/components/modals/AddFeatureFlow.tsx`**
   - Add a user interface component to allow users to define custom suggestion criteria.
   
   ```typescript
   // Import statements
   import { useState } from 'react';

   const AddFeatureFlow = () => {
       const [criteria, setCriteria] = useState<{[key: string]: any}>({});

       const handleCriteriaChange = (newCriteria: {[key: string]: any}) => {
           setCriteria(newCriteria);
       };

       // UI logic to render input fields for criteria
   };
   ```

3. **Modify `frontend/src/components/panels/SuggestionPanel.tsx`**
   - Update the component to use the custom criteria when requesting suggestions from the backend.
   
   ```typescript
   // Import statements
   import { useEffect, useState } from 'react';

   const SuggestionPanel = () => {
       const [suggestions, setSuggestions] = useState([]);
       const [criteria, setCriteria] = useState<{[key: string]: any}>({});

       useEffect(() => {
           const fetchSuggestions = async () => {
               const response = await fetch('/api/suggestions', {
                   method: 'POST',
                   headers: {
                       'Content-Type': 'application/json'
                   },
                   body: JSON.stringify({ criteria })
               });
               const data = await response.json();
               setSuggestions(data);
           };

           fetchSuggestions();
       }, [criteria]);

       // Render suggestions
   };
   ```

## Verification Step

Run the test file to confirm the implementation:

```bash
npm test __tests__/customizable-suggestion-criteria.test.ts
```

## Constraints

- Do NOT modify .env, CI configs, or deployment configs.