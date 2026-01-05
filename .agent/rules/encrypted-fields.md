---
trigger: manual
description: this rule applies when dealing with backend fields that store encrypted values
---

- in the backend, when user get record containing encrypted fields , the fields should not be decrypted. use `__REDACTED__` 
- to clear encrypted field, user have to set the field value as `__CLEAR__` and submit to update endpoint. backend will set the value to blank string
- if user provide `__REDACTED__` as input in update operation for encrypted field, backend should not change existing value and keep current value
