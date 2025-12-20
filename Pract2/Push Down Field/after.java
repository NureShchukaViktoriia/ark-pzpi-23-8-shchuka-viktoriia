public abstract class User {
    private String name;
    private String email;
    private UserProfile profile;

    public User(String name, String email, UserProfile profile) {
        this.name = name;
        this.email = email;
        this.profile = profile;
    }
}

public class CustomerUser extends User {
    private int loyaltyPoints;

    public CustomerUser(String name, String email, UserProfile profile) {
        super(name, email, profile);
    }

    public void addPoints(int points) {
        loyaltyPoints += points;
    }
}

public class AdminUser extends User {
    private String adminRole;

    public AdminUser(String name, String email, UserProfile profile, String adminRole) {
        super(name, email, profile);
        this.adminRole = adminRole;
    }

    public boolean canDeleteUsers() {
        return "SUPER_ADMIN".equals(adminRole);
    }
}
