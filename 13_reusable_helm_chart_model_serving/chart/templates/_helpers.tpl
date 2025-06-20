{{- define "model-serving.name" -}}
{{- default .Chart.Name .Values.nameOverride -}}
{{- end -}}

{{- define "model-serving.fullname" -}}
{{- if .Values.fullnameOverride -}}
{{- .Values.fullnameOverride -}}
{{- else -}}
{{- printf "%s-%s" .Release.Name (include "model-serving.name" .) | trunc 63 | trimSuffix "-" -}}
{{- end -}}
{{- end -}}
