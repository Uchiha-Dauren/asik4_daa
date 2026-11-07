package spell.chek;

import java.util.ArrayList;
import java.util.List;

public class KmpSearch implements StringSearch {
    private long searchComparisons;
    private long lpsComparisons;

    // lps[i] is the length of the longest proper prefix of p[0..i]
    // that is also its suffix. Public so tests can check it independently.
    public int[] lps(String p) {
        lpsComparisons = 0;
        int[] lps = new int[p.length()];
        int len = 0;
        int i = 1;
        while (i < p.length()) {
            lpsComparisons++;
            if (p.charAt(i) == p.charAt(len)) {
                lps[i++] = ++len;
            } else if (len > 0) {
                len = lps[len - 1];
            } else {
                lps[i++] = 0;
            }
        }
        return lps;
    }

    @Override
    public List<Integer> search(String text, String pattern) {
        searchComparisons = 0;
        lpsComparisons = 0;
        if (pattern.isEmpty()) throw new IllegalArgumentException("Pattern must not be empty");
        List<Integer> matches = new ArrayList<>();
        if (pattern.length() > text.length()) return matches;
        int[] prefix = lps(pattern);
        int i = 0, j = 0;
        while (i < text.length()) {
            searchComparisons++;
            if (text.charAt(i) == pattern.charAt(j)) {
                i++;
                j++;
                if (j == pattern.length()) {
                    matches.add(i - j);
                    j = prefix[j - 1]; // Keep a matching suffix, including overlaps.
                }
            } else if (j > 0) {
                j = prefix[j - 1]; // Text index i never moves backwards.
            } else {
                i++;
            }
        }
        return matches;
    }

    @Override
    public long searchComparisons() { return searchComparisons; }

    @Override
    public long lpsComparisons() { return lpsComparisons; }
}
