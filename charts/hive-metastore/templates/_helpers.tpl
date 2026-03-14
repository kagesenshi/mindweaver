{{/*
Expand the name of the chart.
*/}}
{{- define "hive-metastore.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Create a default fully qualified app name.
We truncate at 63 chars because some Kubernetes name fields are limited to this (by the DNS naming spec).
If release name contains chart name it will be used as a full name.
*/}}
{{- define "hive-metastore.fullname" -}}
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
{{- define "hive-metastore.chart" -}}
{{- printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Common labels
*/}}
{{- define "hive-metastore.labels" -}}
helm.sh/chart: {{ include "hive-metastore.chart" . }}
{{ include "hive-metastore.selectorLabels" . }}
{{- if .Chart.AppVersion }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
{{- end }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end }}

{{/*
Selector labels
*/}}
{{- define "hive-metastore.selectorLabels" -}}
app.kubernetes.io/name: {{ include "hive-metastore.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}

{{/*
Create the name of the service account to use
*/}}
{{- define "hive-metastore.serviceAccountName" -}}
{{- if .Values.serviceAccount.create }}
{{- default (include "hive-metastore.fullname" .) .Values.serviceAccount.name }}
{{- else }}
{{- default "default" .Values.serviceAccount.name }}
{{- end }}
{{- end }}

{{/*
Common env variables for DB connection used in Deployment and InitSchema Job
*/}}
{{- define "hive-metastore.databaseEnv" -}}
{{- $secretName := default (printf "%s-db-secret" (include "hive-metastore.fullname" .)) .Values.database.secretRef.name -}}
- name: DB_HOST
  valueFrom:
    secretKeyRef:
      name: {{ $secretName }}
      key: {{ .Values.database.secretRef.hostKey | quote }}
- name: DB_PORT
  valueFrom:
    secretKeyRef:
      name: {{ $secretName }}
      key: {{ .Values.database.secretRef.portKey | quote }}
- name: DB_NAME
  valueFrom:
    secretKeyRef:
      name: {{ $secretName }}
      key: {{ .Values.database.secretRef.dbnameKey | quote }}
- name: DB_USER
  valueFrom:
    secretKeyRef:
      name: {{ $secretName }}
      key: {{ .Values.database.secretRef.userKey | quote }}
- name: DB_PASSWORD
  valueFrom:
    secretKeyRef:
      name: {{ $secretName }}
      key: {{ .Values.database.secretRef.passwordKey | quote }}
{{- end -}}

{{/*
Common env variables for S3 connection used in Deployment
*/}}
{{- define "hive-metastore.s3Env" -}}
{{- $secretName := default (printf "%s-db-secret" (include "hive-metastore.fullname" .)) .Values.database.secretRef.name -}}
- name: S3_ENDPOINT_URL
  valueFrom:
    secretKeyRef:
      name: {{ $secretName }}
      key: "s3_endpoint_url"
      optional: true
- name: S3_REGION
  valueFrom:
    secretKeyRef:
      name: {{ $secretName }}
      key: "s3_region"
      optional: true
- name: S3_USE_SSL
  valueFrom:
    secretKeyRef:
      name: {{ $secretName }}
      key: "s3_use_ssl"
      optional: true
- name: AWS_ACCESS_KEY_ID
  valueFrom:
    secretKeyRef:
      name: {{ $secretName }}
      key: "aws_access_key_id"
      optional: true
- name: AWS_SECRET_ACCESS_KEY
  valueFrom:
    secretKeyRef:
      name: {{ $secretName }}
      key: "aws_secret_access_key"
      optional: true
{{- end -}}
