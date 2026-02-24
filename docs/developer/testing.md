# Testing

Reliable tests are essential for maintaining the quality and stability of Mindweaver.

## Backend Testing

Mindweaver uses **pytest** for backend unit and integration testing.

### Running Tests

To run the entire backend test suite:
```bash
uv run --package mindweaver pytest backend/tests
```

### Test Structure
- **Units**: Test individual functions and service methods.
- **API Tests**: Use the `crud_client` and `project_scoped_crud_client` fixtures to test API endpoints.
- **Fixtures**: Standard fixtures are provided for database setup, authentication, and client initialization.

### Negative Tests
Always include negative tests to verify that your service handles error conditions (e.g., duplicate names, missing required fields, unauthorized access) correctly.

## Frontend Testing

The frontend is a React application built with Vite.

### Current Status
Currently, the frontend relies on manual verification. When implementing new UI features:
- Verify responsiveness across different screen sizes.
- Ensure that dynamic forms render correctly based on backend metadata.
- Check that all interactive elements have semantic identifiers for future automation.

## CI/CD

Mindweaver uses GitHub Actions to run tests automatically on every pull request. Ensure that your changes pass all CI checks before requesting a review.
