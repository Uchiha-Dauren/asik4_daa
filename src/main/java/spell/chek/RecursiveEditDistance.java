package spell.chek;

public class RecursiveEditDistance implements EditDistance {
    private long states;

    // State: D(i,j) = distance between the first i characters of a and first j of b.
    // Transition: equal last chars -> D(i-1,j-1); otherwise 1 + min(delete, insert, replace).
    // Base: D(0,j)=j and D(i,0)=i. No cache: repeated states are recomputed.
    @Override
    public int distance(String a, String b) {
        states = 0;
        return solve(a, b, a.length(), b.length());
    }

    private int solve(String a, String b, int i, int j) {
        states++;
        if (i == 0) return j;
        if (j == 0) return i;
        if (a.charAt(i - 1) == b.charAt(j - 1)) {
            return solve(a, b, i - 1, j - 1);
        }
        int delete = solve(a, b, i - 1, j);
        int insert = solve(a, b, i, j - 1);
        int replace = solve(a, b, i - 1, j - 1);
        return 1 + Math.min(delete, Math.min(insert, replace));
    }

    @Override
    public long stateVisits() { return states; }
}
