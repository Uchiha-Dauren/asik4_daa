package spell.chek;

import java.util.List;

public interface StringSearch {
    List<Integer> search(String text, String pattern);
    long searchComparisons();
    long lpsComparisons();

    default long comparisons() {
        return searchComparisons() + lpsComparisons();
    }
}
