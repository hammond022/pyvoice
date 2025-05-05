package com.pyvoice.auth;

import com.sun.net.httpserver.HttpServer;
import com.sun.net.httpserver.HttpHandler;
import com.sun.net.httpserver.HttpExchange;
import java.io.*;
import java.net.InetSocketAddress;
import java.util.*;
import java.util.concurrent.Executors;
import org.json.JSONObject;
import org.json.JSONArray;

public class UserAuth {
    private static Map<String, User> users = new HashMap<>();
    
    static {
        users.put("admin", new User("admin", "admin000", true));
        users.put("user", new User("user", "user123", false));
    }

    private static final String USERS_FILE = "users.json";
    private static boolean isRunning = true;
    
    private static void loadUsers() {
        try {
            File file = new File(USERS_FILE);
            if (file.exists()) {
                String content = new String(java.nio.file.Files.readAllBytes(file.toPath()));
                JSONArray jsonArray = new JSONArray(content);
                for (int i = 0; i < jsonArray.length(); i++) {
                    JSONObject obj = jsonArray.getJSONObject(i);
                    users.put(obj.getString("username"),
                            new User(obj.getString("username"),
                                   obj.getString("password"),
                                   obj.getBoolean("isAdmin")));
                }
            }
        } catch (Exception e) {
            System.err.println("Error loading users: " + e.getMessage());
        }
    }

    private static void saveUsers() {
        try {
            JSONArray jsonArray = new JSONArray();
            for (User user : users.values()) {
                JSONObject obj = new JSONObject();
                obj.put("username", user.getUsername());
                obj.put("password", user.getPassword());
                obj.put("isAdmin", user.isAdmin());
                jsonArray.put(obj);
            }
            java.nio.file.Files.write(new File(USERS_FILE).toPath(),
                                    jsonArray.toString(2).getBytes());
        } catch (Exception e) {
            System.err.println("Error saving users: " + e.getMessage());
        }
    }

    private static boolean isValidPassword(String password) {
        return password != null && password.length() >= 6;
    }

    private static void startCLI() {
        Scanner scanner = new Scanner(System.in);
        System.out.println("Type 'help' for commands");
        
        while (isRunning) {
            System.out.print("\n> ");
            String input = scanner.nextLine().trim();
            String[] args = input.split("\\s+");
            
            if (args.length == 0 || args[0].isEmpty()) continue;

            switch (args[0].toLowerCase()) {
                case "help":
                    System.out.println("Available commands:");
                    System.out.println("  add <username> <password>     Add new regular user");
                    System.out.println("  remove <username>             Remove a user");
                    System.out.println("  passwd <username> <password>  Change password");
                    System.out.println("  list                          List all users");
                    System.out.println("  quit                          Exit the CLI");
                    break;

                case "add":
                    if (args.length != 3) {
                        System.out.println("Usage: add <username> <password>");
                        break;
                    }
                    if (args[1].equals("admin")) {
                        System.out.println("Cannot create admin user");
                        break;
                    }
                    if (!isValidPassword(args[2])) {
                        System.out.println("Password must be at least 6 characters");
                        break;
                    }
                    if (users.containsKey(args[1])) {
                        System.out.println("User already exists");
                        break;
                    }
                    users.put(args[1], new User(args[1], args[2], false));
                    saveUsers();
                    System.out.println("User added successfully");
                    break;

                case "remove":
                    if (args.length != 2) {
                        System.out.println("Usage: remove <username>");
                        break;
                    }
                    if (args[1].equals("admin")) {
                        System.out.println("Cannot remove admin user");
                        break;
                    }
                    if (!users.containsKey(args[1])) {
                        System.out.println("User not found");
                        break;
                    }
                    System.out.print("Are you sure? (y/N): ");
                    if (scanner.nextLine().toLowerCase().equals("y")) {
                        users.remove(args[1]);
                        saveUsers();
                        System.out.println("User removed successfully");
                    }
                    break;

                case "passwd":
                    if (args.length != 3) {
                        System.out.println("Usage: passwd <username> <newpassword>");
                        break;
                    }
                    if (args[1].equals("admin")) {
                        System.out.println("Cannot change admin password");
                        break;
                    }
                    if (!users.containsKey(args[1])) {
                        System.out.println("User not found");
                        break;
                    }
                    if (!isValidPassword(args[2])) {
                        System.out.println("Password must be at least 6 characters");
                        break;
                    }
                    users.put(args[1], new User(args[1], args[2], users.get(args[1]).isAdmin()));
                    saveUsers();
                    System.out.println("Password changed successfully");
                    break;

                case "list":
                    System.out.println("\nUser List:");
                    System.out.println("-----------------");
                    users.values().forEach(user -> 
                        System.out.printf("%-20s %s%n", user.getUsername(), 
                                        user.isAdmin() ? "(admin)" : ""));
                    break;

                case "quit":
                    isRunning = false;
                    break;

                default:
                    System.out.println("Unknown command. Type 'help' for usage information.");
            }
        }
        scanner.close();
        System.exit(0);
    }

    public static void main(String[] args) throws IOException {
        loadUsers();
        
        // Start HTTP server
        HttpServer server = HttpServer.create(new InetSocketAddress(8000), 0);
        server.createContext("/auth", new AuthHandler());
        server.setExecutor(Executors.newFixedThreadPool(10));
        server.start();
        System.out.println("Auth server started on port 8000");
        
        // Start interactive CLI
        startCLI();
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
