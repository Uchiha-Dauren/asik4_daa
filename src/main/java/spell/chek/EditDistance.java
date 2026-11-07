package spell.chek;

public interface EditDistance {
    int distance(String a, String b);
    long stateVisits();
}
