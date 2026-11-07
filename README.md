# City Search & Spell-Check

Assignment 4: three Edit Distance implementations, Naive and KMP search,
JUnit 5 tests, a fixed-seed experiment, measured data, four plots and a four-page report.

## Open and run

Use **JDK 17 or newer** and **Maven 3.9+**. In IntelliJ IDEA, open this folder
or its `pom.xml`, choose a JDK and let Maven load the dependencies.

```bash
mvn test
mvn package
java -jar target/city-search-spell-check-1.0.jar
```

The demo compares `Abylai Han` and `Abylai Khan`, then finds `ERROR` in a log.
The distance is **2**, because search is case-sensitive: insert `K` and replace
`H` with `h`. If both inputs are lowercased first, the distance is **1**.
Both searches print `[10, 25]`.

## Repeat the experiment

From this project's root:

```bash
mvn package
java -Xms128m -Xmx512m -cp target/classes kz.aitu.city.Experiment
```

This overwrites `results/results.csv` and `results/environment.txt` with a fresh
570-row measurement. The largest recursive case may take a few seconds on a
slower machine. An optional output directory keeps the original results:

```bash
java -Xms128m -Xmx512m -cp target/classes kz.aitu.city.Experiment results-rerun
```

The seed is **20261107**. Every case has two warmup batches and five measured
batches. Inputs, hashes, answers and counters are deterministic; clock times
vary. No claim is made that timings will be byte-for-byte identical.

To rebuild plots and both reports (Python 3.10+):

```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -r requirements.txt
python3 scripts/analyze.py
python3 scripts/build_report.py
```

Run `mvn test` first: the report generator reads the actual JUnit XML results.
The scripts read the default `results/` directory. The supplied reports and plots
are already generated, so Python is optional for viewing/submitting the project.

## Files

| Path | Purpose |
| --- | --- |
| `src/main/java/kz/aitu/city/` | Five algorithms, two family interfaces, input generator, experiment and demo |
| `src/test/java/kz/aitu/city/` | JUnit 5 references, edges, random comparisons and counter checks |
| `EXPERIMENT_PLAN.md` | Design card committed before measurements; full batching protocol |
| `REPORT.pdf`, `REPORT.md` | Report with design card, plots, predictions, results and short answers |
| `results/results.csv` | One row per measured batch/run, 570 rows |
| `results/summary.csv` | Five-run medians and observed minimum/maximum, 114 cases |
| `results/plots/` | Four labeled plots, PNG and SVG versions |
| `results/environment.txt` | JVM, CPU, OS, seed and runtime options |
| `results/validation.txt` | Actual JUnit and CSV validation summary |
| `scripts/analyze.py` | Validates CSV, creates summary and plots |
| `scripts/build_report.py` | Builds reports from measured data and JUnit results |

## APIs and complexity

| Implementation | Main method | Time | Extra memory |
| --- | --- | --- | --- |
| `RecursiveEditDistance` | `int distance(String a, String b)` | Exponential in general; linear for equal strings | O(n+m) call stack |
| `TableEditDistance` | Same interface | O(n*m) | O(n*m) |
| `TwoRowEditDistance` | Same interface | O(n*m) | O(m) |
| `NaiveSearch` | `List<Integer> search(String text, String pattern)` | O((n-m+1)*m) worst case when m<=n | O(1), excluding matches |
| `KmpSearch` | Same search interface; public `int[] lps(String p)` | O(n+m), including LPS | O(m), excluding matches |

Search positions start at zero and include overlaps. No match and overlong
patterns return an empty list; empty search patterns throw
`IllegalArgumentException`. `lps("")` returns an empty array. Inputs must be
non-null; comparisons use Java UTF-16 `char` units, without normalization.
The algorithm instances keep counters and are intended for single-threaded use.

## What the counters mean

`stateVisits()` counts recursive calls (including repeated/base states), or DP
states actually evaluated, including initialization. It resets on each distance
call. It is a work proxy, not an instruction count.

`searchComparisons()` and `lpsComparisons()` increment at the actual character
comparison in each loop. `comparisons()` is their sum. Search resets both
counters; a standalone `lps()` call resets the LPS counter only. Naive has zero
LPS comparisons. KMP's elapsed time includes LPS allocation and construction.

The two-row version allocates exactly two `int[m+1]` arrays and swaps references;
it does not copy rows or retain the whole matrix. The memory chart is a theoretical
count of retained integer slots, not a measured heap or process-memory figure.

## CSV columns

| Columns | Meaning |
| --- | --- |
| `algorithm,input,n,m,suite` | Implementation, input kind, lengths and experiment group |
| `run,seed` | Measured run 1..5 and fixed master seed |
| `batch_iterations,batch_time_ms` | Repeated invocations in this run and total measured batch milliseconds |
| `time_ms` | Batch milliseconds divided by repetitions; retains sub-millisecond precision |
| `state_visits` | Measured edit work per invocation; 0 for search |
| `search_comparisons,lps_comparisons,total_comparisons` | Measured search work per invocation; 0 for edit |
| `result` | Distance, or number of search matches |
| `input_sha256` | SHA-256 of first input + NUL + second input, UTF-8; verifies equal inputs |

The summaries use the median of five `time_ms` values. The experiment validates
answers after timing, writes files outside timing, and consumes returned results.
There is one generated input per type/size; repeated runs measure timing variation,
not variation across different random samples.

## Tests

`mvn test` runs 12 JUnit test methods. They cover every supplied reference value,
empty strings, an empty pattern exception, patterns longer than text, overlap,
first/last positions, missing matches, LPS fallback and counter resets.
One test checks 100 seeded short edit pairs across all three versions (and symmetry).
Another checks 100 seeded searches against both implementations and Java's `indexOf`.
`scripts/analyze.py` independently validates all 570 recorded runs and their
counter consistency, five-run groups, hashes and cross-algorithm results.

## Git

The ZIP includes the local `.git` directory, branch **main**, small commits and
the final annotated tag **v1.0**. Some file managers hide `.git`; keep it when
moving the project. Verify the included history with:

```bash
git status
git log --oneline
git tag
```

To submit through your own GitHub repository, create an empty repository there,
then substitute its real URL:

```bash
git remote add origin YOUR_REPOSITORY_URL
git push -u origin main
git push origin v1.0
```

## Қорғауға қысқаша

- **DP state:** `D(i,j)` - екі жолдың алғашқы `i` және `j` таңбаларының арақашықтығы.
- **Transition:** соңғы таңбалар бірдей болса диагональды аламыз; әйтпесе өшіру, қосу, ауыстырудың ең кішісіне 1 қосамыз.
- **Base case:** бір жол бос болса, жауап екінші жолдың ұзындығына тең.
- **Рекурсия:** бірдей ішкі есептерді қайта-қайта шығарады, сондықтан қиын кірісте баяулайды.
- **Two rows:** тек алдыңғы және қазіргі қатар керек; жауап сақталады, жад азаяды.
- **LPS:** pattern бөлігінің басы мен соңы сәйкес келетін ең ұзын proper prefix ұзындығы.
- **KMP:** сәйкессіздікте мәтін индексін кері жылжытпай, LPS арқылы pattern ішіндегі орынды ауыстырады.
- **Overlap:** сәйкестік табылғаннан кейін `j = lps[j - 1]`, сондықтан қабаттасқан сәйкестіктер жоғалмайды.
- **Медиана:** бес өлшеуді реттегенде ортасында тұрған уақыт; бір кездейсоқ секірістің әсері азаяды.
- **Қиын input:** `aaaa...a` мәтіні және `aaa...ab` үлгісі Naive алгоритмін бір таңбаларды қайта салыстыруға мәжбүрлейді.

The report is a measured worked example. Read the code and results so you can
explain the experiment and adjust it if your instructor changes an input.
