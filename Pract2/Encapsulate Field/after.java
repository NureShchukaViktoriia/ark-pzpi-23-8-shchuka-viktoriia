public class User {
    private String name;
    private String email;
    private int loyaltyPoints;
    private String adminRole;
    private String address;
    private String phone;

    public String getName() {
        return name;
    }

    public String getEmail() {
        return email;
    }

    public int getLoyaltyPoints() {
        return loyaltyPoints;
    }

    protected void setLoyaltyPoints(int loyaltyPoints) {
        this.loyaltyPoints = loyaltyPoints;
    }

    protected String getAdminRole() {
        return adminRole;
    }
}
