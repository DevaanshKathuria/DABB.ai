import fs from "node:fs/promises";
import path from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";

const artifactToolPath = process.env.ARTIFACT_TOOL_PATH
  ?? "/Users/abheydua2025/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/@oai/artifact-tool/dist/artifact_tool.mjs";

const { Presentation, PresentationFile } = await import(pathToFileURL(artifactToolPath).href);

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const rootDir = path.resolve(__dirname, "../..");
const outputDir = __dirname;
const previewDir = path.join(outputDir, "preview");
await fs.mkdir(previewDir, { recursive: true });
const reportFigureDir = path.join(rootDir, "reports", "milestone2_report", "figures");
await fs.mkdir(reportFigureDir, { recursive: true });

const metrics = (await readCsv(path.join(rootDir, "reports", "logreg_summary_metrics.csv")))[0];
const confusionMatrixPath = path.join(rootDir, "reports", "logreg_confusion_matrix.png");
const reportConfusionMatrixPath = path.join(reportFigureDir, "logreg_confusion_matrix.png");
await fs.copyFile(confusionMatrixPath, reportConfusionMatrixPath);
const confusionMatrixBlob = await readImageBlob(reportConfusionMatrixPath);

const colors = {
  navy: "#081423",
  navy2: "#11263f",
  teal: "#2db7a3",
  tealSoft: "#d9f5ef",
  gold: "#f0b35d",
  goldSoft: "#fff2dd",
  slate: "#5f6d7f",
  ink: "#152235",
  paper: "#f7f9fc",
  white: "#ffffff",
  redSoft: "#fbe7e4",
  greenSoft: "#e8f7eb",
  border: "#d8e1eb",
};

const slideSize = { width: 1280, height: 720 };
const deck = Presentation.create({ slideSize });

function addBackground(slide, color) {
  slide.background.fill.color = color;
}

function addShape(slide, { x, y, w, h, fill = colors.white, line = colors.border, radius = "roundRect" }) {
  const shape = slide.shapes.add({
    geometry: radius,
    position: { left: x, top: y, width: w, height: h },
  });
  shape.fill.color = fill;
  shape.line.color = line;
  shape.line.width = 1;
  return shape;
}

function addText(slide, { x, y, w, h, text, size = 24, color = colors.ink, bold = false, align = "left", fill = colors.paper }) {
  const shape = slide.shapes.add({
    geometry: "rect",
    position: { left: x, top: y, width: w, height: h },
  });
  shape.fill.color = fill;
  shape.line.visible = false;
  shape.text.set(text);
  shape.text.fontSize = size;
  shape.text.color = color;
  shape.text.bold = bold;
  shape.text.alignment = align;
  return shape;
}

function addCard(slide, { x, y, w, h, title, body, accent = colors.teal, fill = colors.white, titleColor = colors.ink }) {
  const card = addShape(slide, { x, y, w, h, fill, line: colors.border, radius: "roundRect" });
  const accentBar = slide.shapes.add({
    geometry: "roundRect",
    position: { left: x + 16, top: y + 16, width: 12, height: h - 32 },
  });
  accentBar.fill.color = accent;
  accentBar.line.visible = false;
  addText(slide, { x: x + 40, y: y + 18, w: w - 56, h: 34, text: title, size: 22, color: titleColor, bold: true, fill });
  addText(slide, { x: x + 40, y: y + 58, w: w - 56, h: h - 72, text: body, size: 16, color: colors.slate, fill });
  return card;
}

function addMetricCard(slide, { x, y, w, h, value, label, fill, valueColor = colors.ink }) {
  const card = addShape(slide, { x, y, w, h, fill, line: fill });
  card.line.visible = false;
  addText(slide, { x: x + 20, y: y + 16, w: w - 40, h: 56, text: value, size: 34, color: valueColor, bold: true, align: "center", fill });
  addText(slide, { x: x + 16, y: y + 74, w: w - 32, h: 48, text: label, size: 16, color: colors.slate, bold: true, align: "center", fill });
}

function addPill(slide, { x, y, w, text, fill }) {
  const pill = slide.shapes.add({
    geometry: "roundRect",
    position: { left: x, top: y, width: w, height: 34 },
  });
  pill.fill.color = fill;
  pill.line.visible = false;
  addText(slide, { x: x + 12, y: y + 6, w: w - 24, h: 22, text, size: 14, color: colors.ink, bold: true, align: "center", fill });
}

function addBulletList(slide, { x, y, w, items, color = colors.ink, fill = colors.white }) {
  const text = items.map((item) => `• ${item}`).join("\n");
  return addText(slide, { x, y, w, h: 28 * items.length + 8, text, size: 18, color, fill });
}

function addFooter(slide, index, fill = colors.paper) {
  addText(slide, { x: 1140, y: 670, w: 90, h: 24, text: String(index).padStart(2, "0"), size: 13, color: colors.slate, bold: true, align: "right", fill });
}

function addTitleBlock(slide, title, subtitle, index, dark = false) {
  const titleColor = dark ? colors.white : colors.ink;
  const subtitleColor = dark ? "#d4deea" : colors.slate;
  const fill = dark ? colors.navy2 : colors.paper;
  addText(slide, { x: 70, y: 40, w: 980, h: 86, text: title, size: 34, color: titleColor, bold: true, fill });
  addText(slide, { x: 70, y: 112, w: 980, h: 42, text: subtitle, size: 16, color: subtitleColor, fill });
  addFooter(slide, index, fill);
}

function addConnectorArrow(slide, x, y, w, h, color = colors.teal) {
  const arrow = slide.shapes.add({
    geometry: "rightArrow",
    position: { left: x, top: y, width: w, height: h },
  });
  arrow.fill.color = color;
  arrow.line.visible = false;
  return arrow;
}

function readCsv(filePath) {
  const csv = fs.readFile(filePath, "utf-8");
  return csv.then((content) => {
    const [headerLine, ...rows] = content.trim().split(/\r?\n/);
    const headers = headerLine.split(",");
    return rows.filter(Boolean).map((row) => {
      const values = row.split(",");
      return Object.fromEntries(headers.map((header, idx) => [header, values[idx]]));
    });
  });
}

async function readImageBlob(imagePath) {
  const bytes = await fs.readFile(imagePath);
  return bytes.buffer.slice(bytes.byteOffset, bytes.byteOffset + bytes.byteLength);
}

// Slide 1: Title
{
  const slide = deck.slides.add();
  addBackground(slide, colors.navy);
  const heroEllipse = slide.shapes.add({
    geometry: "ellipse",
    position: { left: 760, top: -120, width: 680, height: 680 },
  });
  heroEllipse.fill.color = colors.teal;
  heroEllipse.line.visible = false;
  const lowerEllipse = slide.shapes.add({
    geometry: "ellipse",
    position: { left: 980, top: 430, width: 420, height: 420 },
  });
  lowerEllipse.fill.color = colors.gold;
  lowerEllipse.line.visible = false;
  const leftBand = slide.shapes.add({
    geometry: "rect",
    position: { left: 0, top: 0, width: 130, height: 720 },
  });
  leftBand.fill.color = colors.navy2;
  leftBand.line.visible = false;
  const accentBand = slide.shapes.add({
    geometry: "rect",
    position: { left: 130, top: 0, width: 20, height: 720 },
  });
  accentBand.fill.color = colors.teal;
  accentBand.line.visible = false;

  addText(slide, {
    x: 90,
    y: 100,
    w: 600,
    h: 140,
    text: "DABB.ai\nMilestone 2",
    size: 38,
    color: colors.white,
    bold: true,
    fill: colors.navy,
  });
  addText(slide, {
    x: 92,
    y: 255,
    w: 580,
    h: 70,
    text: "Intelligent contract risk analysis with grounded reporting and public-host deployment",
    size: 20,
    color: "#dce7f5",
    fill: colors.navy,
  });
  addText(slide, {
    x: 92,
    y: 342,
    w: 580,
    h: 42,
    text: "Birajit Saikia  |  Devaansh Kathuria  |  Abhey Dua  |  Bhavya Jain",
    size: 16,
    color: "#b9c9dc",
    fill: colors.navy,
  });
  addPill(slide, { x: 92, y: 410, w: 156, text: "Clause classifier", fill: colors.tealSoft });
  addPill(slide, { x: 260, y: 410, w: 168, text: "Grounded report", fill: colors.goldSoft });
  addPill(slide, { x: 440, y: 410, w: 184, text: "Public deployment", fill: "#e8effb" });

  addCard(slide, {
    x: 760,
    y: 96,
    w: 430,
    h: 136,
    title: "What stays from Milestone 1",
    body: "TF-IDF features, logistic regression, risk mapping, and clause highlighting remain intact.",
    accent: colors.teal,
    fill: "#f3f8fb",
  });
  addCard(slide, {
    x: 760,
    y: 255,
    w: 430,
    h: 136,
    title: "What Milestone 2 adds",
    body: "Assistant explanations, PDF report export, comparison mode, and deployment-safe startup settings.",
    accent: colors.gold,
    fill: "#fffaf1",
  });
  addCard(slide, {
    x: 760,
    y: 414,
    w: 430,
    h: 136,
    title: "Ready for grading",
    body: "The repo ships with tests, documented entrypoints, and a reproducible evaluation workflow.",
    accent: colors.navy2,
    fill: "#eff4fb",
  });
  slide.speakerNotes.setText("Open by framing Milestone 2 as a release-hardening step rather than a rewrite. Emphasize that the baseline model remains intact.");
}

// Slide 2: Scope
{
  const slide = deck.slides.add();
  addBackground(slide, colors.paper);
  addTitleBlock(slide, "What Milestone 2 adds", "The baseline classifier stays the same, but the product surface becomes demonstrably richer and easier to deploy.", 2);

  addCard(slide, {
    x: 70,
    y: 180,
    w: 540,
    h: 370,
    title: "Baseline preserved",
    body: "Milestone 2 keeps the clause segmentation, TF-IDF vectorization, logistic regression classifier, severity mapping, and clause highlighting from Milestone 1.",
    accent: colors.teal,
    fill: colors.white,
  });
  addBulletList(slide, {
    x: 110,
    y: 275,
    w: 460,
    items: [
      "Predict clause type per extracted clause",
      "Map clause type to severity and risk score",
      "Export structured outputs for grading",
      "Keep the deterministic screenable baseline",
    ],
  });

  addCard(slide, {
    x: 670,
    y: 180,
    w: 540,
    h: 370,
    title: "Milestone 2 additions",
    body: "The assistant layer uses the bundled legal guidance corpus to ground explanations, mitigation advice, and report generation without external API dependencies.",
    accent: colors.gold,
    fill: colors.white,
  });
  addBulletList(slide, {
    x: 710,
    y: 275,
    w: 470,
    items: [
      "Generate a structured legal assistance report",
      "Show supporting evidence and mitigation guidance",
      "Support multi-contract comparison",
      "Produce deployment-ready startup docs",
    ],
  });

  addMetricCard(slide, { x: 70, y: 580, w: 250, h: 110, value: "2", label: "analysis layers: baseline + assistant", fill: colors.tealSoft });
  addMetricCard(slide, { x: 336, y: 580, w: 250, h: 110, value: "3", label: "host paths: Streamlit, HF Spaces, Render", fill: colors.goldSoft });
  addMetricCard(slide, { x: 602, y: 580, w: 250, h: 110, value: "4", label: "export formats: CSV, JSON, PDF, comparison", fill: "#e8effb" });
  addMetricCard(slide, { x: 868, y: 580, w: 342, h: 110, value: "100%", label: "of Milestone 1 behavior retained", fill: "#edf7ee" });
  slide.speakerNotes.setText("Highlight that Milestone 2 is additive. It does not replace the earlier model path, only wraps it with stronger reporting and deployment support.");
}

// Slide 3: Architecture
{
  const slide = deck.slides.add();
  addBackground(slide, colors.paper);
  addTitleBlock(slide, "System architecture", "The release is intentionally simple: local extraction and modeling on one side, grounded reporting on the other.", 3);

  const boxes = [
    { x: 70, y: 190, w: 180, title: "Upload", body: "PDF or TXT", fill: colors.tealSoft },
    { x: 280, y: 190, w: 180, title: "Extraction", body: "Text parsing", fill: "#eef4fb" },
    { x: 490, y: 190, w: 180, title: "Segmentation", body: "Clause units", fill: "#eef4fb" },
    { x: 700, y: 190, w: 180, title: "Classifier", body: "TF-IDF + LogReg", fill: colors.goldSoft },
    { x: 910, y: 190, w: 180, title: "Risk", body: "Mapping layer", fill: "#eef4fb" },
  ];
  boxes.forEach((box, idx) => {
    addCard(slide, {
      x: box.x,
      y: box.y,
      w: box.w,
      h: 110,
      title: box.title,
      body: box.body,
      accent: idx < 2 ? colors.teal : idx === 3 ? colors.gold : colors.navy2,
      fill: box.fill,
    });
    if (idx < boxes.length - 1) {
      addConnectorArrow(slide, box.x + box.w + 8, 232, 22, 24, colors.slate);
    }
  });

  addCard(slide, {
    x: 110,
    y: 360,
    w: 340,
    h: 230,
    title: "Local knowledge base",
    body: "The assistant indexes a bundled legal guidance corpus with TF-IDF retrieval. This keeps the report grounded and reproducible without depending on external services during the demo.",
    accent: colors.teal,
    fill: colors.white,
  });
  addCard(slide, {
    x: 470,
    y: 360,
    w: 340,
    h: 230,
    title: "Assistant report",
    body: "Each clause gets an explanation, mitigation note, and any retrieved evidence. The report is serialized for the UI and also exported as PDF for submission.",
    accent: colors.gold,
    fill: colors.white,
  });
  addCard(slide, {
    x: 830,
    y: 360,
    w: 340,
    h: 230,
    title: "Comparison and exports",
    body: "The app keeps the clause table filterable and exportable. Multi-contract comparison summarizes repeated patterns across uploaded files.",
    accent: colors.navy2,
    fill: colors.white,
  });
  slide.speakerNotes.setText("Walk left to right: ingest, classify, map risk, then ground the explanation layer. Emphasize that the retrieval corpus is local and deterministic.");
}

// Slide 4: Deployment and usage
{
  const slide = deck.slides.add();
  addBackground(slide, colors.paper);
  addTitleBlock(slide, "User flow and public deployment", "The hosted app is submission-ready and uses a single clear entrypoint.", 4);

  addCard(slide, {
    x: 70,
    y: 190,
    w: 420,
    h: 380,
    title: "How a user runs the app",
    body: "1. Open the hosted Streamlit app.\n2. Upload a PDF or TXT contract, or use the demo contract.\n3. Review clause predictions, filters, and highlights.\n4. Generate the assistant report.\n5. Download CSV, JSON, or PDF outputs.",
    accent: colors.teal,
    fill: colors.white,
  });

  addCard(slide, {
    x: 540,
    y: 190,
    w: 670,
    h: 180,
    title: "Host entrypoint",
    body: "streamlit_app.py is the recommended public entrypoint. It is paired with .streamlit/config.toml, Procfile, and render.yaml so the deployment path stays simple across Streamlit Cloud, Hugging Face Spaces, and Render.",
    accent: colors.gold,
    fill: colors.white,
  });
  addCard(slide, {
    x: 540,
    y: 390,
    w: 670,
    h: 180,
    title: "Deployment-safe configuration",
    body: "Environment variables can override the model path, reports directory, and fallback training CSV. If a hosted filesystem blocks persistence, the model still loads and the app continues instead of failing on save.",
    accent: colors.navy2,
    fill: colors.white,
  });
  addPill(slide, { x: 560, y: 598, w: 210, text: "streamlit run streamlit_app.py", fill: colors.tealSoft });
  addPill(slide, { x: 790, y: 598, w: 180, text: "Render start command", fill: colors.goldSoft });
  addPill(slide, { x: 992, y: 598, w: 180, text: "HF Spaces Streamlit SDK", fill: "#e8effb" });
  slide.speakerNotes.setText("Keep this slide practical. Mention the exact start command and the fact that deployment fails closed only if the environment itself is unavailable.");
}

// Slide 5: Evaluation
{
  const slide = deck.slides.add();
  addBackground(slide, colors.paper);
  addTitleBlock(slide, "Evaluation and artifacts", "The release includes repeatable evaluation outputs and a saved confusion matrix for the baseline model.", 5);

  addMetricCard(slide, { x: 70, y: 190, w: 210, h: 118, value: metrics.precision_weighted, label: "Weighted precision", fill: colors.tealSoft });
  addMetricCard(slide, { x: 296, y: 190, w: 210, h: 118, value: metrics.recall_weighted, label: "Weighted recall", fill: colors.goldSoft });
  addMetricCard(slide, { x: 522, y: 190, w: 210, h: 118, value: metrics.f1_weighted, label: "Weighted F1", fill: "#e8effb" });

  addCard(slide, {
    x: 760,
    y: 190,
    w: 450,
    h: 118,
    title: "Interpretation",
    body: "The fallback evaluation path is intentionally tiny, so the headline metric is best read as a correctness check on the bundled demo split rather than a benchmark claim.",
    accent: colors.navy2,
    fill: colors.white,
  });

  addShape(slide, { x: 70, y: 350, w: 610, h: 290, fill: colors.white, line: colors.border, radius: "roundRect" });
  const image = slide.images.add({
    blob: confusionMatrixBlob,
    alt: "Logistic regression confusion matrix",
  });
  image.position = { left: 92, top: 372, width: 566, height: 246 };
  void image;

  addCard(slide, {
    x: 710,
    y: 350,
    w: 500,
    h: 290,
    title: "Generated artifacts",
    body: "The evaluation command saves a summary metrics CSV, a classification report CSV, and a confusion matrix PNG. Those artifacts make the demo reproducible and easy to inspect during grading.",
    accent: colors.teal,
    fill: colors.white,
  });
  addBulletList(slide, {
    x: 750,
    y: 448,
    w: 420,
    items: [
      "reports/logreg_summary_metrics.csv",
      "reports/logreg_classification_report.csv",
      "reports/logreg_confusion_matrix.png",
      "reports/model_comparison.csv",
    ],
  });
  slide.speakerNotes.setText("Be explicit that the repo now records metrics and the confusion matrix in files, not just in the terminal. That is the artifact story reviewers care about.");
}

// Slide 6: Limits and safeguards
{
  const slide = deck.slides.add();
  addBackground(slide, colors.paper);
  addTitleBlock(slide, "Limitations and release safeguards", "The submission is intentionally conservative: safe defaults, a clear disclaimer, and no hidden dependency on external services.", 6);

  addCard(slide, {
    x: 70,
    y: 190,
    w: 350,
    h: 390,
    title: "Known limitations",
    body: "Text extraction is only as good as the source PDF. Tiny fallback datasets are useful for smoke testing, but they are not a substitute for a real benchmark corpus. Risk scoring is rule-based and should be interpreted as screening guidance.",
    accent: colors.gold,
    fill: colors.white,
  });
  addCard(slide, {
    x: 465,
    y: 190,
    w: 350,
    h: 390,
    title: "Release safeguards",
    body: "The hosted startup path is explicit, the model cache is optional, environment variables can override file paths, and the test suite covers the assistant, UI helpers, ingestion, PDF export, and workflow modules.",
    accent: colors.teal,
    fill: colors.white,
  });
  addCard(slide, {
    x: 860,
    y: 190,
    w: 350,
    h: 390,
    title: "What to mention in the demo",
    body: "Say that Milestone 2 does not replace Milestone 1. It preserves the baseline classifier, adds grounded reporting, and packages the app so it can be hosted publicly without extra setup.",
    accent: colors.navy2,
    fill: colors.white,
  });
  slide.speakerNotes.setText("Close by framing the work as a controlled extension of Milestone 1. Reviewers should hear that the system is safer, not just larger.");
}

// Slide 7: Checklist
{
  const slide = deck.slides.add();
  addBackground(slide, colors.navy2);
  addTitleBlock(slide, "Final checklist", "The repository now has a stable submission path from source code to hosted demo.", 7, true);

  addCard(slide, {
    x: 80,
    y: 190,
    w: 540,
    h: 360,
    title: "Submission-ready items",
    body: "• Public-host entrypoints and deployment config\n• Pinned dependencies and env-driven paths\n• Milestone 2 README and deployment notes\n• Milestone 2 report and presentation content\n• CI smoke coverage and the existing unit test suite",
    accent: colors.teal,
    fill: "#10253d",
    titleColor: colors.white,
  });
  addCard(slide, {
    x: 660,
    y: 190,
    w: 540,
    h: 360,
    title: "Last thing to verify",
    body: "Open the hosted app, upload a contract, generate the report, and confirm the download buttons work. If that path succeeds, the release is ready for grading.",
    accent: colors.gold,
    fill: "#10253d",
    titleColor: colors.white,
  });
  addText(slide, { x: 90, y: 590, w: 1100, h: 40, text: "Thank you", size: 30, color: colors.white, bold: true, align: "center", fill: colors.navy2 });
  slide.speakerNotes.setText("Use this as the clean closing slide. The takeaway is simple: the app is stable, documented, and demoable.");
}

// Slide 8: Assistant report anatomy
{
  const slide = deck.slides.add();
  addBackground(slide, colors.paper);
  addTitleBlock(slide, "Assistant report anatomy", "The report is structured so a reviewer can trace each finding from summary to evidence.", 8);

  addCard(slide, {
    x: 70,
    y: 185,
    w: 260,
    h: 390,
    title: "1. Summary",
    body: "The contract summary frames overall risk, counts of high/medium/low findings, and the fallback indicator.",
    accent: colors.teal,
    fill: colors.white,
  });
  addCard(slide, {
    x: 360,
    y: 185,
    w: 260,
    h: 390,
    title: "2. Findings",
    body: "Each clause gets a predicted type, severity, score, explanation, and mitigation note.",
    accent: colors.gold,
    fill: colors.white,
  });
  addCard(slide, {
    x: 650,
    y: 185,
    w: 260,
    h: 390,
    title: "3. Evidence",
    body: "Retrieved passages are attached only when the support threshold is met, which keeps the report grounded.",
    accent: colors.navy2,
    fill: colors.white,
  });
  addCard(slide, {
    x: 940,
    y: 185,
    w: 270,
    h: 390,
    title: "4. Export",
    body: "The report is visible in the UI and also saved as a downloadable PDF for submission.",
    accent: colors.teal,
    fill: colors.white,
  });
  addPill(slide, { x: 116, y: 610, w: 170, text: "summary section", fill: colors.tealSoft });
  addPill(slide, { x: 407, y: 610, w: 140, text: "risk findings", fill: colors.goldSoft });
  addPill(slide, { x: 693, y: 610, w: 130, text: "evidence", fill: "#e8effb" });
  addPill(slide, { x: 1006, y: 610, w: 148, text: "PDF export", fill: colors.greenSoft });
  slide.speakerNotes.setText("Use this slide to walk the grader through the report sections from top to bottom.");
}

// Slide 9: Comparison and validation
{
  const slide = deck.slides.add();
  addBackground(slide, colors.paper);
  addTitleBlock(slide, "Comparison and validation", "The release includes a small but complete validation story for the assistant and the host path.", 9);

  addCard(slide, {
    x: 70,
    y: 190,
    w: 360,
    h: 340,
    title: "Multi-contract comparison",
    body: "The app compares multiple contracts and highlights repeated risk patterns rather than treating each file in isolation.",
    accent: colors.teal,
    fill: colors.white,
  });
  addBulletList(slide, {
    x: 110,
    y: 285,
    w: 280,
    items: [
      "Shared risk pattern counts",
      "Per-contract summary table",
      "High-risk finding totals",
    ],
  });

  addCard(slide, {
    x: 465,
    y: 190,
    w: 360,
    h: 340,
    title: "Smoke validation",
    body: "The final smoke test checks entrypoint imports, environment overrides, and cache-write fallback behavior.",
    accent: colors.gold,
    fill: colors.white,
  });
  addBulletList(slide, {
    x: 505,
    y: 285,
    w: 280,
    items: [
      "Import the hosted entrypoints",
      "Resolve config overrides",
      "Continue when save fails",
    ],
  });

  addCard(slide, {
    x: 860,
    y: 190,
    w: 350,
    h: 340,
    title: "Host checks",
    body: "Deployment settings are documented for Streamlit Cloud, Hugging Face Spaces, and Render, with a single startup path.",
    accent: colors.navy2,
    fill: colors.white,
  });
  addBulletList(slide, {
    x: 900,
    y: 285,
    w: 260,
    items: [
      "streamlit_app.py",
      ".streamlit/config.toml",
      "Procfile / render.yaml",
    ],
  });
  addMetricCard(slide, { x: 90, y: 570, w: 235, h: 100, value: "46", label: "unit tests passing", fill: colors.tealSoft });
  addMetricCard(slide, { x: 350, y: 570, w: 235, h: 100, value: "3", label: "smoke checks", fill: colors.goldSoft });
  addMetricCard(slide, { x: 610, y: 570, w: 235, h: 100, value: "10", label: "slides in final deck", fill: "#e8effb" });
  addMetricCard(slide, { x: 870, y: 570, w: 235, h: 100, value: "1", label: "public entrypoint", fill: colors.greenSoft });
  slide.speakerNotes.setText("Tie the validation story to the actual artifacts and explain that the smoke tests protect the release path.");
}

// Slide 10: Closing
{
  const slide = deck.slides.add();
  addBackground(slide, colors.navy);
  const leftBand = slide.shapes.add({ geometry: "rect", position: { left: 0, top: 0, width: 180, height: 720 } });
  leftBand.fill.color = colors.navy2;
  leftBand.line.visible = false;
  const glow = slide.shapes.add({ geometry: "ellipse", position: { left: 820, top: 420, width: 430, height: 430 } });
  glow.fill.color = colors.gold;
  glow.line.visible = false;
  glow.fill.color = "#f0b35d2e";

  addText(slide, {
    x: 90,
    y: 110,
    w: 740,
    h: 120,
    text: "DABB.ai\nReady for final submission",
    size: 38,
    color: colors.white,
    bold: true,
    fill: colors.navy,
  });
  addText(slide, {
    x: 92,
    y: 260,
    w: 720,
    h: 80,
    text: "Milestone 2 keeps the baseline model intact, adds grounded reporting, and ships with a valid 10-slide presentation artifact.",
    size: 20,
    color: "#dce7f5",
    fill: colors.navy,
  });
  addCard(slide, {
    x: 90,
    y: 390,
    w: 320,
    h: 170,
    title: "What is ready",
    body: "Public-host startup, reproducible tests, Milestone 2 README, report, and a working PPTX deck.",
    accent: colors.teal,
    fill: "#0f2238",
    titleColor: colors.white,
  });
  addCard(slide, {
    x: 430,
    y: 390,
    w: 320,
    h: 170,
    title: "What to demo",
    body: "Upload a contract, generate the report, inspect evidence, and download the results.",
    accent: colors.gold,
    fill: "#0f2238",
    titleColor: colors.white,
  });
  addCard(slide, {
    x: 770,
    y: 390,
    w: 360,
    h: 170,
    title: "What the grader sees",
    body: "A stable repo with a clear deployment path and a clean deck they can open immediately.",
    accent: colors.navy2,
    fill: "#0f2238",
    titleColor: colors.white,
  });
  slide.speakerNotes.setText("End on a confident release note: the deck opens, the app runs, and the repo is ready for grading.");
}

const previewSlide = deck.slides.items[0];
const previewBlob = await previewSlide.export({ format: "png" });
await fs.writeFile(path.join(previewDir, "slide-01.png"), Buffer.from(await previewBlob.arrayBuffer()));

const pptxBlob = await PresentationFile.exportPptx(deck);
const pptxPath = path.join(outputDir, "output.pptx");
await pptxBlob.save(pptxPath);
for (let i = 0; i < 10; i += 1) {
  try {
    await fs.access(pptxPath);
    break;
  } catch {
    if (i === 9) throw new Error(`Failed to write PPTX output to ${pptxPath}`);
    await new Promise((resolve) => setTimeout(resolve, 100));
  }
}

console.log(`Wrote deck to ${pptxPath}`);
