package spell.chek;

public class Demo {
    public static void main(String[] args) {
        for (EditDistance algorithm : new EditDistance[] {
                new RecursiveEditDistance(), new TableEditDistance(), new TwoRowEditDistance()}) {
            System.out.println(algorithm.getClass().getSimpleName() + ": "
                    + algorithm.distance("Abylai Han", "Abylai Khan"));
        }
        String log = "INFO OK | ERROR | WARN | ERROR | OK";
        for (StringSearch algorithm : new StringSearch[] {new NaiveSearch(), new KmpSearch()}) {
            System.out.println(algorithm.getClass().getSimpleName() + ": "
                    + algorithm.search(log, "ERROR"));
        }
    }
}
