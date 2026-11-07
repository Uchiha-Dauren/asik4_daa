package kz.aitu.city;

import org.junit.jupiter.api.Test;
import java.util.ArrayList;
import java.util.List;
import java.util.Random;
import static org.junit.jupiter.api.Assertions.*;

class StringSearchTest {
    private StringSearch[] algorithms() { return new StringSearch[] {new NaiveSearch(), new KmpSearch()}; }

    @Test
    void referenceAndOverlappingMatches() {
        for (StringSearch a : algorithms()) {
            assertEquals(List.of(10), a.search("ABABDABACDABABCABAB", "ABABCABAB"));
            assertEquals(List.of(0, 1, 2, 3), a.search("AAAAA", "AA"));
            assertEquals(List.of(0, 2, 4), a.search("ABABABA", "ABA"));
        }
    }

    @Test
    void emptyPatternThrowsEvenForEmptyText() {
        for (StringSearch a : algorithms()) {
            assertThrows(IllegalArgumentException.class, () -> a.search("abc", ""));
            assertThrows(IllegalArgumentException.class, () -> a.search("", ""));
        }
    }

    @Test
    void longerPatternAndEmptyTextReturnEmpty() {
        for (StringSearch a : algorithms()) {
            assertEquals(List.of(), a.search("AB", "ABC"));
            assertEquals(0, a.comparisons());
            assertEquals(List.of(), a.search("", "A"));
        }
    }

    @Test
    void noMatchExactMatchAndBoundaries() {
        for (StringSearch a : algorithms()) {
            assertEquals(List.of(), a.search("ABCDE", "FG"));
            assertEquals(List.of(0), a.search("ABC", "ABC"));
            assertEquals(List.of(0, 4), a.search("ABCXABC", "ABC"));
            assertEquals(List.of(0, 2), a.search("ABA", "A"));
        }
    }

    @Test
    void oneHundredSeededRandomTextsAgreeWithIndexOf() {
        Random random = new Random(20261107L);
        for (int test = 0; test < 100; test++) {
            String text = randomString(random, random.nextInt(51));
            String pattern = randomString(random, 1 + random.nextInt(10));
            List<Integer> expected = new ArrayList<>();
            for (int at = text.indexOf(pattern); at >= 0; at = text.indexOf(pattern, at + 1)) {
                expected.add(at);
            }
            for (StringSearch a : algorithms()) assertEquals(expected, a.search(text, pattern));
        }
    }

    @Test
    void countersIncludePreprocessingAndReset() {
        NaiveSearch naive = new NaiveSearch();
        KmpSearch kmp = new KmpSearch();
        naive.search("AAAAA", "AA");
        assertEquals(8, naive.comparisons());
        kmp.search("AAAAA", "AA");
        assertEquals(5, kmp.searchComparisons());
        assertEquals(1, kmp.lpsComparisons());
        assertEquals(6, kmp.comparisons());
        kmp.search("A", "A");
        assertEquals(1, kmp.comparisons());
        naive.search("A", "A");
        assertEquals(1, naive.comparisons());
    }

    private static String randomString(Random random, int length) {
        StringBuilder s = new StringBuilder();
        for (int i = 0; i < length; i++) s.append((char) ('A' + random.nextInt(3)));
        return s.toString();
    }
}
