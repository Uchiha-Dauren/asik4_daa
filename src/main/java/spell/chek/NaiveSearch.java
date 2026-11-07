package spell.chek;

import java.util.ArrayList;
import java.util.List;

public class NaiveSearch implements StringSearch {
    private long comparisons;

    @Override
    public List<Integer> search(String text, String pattern) {
        comparisons = 0;
        if (pattern.isEmpty()) throw new IllegalArgumentException("Pattern must not be empty");
        List<Integer> matches = new ArrayList<>();
        for (int start = 0; start <= text.length() - pattern.length(); start++) {
            int j = 0;
            while (j < pattern.length()) {
                comparisons++;
                if (text.charAt(start + j) != pattern.charAt(j)) break;
                j++;
            }
            if (j == pattern.length()) matches.add(start);
        }
        return matches;
    }

    @Override
    public long searchComparisons() { return comparisons; }

    @Override
    public long lpsComparisons() { return 0; }
}
