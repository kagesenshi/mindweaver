{{/*
Mindweaver database environment variables
*/}}
{{- define "mindweaver.dbEnv" -}}
{{- if .Values.postgresql.enabled }}
- name: MINDWEAVER_DB_HOST
  valueFrom:
    secretKeyRef:
      name: {{ include "mindweaver.fullname" . }}-db-app
      key: host
- name: MINDWEAVER_DB_PORT
  valueFrom:
    secretKeyRef:
      name: {{ include "mindweaver.fullname" . }}-db-app
      key: port
- name: MINDWEAVER_DB_NAME
  valueFrom:
    secretKeyRef:
      name: {{ include "mindweaver.fullname" . }}-db-app
      key: dbname
- name: MINDWEAVER_DB_USER
  valueFrom:
    secretKeyRef:
      name: {{ include "mindweaver.fullname" . }}-db-app
      key: user
- name: MINDWEAVER_DB_PASS
  valueFrom:
    secretKeyRef:
      name: {{ include "mindweaver.fullname" . }}-db-app
      key: password
{{- end }}
{{- end }}
