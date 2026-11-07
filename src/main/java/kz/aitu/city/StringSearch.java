package kz.aitu.city;

import java.util.List;

/** Searches are case-sensitive. Counters reset on each search. */
public interface StringSearch {
    List<Integer> search(String text, String pattern);
    long searchComparisons();
    long lpsComparisons();

    default long comparisons() {
        return searchComparisons() + lpsComparisons();
    }
}
