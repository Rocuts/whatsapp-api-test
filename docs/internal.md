## Checklist para replicar un nuevo tenant (WhatsApp Webhook)

```
PROJECT_ID=agentes-ia-dev
REGION=us-central1
SERVICE=whatsapp-webhook
API_ID=agentes-ia-webhook
GW_ID=agentes-ia-webhook-gw
GW_SA=agw-invoker@$PROJECT_ID.iam.gserviceaccount.com
TENANT=<NUEVO_TENANT>            # p.ej. "mi-cliente"
VERIFY_TOKEN=<VALOR_TOKEN>       # define el valor
SECRET_VERIFY="tenants-${TENANT}-VERIFY_TOKEN"
CR_URL="https://whatsapp-webhook-878958463385.us-central1.run.app"
OPENAPI=api.yaml
```

1. **Crear/actualizar secretos del tenant**

   ```
   # VERIFY_TOKEN
   gcloud secrets describe "$SECRET_VERIFY" --project $PROJECT_ID >/dev/null 2>&1 || \
     gcloud secrets create "$SECRET_VERIFY" --project $PROJECT_ID --replication-policy=automatic

   printf "%s" "$VERIFY_TOKEN" | gcloud secrets versions add "$SECRET_VERIFY" \
     --project $PROJECT_ID --data-file=-
   ```

2. **Dar permisos de lectura al runtime SA de Cloud Run**

   ```
   SVC_SA=$(gcloud run services describe $SERVICE --region $REGION --project $PROJECT_ID --format='value(spec.template.spec.serviceAccountName)')
   gcloud secrets add-iam-policy-binding "$SECRET_VERIFY" \
     --project $PROJECT_ID \
     --member="serviceAccount:${SVC_SA}" \
     --role="roles/secretmanager.secretAccessor"
   ```

3. **(Opcional) Exportar var de entorno temporal (fallback)**

   ```
   # Solo si quieres fallback por entorno
   gcloud run services update $SERVICE \
     --region=$REGION --project=$PROJECT_ID \
     --update-env-vars=VERIFY_TOKEN="$VERIFY_TOKEN"
   ```

4. **Regenerar config del API Gateway y actualizar gateway**

   - GET `/api/webhook/{tenant}` debe tener `security: []`.
   - POST protegido por `api_key`.
   - `x-google-backend.address` apunta a `$CR_URL`.
   - `jwt_audience = $CR_URL`.
   - `path_translation: APPEND_PATH_TO_ADDRESS`.

   ```
   CFG_ID=cfg-$(date +%Y%m%d%H%M)
   gcloud api-gateway api-configs create $CFG_ID \
     --api=$API_ID \
     --openapi-spec=$OPENAPI \
     --project=$PROJECT_ID \
     --backend-auth-service-account=$GW_SA

   gcloud api-gateway gateways update $GW_ID \
     --api=$API_ID \
     --api-config=$CFG_ID \
     --location=$REGION \
     --project=$PROJECT_ID
   ```

5. **Smoke test**

   ```
   TOKEN_VALUE=$(gcloud secrets versions access latest --secret="$SECRET_VERIFY" --project="$PROJECT_ID")

   # Directo a Cloud Run (autenticado)
   curl -i -H "Authorization: Bearer $(gcloud auth print-identity-token)" \
     "$CR_URL/api/webhook/${TENANT}?hub.mode=subscribe&hub.verify_token=${TOKEN_VALUE}&hub.challenge=ping"

   # Por API Gateway (público)
   HOST=$(gcloud api-gateway gateways describe $GW_ID --location=$REGION --project=$PROJECT_ID --format='get(defaultHostname)')
   curl -i "https://${HOST}/api/webhook/${TENANT}?hub.mode=subscribe&hub.verify_token=${TOKEN_VALUE}&hub.challenge=ping"
   ```

6. **Configurar en Meta (WhatsApp)**

   - Callback URL: `https://${HOST}/api/webhook/${TENANT}`
   - Verify Token: `$VERIFY_TOKEN`
   - Suscribir campos necesarios (messages, etc.).

7. **Hardening recomendado**

   - No publicar Cloud Run a `allUsers`.
   - Mantener GET público en Gateway solo para verificación; POST protegido por API key.
   - Rotar `VERIFY_TOKEN` desde Secret Manager cuando sea necesario:

     ```
     printf "%s" "NUEVO_TOKEN" | gcloud secrets versions add "$SECRET_VERIFY" --project $PROJECT_ID --data-file=-
     ```

8. **Troubleshooting express**

   - 403 Forbidden en GET ⇒ mismatch de token o SA sin `secretmanager.secretAccessor`.
   - 500 ⇒ revisar logs Cloud Run (alias de query o lectura de secreto).
   - 403 `insufficient_scope` en Gateway ⇒ GET no está sin seguridad o gateway usa config antigua.
   - 401 directo a Cloud Run ⇒ faltó `Authorization: Bearer <id_token>`.

## Comandos útiles

```
PROJECT_ID=agentes-ia-dev
REGION=us-central1
SERVICE=whatsapp-webhook
GW_ID=agentes-ia-webhook-gw
GW_SA=agw-invoker@$PROJECT_ID.iam.gserviceaccount.com
```

- **Ver envs actuales**

  ```
  gcloud run services describe $SERVICE --region $REGION --project $PROJECT_ID \
    --format='yaml(spec.template.spec.containers[0].env)'
  ```

- **Re-bind de invoker al Gateway SA**

  ```
  gcloud run services add-iam-policy-binding $SERVICE \
    --member=serviceAccount:$GW_SA \
    --role=roles/run.invoker \
    --region=$REGION \
    --project=$PROJECT_ID
  ```
