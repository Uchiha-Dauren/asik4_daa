package spell.chek;

public class TableEditDistance implements EditDistance {
    private long states;

    // State: dp[i][j] = distance between prefixes a[0..i) and b[0..j).
    // Transition: equal -> dp[i-1][j-1]; otherwise 1+min(dp[i-1][j],dp[i][j-1],dp[i-1][j-1]).
    // Base: dp[0][j]=j and dp[i][0]=i.
    @Override
    public int distance(String a, String b) {
        states = 0;
        int n = a.length(), m = b.length();
        int[][] dp = new int[n + 1][m + 1];
        for (int j = 0; j <= m; j++) {
            dp[0][j] = j;
            states++;
        }
        for (int i = 1; i <= n; i++) {
            dp[i][0] = i;
            states++;
            for (int j = 1; j <= m; j++) {
                states++;
                if (a.charAt(i - 1) == b.charAt(j - 1)) {
                    dp[i][j] = dp[i - 1][j - 1];
                } else {
                    dp[i][j] = 1 + Math.min(dp[i - 1][j],
                            Math.min(dp[i][j - 1], dp[i - 1][j - 1]));
                }
            }
        }
        return dp[n][m];
    }

    @Override
    public long stateVisits() { return states; }
}
