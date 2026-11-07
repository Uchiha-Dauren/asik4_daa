package kz.aitu.city;

import java.io.PrintWriter;
import java.lang.management.ManagementFactory;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.security.MessageDigest;
import java.util.HexFormat;
import java.util.List;
import java.util.Locale;

/** Fixed experimental protocol; every CSV row is one measured batch/run. */
public class Experiment {
    private static final int RUNS = 5;
    private static final int WARMUPS = 2;
    private static volatile long blackhole;

    public static void main(String[] args) throws Exception {
        Path output = Path.of(args.length == 0 ? "results" : args[0]);
        Files.createDirectories(output);
        writeEnvironment(output);
        try (PrintWriter csv = new PrintWriter(Files.newBufferedWriter(output.resolve("results.csv")))) {
            csv.println("algorithm,input,n,m,suite,run,seed,batch_iterations,batch_time_ms,time_ms,state_visits,search_comparisons,lps_comparisons,total_comparisons,result,input_sha256");
            runEdit(csv, "edit_small", new int[] {2, 4, 6, 8, 10, 12}, true);
            runEdit(csv, "edit_large", new int[] {128, 256, 512, 1024, 2048}, false);
            runSearch(csv);
            if (csv.checkError()) throw new IllegalStateException("Could not write results.csv");
        }
        System.out.println("Saved 570 measured runs to " + output.resolve("results.csv"));
    }

    private static void runEdit(PrintWriter csv, String suite, int[] sizes, boolean includeRecursive) throws Exception {
        for (String type : new String[] {"identical", "random", "disjoint"}) {
            for (int n : sizes) {
                InputGenerator.Pair pair = InputGenerator.edit(type, n);
                String hash = hash(pair);
                int expected = new TableEditDistance().distance(pair.first(), pair.second());
                EditDistance[] algorithms = includeRecursive
                        ? new EditDistance[] {new RecursiveEditDistance(), new TableEditDistance(), new TwoRowEditDistance()}
                        : new EditDistance[] {new TableEditDistance(), new TwoRowEditDistance()};
                for (EditDistance algorithm : algorithms) {
                    int batch = editBatch(algorithm, n, includeRecursive);
                    long expectedStates = -1;
                    for (int run = -WARMUPS; run < RUNS; run++) {
                        int result = 0;
                        long checksum = 0;
                        long start = System.nanoTime();
                        for (int repetition = 0; repetition < batch; repetition++) {
                            result = algorithm.distance(pair.first(), pair.second());
                            checksum += result;
                        }
                        long elapsed = System.nanoTime() - start;
                        blackhole = checksum;
                        if (result != expected) throw new AssertionError("Edit result mismatch");
                        if (expectedStates >= 0 && expectedStates != algorithm.stateVisits()) {
                            throw new AssertionError("Edit counter changed across repetitions");
                        }
                        expectedStates = algorithm.stateVisits();
                        if (run >= 0) write(csv, algorithm.getClass().getSimpleName(), type, n, n, suite,
                                run + 1, batch, elapsed, algorithm.stateVisits(), 0, 0, result, hash);
                    }
                }
                csv.flush();
                System.out.println(suite + " " + type + " n=" + n);
            }
        }
    }

    private static int editBatch(EditDistance algorithm, int n, boolean small) {
        if (algorithm instanceof RecursiveEditDistance) {
            return switch (n) {
                case 2 -> 10000;
                case 4 -> 1000;
                case 6 -> 20;
                case 8 -> 2;
                default -> 1;
            };
        }
        return small ? 2000 : Math.max(1, 1000000 / (n * n));
    }

    private static void runSearch(PrintWriter csv) throws Exception {
        for (String type : new String[] {"random", "first_mismatch", "near_match"}) {
            for (int n : new int[] {10000, 20000, 40000, 80000, 160000}) {
                int m = n / 1000;
                int batch = Math.max(1, 160000 / n);
                InputGenerator.Pair pair = InputGenerator.search(type, n, m);
                String hash = hash(pair);
                List<Integer> expected = new NaiveSearch().search(pair.first(), pair.second());
                for (StringSearch algorithm : new StringSearch[] {new NaiveSearch(), new KmpSearch()}) {
                    long expectedComparisons = -1;
                    for (int run = -WARMUPS; run < RUNS; run++) {
                        List<Integer> result = List.of();
                        long checksum = 0;
                        long start = System.nanoTime();
                        for (int repetition = 0; repetition < batch; repetition++) {
                            result = algorithm.search(pair.first(), pair.second());
                            checksum += result.size();
                        }
                        long elapsed = System.nanoTime() - start;
                        blackhole = checksum;
                        if (!result.equals(expected)) throw new AssertionError("Search result mismatch");
                        if (expectedComparisons >= 0 && expectedComparisons != algorithm.comparisons()) {
                            throw new AssertionError("Search counter changed across repetitions");
                        }
                        expectedComparisons = algorithm.comparisons();
                        if (run >= 0) write(csv, algorithm.getClass().getSimpleName(), type, n, m, "search",
                                run + 1, batch, elapsed, 0, algorithm.searchComparisons(),
                                algorithm.lpsComparisons(), result.size(), hash);
                    }
                }
                csv.flush();
                System.out.println("search " + type + " n=" + n + " m=" + m);
            }
        }
    }

    private static void write(PrintWriter csv, String algorithm, String input, int n, int m,
                              String suite, int run, int batch, long ns, long states,
                              long search, long lps, int result, String hash) {
        csv.printf(Locale.ROOT, "%s,%s,%d,%d,%s,%d,%d,%d,%.9f,%.9f,%d,%d,%d,%d,%d,%s%n",
                algorithm, input, n, m, suite, run, InputGenerator.SEED, batch,
                ns / 1_000_000.0, ns / 1_000_000.0 / batch, states, search, lps, search + lps, result, hash);
    }

    private static String hash(InputGenerator.Pair pair) throws Exception {
        byte[] bytes = (pair.first() + "\0" + pair.second()).getBytes(StandardCharsets.UTF_8);
        return HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(bytes));
    }

    private static void writeEnvironment(Path output) throws Exception {
        String cpu = "Not available";
        Path cpuinfo = Path.of("/proc/cpuinfo");
        if (Files.isReadable(cpuinfo)) {
            try (var lines = Files.lines(cpuinfo)) {
                cpu = lines.filter(line -> line.startsWith("model name")).findFirst().orElse(cpu);
            }
        }
        Files.writeString(output.resolve("environment.txt"),
                "java.version=" + System.getProperty("java.version") + "\n"
                + "java.vm=" + System.getProperty("java.vm.name") + "\n"
                + "os=" + System.getProperty("os.name") + " " + System.getProperty("os.arch") + "\n"
                + "available_processors=" + Runtime.getRuntime().availableProcessors() + "\n"
                + "cpu=" + cpu + "\n"
                + "jvm_arguments=" + ManagementFactory.getRuntimeMXBean().getInputArguments() + "\n"
                + "seed=" + InputGenerator.SEED + "\nwarmup_batches=2\nmeasured_batches=5\n"
                + "note=Instrumented single-threaded JVM; timings are machine-dependent.\n");
    }
}
