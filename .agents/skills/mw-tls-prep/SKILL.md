---
name: MindWeaver TLS Preparation
description: Guidelines and best practices for preparing TLS certificates, Java keystores, and truststores in Kubernetes initContainers.
---
# MindWeaver TLS Preparation

This skill documents how to safely prepare and manage TLS certificates, Java Keystores (`.jks`), and Cryptography Credential Stores (`.jceks`) in Kubernetes components.

## Overview

In Mindweaver, many platform services (such as Trino, Ranger, and Hive Metastore) run on Java and require JKS or JCEKS format keystores/truststores for secure HTTPS communication and database links. Since Kubernetes `Secret` resources from cert-manager typically output standard PEM-formatted certificates (`tls.crt`, `tls.key`, `ca.crt`), an `initContainer` is used to:
1. Combine PEM keys/certificates into a unified file.
2. Copy pre-built cert-manager keystores.
3. Import sensitive passwords/secrets into a `.jceks` database using `keytool`.

---

## Critical Rules & Guidelines

### 1. Avoid Restart Failures (Alias Already Exists)
When containers restart or are rescheduled, the volumes (even `emptyDir`) can persist or the commands in `initContainers` can be executed multiple times. If a keytool command attempts to import an alias that is already present in a `.jceks` or `.jks` file, the command will fail and block pod startup.

*   **Rule**: Always remove existing keystore/JCEKS files or clear pre-existing aliases before running the `keytool` command.
*   **Example**:
    ```sh
    # Good pattern: delete file first
    rm -f /tls/ranger-link.jceks
    echo "changeit" | keytool -importpass -alias sslKeyStore -keypass changeit -storepass changeit -keystore /tls/ranger-link.jceks -storetype JCEKS -noprompt
    ```

### 2. Copy Default JVM Truststores Safely
When importing custom CA certificates (such as a cluster CA) into the Java runtime's truststore, copy the system `cacerts` file to the destination volume first:
*   **Example**:
    ```sh
    # Check both jre and jdk locations and copy
    cp /opt/java/openjdk/jre/lib/security/cacerts /etc/ranger/truststore/truststore.jks || cp /opt/java/openjdk/lib/security/cacerts /etc/ranger/truststore/truststore.jks
    
    # Import the custom CA certificate
    /opt/java/openjdk/bin/keytool -importcert -alias mindweaver-ca -file /tls-secret/ca.crt -keystore /etc/ranger/truststore/truststore.jks -storepass changeit -noprompt
    ```

---

## Reference Implementation (Trino/Ranger Templates)

### Pod initContainer Manifest Example
```yaml
initContainers:
  coordinator:
    - name: prepare-tls
      image: "{{ image }}"
      command:
        - sh
        - -c
        - |
          # 1. Combine key and cert for envoy/http-server PEM format
          cat /tls-secret/tls.key /tls-secret/tls.crt > /tls/tls.pem
          
          # 2. Copy cert-manager keystores to shared volume
          cp /tls-secret/keystore.jks /tls/keystore.jks
          cp /tls-secret/truststore.jks /tls/truststore.jks
          
          # 3. Clean and recreate credential store to prevent alias error on restarts
          {% if ranger_enabled %}
          rm -f /tls/ranger-link.jceks
          echo "changeit" | keytool -importpass -alias sslKeyStore -keypass changeit -storepass changeit -keystore /tls/ranger-link.jceks -storetype JCEKS -noprompt
          echo "changeit" | keytool -importpass -alias sslTrustStore -keypass changeit -storepass changeit -keystore /tls/ranger-link.jceks -storetype JCEKS -noprompt
          {% endif %}
      volumeMounts:
        - name: tls-secret
          mountPath: /tls-secret
          readOnly: true
        - name: certs
          mountPath: /tls
```
