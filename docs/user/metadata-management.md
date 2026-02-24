# Metadata Management

Mindweaver acts as a centralized repository for your data platform's metadata.

## Data Sources

Data Sources represent external databases or APIs that your platform interacts with.
- **Types**: PostgreSQL, MySQL, Snowflake, etc.
- **Configuration**: Store connection strings, hosts, and ports.
- **Security**: Authentication details (usernames, passwords) are encrypted and redacted in the UI.

## S3 Storage

Manage your S3-compatible storage connections (AWS S3, MinIO, etc.) for data lakes and file handling.
- **Endpoint**: The URL of your S3 service.
- **Access Keys**: Securely manage your Access Key ID and Secret Access Key.

## AI Agents and Knowledge Bases

Mindweaver provides integrated support for AI orchestration:
- **Knowledge Bases**: Define and manage sources of knowledge (e.g., S3 buckets, databases) for AI ingestion.
- **AI Agents**: Configure agents with specific models and toolsets, leveraging Knowledge Bases for context.

## Handling Sensitive Data

When working with metadata, you will often encounter sensitive fields.
- **Redaction**: Fields like `password` or `secret_key` will appear as `__REDACTED__`.
- **Updating**: To update a sensitive field, simply type the new value. To keep the existing value, leave it as `__REDACTED__`. To clear it, use the `__CLEAR__` keyword.
