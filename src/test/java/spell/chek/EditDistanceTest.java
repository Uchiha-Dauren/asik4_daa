package spell.chek;

import org.junit.jupiter.api.Test;
import java.util.Random;
import static org.junit.jupiter.api.Assertions.*;

class EditDistanceTest {
    private EditDistance[] algorithms() {
        return new EditDistance[] {new RecursiveEditDistance(), new TableEditDistance(), new TwoRowEditDistance()};
    }

    @Test
    void referenceValues() {
        for (EditDistance a : algorithms()) {
            assertEquals(3, a.distance("kitten", "sitting"));
            assertEquals(2, a.distance("flaw", "lawn"));
            assertEquals(5, a.distance("intention", "execution"));
            assertEquals(3, a.distance("", "abc"));
            assertEquals(0, a.distance("abc", "abc"));
        }
    }

    @Test
    void emptyAndSingleCharacterStrings() {
        for (EditDistance a : algorithms()) {
            assertEquals(0, a.distance("", ""));
            assertEquals(3, a.distance("abc", ""));
            assertEquals(1, a.distance("a", "b"));
            assertEquals(0, a.distance("x", "x"));
            assertEquals(2, a.distance("a", "abc"));
            assertEquals(2, a.distance("abc", "a"));
        }
    }

    @Test
    void oneHundredSeededRandomPairsAgree() {
        Random random = new Random(20261107L);
        EditDistance[] algorithms = algorithms();
        for (int test = 0; test < 100; test++) {
            String a = randomString(random, random.nextInt(7));
            String b = randomString(random, random.nextInt(7));
            int expected = algorithms[0].distance(a, b);
            for (EditDistance algorithm : algorithms) {
                assertEquals(expected, algorithm.distance(a, b), a + " -> " + b);
                assertEquals(expected, algorithm.distance(b, a), "Distance is symmetric");
            }
            assertTrue(expected >= Math.abs(a.length() - b.length()));
            assertTrue(expected <= Math.max(a.length(), b.length()));
        }
    }

    @Test
    void countersMeasureWorkAndReset() {
        for (EditDistance a : algorithms()) {
            a.distance("a", "b");
            assertEquals(4, a.stateVisits());
            a.distance("", "");
            assertEquals(1, a.stateVisits());
        }
        RecursiveEditDistance recursive = new RecursiveEditDistance();
        recursive.distance("aa", "bb");
        assertEquals(19, recursive.stateVisits());
        recursive.distance("abc", "abc");
        assertEquals(4, recursive.stateVisits());
    }

    private static String randomString(Random random, int length) {
        StringBuilder s = new StringBuilder();
        for (int i = 0; i < length; i++) s.append((char) ('a' + random.nextInt(3)));
        return s.toString();
    }
}
