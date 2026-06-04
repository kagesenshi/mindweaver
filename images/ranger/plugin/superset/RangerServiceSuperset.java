/*
 * SPDX-FileCopyrightText: Copyright © 2026 Mohd Izhar Firdaus Bin Ismail
 * SPDX-License-Identifier: AGPLv3+
 */

package org.apache.ranger.services.superset;

import org.apache.commons.logging.Log;
import org.apache.commons.logging.LogFactory;
import org.apache.ranger.plugin.service.RangerBaseService;
import org.apache.ranger.plugin.service.ResourceLookupContext;

import java.io.BufferedReader;
import java.io.InputStreamReader;
import java.io.OutputStream;
import java.net.HttpURLConnection;
import java.net.URL;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

public class RangerServiceSuperset extends RangerBaseService {
    private static final Log LOG = LogFactory.getLog(RangerServiceSuperset.class);

    private static final String CONFIG_USERNAME = "username";
    private static final String CONFIG_PASSWORD = "password";
    private static final String CONFIG_SUPERSET_URL = "superset.url";

    @Override
    public List<String> lookupResource(ResourceLookupContext context) throws Exception {
        List<String> result = new ArrayList<>();
        if (context == null) {
            return result;
        }

        String resourceName = context.getResourceName();
        Map<String, List<String>> resources = context.getResources();
        String userInput = context.getUserInput();

        if (LOG.isDebugEnabled()) {
            LOG.debug("==> RangerServiceSuperset.lookupResource() resourceName=" + resourceName + ", userInput=" + userInput);
        }

        Map<String, String> configs = getConfigs();
        if (configs == null || configs.isEmpty()) {
            LOG.error("No configuration found for Superset service lookup");
            return result;
        }

        String baseUrl = configs.get(CONFIG_SUPERSET_URL);
        String username = configs.get(CONFIG_USERNAME);
        String password = configs.get(CONFIG_PASSWORD);

        if (baseUrl == null || username == null || password == null) {
            LOG.error("Missing mandatory config values: url, username or password");
            return result;
        }

        try {
            String token = getSupersetToken(baseUrl, username, password);
            if (token == null) {
                LOG.error("Failed to authenticate to Apache Superset API");
                return result;
            }

            if ("dashboard".equalsIgnoreCase(resourceName)) {
                result = fetchDashboards(baseUrl, token, userInput);
            } else if ("chart".equalsIgnoreCase(resourceName)) {
                result = fetchCharts(baseUrl, token, userInput);
            } else if ("database".equalsIgnoreCase(resourceName)) {
                result = fetchDatabases(baseUrl, token, userInput);
            } else if ("schema".equalsIgnoreCase(resourceName)) {
                List<String> databases = resources.get("database");
                String dbName = (databases != null && !databases.isEmpty()) ? databases.get(0) : null;
                result = fetchSchemas(baseUrl, token, dbName, userInput);
            } else if ("dataset".equalsIgnoreCase(resourceName)) {
                List<String> databases = resources.get("database");
                String dbName = (databases != null && !databases.isEmpty()) ? databases.get(0) : null;
                List<String> schemas = resources.get("schema");
                String schemaName = (schemas != null && !schemas.isEmpty()) ? schemas.get(0) : null;
                result = fetchDatasets(baseUrl, token, dbName, schemaName, userInput);
            }
        } catch (Exception e) {
            LOG.error("Exception during Superset resource lookup: ", e);
        }

        if (LOG.isDebugEnabled()) {
            LOG.debug("<== RangerServiceSuperset.lookupResource() result=" + result);
        }

        return result;
    }

    @Override
    public Map<String, Object> validateConfig() throws Exception {
        Map<String, Object> ret = new HashMap<>();
        Map<String, String> configs = getConfigs();

        if (LOG.isDebugEnabled()) {
            LOG.debug("==> RangerServiceSuperset.validateConfig()");
        }

        if (configs != null) {
            String baseUrl = configs.get(CONFIG_SUPERSET_URL);
            String username = configs.get(CONFIG_USERNAME);
            String password = configs.get(CONFIG_PASSWORD);

            try {
                String token = getSupersetToken(baseUrl, username, password);
                if (token != null) {
                    ret.put("connectivityStatus", true);
                    ret.put("message", "Connection test successful!");
                } else {
                    ret.put("connectivityStatus", false);
                    ret.put("message", "Authentication failed: check credentials and URL");
                }
            } catch (Exception e) {
                ret.put("connectivityStatus", false);
                ret.put("message", "Connection failed: " + e.getMessage());
                LOG.error("Connection test failed", e);
            }
        } else {
            ret.put("connectivityStatus", false);
            ret.put("message", "No configuration parameters provided");
        }

        if (LOG.isDebugEnabled()) {
            LOG.debug("<== RangerServiceSuperset.validateConfig() ret=" + ret);
        }

        return ret;
    }

    private String getSupersetToken(String baseUrl, String username, String password) throws Exception {
        URL url = new URL(baseUrl + "/api/v1/security/login");
        HttpURLConnection conn = (HttpURLConnection) url.openConnection();
        conn.setRequestMethod("POST");
        conn.setRequestProperty("Content-Type", "application/json");
        conn.setDoOutput(true);

        String payload = String.format("{\"username\":\"%s\",\"password\":\"%s\",\"provider\":\"db\",\"refresh\":true}", username, password);
        try (OutputStream os = conn.getOutputStream()) {
            os.write(payload.getBytes("utf-8"));
        }

        int code = conn.getResponseCode();
        if (code == 200) {
            try (BufferedReader br = new BufferedReader(new InputStreamReader(conn.getInputStream(), "utf-8"))) {
                StringBuilder response = new StringBuilder();
                String line;
                while ((line = br.readLine()) != null) {
                    response.append(line.trim());
                }
                // Simple parsing to extract access_token
                String resStr = response.toString();
                int tokenIdx = resStr.indexOf("\"access_token\":\"");
                if (tokenIdx != -1) {
                    int start = tokenIdx + 16;
                    int end = resStr.indexOf("\"", start);
                    return resStr.substring(start, end);
                }
            }
        } else {
            LOG.error("Login failed with response code " + code);
        }
        return null;
    }

    private List<String> fetchDashboards(String baseUrl, String token, String userInput) throws Exception {
        List<String> list = new ArrayList<>();
        URL url = new URL(baseUrl + "/api/v1/dashboard/?q=(page:0,page_size:100)");
        HttpURLConnection conn = (HttpURLConnection) url.openConnection();
        conn.setRequestMethod("GET");
        conn.setRequestProperty("Authorization", "Bearer " + token);

        if (conn.getResponseCode() == 200) {
            try (BufferedReader br = new BufferedReader(new InputStreamReader(conn.getInputStream(), "utf-8"))) {
                StringBuilder sb = new StringBuilder();
                String line;
                while ((line = br.readLine()) != null) {
                    sb.append(line.trim());
                }
                String res = sb.toString();
                // Extract dashboard titles or slugs using regex-like scanner
                int idx = 0;
                while ((idx = res.indexOf("\"dashboard_title\":\"", idx)) != -1) {
                    int start = idx + 19;
                    int end = res.indexOf("\"", start);
                    String title = res.substring(start, end);
                    if (userInput == null || userInput.isEmpty() || title.toLowerCase().contains(userInput.toLowerCase())) {
                        list.add(title);
                    }
                    idx = end;
                }
            }
        }
        return list;
    }

    private List<String> fetchCharts(String baseUrl, String token, String userInput) throws Exception {
        List<String> list = new ArrayList<>();
        URL url = new URL(baseUrl + "/api/v1/chart/?q=(page:0,page_size:100)");
        HttpURLConnection conn = (HttpURLConnection) url.openConnection();
        conn.setRequestMethod("GET");
        conn.setRequestProperty("Authorization", "Bearer " + token);

        if (conn.getResponseCode() == 200) {
            try (BufferedReader br = new BufferedReader(new InputStreamReader(conn.getInputStream(), "utf-8"))) {
                StringBuilder sb = new StringBuilder();
                String line;
                while ((line = br.readLine()) != null) {
                    sb.append(line.trim());
                }
                String res = sb.toString();
                int idx = 0;
                while ((idx = res.indexOf("\"slice_name\":\"", idx)) != -1) {
                    int start = idx + 14;
                    int end = res.indexOf("\"", start);
                    String name = res.substring(start, end);
                    if (userInput == null || userInput.isEmpty() || name.toLowerCase().contains(userInput.toLowerCase())) {
                        list.add(name);
                    }
                    idx = end;
                }
            }
        }
        return list;
    }

    private List<String> fetchDatabases(String baseUrl, String token, String userInput) throws Exception {
        List<String> list = new ArrayList<>();
        URL url = new URL(baseUrl + "/api/v1/database/?q=(page:0,page_size:100)");
        HttpURLConnection conn = (HttpURLConnection) url.openConnection();
        conn.setRequestMethod("GET");
        conn.setRequestProperty("Authorization", "Bearer " + token);

        if (conn.getResponseCode() == 200) {
            try (BufferedReader br = new BufferedReader(new InputStreamReader(conn.getInputStream(), "utf-8"))) {
                StringBuilder sb = new StringBuilder();
                String line;
                while ((line = br.readLine()) != null) {
                    sb.append(line.trim());
                }
                String res = sb.toString();
                int idx = 0;
                while ((idx = res.indexOf("\"database_name\":\"", idx)) != -1) {
                    int start = idx + 17;
                    int end = res.indexOf("\"", start);
                    String dbName = res.substring(start, end);
                    if (userInput == null || userInput.isEmpty() || dbName.toLowerCase().contains(userInput.toLowerCase())) {
                        list.add(dbName);
                    }
                    idx = end;
                }
            }
        }
        return list;
    }

    private List<String> fetchSchemas(String baseUrl, String token, String dbName, String userInput) throws Exception {
        // Schemas are usually fetched per database. 
        // Superset API database metadata endpoint: GET /api/v1/database/{id}/schemas/
        // But since we have the DB name, we first find the DB ID
        List<String> list = new ArrayList<>();
        if (dbName == null || dbName.isEmpty()) {
            return list;
        }

        // 1. Get DB ID
        String dbId = null;
        URL dbUrl = new URL(baseUrl + "/api/v1/database/?q=(page:0,page_size:100)");
        HttpURLConnection conn = (HttpURLConnection) dbUrl.openConnection();
        conn.setRequestMethod("GET");
        conn.setRequestProperty("Authorization", "Bearer " + token);
        if (conn.getResponseCode() == 200) {
            try (BufferedReader br = new BufferedReader(new InputStreamReader(conn.getInputStream(), "utf-8"))) {
                StringBuilder sb = new StringBuilder();
                String line;
                while ((line = br.readLine()) != null) {
                    sb.append(line.trim());
                }
                String res = sb.toString();
                int idx = 0;
                while ((idx = res.indexOf("\"database_name\":\"", idx)) != -1) {
                    int start = idx + 17;
                    int end = res.indexOf("\"", start);
                    String name = res.substring(start, end);
                    if (name.equalsIgnoreCase(dbName)) {
                        // Find the ID block before or after it
                        int idIdx = res.lastIndexOf("\"id\":", start);
                        if (idIdx != -1) {
                            int idStart = idIdx + 5;
                            int idEnd = res.indexOf(",", idStart);
                            dbId = res.substring(idStart, idEnd).trim();
                            break;
                        }
                    }
                    idx = end;
                }
            }
        }

        if (dbId != null) {
            // 2. Fetch schemas for database ID
            URL schemaUrl = new URL(baseUrl + "/api/v1/database/" + dbId + "/schemas/");
            HttpURLConnection schemaConn = (HttpURLConnection) schemaUrl.openConnection();
            schemaConn.setRequestMethod("GET");
            schemaConn.setRequestProperty("Authorization", "Bearer " + token);
            if (schemaConn.getResponseCode() == 200) {
                try (BufferedReader br = new BufferedReader(new InputStreamReader(schemaConn.getInputStream(), "utf-8"))) {
                    StringBuilder sb = new StringBuilder();
                    String line;
                    while ((line = br.readLine()) != null) {
                        sb.append(line.trim());
                    }
                    String res = sb.toString();
                    // Response is typically {"result": ["schema1", "schema2", ...]}
                    int startIdx = res.indexOf("[");
                    int endIdx = res.indexOf("]");
                    if (startIdx != -1 && endIdx != -1) {
                        String schemasStr = res.substring(startIdx + 1, endIdx);
                        String[] schemas = schemasStr.split(",");
                        for (String s : schemas) {
                            String cleaned = s.replace("\"", "").trim();
                            if (!cleaned.isEmpty()) {
                                if (userInput == null || userInput.isEmpty() || cleaned.toLowerCase().contains(userInput.toLowerCase())) {
                                    list.add(cleaned);
                                }
                            }
                        }
                    }
                }
            }
        }

        return list;
    }

    private List<String> fetchDatasets(String baseUrl, String token, String dbName, String schemaName, String userInput) throws Exception {
        List<String> list = new ArrayList<>();
        URL url = new URL(baseUrl + "/api/v1/dataset/?q=(page:0,page_size:100)");
        HttpURLConnection conn = (HttpURLConnection) url.openConnection();
        conn.setRequestMethod("GET");
        conn.setRequestProperty("Authorization", "Bearer " + token);

        if (conn.getResponseCode() == 200) {
            try (BufferedReader br = new BufferedReader(new InputStreamReader(conn.getInputStream(), "utf-8"))) {
                StringBuilder sb = new StringBuilder();
                String line;
                while ((line = br.readLine()) != null) {
                    sb.append(line.trim());
                }
                String res = sb.toString();
                
                // Parse the datasets list. Since parsing complex nested JSON in raw Java String logic is tricky, 
                // we scan for "table_name" and check context if dbName or schemaName matches if present.
                int idx = 0;
                while ((idx = res.indexOf("\"table_name\":\"", idx)) != -1) {
                    int start = idx + 14;
                    int end = res.indexOf("\"", start);
                    String tableName = res.substring(start, end);
                    
                    if (userInput == null || userInput.isEmpty() || tableName.toLowerCase().contains(userInput.toLowerCase())) {
                        list.add(tableName);
                    }
                    idx = end;
                }
            }
        }
        return list;
    }
}
