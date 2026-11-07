"""Build the four-page PDF and matching Markdown report from measured results."""
import csv
import xml.etree.ElementTree as ET
import matplotlib
from pathlib import Path
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, PageBreak
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

ROOT = Path(__file__).resolve().parents[1]
rows = list(csv.DictReader((ROOT / "results/summary.csv").open()))

def get(algorithm, kind, n, suite):
    return next(r for r in rows if r["algorithm"] == algorithm and r["input"] == kind
                and int(r["n"]) == n and r["suite"] == suite)

def ms(r): return float(r["median_time_ms"])
def number(r, field): return f"{int(r[field]):,}"

rec = get("RecursiveEditDistance", "disjoint", 12, "edit_small")
tab = get("TableEditDistance", "disjoint", 2048, "edit_large")
two = get("TwoRowEditDistance", "disjoint", 2048, "edit_large")
naive = get("NaiveSearch", "near_match", 160000, "search")
kmp = get("KmpSearch", "near_match", 160000, "search")
ratio = int(naive["total_comparisons"]) / int(kmp["total_comparisons"])
speed = ms(naive) / ms(kmp)
test_files = sorted((ROOT / "target/surefire-reports").glob("TEST-*.xml"))
assert test_files, "Run mvn test before building the report"
test_suites = [ET.parse(p).getroot() for p in test_files]
tests = sum(int(s.attrib["tests"]) for s in test_suites)
assert all(int(s.attrib["failures"]) == int(s.attrib["errors"]) == int(s.attrib["skipped"]) == 0 for s in test_suites)
env = (ROOT / "results/environment.txt").read_text()

card = [
    ("Question", "Edit: how do recursion and DP change work growth and retained storage? Search: which inputs let KMP avoid the repeated comparisons made by Naive?"),
    ("Sizes", "All edit versions: n = m = 2, 4, 6, 8, 10, 12. Extra table/two-row runs: n = m = 128, 256, 512, 1024, 2048. Search: n = 10000, 20000, 40000, 80000, 160000; m = n/1000. Every range spans at least 4x. Recursion is capped at 12 to keep runtime practical."),
    ("Inputs", "Edit: identical seeded strings show the matching shortcut; independent random strings (a..z) show a less regular case; a^n vs b^n forces recursive branching. Search: random text with a middle substring guarantees a match; a^n vs b^m rejects immediately; a^n vs a^(m-1)b forces a late mismatch at every Naive alignment."),
    ("Metrics", "Elapsed milliseconds per invocation, median of 5 runs. Edit state_visits counts each call or evaluated DP state, including bases. Search counts actual character comparisons, separating LPS from scanning; totals and timings include both. Each counter increments inside the Java algorithm. Storage plots count theoretical int slots, not heap usage."),
    ("Prediction", "Disjoint recursion grows exponentially; identical recursion needs n+1 calls. DP performs (n+1)^2 state evaluations, but two rows retain only 2(n+1) int slots. Near-match Naive work grows approximately quadratically because m grows with n; KMP remains linear in n+m. Random and first-mismatch search should be near-linear."),
    ("Plots", "1: small edit states (log y) reveals repeated work. 2: large DP time and theoretical slots shows the time/space tradeoff. 3: search comparisons isolates repeated character work. 4: search time checks whether clock measurements support the counter trend. Search panels use log axes."),
]

protocol = ("Seed 20261107. Each case has 2 warmup batches and 5 measured batches. Short calls are batched; "
            "time_ms is batch_time_ms / batch_iterations. CSV counters are per invocation, not batch totals. "
            "Inputs, validation and file writing are outside the timer; result checks prevent silent mismatches. "
            "The full batch schedule was recorded in EXPERIMENT_PLAN.md before the first run.")
change = ("Plan changes: no sizes, inputs, counters or predictions changed. An initial Java 21 run was replaced by a complete "
          "Java 17 run to match the project's target; only the latter is reported. Fixed inputs, hashes, answers and counters "
          "are reproducible; elapsed time cannot be identical across runs or computers.")
validation = (f"Validation: {tests} JUnit 5 tests passed with zero failures, errors or skips. These include all supplied distance, "
              "LPS and search references, empty/overlong cases, counter resets, 100 random edit pairs and 100 random search cases "
              "(also checked with String.indexOf). All 570 measured CSV rows passed consistency checks.")

captions = [
    f"Disjoint recursion reaches {number(rec, 'state_visits')} calls at n=12, while either DP method evaluates only 169 states; identical recursion uses 13 calls.",
    f"At n=2048, two rows retain 4,098 int slots versus 4,198,401 for the table; their disjoint medians are {ms(two):.3f} ms and {ms(tab):.3f} ms, respectively.",
    f"For n=160,000 and m=160 on near-match input, Naive makes {number(naive, 'total_comparisons')} comparisons versus {number(kmp, 'total_comparisons')} for KMP, about {ratio:.1f} times as many.",
    f"At the largest near-match case, Naive takes {ms(naive):.3f} ms and KMP {ms(kmp):.3f} ms ({speed:.1f}x measured speedup); timing ratios need not equal comparison ratios.",
]
prediction_edit = (f"Expected: repeated disjoint recursion should grow much faster than DP, and two rows should save space. "
                   f"Observed: at n=12 recursion made {number(rec, 'state_visits')} calls, while both DP variants made 169 state evaluations. "
                   f"At n=2048 both DP variants evaluated {number(tab, 'state_visits')} states; two rows were faster on this run and "
                   "used 1,024.5 times fewer retained int slots. This agrees with the predicted work/space trend, but state counts "
                   "are not CPU instructions and smaller-case timing irregularities are compatible with JIT, allocation and shared-host noise.")
prediction_search = (f"Expected: long repeated prefixes should make Naive expensive while KMP reuses prefix information. "
                     f"Observed: the near-match counter ratio reached {ratio:.1f}x and the time ratio {speed:.1f}x at the largest case. "
                     "Random and first-mismatch comparison curves nearly overlap between algorithms and grow roughly linearly. "
                     "Time does not track comparisons exactly because preprocessing, branches, loop overhead and JVM optimization differ; "
                     "the experiment does not establish a universal speed ranking. KMP's random-input time drops from n=10000 "
                     "to n=20000 despite more comparisons; incomplete JVM warmup or host noise is a plausible explanation, not improved asymptotic complexity.")

answers = [
    ("Which input made string search slowest, and why?",
     f"The largest near_match input was the slowest measured case for both implementations: text a^160000 and pattern a^159b. "
     "Naive matches a long prefix and then fails on b at every alignment, so it repeats almost the same work (n-m+1) times. "
     f"It performs {number(naive, 'total_comparisons')} character comparisons. KMP uses LPS to fall back within the pattern without "
     "moving backwards in the text, so its work stays O(n+m), although this case still causes extra fallback comparisons."),
    ("How large an n could recursive edit distance handle, and what stopped it?",
     f"The largest tested length was n=m=12, and the disjoint case completed with a median of {ms(rec):.3f} ms per invocation. "
     f"That call already visited {number(rec, 'state_visits')} recursive states. The predeclared experiment budget stopped further "
     "sizes because mismatches create three branches and repeated work grows exponentially. This is the largest measured size, "
     "not a proven hardware limit; identical strings are much easier, and no timeout or stack overflow was observed."),
    ("What do two rows gain and lose compared with the full table?",
     "Two rows reduce auxiliary DP storage from O(n*m) to O(m), while preserving the same distance and O(n*m) time. "
     "At n=m=2048, the implementation retains 4,098 integer slots instead of 4,198,401, excluding array headers and input strings. "
     "It discards previous rows, so a direct traceback of the edit sequence is no longer available. "
     "Recovering the operations needs recomputation or another technique; using two rows alone does not guarantee a time speedup."),
]

limits = ("Scope: Java 17.0.21 on Linux amd64, AMD EPYC 9V74, single-threaded, -Xms128m -Xmx512m. "
          "One deterministic input per type/size is repeated five times; this is a teaching experiment, not JMH or a distribution of inputs. "
          "Counters add overhead, algorithm order is fixed, and sub-microsecond results are noisy. Search grows m with n; with a fixed m, "
          "Naive's O(n*m) bound is linear in n. Strings use case-sensitive Java UTF-16 char units, with no normalization or case folding.")

plots = ["01_edit_states", "02_dp_time_space", "03_search_comparisons", "04_search_time"]
edit_table = [["Disjoint edit case", "Median time (ms)", "State visits"],
              ["Recursive, n=12", f"{ms(rec):.3f}", number(rec, "state_visits")],
              ["Table, n=2048", f"{ms(tab):.3f}", number(tab, "state_visits")],
              ["Two rows, n=2048", f"{ms(two):.3f}", number(two, "state_visits")]]
search_table = [["Input, n=160000; m=160", "Naive (ms)", "KMP (ms)"]]
for kind in ["random", "first_mismatch", "near_match"]:
    search_table.append([kind, f"{ms(get('NaiveSearch', kind, 160000, 'search')):.3f}",
                         f"{ms(get('KmpSearch', kind, 160000, 'search')):.3f}"])

def md_table(data):
    return "\n".join(["| " + " | ".join(data[0]) + " |", "| " + " | ".join(["---"] * len(data[0])) + " |"]
                     + ["| " + " | ".join(row) + " |" for row in data[1:]])

md = ["# City Search & Spell-Check - Assignment 4", "Java 17 | 7 November 2026", "## Experiment Design Card",
      "Recorded in EXPERIMENT_PLAN.md and committed before the first benchmark.",
      md_table([["Field", "Design"]] + [[k, v] for k, v in card]), protocol, change, validation,
      "## Edit distance results"]
for i in [0, 1]:
    md += [f"![{plots[i]}](results/plots/{plots[i]}.png)", captions[i]]
md += [md_table(edit_table), "Times are medians of five runs; rows with different n are not equal-size timing comparisons.",
       "## String search results"]
for i in [2, 3]:
    md += [f"![{plots[i]}](results/plots/{plots[i]}.png)", captions[i]]
md += [md_table(search_table), "KMP includes LPS construction in both time and total comparisons.",
       "## Prediction vs result", "**Edit distance.** " + prediction_edit, "**String search.** " + prediction_search,
       "## Short answers"]
for question, answer in answers:
    md += ["### " + question, answer]
md += ["## Environment and limitations", limits,
       "Data: results/results.csv (570 runs); results/summary.csv (114 medians). Full environment: results/environment.txt.",
       "Sources: assignment's supplied reference values and standard recurrences described in its specification; no external benchmark data used."]
(ROOT / "REPORT.md").write_text("\n\n".join(md) + "\n")

styles = getSampleStyleSheet()
font_dir = Path(matplotlib.get_data_path()) / "fonts/ttf"
pdfmetrics.registerFont(TTFont("DejaVu", str(font_dir / "DejaVuSans.ttf")))
pdfmetrics.registerFont(TTFont("DejaVu-Bold", str(font_dir / "DejaVuSans-Bold.ttf")))
styles.add(ParagraphStyle(name="BodyCustom", fontName="DejaVu", fontSize=9.5, leading=13.1, spaceAfter=7, textColor=colors.HexColor("#233044")))
styles.add(ParagraphStyle(name="SmallCustom", parent=styles["BodyCustom"], fontSize=8.5, leading=11.5, spaceAfter=4))
styles.add(ParagraphStyle(name="CaptionCustom", parent=styles["BodyCustom"], fontSize=8.8, leading=12, textColor=colors.HexColor("#435167"), spaceAfter=10))
styles["Title"].fontName = "DejaVu-Bold"
styles["Title"].fontSize = 20
styles["Title"].leading = 24
styles["Title"].alignment = 0
styles["Title"].textColor = colors.HexColor("#17385c")
styles["Heading1"].fontSize = 15
styles["Heading1"].fontName = "DejaVu-Bold"
styles["Heading1"].leading = 19
styles["Heading1"].textColor = colors.HexColor("#17385c")
styles["Heading2"].fontSize = 10.5
styles["Heading2"].fontName = "DejaVu-Bold"
styles["Heading2"].leading = 14
styles["Heading2"].spaceBefore = 8
styles["Heading2"].spaceAfter = 4

def para(text, style="BodyCustom"):
    return Paragraph(escape(text), styles[style])

def table(data, widths, small=False):
    cells = [[para(str(c), "SmallCustom" if small else "BodyCustom") for c in r] for r in data]
    t = Table(cells, colWidths=widths, hAlign="LEFT")
    t.setStyle(TableStyle([("BACKGROUND", (0,0), (-1,0), colors.HexColor("#e6edf5")),
                           ("VALIGN", (0,0), (-1,-1), "TOP"), ("LEFTPADDING", (0,0), (-1,-1), 8),
                           ("RIGHTPADDING", (0,0), (-1,-1), 8), ("TOPPADDING", (0,0), (-1,-1), 6),
                           ("BOTTOMPADDING", (0,0), (-1,-1), 5),
                           ("LINEBELOW", (0,0), (-1,-1), 0.4, colors.HexColor("#dce3eb"))]))
    return t

width = A4[0] - 84
story = [para("City Search & Spell-Check", "Title"), para("ASSIGNMENT 4  |  JAVA 17  |  7 NOVEMBER 2026", "SmallCustom"),
         para("Experiment Design Card", "Heading1"),
         para("Recorded and committed before the first benchmark.", "SmallCustom"),
         table([["Field", "Design"]] + [[k,v] for k,v in card], [64, width-64], small=True),
         Spacer(1,8), para(protocol, "SmallCustom"), para(change, "SmallCustom"), para(validation, "SmallCustom"),
         PageBreak(), para("Edit distance: work and storage", "Heading1")]

def add_plot(i):
    image = Image(str(ROOT / "results/plots" / (plots[i] + ".png")))
    image.drawHeight = image.imageHeight * width / image.imageWidth
    image.drawWidth = width
    story.extend([image, Spacer(1,4), para(captions[i], "CaptionCustom")])

add_plot(0)
add_plot(1)
story += [table(edit_table, [width*0.45, width*0.26, width*0.29], small=True), Spacer(1,8),
          para("Different n values are not equal-size timing comparisons. The full CSV also contains all random and identical cases. "
               "DP time is O(n*m), recursion is exponential on disjoint inputs, and its best matching path is linear.", "SmallCustom"),
          PageBreak(), para("String search: repeated prefixes", "Heading1")]
add_plot(2)
add_plot(3)
story += [table(search_table, [width*0.50, width*0.25, width*0.25], small=True), Spacer(1,8),
          para("All times are medians of five measured runs. KMP includes LPS construction. Nearly overlapping count curves on "
               "random and first-mismatch inputs show that KMP's comparison advantage depends on the input.", "SmallCustom"),
          PageBreak(), para("Interpretation and short answers", "Heading1"),
          para("Prediction vs result: edit distance", "Heading2"), para(prediction_edit),
          para("Prediction vs result: string search", "Heading2"), para(prediction_search)]
for question, answer in answers:
    story += [para(question, "Heading2"), para(answer)]
story += [para("Environment and limitations", "Heading2"), para(limits, "SmallCustom"),
          para("Evidence: results/results.csv (570 runs), summary.csv (114 medians), environment.txt. "
               "Correctness references come from the assignment specification; all benchmark data were measured in this project.", "SmallCustom")]

def footer(canvas, doc):
    canvas.setStrokeColor(colors.HexColor("#dce3eb"))
    canvas.line(42, 34, A4[0]-42, 34)
    canvas.setFont("DejaVu", 8)
    canvas.setFillColor(colors.HexColor("#5d6a7b"))
    canvas.drawString(42, 22, "City Search & Spell-Check | Assignment 4")
    canvas.drawRightString(A4[0]-42, 22, str(doc.page))

SimpleDocTemplate(str(ROOT / "REPORT.pdf"), pagesize=A4, rightMargin=42, leftMargin=42,
                  topMargin=35, bottomMargin=44, title="City Search & Spell-Check - Assignment 4",
                  author="Dauren Serikbay").build(story, onFirstPage=footer, onLaterPages=footer)
print("Created REPORT.md and REPORT.pdf from measured data and JUnit results.")
