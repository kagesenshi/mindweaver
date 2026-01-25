---
name: MindWeaver Frontend Development
description: Guide for creating frontend components and working with DynamicForm in MindWeaver.
---
# MindWeaver Frontend Development

This document outlines core skills for working with the MindWeaver frontend.

## Creating a Dynamic Form

The frontend `DynamicForm` component renders forms based on schemas provided by the backend.

1.  **Backend Support**: The backend `Service` class automatically generates JSON schemas and widget metadata via `_create-form` and `_edit-form` endpoints.
2.  **Frontend Usage**:
    ```jsx
    import DynamicForm from '../components/DynamicForm';

    <DynamicForm
        entityPath="/api/v1/my_models"
        mode="create" // or "edit"
        onSuccess={(data) => console.log('Created:', data)}
    />
    ```
