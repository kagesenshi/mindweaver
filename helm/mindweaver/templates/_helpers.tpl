{{/*
Expand the name of the chart.
*/}}
{{- define "mindweaver.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Create a default fully qualified app name.
We truncate at 63 chars because some Kubernetes name fields are limited to this (by the DNS naming spec).
If release name contains chart name it will be used as a full name.
*/}}
{{- define "mindweaver.fullname" -}}
{{- if .Values.fullnameOverride }}
{{- .Values.fullnameOverride | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- $name := default .Chart.Name .Values.nameOverride }}
{{- if contains $name .Release.Name }}
{{- .Release.Name | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- printf "%s-%s" .Release.Name $name | trunc 63 | trimSuffix "-" }}
{{- end }}
{{- end }}
{{- end }}

{{/*
Create chart name and version as used by the chart label.
*/}}
{{- define "mindweaver.chart" -}}
{{- printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Common labels
*/}}
{{- define "mindweaver.labels" -}}
helm.sh/chart: {{ include "mindweaver.chart" . }}
{{ include "mindweaver.selectorLabels" . }}
{{- if .Chart.AppVersion }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
{{- end }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end }}

{{/*
Selector labels
*/}}
{{- define "mindweaver.selectorLabels" -}}
app.kubernetes.io/name: {{ include "mindweaver.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}

{{/*
Create the name of the service account to use
*/}}
{{- define "mindweaver.serviceAccountName" -}}
{{- if .Values.serviceAccount.create }}
{{- default (include "mindweaver.fullname" .) .Values.serviceAccount.name }}
{{- else }}
{{- default "default" .Values.serviceAccount.name }}
{{- end }}
{{- end }}

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
