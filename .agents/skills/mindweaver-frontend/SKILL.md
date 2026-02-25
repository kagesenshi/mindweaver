---
name: MindWeaver Frontend Development
description: Guide for creating frontend components, working with DynamicForm, and state management in MindWeaver.
---
# MindWeaver Frontend Development

This document outlines core skills for working with the MindWeaver frontend, built with **React**, **Vite**, and **Vanilla CSS** (accelerated by Tailwind utility logic).

## Project Structure

- `src/components`: Reusable UI components (Modals, Drawers, Cards).
- `src/hooks`: Custom React hooks, notably `useResources.js` for data fetching.
- `src/pages`: Feature-specific views (e.g., `src/pages/pgsql`).
- `src/providers`: React Context providers (Auth, Notifications).
- `src/services/api.js`: Axios instance with interceptors for authentication and error handling.

## State Management (`useResources`)

Data fetching is centralized in `src/hooks/useResources.js`. Each resource type (e.g., Projects, S3 Storage) has a dedicated hook that returns data, loading state, and CRUD methods.

```javascript
import { useProjects } from '../hooks/useResources';

const ProjectList = () => {
    const { projects, loading, error, deleteProject } = useProjects();

    if (loading) return <Spinner />;
    
    return (
        <ul>
            {projects.map(p => (
                <li key={p.id}>
                    {p.name}
                    <button onClick={() => deleteProject(p.id)}>Delete</button>
                </li>
            ))}
        </ul>
    );
};
```

## Form Handling

### Dynamic Forms
Use `DynamicForm` for standard CRUD. It fetches column metadata and widget types from the backend.

```jsx
import DynamicForm from '../components/DynamicForm';

<DynamicForm
    entityPath="/api/v1/my_models"
    mode="create" // or "edit"
    onSuccess={(data) => {
        showSuccess('Created successfully');
        onClose();
    }}
/>
```

### Custom Forms
Use a custom form if you need complex conditional logic or multi-step flows. Prefer `LargeDialog` for consistent layout.

## Custom Views and Actions

Frontend providers should align with the backend's `_` prefix convention for custom endpoints.

```javascript
// Example in useResources.js
const testConnection = useCallback(async (id) => {
    const response = await apiClient.post(`/data_sources/${id}/_test-connection`);
    return response.data;
}, []);
```

## Notifications

Use the `useNotification` hook to provide feedback.

```javascript
import { useNotification } from '../providers/NotificationProvider';

const MyComponent = () => {
    const { showSuccess, showError } = useNotification();

    const handleAction = async () => {
        try {
            await doSomething();
            showSuccess('Done!');
        } catch (err) {
            showError('Failed: ' + err.message);
        }
    };
};
```

## UI/UX Best Practices

1.  **Consistent Styling**: Use Tailwind utility classes or custom CSS in `index.css`.
2.  **Icons**: Use `lucide-react` for all iconography.
3.  **Semantic Elements**: Use `ResourceCard` for listing entities and `PageLayout` for top-level headers.
4.  **Confirmations**: Use `ResourceConfirmModal` before destructive actions like deletions.
