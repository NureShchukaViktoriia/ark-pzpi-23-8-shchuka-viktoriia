// User.java
public class User {
    public String name;
    public String email;

    // Використовується лише CustomerUser
    public int loyaltyPoints;

    // Використовується лише AdminUser
    public String adminRole;

    // Дані профілю
    public String address;
    public String phone;
}

// CustomerUser.java
public class CustomerUser extends User {
    public void addPoints(int points) {
        loyaltyPoints += points;
    }
}

// AdminUser.java
public class AdminUser extends User {
    public boolean canDeleteUsers() {
        return adminRole.equals("SUPER_ADMIN");
    }
}
