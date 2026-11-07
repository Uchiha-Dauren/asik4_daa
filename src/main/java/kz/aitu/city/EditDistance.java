package kz.aitu.city;

/** Counter describes the most recent call; implementations are not thread-safe. */
public interface EditDistance {
    int distance(String a, String b);
    long stateVisits();
}
