package spell.chek;

public class RecursiveEditDistance implements EditDistance {
    private long states;

 
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
