---
trigger: always_on
glob:
description: this rule applies when dealing with backend fields that store encrypted values
---

- in the backend, when user get record containing encrypted fields , the fields should not be decrypted. use `__REDACTED__` 
