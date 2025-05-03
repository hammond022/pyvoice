package com.pyvoice.auth;

import com.sun.net.httpserver.HttpServer;
import com.sun.net.httpserver.HttpHandler;
import com.sun.net.httpserver.HttpExchange;
import java.io.IOException;
import java.io.OutputStream;
import java.net.InetSocketAddress;
import java.util.HashMap;
import java.util.Map;
import java.util.concurrent.Executors;
import org.json.JSONObject;

public class UserAuth {
    private static Map<String, User> users = new HashMap<>();
    
    static {
        users.put("admin", new User("admin", "admin123", true));
        users.put("user", new User("user", "user123", false));
    }

    public static void main(String[] args) throws IOException {
        HttpServer server = HttpServer.create(new InetSocketAddress(8000), 0);
        server.createContext("/auth", new AuthHandler());
        server.setExecutor(Executors.newFixedThreadPool(10));
        server.start();
        System.out.println("Auth server started on port 8000");
    }

    static class AuthHandler implements HttpHandler {
        @Override
        public void handle(HttpExchange exchange) throws IOException {
            if ("POST".equals(exchange.getRequestMethod())) {
                try {
                    // Read request body
                    String requestBody = new String(exchange.getRequestBody().readAllBytes());
                    JSONObject json = new JSONObject(requestBody);
                    String username = json.getString("username");
                    String password = json.getString("password");

                    // Authenticate
                    User user = users.get(username);
                    JSONObject response = new JSONObject();
                    
                    if (user != null && user.getPassword().equals(password)) {
                        response.put("success", true);
                        response.put("isAdmin", user.isAdmin());
                    } else {
                        response.put("success", false);
                    }

                    // Send response
                    byte[] responseBytes = response.toString().getBytes();
                    exchange.sendResponseHeaders(200, responseBytes.length);
                    try (OutputStream os = exchange.getResponseBody()) {
                        os.write(responseBytes);
                    }
                } catch (Exception e) {
                    String response = "{\"success\": false, \"error\": \"" + e.getMessage() + "\"}";
                    exchange.sendResponseHeaders(400, response.length());
                    try (OutputStream os = exchange.getResponseBody()) {
                        os.write(response.getBytes());
                    }
                }
            } else {
                exchange.sendResponseHeaders(405, -1); // Method not allowed
            }
        }
    }
}
