---
trigger: manual
description: this rule applies on actions related to custom entity type
---

- When creating custom entity type (service, platform service), 
  default to use dynamic form in the frontend.
- Dynamic form shall be used only for simple forms, while more complex requirement
  shall be created as custom form. Always remind the developer this if you noticed that
  the form required is complex  (more than simple data entry form, such as having 
  conditional display of fields) and the developer requested to use dynamic form in 
  such scenario
- Custom views should have '+' prefix to differentiate it from collections. eg: +apply, +decommission, +test-connection
