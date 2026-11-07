package spell.chek;

import java.util.Random;

public class InputGenerator {
    public static final long SEED = 20261107L;
    public record Pair(String first, String second) {}

    public static Pair edit(String type, int n) {
        Random random = new Random(SEED + 31L * n + type.hashCode());
        return switch (type) {
            case "identical" -> {
                String a = randomString(random, n);
                yield new Pair(a, a);
            }
            case "random" -> new Pair(randomString(random, n), randomString(random, n));
            case "disjoint" -> new Pair("a".repeat(n), "b".repeat(n));
            default -> throw new IllegalArgumentException("Unknown edit input: " + type);
        };
    }

    public static Pair search(String type, int n, int m) {
        Random random = new Random(SEED + 31L * n + 17L * m + type.hashCode());
        return switch (type) {
            case "random" -> {
                String text = randomString(random, n);
                yield new Pair(text, text.substring(n / 2, n / 2 + m));
            }
            case "first_mismatch" -> new Pair("a".repeat(n), "b".repeat(m));
            case "near_match" -> new Pair("a".repeat(n), "a".repeat(m - 1) + "b");
            default -> throw new IllegalArgumentException("Unknown search input: " + type);
        };
    }

    private static String randomString(Random random, int n) {
        StringBuilder s = new StringBuilder(n);
        for (int i = 0; i < n; i++) s.append((char) ('a' + random.nextInt(26)));
        return s.toString();
    }
}
