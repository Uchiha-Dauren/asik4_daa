package spell.chek;

public class TwoRowEditDistance implements EditDistance {
    private long states;
    @Override
    public int distance(String a, String b) {
        states = 0;
        int n = a.length(), m = b.length();
        int[] previous = new int[m + 1];
        int[] current = new int[m + 1];
        for (int j = 0; j <= m; j++) {
            previous[j] = j;
            states++;
        }
        for (int i = 1; i <= n; i++) {
            current[0] = i;
            states++;
            for (int j = 1; j <= m; j++) {
                states++;
                if (a.charAt(i - 1) == b.charAt(j - 1)) {
                    current[j] = previous[j - 1];
                } else {
                    current[j] = 1 + Math.min(previous[j],
                            Math.min(current[j - 1], previous[j - 1]));
                }
            }
            int[] temp = previous;
            previous = current;
            current = temp;
        }
        return previous[m];
    }

    @Override
    public long stateVisits() { return states; }
}
