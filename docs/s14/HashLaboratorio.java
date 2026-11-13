import org.springframework.security.crypto.bcrypt.BCryptPasswordEncoder;

class HashLaboratorio {
    public static void main(String[] args) {
        System.out.print(new BCryptPasswordEncoder().encode(System.getenv("S14_LAB_LOGIN")));
    }
}
