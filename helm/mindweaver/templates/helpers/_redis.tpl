{{/*
Mindweaver Redis Auth Details
Returns a JSON string of a dict with host, port, and password.
*/}}
{{- define "mindweaver.redisAuth" -}}
{{- if .Values.valkey.enabled -}}
  {{- $secretName := printf "%s-default-auth" (include "mindweaver.fullname" .) -}}
  {{- $existingSecret := (lookup "v1" "Secret" .Release.Namespace $secretName) -}}
  {{- $password := "" -}}
  {{- if $existingSecret -}}
    {{- $password = index $existingSecret.data "valkey-password" | b64dec -}}
  {{- else -}}
    {{- $password = randAlphaNum 32 -}}
  {{- end -}}
  {{- $host := printf "%s-valkey-master" (include "mindweaver.fullname" .) -}}
  {{- $port := "6379" -}}
  {{- dict "host" $host "port" $port "password" $password | toJson -}}
{{- else -}}
  {{- dict "host" (.Values.secret.redis.host | default "") "port" (.Values.secret.redis.port | default 6379) "password" (.Values.secret.redis.password | default "") | toJson -}}
{{- end -}}
{{- end -}}

{{/*
Mindweaver Redis Host
*/}}
{{- define "mindweaver.redisHost" -}}
{{- $auth := include "mindweaver.redisAuth" . | fromJson -}}
{{- $auth.host -}}
{{- end -}}

{{/*
Mindweaver Redis Port
*/}}
{{- define "mindweaver.redisPort" -}}
{{- $auth := include "mindweaver.redisAuth" . | fromJson -}}
{{- $auth.port -}}
{{- end -}}

{{/*
Mindweaver Redis Password
*/}}
{{- define "mindweaver.redisPassword" -}}
{{- $auth := include "mindweaver.redisAuth" . | fromJson -}}
{{- $auth.password -}}
{{- end -}}

{{/*
Mindweaver Redis URL
*/}}
{{- define "mindweaver.redisUrl" -}}
{{- $auth := include "mindweaver.redisAuth" . | fromJson -}}
{{- if $auth.password -}}
{{- printf "redis://:%s@%s:%s/0" $auth.password $auth.host ($auth.port | toString) -}}
{{- else -}}
{{- printf "redis://%s:%s/0" $auth.host ($auth.port | toString) -}}
{{- end -}}
{{- end -}}
