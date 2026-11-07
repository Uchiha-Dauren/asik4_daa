package kz.aitu.city;

import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.*;

class KmpLpsTest {
    @Test
    void referenceArrays() {
        KmpSearch kmp = new KmpSearch();
        assertArrayEquals(new int[] {0, 1, 2, 0, 1, 2, 3, 3}, kmp.lps("AAACAAAA"));
        assertArrayEquals(new int[] {0, 0, 1, 2, 0, 1, 2, 3, 4}, kmp.lps("ABABCABAB"));
    }

    @Test
    void simpleAndEmptyPatterns() {
        KmpSearch kmp = new KmpSearch();
        assertArrayEquals(new int[] {}, kmp.lps(""));
        assertArrayEquals(new int[] {0}, kmp.lps("A"));
        assertArrayEquals(new int[] {0, 1, 2, 3}, kmp.lps("AAAA"));
        assertEquals(3, kmp.lpsComparisons());
        assertArrayEquals(new int[] {0, 0, 0}, kmp.lps("ABC"));
        assertEquals(2, kmp.lpsComparisons());
    }
}
