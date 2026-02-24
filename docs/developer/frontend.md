# Frontend Development

This guide covers the development and customization of the Mindweaver frontend.

## Overview

The frontend is a React application built with **Vite** and styled with **Tailwind CSS**. It is designed to be highly dynamic, leveraging backend metadata to render UI components.

## Dynamic Forms

The `DynamicForm` component is the heart of Mindweaver's CRUD UI.
- **Automatic Rendering**: It fetches the JSON:API schema from the backend and builds the form automatically.
- **Backend-Driven UX**: UX properties like field order, labels, and column spans are configured in the **Backend Service**'s `widgets()` method.

### Customizing Forms

If a form requires complex logic (e.g., conditional visibility or custom validation), implement a **Custom Form** (like a `LargeDialog`) instead of using `DynamicForm`.

## Providers

Providers abstract the API communication logic. Most entities have a corresponding provider that handles fetching, updating, and deleting records.

## UI Standards

- **Aesthetics**: Mindweaver prioritizes a modern, premium look with harmonious color palettes and subtle animations.
- **Responsiveness**: Ensure all new components are fully responsive.
- **Identifiers**: Use semantic IDs and class names for all key elements to facilitate automated testing.

## State Management

- Centralized state is handled via the context API or custom hooks.
- API interactions are centralized in `frontend/src/api.js`.
