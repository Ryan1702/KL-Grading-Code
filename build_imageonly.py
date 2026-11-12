# -*- coding: utf-8 -*-
"""Build the final image-only KOA grading manuscript (Option C)."""
import json
import re
from pathlib import Path

from docx import Document
from docx.enum.section import WD_SECTION
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_TAB_ALIGNMENT
from docx.opc.constants import RELATIONSHIP_TYPE as RT
from docx.oxml import OxmlElement, parse_xml
from docx.oxml.ns import nsdecls, qn
from docx.shared import Cm, Inches, Pt, RGBColor

WORK = Path(__file__).resolve().parent
RES = WORK.parent / "audit" / "final_model" / "analysis.json"
FIG = WORK.parent / "audit" / "final_model" / "figures"
OUT = WORK.parent / "KOA_Image_Only_Final_Submission.docx"
R = json.loads(RES.read_text()) if RES.exists() else None
_BL = WORK.parent / "audit" / "baselines" / "baselines.json"
BASELINES = json.loads(_BL.read_text()) if _BL.exists() else None

doc = Document()
sec = doc.sections[0]
sec.page_width, sec.page_height = Cm(21.0), Cm(29.7)
sec.left_margin = sec.right_margin = Cm(2.54)
sec.top_margin = Cm(2.29)
sec.bottom_margin = Cm(2.29)
sec.header_distance = Cm(1.25)
sec.footer_distance = Cm(1.25)
sec.different_first_page_header_footer = True

normal = doc.styles["Normal"]
normal.font.name = "Times New Roman"
normal.font.size = Pt(10.5)
normal.element.rPr.rFonts.set(qn("w:eastAsia"), "Times New Roman")
for a in ("w:asciiTheme", "w:hAnsiTheme", "w:eastAsiaTheme", "w:cstheme"):
    normal.element.rPr.rFonts.attrib.pop(qn(a), None)
pf = normal.paragraph_format
pf.line_spacing = 1.5
pf.space_before = Pt(0)
pf.space_after = Pt(0)
pf.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY

HEAD = {"Heading 1": (15, True, WD_ALIGN_PARAGRAPH.CENTER, 18, 8),
        "Heading 2": (13, True, WD_ALIGN_PARAGRAPH.LEFT, 12, 6),
        "Heading 3": (11.5, True, WD_ALIGN_PARAGRAPH.LEFT, 10, 4)}
for name, (size, bold, align, before, after) in HEAD.items():
    st = doc.styles[name]
    st.font.name = "Times New Roman"
    st.font.size = Pt(size)
    st.font.bold = bold
    st.font.color.rgb = RGBColor(0, 0, 0)
    st.element.rPr.rFonts.set(qn("w:eastAsia"), "Times New Roman")
    for a in ("w:asciiTheme", "w:hAnsiTheme", "w:eastAsiaTheme", "w:cstheme"):
        st.element.rPr.rFonts.attrib.pop(qn(a), None)
    st.paragraph_format.alignment = align
    st.paragraph_format.space_before = Pt(before)
    st.paragraph_format.space_after = Pt(after)
    st.paragraph_format.line_spacing = 1.5
    st.paragraph_format.keep_with_next = True

hp = sec.header.paragraphs[0]
hp.text = ""
hr = hp.add_run("Deep learning for Kellgren–Lawrence grading of knee osteoarthritis")
hr.font.size = Pt(8.5)
hr.italic = True
hp.alignment = WD_ALIGN_PARAGRAPH.CENTER
pPr = hp._p.get_or_add_pPr()
pbdr = OxmlElement("w:pBdr")
bt = OxmlElement("w:bottom")
bt.set(qn("w:val"), "single"); bt.set(qn("w:sz"), "4"); bt.set(qn("w:space"), "4"); bt.set(qn("w:color"), "auto")
pbdr.append(bt); pPr.append(pbdr)

fp = sec.footer.paragraphs[0]
fp.alignment = WD_ALIGN_PARAGRAPH.CENTER
run = fp.add_run()
fld = OxmlElement("w:fldSimple")
fld.set(qn("w:instr"), "PAGE")
run._r.addnext(fld)
for r_ in fp.runs:
    r_.font.size = Pt(10)

M_NS = 'xmlns:m="http://schemas.openxmlformats.org/officeDocument/2006/math" ' + nsdecls("w")
MRPR = ('<w:rPr><w:rFonts w:ascii="Cambria Math" w:hAnsi="Cambria Math"/>'
        '<w:sz w:val="21"/><w:szCs w:val="21"/></w:rPr>')


def m(t):
    return '<m:r>%s<m:t xml:space="preserve">%s</m:t></m:r>' % (MRPR, t)


def mu(t):
    return '<m:r><m:rPr><m:nor/></m:rPr>%s<m:t xml:space="preserve">%s</m:t></m:r>' % (MRPR, t)


def msub(b, s_):
    return '<m:sSub><m:e>%s</m:e><m:sub>%s</m:sub></m:sSub>' % (b, s_)


def msup(b, s_):
    return '<m:sSup><m:e>%s</m:e><m:sup>%s</m:sup></m:sSup>' % (b, s_)


def mfrac(n, d):
    return '<m:f><m:num>%s</m:num><m:den>%s</m:den></m:f>' % (n, d)


def mnary(ch, lo, hi, e):
    return ('<m:nary><m:naryPr><m:chr m:val="%s"/><m:limLoc m:val="undOvr"/></m:naryPr>'
            '<m:sub>%s</m:sub><m:sup>%s</m:sup><m:e>%s</m:e></m:nary>') % (ch, lo, hi, e)


def _sup(p, t):
    r = p.add_run(t); r.font.superscript = True; r.font.name = "Times New Roman"
    return r


def cite_field(p, num):
    name = "_Ref%08d" % num
    W = nsdecls("w")
    p._p.append(parse_xml('<w:r %s><w:fldChar w:fldCharType="begin"/></w:r>' % W))
    p._p.append(parse_xml('<w:r %s><w:instrText xml:space="preserve"> REF %s \\h </w:instrText></w:r>' % (W, name)))
    p._p.append(parse_xml('<w:r %s><w:fldChar w:fldCharType="separate"/></w:r>' % W))
    p._p.append(parse_xml('<w:r %s><w:rPr><w:vertAlign w:val="superscript"/></w:rPr><w:t>[%d]</w:t></w:r>' % (W, num)))
    p._p.append(parse_xml('<w:r %s><w:fldChar w:fldCharType="end"/></w:r>' % W))


def add_cite(p, spec):
    for num in [int(n) for n in spec.replace(" ", "").split(",")]:
        cite_field(p, num)


TOKEN = re.compile(r"(\*\*.+?\*\*|~[^~]+~|\^[^\^]+\^|\{\{[^}]+\}\})")


def runs(p, text, size=None, bold=False):
    for part in TOKEN.split(text):
        if not part:
            continue
        b = bold
        if part.startswith("{{") and part.endswith("}}"):
            add_cite(p, part[2:-2]); continue
        if part.startswith("**") and part.endswith("**"):
            part, b = part[2:-2], True
        elif part.startswith("~") and part.endswith("~"):
            r = p.add_run(part[1:-1]); r.font.subscript = True; r.bold = b
            if size: r.font.size = Pt(size)
            continue
        elif part.startswith("^") and part.endswith("^"):
            r = p.add_run(part[1:-1]); r.font.superscript = True; r.bold = b
            if size: r.font.size = Pt(size)
            continue
        r = p.add_run(part); r.bold = b; r.font.name = "Times New Roman"
        if size: r.font.size = Pt(size)


def para(text="", size=None, bold=False, indent=True, align=None, before=0, after=0, keep=False):
    p = doc.add_paragraph()
    fmt = p.paragraph_format
    fmt.line_spacing = 1.5
    fmt.space_before = Pt(before)
    fmt.space_after = Pt(after)
    if indent: fmt.first_line_indent = Cm(0.74)
    if align is not None: fmt.alignment = align
    if keep: fmt.keep_with_next = True
    runs(p, text, size=size, bold=bold)
    return p


def h(text, level):
    p = doc.add_paragraph(style="Heading %d" % level)
    p.text = ""
    r = p.add_run(text); r.font.name = "Times New Roman"
    return p


def caption(text, before=6, after=6):
    p = doc.add_paragraph()
    p.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_before = Pt(before)
    p.paragraph_format.space_after = Pt(after)
    p.paragraph_format.line_spacing = 1.0
    p.paragraph_format.keep_with_next = True
    runs(p, text, size=9.5, bold=True)


def table(header, rows, widths, cap, size=9, note=None):
    caption(cap)
    t = doc.add_table(rows=1 + len(rows), cols=len(header))
    t.style = "Table Grid"
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    t.autofit = False
    tblPr = t._tbl.tblPr
    lay = OxmlElement("w:tblLayout"); lay.set(qn("w:type"), "fixed"); tblPr.append(lay)
    tw = OxmlElement("w:tblW"); tw.set(qn("w:type"), "dxa"); tw.set(qn("w:w"), str(int(sum(widths) * 567))); tblPr.append(tw)
    for j, w in enumerate(widths):
        t.columns[j].width = Cm(w)
        for row in t.rows:
            row.cells[j].width = Cm(w)
    trPr = t.rows[0]._tr.get_or_add_trPr()
    th = OxmlElement("w:tblHeader"); th.set(qn("w:val"), "true"); trPr.append(th)
    for row in t.rows:
        row._tr.get_or_add_trPr().append(OxmlElement("w:cantSplit"))
    for j, txt in enumerate(header):
        cell = t.rows[0].cells[j]; cell.text = ""
        p = cell.paragraphs[0]; p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.paragraph_format.space_before = Pt(2); p.paragraph_format.space_after = Pt(2)
        p.paragraph_format.line_spacing = 1.0
        runs(p, txt, size=size, bold=True)
    for i, row in enumerate(rows, start=1):
        for j, txt in enumerate(row):
            cell = t.rows[i].cells[j]; cell.text = ""
            p = cell.paragraphs[0]
            p.alignment = WD_ALIGN_PARAGRAPH.LEFT if j == 0 else WD_ALIGN_PARAGRAPH.CENTER
            p.paragraph_format.space_before = Pt(2); p.paragraph_format.space_after = Pt(2)
            p.paragraph_format.line_spacing = 1.0
            runs(p, str(txt), size=size)
    for row in t.rows[:-1]:
        for cell in row.cells:
            for par in cell.paragraphs:
                par.paragraph_format.keep_with_next = True
    if note:
        p = doc.add_paragraph()
        p.paragraph_format.space_before = Pt(4); p.paragraph_format.space_after = Pt(10)
        p.paragraph_format.line_spacing = 1.0
        runs(p, note, size=8.5)


def figure(path, width, cap):
    p = doc.add_paragraph()
    p.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_before = Pt(8); p.paragraph_format.space_after = Pt(4)
    p.paragraph_format.keep_with_next = True
    p.add_run().add_picture(str(path), width=Inches(width))
    q = doc.add_paragraph()
    q.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.CENTER
    q.paragraph_format.space_after = Pt(12)
    q.paragraph_format.line_spacing = 1.0
    runs(q, cap, size=9.5, bold=True)


def pct(x):
    return "%.1f" % x


def f3(x):
    return "%.3f" % x


# ---------------------------------------------------------------- title page
for _ in range(5):
    p = doc.add_paragraph(); p.paragraph_format.space_after = Pt(0)
p = doc.add_paragraph()
p.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.CENTER
p.paragraph_format.space_after = Pt(18)
p.paragraph_format.line_spacing = 1.3
r = p.add_run("Automated Kellgren–Lawrence Grading of Knee Osteoarthritis from Plain "
              "Radiographs: Development and Internal Validation with Grad-CAM Explanations")
r.bold = True; r.font.size = Pt(18); r.font.name = "Times New Roman"
for text, size, bold, after in [("Youfan Wu", 13, True, 14),
                                ("School of Computing and Data Science", 11.5, False, 2),
                                ("Xiamen University Malaysia, Sepang, Malaysia", 11.5, False, 26)]:
    p = doc.add_paragraph(); p.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_after = Pt(after); p.paragraph_format.line_spacing = 1.15
    r = p.add_run(text); r.font.size = Pt(size); r.bold = bold; r.font.name = "Times New Roman"
for text, after in [("Corresponding author: Youfan Wu", 2),
                    ("School of Computing and Data Science, Xiamen University Malaysia", 2),
                    ("E-mail: CST2509046@xmu.edu.my", 26)]:
    p = doc.add_paragraph(); p.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_after = Pt(after); p.paragraph_format.line_spacing = 1.15
    p.add_run(text).font.size = Pt(10.5)
for text in ["Running title: Deep learning for KL grading of knee osteoarthritis",
             "Tables: 4    Figures: 5    References: 23"]:
    p = doc.add_paragraph(); p.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_after = Pt(2); p.paragraph_format.line_spacing = 1.15
    p.add_run(text).font.size = Pt(10)

body_sec = doc.add_section(WD_SECTION.NEW_PAGE)
body_sec.page_width, body_sec.page_height = Cm(21.0), Cm(29.7)
body_sec.left_margin = body_sec.right_margin = Cm(2.54)
body_sec.top_margin = body_sec.bottom_margin = Cm(2.29)
body_sec.header_distance = Cm(1.25)
body_sec.footer_distance = Cm(1.25)
body_sec.different_first_page_header_footer = False
_bp = None
for _p in doc.element.body.iterchildren(qn("w:p")):
    _pPr = _p.find(qn("w:pPr"))
    if _pPr is not None and _pPr.find(qn("w:sectPr")) is not None:
        _bp = _p; break
if _bp is not None:
    _sp = _bp.find(qn("w:pPr")).find(qn("w:sectPr"))
    _prev = _bp.getprevious()
    if _prev is not None and _prev.tag == qn("w:p"):
        _prev.get_or_add_pPr().append(_sp)
        _bp.getparent().remove(_bp)

# ---------------------------------------------------------------- abstract
h("Abstract", 1)
ACC = pct(100 * R["accuracy"]) if R else "—"
A_LO, A_HI = ("%.1f" % (100 * R["acc_ci"][0]), "%.1f" % (100 * R["acc_ci"][1])) if R else ("—", "—")
para("Kellgren–Lawrence (KL) grading of knee osteoarthritis (KOA) is a semi-quantitative task with "
     "substantial inter-reader variability, and disagreement concentrates at the early grades. This study "
     "developed and internally validated an explainable deep learning grader for five-class KL "
     "grading, and examined how performance is distributed across grades. We analysed 8,260 knee "
     "radiographs that the dataset assigns to 4,130 participants (Mendeley Data). Partitions were formed from the identifier embedded in each file name so "
     "that both knees of a participant remained in the same set: training (5,778 radiographs, 2,889 "
     "identifiers), validation (826, 413) and test (1,656, 828), with no identifier shared between sets. "
     "Images were contrast-enhanced with contrast-limited adaptive histogram equalisation and classified "
     "with an ImageNet-pretrained ResNet-50 fine-tuned end-to-end. On the held-out test set the model "
     "reached an accuracy of " + ACC + "% (95% CI " + A_LO + "–" + A_HI + "), a macro F1 of "
     + (f3(R["macro_f1"]) if R else "—") + ", a quadratic-weighted Cohen's kappa of "
     + (f3(R["kappa_quadratic"]) if R else "—") + " and a macro one-vs-rest area under the curve (AUC) of "
     + (f3(R["macro_auc"]) if R else "—") + ". Class-wise recall for KL grades 0–4 was "
     + (", ".join("%.2f" % R["per_class"][str(i)]["recall"] for i in range(5)) if R else "—")
     + ", and " + (pct(100 * R["adjacent"] / R["errors"]) if R else "—") + "% of misclassifications were "
     "confined to adjacent grades. Performance was lowest at KL 1 (recall "
     + ("%.2f" % R["per_class"]["1"]["recall"] if R else "—") + "), the grade with the weakest reader "
     "agreement. Grad-CAM maps concentrated on the tibiofemoral joint line and adjacent subchondral bone. "
     "Because the analysis is internal to a single cohort, external validation and reader studies are "
     "required before clinical use.", after=6)
para("**Keywords:** knee osteoarthritis; Kellgren–Lawrence grading; deep learning; data partitioning; "
     "explainable artificial intelligence; radiography", indent=False, after=6)

# ---------------------------------------------------------------- introduction
h("1. Introduction", 1)
para("Knee osteoarthritis (KOA) is the most common musculoskeletal disorder of later life and a leading "
     "cause of global disability {{1}}. Its incidence rises with age and with obesity, and the disease is "
     "now understood as a disorder of the whole joint rather than of cartilage alone {{2,4}}. Radiographic "
     "severity is reported almost universally with the "
     "Kellgren–Lawrence (KL) scale, a five-level ordinal system defined by marginal osteophytes, "
     "joint-space narrowing, subchondral sclerosis and cystic change {{3}}. These features reflect coupled "
     "remodelling of the osteochondral unit, in which cartilage loss, subchondral bone thickening and "
     "osteophyte formation develop together {{4}}. The scale is semi-quantitative, "
     "and its reliability is limited: agreement between experienced readers is reported to be moderate, and "
     "disagreement concentrates at the KL 0–2 boundary, where the defining abnormalities are "
     "small, partly projection-dependent, and judged against an implicit clinical impression of the patient "
     "{{3,5}}.")
para("Deep learning has brought automatic KL grading close to reader performance, but the improvement is "
     "uneven across the scale. Reported models approach or exceed expert agreement at KL 3–4, where "
     "structural change is conspicuous, whereas performance at KL 1–2 remains poor and class-wise recall is "
     "frequently below 0.5 {{6,7,8,9,10,11}}. Two explanations are usually offered. The first is "
     "representational: a single two-dimensional projection may not contain enough information to separate "
     "doubtful from minimal disease. The second concerns the reference standard: because the grade itself is "
     "uncertain at the early end of the scale, a model trained on it inherits part of that uncertainty. The "
     "two mechanisms are not equivalent — one concerns the image, the other the label — and both may "
     "contribute to the observed pattern without either being established for a particular cohort.")
para("A further complication is that reported performance is sensitive to the partitioning used. When images "
     "rather than participants are split, the contralateral knee of a patient can appear on both sides of the "
     "evaluation, and the resulting estimates are optimistically biased; this point has recently been made "
     "explicitly for KL grading, together with the domain shift that appears when a model is transported "
     "across institutions {{12}}. The present study therefore groups images by the file identifier and "
     "evaluates on a single internal test set.")

para("Two further issues recur in this literature. First, performance is often summarised by accuracy "
     "alone, which hides the ordinal structure of the scale and the systematic difficulty of the early "
     "grades. Second, explainability is frequently asserted rather than demonstrated, and the evidence is "
     "usually a single heat map without a description of how it was generated.")
para("This study therefore had three aims: to develop and evaluate a five-class KL grader on a "
     "single-cohort partition with no identifier overlap; to characterise its performance across grades, "
     "including the ordinal structure of its errors and two clinically motivated dichotomies; and to "
     "examine, with Grad-CAM, which image regions drive the predictions. The study is a methodological and "
     "evaluative contribution rather than a new architecture: it provides an internal, "
     "file-identifier-controlled evaluation of a standard backbone, a complete account of the ordinal error "
     "structure, a calibrated probability analysis, an exploratory comparison of four backbones, and a "
     "reproducible baseline with public code and predictions. Two 2026 studies that use the same release "
     "address complementary questions — domain adaptation across institutions {{22}} and an uncertainty-aware "
     "three-class formulation with repeated seeds {{23}} — and neither reports a five-class internal "
     "evaluation of the kind presented here.")

# ---------------------------------------------------------------- methods
h("2. Materials and Methods", 1)
figure(FIG / "figure0_pipeline.png", 6.0,
       "**Figure 1.** Study workflow: dataset and participant grouping (by file identifier), "
       "preprocessing and augmentation, network, training and test-set evaluation.")
para("The workflow is summarised in Figure 1. Radiographs were grouped by file identifier before any "
     "preprocessing, so that the two knees of a participant never crossed partitions, and the test partition "
     "was opened only after training and checkpoint selection had finished.")

h("2.1 Data Source and Cohort", 2)
para("This study used version 1 of the Knee Osteoarthritis Severity Grading Dataset (Mendeley Data, "
     "doi:10.17632/56rmx5bjcr.1), retrieved in November 2026 {{13}}. The release contains knee radiographs "
     "derived from the Osteoarthritis Initiative (OAI) {{14}}, distributed as single-channel 8-bit PNG files "
     "at 224 × 224 pixels and organised into training, validation and test folders, each subdivided into five "
     "folders representing the KL grades. It comprises 8,260 radiographs that the dataset assigns to 4,130 "
     "participants, with one left and one right knee image per participant. The participant count is "
     "therefore the one reported with the dataset, whereas the grouping applied here uses the identifier "
     "embedded in each file name (Section 2.2). The class distribution of the released files is imbalanced, "
     "with KL 2 the largest class and KL 4 the smallest (Table 1); no claim is made that it represents the "
     "distribution of the source cohort.")
para("The KL grade of each image was taken from the folder in which it was distributed. The labels were not "
     "re-read, re-scored or adjudicated for this study, and the release does not document the number of "
     "original readers, their training or the adjudication procedure; the grade should therefore be treated "
     "as the dataset label rather than as a reference standard established for this work. The images are "
     "downsampled derivatives, and the acquisition parameters of the original radiographs — projection, beam "
     "angle, detector and exposure — cannot be recovered from them. Whether all images come from a single "
     "OAI visit, and which visit, cannot be confirmed from the release either. These four points are "
     "restated as limitations in Section 4.1.")
para("All 8,260 files in the release were used. Every file was readable and had identical dimensions "
     "(224 × 224 pixels, single-channel 8-bit PNG); no file name was duplicated, a checksum comparison "
     "found no pair of byte-identical images within or across partitions, and each image carried exactly "
     "one folder label. No image was excluded, and no label was re-read or modified.")
para("Participant-level clinical and laboratory data were not available for this cohort: the clinical "
     "tables distributed with related work come from a separate cohort without participant identifiers and "
     "cannot be linked to these radiographs. No clinical variable is used, imputed or simulated in this "
     "paper.")
table(["Partition", "Radiographs", "File identifiers", "KL 0", "KL 1", "KL 2", "KL 3", "KL 4"],
      [["Training", "5,778", "2,889", "2,286", "1,046", "1,516", "757", "173"],
       ["Validation", "826", "413", "328", "153", "212", "106", "27"],
       ["Test", "1,656", "828", "639", "296", "447", "223", "51"],
       ["Total", "8,260", "4,130", "3,253", "1,495", "2,175", "1,086", "251"]],
      [2.4, 2.4, 2.4, 1.7, 1.7, 1.7, 1.7, 1.7],
      "Table 1. Composition of the cohort and distribution of KL grades across the three partitions.",
      note="Values are numbers of radiographs. The identifier is the number embedded in the file name. One "
           "identifier corresponds to one participant as reported with the dataset, and the two knees sharing "
           "an identifier were always assigned to the same partition. The partitions are the ones distributed "
           "with the release; they were not re-drawn for this study (Section 2.2).")

h("2.2 Partitioning and Leakage Control", 2)
para("The training, validation and test partitions distributed with the dataset were used as provided; no "
     "image was moved between partitions and no re-splitting was performed; the three partitions account for "
     "approximately 70%, 10% and 20% of the release. The three partitions were "
     "therefore fixed before any preprocessing, augmentation or model fitting, and the validation partition "
     "was used only for early stopping and checkpoint selection. No formal sample-size calculation was "
     "performed, and no stratified redistribution of classes was applied: the class proportions of the three "
     "partitions are those of the release (Table 1). The identifier of an image is the number "
     "that precedes the laterality suffix in its file name, so that, for example, 9003175L and 9003175R share "
     "the identifier 9003175. Because both knees of an identifier were placed in the same partition by the "
     "release, the design protects against contralateral-knee leakage between training and test data, which "
     "would be expected if images rather than identifiers were split.")
para("This protection was verified rather than assumed. The three partitions shared no identifier (0 for "
     "each of the three pairwise comparisons), and every identifier contributed exactly two images, one with "
     "each laterality suffix (2,889, 413 and 828 identifiers in the training, validation and test "
     "partitions). Exact duplicates were also excluded by checksum, as reported in Section 2.1. The complete "
     "partition, with the file identifier, laterality and KL grade of every radiograph, is provided as "
     "Table S1, from which the grouping can be reconstructed.")
para("The grouping is file-identifier-based rather than participant-verified. The identifiers are consistent "
     "with participant-level identifiers and pair the two knees correctly, but they were not independently "
     "linked to the original OAI clinical records for this study, so they should not be read as verified "
     "participant identifiers. Image-level splitting would have placed the contralateral knee of a "
     "participant in a different partition and produced optimistically biased estimates, because the two "
     "knees share anatomy, acquisition parameters and imaging conditions.")

h("2.3 Image Preprocessing and Augmentation", 2)
para("Each radiograph was read as an 8-bit PNG and converted to a single-channel image with the OpenCV "
     "grayscale transform. The image was sharpened by unsharp masking with a 3 × 3 Laplacian, "
     "I~s~ = I − 0.5∇²I, and clipped to 0–255; the sharpened image was then filtered with a 3 × 3 high-pass "
     "kernel (centre 9, neighbours −1) and smoothed with a 3 × 3 Gaussian kernel (standard deviation derived "
     "from the kernel size by OpenCV). Contrast-limited adaptive histogram equalisation was applied with a "
     "clip limit of 2.0 and an 8 × 8 tile grid, after which the single channel was replicated to three "
     "channels and normalised with the ImageNet statistics (mean [0.485, 0.456, 0.406], standard deviation "
     "[0.229, 0.224, 0.225]). The released images are already 224 × 224 pixels, so no resampling, cropping or "
     "padding was required; images were converted to tensors at that size. All operations were implemented "
     "in OpenCV 5.0.0 and applied identically to the three partitions.")
para("Augmentation was applied to the training partition only {{15}}. Each training image was horizontally "
     "flipped with probability 0.5 and rotated by an angle drawn uniformly from −15° to +15° with probability 0.5, "
     "using bilinear interpolation and reflected borders; the two operations were applied independently. No "
     "augmentation was applied at validation or test time. Horizontal flipping was retained because the "
     "grading target is defined by osteophytes, joint-space narrowing and sclerosis rather than by "
     "laterality; this choice is revisited as a limitation because it removes medial–lateral orientation.")

h("2.4 Network Architecture and Training", 2)
para("The image branch was a ResNet-50 {{16}} taken from torchvision 0.29 with ImageNet weights "
     "(``IMAGENET1K_V2''), in which all layers, including the residual blocks, were fine-tuned; transfer "
     "learning from ImageNet is the standard approach when the target cohort is small relative to the source "
     "of pretraining {{17}}. Global average pooling produced a 2,048-dimensional vector, which was mapped by "
     "a single fully connected layer (2,048 × 5 weights plus 5 biases) to the five class logits ordered "
     "KL 0 to KL 4. The complete network has 23.52 million parameters.")
para("Training used AdamW with the default moment estimates (β~1~ = 0.9, β~2~ = 0.999, ε = 1 × 10^−8^), a "
     "weight decay of 0.01, an initial learning rate of 1 × 10^−4^ changed manually to 5 × 10^−5^ at the "
     "start of epoch 5 (no scheduler was used), "
     "epoch, and a batch size of 32. The loss was standard cross-entropy without label smoothing. Class "
     "imbalance was addressed with a WeightedRandomSampler {{18}} that assigns each training image a weight "
     "inversely proportional to the frequency of its class, sampling with replacement for as many draws as "
     "there are training images in each epoch. Random seeds were fixed for Python, NumPy and PyTorch "
     "(seed 42). Training and evaluation used Python 3.14.2, PyTorch 2.15.0, torchvision 0.29.2, NumPy "
     "2.5.4, OpenCV 5.0.0, Pillow 13.0.0, scikit-learn 1.9.1, SciPy 1.18.1 and Matplotlib 3.11.2, on a single "
     "Apple M1 GPU through the Metal Performance Shaders backend; no CUDA device was available or used.")
para("The training protocol specified a maximum of 30 epochs with early stopping on validation accuracy "
     "(patience 7 epochs, minimum improvement 0.001). Training converged to the stopping criterion and ended "
     "at epoch 18, seven epochs after the last improvement; the checkpoint from epoch 11, which had the "
     "highest validation accuracy of the run (0.650), was retained for evaluation. The test partition was "
     "not used at any point during training or model selection.")

h("2.5 Grad-CAM Visualization", 2)
para("Gradient-weighted class activation mapping (Grad-CAM) {{19}} was computed on the final residual block of layer 4, whose output is a 7 × 7 × 2,048 "
     "feature map. Forward and backward hooks recorded the activations and the gradients with respect to "
     "the predicted class. Channel weights were obtained by global average pooling of the gradients over "
     "the 7 × 7 grid, and the class activation map was formed as the rectified weighted sum of the 2,048 "
     "feature maps. The map was resized bilinearly to 224 × 224 pixels, min–max normalised to the interval "
     "0–1, colour-mapped with the JET palette and blended with the original radiograph at α = 0.5. Maps are "
     "shown for one correctly classified test radiograph of each KL grade.")

h("2.6 Evaluation Metrics and Statistical Analysis", 2)
para("Performance was summarised by overall accuracy, class-wise precision, recall and F1 score, macro "
     "averages of these quantities, the one-vs-rest area under the receiver operating characteristic curve "
     "(AUC) for each grade, and the unweighted mean of the five class-wise AUCs (macro AUC). Because the KL "
     "scale is ordinal, quadratic-weighted Cohen's kappa (κ) was computed; this statistic treats a "
     "one-grade error as less severe than a two-grade error and is the standard agreement measure for "
     "ordinal KL data {{5}}.")
para("Ninety-five per cent confidence intervals (CIs) for proportions were obtained with the Wilson score "
     "interval. Intervals for accuracy, macro F1, quadratic-weighted κ and macro AUC were obtained by an "
     "identifier-level cluster bootstrap with 5,000 resamples and a fixed seed (2026), in which whole file "
     "identifiers were drawn with replacement so that the two knees sharing an identifier always entered "
     "the resample together, and the interval was taken as the 2.5th and 97.5th percentiles of the resampled "
     "statistics. The 1,656 test images were therefore not treated as 1,656 independent observations.")
para("Comparisons between the ResNet-50 model and each alternative backbone used the same test images. "
     "Accuracy differences were tested with a cluster-level sign-flip permutation test (10,000 permutations, "
     "seed 7), in which the sign of the per-identifier accuracy difference was randomly reversed so that the "
     "within-identifier correlation of the left and right knees was preserved; the conventional McNemar test "
     "is reported alongside it but is treated as secondary because it ignores that correlation. Differences "
     "in accuracy, macro F1, quadratic-weighted κ and macro AUC were also expressed with paired "
     "identifier-level bootstrap intervals (5,000 resamples, seed 2026). The three pairwise comparisons were "
     "adjusted with the Holm method, and the accuracy was the primary endpoint while the remaining metrics "
     "were secondary.")
para("Two dichotomies were evaluated post hoc from the same five-class predictions: KL ≥ 2 versus KL 0–1 "
     "(any definite radiographic osteoarthritis) and KL ≥ 3 versus KL 0–2 (moderate-to-severe disease), "
     "reporting sensitivity, specificity and accuracy; a three-tier collapse (KL 0–1, KL 2, KL 3–4) was "
     "evaluated in the same way. These analyses are post hoc and are not independent clinical endpoints. No "
     "threshold tuning was performed; class predictions were the argmax of the softmax output.")
para("Calibration was assessed on the test predictions with the expected calibration error (ECE) and the "
     "multiclass Brier score. ECE was computed over 15 equal-width bins of the maximum predicted "
     "probability, ECE = Σ~b~ (n~b~/N) |acc~b~ − conf~b~|, where n~b~ is the number of radiographs in bin b "
     "and acc~b~ and conf~b~ are the observed accuracy and mean predicted confidence in that bin. The Brier "
     "score was the mean over radiographs of the squared difference between the predicted probability "
     "vector and the one-hot reference, summed over the five classes. A single temperature T was fitted on "
     "the validation partition by minimising the negative log-likelihood of softmax(z/T), then applied to "
     "the test logits; this is a monotone transformation, so no predicted class changes. The test partition "
     "was never used to fit the temperature.")

h("2.7 Reporting Guideline", 2)
para("Reporting followed the Checklist for Artificial Intelligence in Medical Imaging (CLAIM) 2024 update "
     "and the TRIPOD+AI statement {{20,21}}.")

# ---------------------------------------------------------------- results
h("3. Results", 1)
h("3.1 Overall Classification Performance", 2)
para("On the held-out test set of 1,656 radiographs, the model classified " + (str(R["correct"]) if R else "—")
     + " correctly (1,051/1,656), an accuracy of " + ACC + "% (Wilson 95% CI " + A_LO + "–" + A_HI + "; cluster bootstrap "
     "60.9–65.9%). Macro F1 was "
     + (f3(R["macro_f1"]) if R else "—") + " (95% CI 0.620–0.674), quadratic-weighted κ was "
     + (f3(R["kappa_quadratic"]) if R else "—") + " (0.768–0.814) and macro AUC was "
     + (f3(R["macro_auc"]) if R else "—") + " (0.865–0.887), all from the identifier-level bootstrap (Table 2). Discrimination was best for the two ends of the "
     "scale and weakest for KL 1, whose recall was "
     + ("%.2f" % R["per_class"]["1"]["recall"] if R else "—") + " and whose AUC was "
     + ("%.3f" % R["per_class"]["1"]["auc"] if R else "—") + ".")
para("The gap between accuracy (" + ACC + "%) and quadratic-weighted κ ("
     + (f3(R["kappa_quadratic"]) if R else "—") + ") is informative. Accuracy counts every disagreement "
     "equally, whereas κ weights disagreements by their ordinal distance; the simultaneously moderate "
     "accuracy and high weighted agreement therefore indicate that the model's errors are concentrated "
     "between neighbouring grades rather than distributed across the scale. Macro-averaged precision and "
     "recall weight the five grades equally and are therefore lower than the overall accuracy, which is "
     "dominated by the two largest classes.")
table(["KL grade", "n", "Recall (95% CI)", "Precision", "F1", "AUC"],
      [["0", "639", "%.2f (%.2f–%.2f)" % (R["per_class"]["0"]["recall"], *R["per_class"]["0"]["rec_ci"]),
        "%.2f" % R["per_class"]["0"]["precision"], "%.2f" % R["per_class"]["0"]["f1"],
        "%.3f" % R["per_class"]["0"]["auc"]],
       ["1", "296", "%.2f (%.2f–%.2f)" % (R["per_class"]["1"]["recall"], *R["per_class"]["1"]["rec_ci"]),
        "%.2f" % R["per_class"]["1"]["precision"], "%.2f" % R["per_class"]["1"]["f1"],
        "%.3f" % R["per_class"]["1"]["auc"]],
       ["2", "447", "%.2f (%.2f–%.2f)" % (R["per_class"]["2"]["recall"], *R["per_class"]["2"]["rec_ci"]),
        "%.2f" % R["per_class"]["2"]["precision"], "%.2f" % R["per_class"]["2"]["f1"],
        "%.3f" % R["per_class"]["2"]["auc"]],
       ["3", "223", "%.2f (%.2f–%.2f)" % (R["per_class"]["3"]["recall"], *R["per_class"]["3"]["rec_ci"]),
        "%.2f" % R["per_class"]["3"]["precision"], "%.2f" % R["per_class"]["3"]["f1"],
        "%.3f" % R["per_class"]["3"]["auc"]],
       ["4", "51", "%.2f (%.2f–%.2f)" % (R["per_class"]["4"]["recall"], *R["per_class"]["4"]["rec_ci"]),
        "%.2f" % R["per_class"]["4"]["precision"], "%.2f" % R["per_class"]["4"]["f1"],
        "%.3f" % R["per_class"]["4"]["auc"]],
       ["Macro average", "—", "%.2f" % R["macro_recall"], "%.2f" % R["macro_precision"],
        f3(R["macro_f1"]), f3(R["macro_auc"])]] if R else [["—"] * 6],
      [2.8, 2.0, 4.2, 2.6, 2.0, 2.0],
      "Table 2. Class-wise and aggregate performance of the model on the test set.",
      note="AUC, one-vs-rest area under the receiver operating characteristic curve. Overall accuracy was "
           + ACC + "% (" + (str(R["correct"]) if R else "—") + "/1,656). Confidence intervals for recall "
           "were computed with the Wilson score interval; the macro AUC is the unweighted mean of the five "
           "class-wise AUCs.")

if BASELINES:
    para("To test whether the choice of backbone materially affects performance, three further architectures "
         "were trained under the identical protocol on the same partitions: ResNet-18, ResNet-34 and "
         "MobileNetV2. Each was initialised with ImageNet weights and trained with AdamW under the same "
         "learning-rate schedule, batch size and sampler, with early stopping on the validation partition "
         "(patience 7, minimum improvement 0.001); the test partition was evaluated once per model (Table 3).")
    table(["Model", "Parameters (M)", "Epochs (best / stopped)", "Accuracy (%)", "Macro F1", "Quadratic κ", "Macro AUC"],
          [["ResNet-18", "11.2", "7 / 14", pct(100 * BASELINES["resnet18"]["accuracy"]),
            f3(BASELINES["resnet18"]["macro_f1"]), f3(BASELINES["resnet18"]["kappa_quadratic"]),
            f3(BASELINES["resnet18"]["macro_auc"])],
           ["ResNet-34", "21.3", "14 / 15", pct(100 * BASELINES["resnet34"]["accuracy"]),
            f3(BASELINES["resnet34"]["macro_f1"]), f3(BASELINES["resnet34"]["kappa_quadratic"]),
            f3(BASELINES["resnet34"]["macro_auc"])],
           ["MobileNetV2", "2.2", "15 / 21", pct(100 * BASELINES["mobilenet_v2"]["accuracy"]),
            f3(BASELINES["mobilenet_v2"]["macro_f1"]), f3(BASELINES["mobilenet_v2"]["kappa_quadratic"]),
            f3(BASELINES["mobilenet_v2"]["macro_auc"])],
           ["ResNet-50 (this work)", "23.5", "11 / 18", pct(100 * R["accuracy"]), f3(R["macro_f1"]),
            f3(R["kappa_quadratic"]), f3(R["macro_auc"])]],
          [3.6, 2.2, 2.6, 2.2, 1.8, 2.0, 1.9],
          "Table 3. Comparison of backbone architectures trained under the same protocol.",
          note="All models used the same partitions, preprocessing, optimiser schedule, batch size and "
               "weighted sampler. Epochs are given as best-validation epoch / epoch at which training "
               "stopped. ResNet-18 and the ResNet-50 model reached the early-stopping criterion; ResNet-34 "
               "and MobileNetV2 were stopped by the per-model time limit after the epoch shown.")
    para("The ResNet-50 model was specified before any experiments were run; the three alternative backbones "
     "were trained afterwards for comparison, and no model was selected on the basis of test-set performance.")
para("The four backbones performed within a narrow band (61.3–66.4% accuracy; macro AUC 0.866–0.876), and "
         "the differences were of the same order as the width of the confidence intervals reported in Table 2. "
         "ResNet-34 reached the highest accuracy and quadratic-weighted agreement, whereas the ResNet-50 model "
         "reported here had the highest macro AUC; the smallest network, MobileNetV2, was the weakest on "
         "agreement. ResNet-50 was therefore not the best-performing choice on this dataset, and the "
         "comparison does not support the view that a larger backbone is required for KL grading. The "
         "remaining error is more plausibly attributable to the ambiguity of the reference labels than to "
         "model capacity.")

para("Paired comparisons on the same test images were performed for each alternative backbone. Against "
     "ResNet-18 the ResNet-50 model did not differ in accuracy (Δ = −0.5 percentage points; 95% CI −3.0 to "
     "+1.9; cluster permutation p = 0.70) or in macro AUC (Δ = +0.005; 95% CI −0.006 to +0.016). Against "
     "ResNet-34 the accuracy was 3.0 percentage points lower for the ResNet-50 model (Δ = −3.0; 95% CI −5.3 "
     "to −0.6; cluster permutation p = 0.018; Holm-adjusted p = 0.054), whereas macro AUC did not differ "
     "(Δ = +0.006; 95% CI −0.005 to +0.016). Against MobileNetV2 neither accuracy (Δ = +2.2 points; 95% CI "
     "−0.4 to +4.8; p = 0.11) nor macro AUC (Δ = +0.010; 95% CI −0.001 to +0.021) differed. After Holm "
     "correction across the three comparisons no difference reached the 0.05 level (adjusted p = 0.054, 0.34 "
     "and 1.00), so the comparison does not establish superiority of any backbone. The pattern suggests that "
     "the architecture acts mainly on the placement of decision boundaries rather than on the underlying "
     "ordinal information, but the unequal stopping conditions of the four models limit this reading.")

h("3.2 Error Structure and Ordinal Consistency", 2)
figure(FIG / "figure1_confusion.png", 4.2,
       "**Figure 2.** Normalised confusion matrix on the test set. Rows are reference KL grades and columns "
       "are predicted grades; values are row-normalised proportions.")

para("The normalised confusion matrix (Figure 2) shows that errors were overwhelmingly ordinal. Of "
     + (str(R["errors"]) if R else "—") + " misclassifications, " + (str(R["adjacent"]) if R else "—")
     + " (" + (pct(100 * R["adjacent"] / R["errors"]) if R else "—") + "%) were within one grade and "
     + (str(R["far"]) if R else "—") + " (" + (pct(100 * R["far"] / R["errors"]) if R else "—")
     + "%) spanned two or more grades. KL 1 was the principal source of error, and its cases moved "
     "predominantly toward the neighbouring KL 0 and KL 2 categories rather than to distant grades.")
para("Collapsing the five-level scale into the two dichotomies that drive referral sharpens the picture. "
     "For KL ≥ 2 versus KL 0–1, sensitivity was " + ("%.3f" % R["kl_ge2"]["sens"] if R else "—")
     + " (95% CI 0.761–0.820), specificity was " + ("%.3f" % R["kl_ge2"]["spec"] if R else "—")
     + " (0.834–0.879) and accuracy was " + ("%.3f" % R["kl_ge2"]["acc"] if R else "—")
     + ". For KL ≥ 3 versus KL 0–2, sensitivity was " + ("%.3f" % R["kl_ge3"]["sens"] if R else "—")
     + " (0.799–0.885), specificity was " + ("%.3f" % R["kl_ge3"]["spec"] if R else "—")
     + " (0.964–0.981) and accuracy was " + ("%.3f" % R["kl_ge3"]["acc"] if R else "—")
     + ". A three-tier collapse (KL 0–1, KL 2 and KL 3–4) "
     "classified " + (str(R["three_tier"]["correct"]) if R else "—") + " of 1,656 radiographs correctly ("
     + (pct(100 * R["three_tier"]["acc"]) if R else "—") + "%). The two dichotomies were therefore separated "
     "more accurately than the five-level task. These are post hoc analyses of the same predictions, and they "
     "indicate discrimination rather than clinical utility.")
h("3.3 Grad-CAM Visualization", 2)
figure(FIG / "figure2_gradcam.png", 5.0,
       "**Figure 3.** Grad-CAM overlays for representative test radiographs of KL grades 0–4. Warm colours "
       "indicate regions that contributed most strongly to the predicted class (JET colour map, α = 0.5).")

para("Figure 3 shows Grad-CAM maps for one correctly classified test radiograph of each KL grade. "
     "Activation was concentrated along the tibiofemoral joint line and the adjacent subchondral bone of "
     "both compartments, with little weight on the soft tissues or the image background. At the 7 × 7 "
     "spatial resolution of the final layer the map cannot resolve individual osteophytes, so the overlay "
     "should be read as evidence that the network attends to the joint line rather than as a localisation "
     "of specific radiographic features. The analysis is qualitative and covers five cases; no reader study "
     "or quantitative localisation was performed.")
h("3.4 Class-Wise ROC Analysis", 2)
figure(FIG / "figure3_roc.png", 4.4,
       "**Figure 4.** One-vs-rest ROC curves for the five KL grades on the test set.")

para("The class-wise ROC curves are shown in Figure 4. The macro-average AUC was "
     + (f3(R["macro_auc"]) if R else "—") + ". The highest class-wise values were obtained for KL 4 ("
     + ("%.3f" % R["per_class"]["4"]["auc"] if R else "—") + ") and KL 3 ("
     + ("%.3f" % R["per_class"]["3"]["auc"] if R else "—") + "), and the lowest for KL 1 ("
     + ("%.3f" % R["per_class"]["1"]["auc"] if R else "—") + "). The ranking of AUCs reproduces the pattern "
     "seen in the confusion matrix and is consistent with the observation that the KL 1–2 boundary is the "
     "least reproducible part of the scale. The AUC of KL 4 should be interpreted with caution because it "
     "rests on 51 positive cases, and its confidence interval is correspondingly wide.")
h("3.5 Calibration", 2)
para("Discrimination and calibration are separate properties: a model can rank patients correctly while its "
     "probabilities are systematically too high or too low. Calibration was assessed with the definitions "
     "given in Section 2.6.")
para("The uncalibrated model was overconfident: mean predicted confidence was 0.797 against an observed "
     "accuracy of 0.635, ECE was 0.162 and the Brier score was 0.528. The fitted temperature was 1.96; after "
     "scaling, ECE fell to 0.026 and the Brier score to 0.479, while accuracy and all class predictions were "
     "unchanged (Figure 5). The softmax outputs of the trained model should therefore not be read as "
     "probabilities of disease without recalibration. Temperature scaling fitted on a separate validation "
     "partition reduced the calibration error substantially in this cohort, but whether the scaled "
     "probabilities are adequate for a particular clinical decision would require a decision-specific "
     "analysis that this study did not perform.")
figure(FIG / "figure5_calibration.png", 5.6,
       "**Figure 5.** Calibration of the test-set predictions. Left: reliability diagram before and after "
       "temperature scaling; right: distribution of predicted confidence.")

h("3.6 Comparison with Published Models", 2)
para("Direct comparison with published KL grading models is constrained by differences in cohort, "
     "partitioning, architecture and metric definition, and Table 4 is therefore a contextual reference "
     "rather than a head-to-head benchmark. The most closely comparable study is that of Alkhatatbeh et "
     "al., who used the same 8,260-image OAI-derived dataset with patient-wise stratified splits and a "
     "multitask architecture, and reported an internal accuracy of 70.3% and a quadratic-weighted κ of "
     "0.881 on a 1,239-image internal test set. On an independent Chinese cohort of 2,295 images, the same "
     "model was fine-tuned on the external training and validation partitions (1,606 and 344 images) and "
     "then evaluated on an independent 345-image held-out external test, where accuracy rose from 66.1% "
     "under zero-shot transfer to 80.0% {{12}}. Liu et al. used the same 5,778/826/1,656 split of this dataset "
     "and reported a quadratic-weighted κ of 0.8557 for transfer from this cohort to an independent knee "
     "radiograph collection, 0.2652 above source-only training {{22}}. Yepez et al. also used this release, with the "
     "same identifier-based grouping and the same 8,260/4,130 counts, but collapsed the five grades into three "
     "categories and reported a mean accuracy of 0.811 ± 0.008 over seeds 42, 123 and 2026 with grouped "
     "cross-validation {{23}}; that figure describes a three-class task and cannot be compared with the "
     "five-class accuracy reported here. Tiulpin et al. trained on one cohort and tested "
     "on 5,960 OAI knees, reporting a multiclass accuracy of 66.71%, a quadratic-weighted κ of 0.83 and an "
     "AUC of 0.93 for the binary KL ≥ 2 task {{6}}. The present model reached an accuracy of " + ACC + "%, a "
     "quadratic-weighted κ of " + (f3(R["kappa_quadratic"]) if R else "—") + " and a macro one-vs-rest AUC "
     "of " + (f3(R["macro_auc"]) if R else "—") + " across five classes. The AUC values describe different "
     "tasks — 0.93 refers to a single binary threshold, whereas " + (f3(R["macro_auc"]) if R else "—") + " "
     "averages five one-versus-rest curves — and are therefore not ranked here. Because partitions, architectures and training budgets "
     "all differ, the table supports context rather than a claim of superiority in either direction.")

table(["Study", "Test set", "Model / input", "Accuracy", "Quadratic κ", "AUC"],
      [["Tiulpin et al. 2018 {{6}}", "5,960 OAI knees (external to training cohort)",
        "Ensemble of 3 CNNs; radiograph", "66.7%", "0.83", "0.93 (KL ≥ 2)"],
       ["Alkhatatbeh et al. 2026 {{12}}", "OAI-derived internal (n = 1,239); external held-out test (n = 345)",
        "KL-FuseNet; ConvNeXt-Base + ResNet-50, multitask", "70.3% internal; 80.0% external (fine-tuned)",
        "0.881 internal; 0.950 external", "0.981 (KL ≥ 2, internal); 0.984 (KL ≥ 2, external)"],
       ["This work", "1,656 radiographs (internal)",
        "ResNet-50; radiograph", ACC + "%", (f3(R["kappa_quadratic"]) if R else "—"),
        (f3(R["macro_auc"]) if R else "—") + " (macro)"]],
      [3.9, 3.5, 3.7, 2.6, 2.4, 2.4],
      "Table 4. Contextual comparison with published models.",
      note="The three studies differ in partitioning, cohort composition and metric definition, and the "
           "figures are not directly interchangeable. Tiulpin et al. report a binary KL ≥ 2 AUC; Alkhatatbeh "
           "et al. report internal results on a 1,239-image test set and externally fine-tuned results on a "
           "345-image held-out test drawn from a 2,295-image cohort; the present value is a macro "
           "one-vs-rest AUC across five classes. No head-to-head inference should be drawn from this table.")

# ---------------------------------------------------------------- discussion
h("4. Discussion", 1)
para("This study evaluated a single-cohort, explainable ResNet-50 grader for five-class KL grading on "
     "8,260 radiographs grouped into 4,130 file identifiers. Three findings emerge. First, the model reached an accuracy "
     "of " + ACC + "%, a quadratic-weighted κ of " + (f3(R["kappa_quadratic"]) if R else "—") + " and a macro "
     "AUC of " + (f3(R["macro_auc"]) if R else "—") + " on a test set that shared no file identifier with "
     "training. Second, its errors were overwhelmingly ordinal: "
     + (pct(100 * R["adjacent"] / R["errors"]) if R else "—") + "% of misclassifications were confined to "
     "adjacent grades, which is why the weighted κ is much higher than the accuracy. Third, the binary "
     "analyses were easier than the five-class task, with sensitivity and specificity of "
     + ("%.3f and %.3f" % (R["kl_ge2"]["sens"], R["kl_ge2"]["spec"]) if R else "—") + " for KL ≥ 2 versus "
     "KL 0–1 and " + ("%.3f and %.3f" % (R["kl_ge3"]["sens"], R["kl_ge3"]["spec"]) if R else "—") + " for "
     "KL ≥ 3 versus KL 0–2. These are internal test-set estimates from a single cohort; they describe the "
     "performance of this checkpoint under this partition and are not evidence of clinical effectiveness. A "
     "fourth observation concerns architecture: the four backbones trained under the same protocol performed "
     "within a narrow band, with ResNet-34 reaching the highest accuracy and the ResNet-50 model evaluated "
     "here the highest macro AUC, so the spread was within the confidence intervals of Table 2 and no "
     "backbone was clearly superior.")
para("The KL 1 grade deserves separate comment. Its recall of "
     + ("%.2f" % R["per_class"]["1"]["recall"] if R else "—") + " is low. Part of the shortfall is likely to "
     "reflect the model and its training procedure, and part may reflect the reference standard, because KL 1 is "
     "the grade with the weakest reported agreement in the literature {{3,5}}. The two contributions cannot "
     "be separated with these data, so the recall should be read as performance against the dataset labels "
     "rather than against a consensus reference. The same reasoning applies to the pattern of adjacent errors: it is consistent "
     "with an ordinal scale that is difficult to apply reproducibly, but it is not direct evidence about how "
     "readers behaved in this cohort.")
para("Direct comparison with published models is constrained by differences in cohort, partitioning, "
     "architecture and metric definition. Tiulpin et al. trained on one cohort and tested on 5,960 OAI "
     "knees, reporting a multiclass accuracy of 66.71%, a quadratic-weighted κ of 0.83 and an AUC of 0.93 "
     "for the binary KL ≥ 2 task {{6}}. Alkhatatbeh et al. used the same 8,260-image OAI-derived dataset as "
     "the present study, applied patient-wise stratified splits and a multitask architecture that predicts "
     "ordinal grades, label distributions and binary severity jointly, and reported an internal accuracy of "
     "70.3% and a quadratic-weighted κ of 0.881 on their 1,239-image internal test set. On a 2,295-image "
     "external cohort the model was fine-tuned on the external training and validation partitions and then "
     "evaluated on the independent 345-image held-out external test, where accuracy rose from 66.1% under "
     "zero-shot transfer to 80.0% {{12}}. The present model's accuracy and quadratic-weighted agreement "
     "are lower than those of the latter study. The most plausible explanations are the simpler single-task "
     "architecture (a ResNet-50 without multitask heads or label-distribution modelling) and the absence of "
     "any adaptation to a second "
     "domain. Because the partitions and the tasks differ, these figures are contextual rather than a "
     "head-to-head comparison.")
para("Two 2026 studies used the same release, which places the present results in context. Liu et al. "
     "addressed domain shift with a contrastive adaptation framework and reported a quadratic-weighted κ of "
     "0.8557 for transfer from this cohort to an external collection, a task that the present study does not "
     "attempt {{22}}. Yepez et al. collapsed the five grades into three categories, kept identifier-disjoint "
     "splits, trained with seeds 42, 123 and 2026 and used a grouped bootstrap, reporting a mean accuracy of "
     "0.811 ± 0.008 {{23}}; a three-class accuracy is not comparable with the five-class accuracy of 0.635 "
     "reported here, and the difference in task difficulty rather than in method accounts for most of the "
     "gap. What the present study adds is a five-class, internally validated baseline with a complete "
     "ordinal error analysis, an architecture comparison and a calibration assessment on the same release.")
para("The Grad-CAM maps support the plausibility of the image pathway, since activation concentrated on the "
     "tibiofemoral joint line rather than on background or acquisition artefacts. They do not establish that "
     "the network uses the same features as a radiologist; the maps are qualitative, cover five cases, and "
     "were not compared with expert annotations. The binary analyses are exploratory and post hoc: they were "
     "derived from the same predictions to describe a clinically relevant dichotomy, and no referral "
     "pathway, decision impact or reader interaction was evaluated. A tool of this kind would require a "
     "prospective comparison with routine reporting before any claim about triage could be made.")
para("Finally, the macro one-vs-rest AUC reported here and a binary KL ≥ 2 AUC reported elsewhere answer "
     "different questions. The macro value averages five one-versus-rest tasks and summarises discrimination "
     "across the whole ordinal scale, but it does not weight an error by its ordinal distance; that weighting "
     "is the role of the quadratic-weighted κ. The binary value describes a single threshold. Neither is "
     "intrinsically stricter, and the two should not be ranked against each other.")

h("4.1 Limitations", 2)
para("Nine limitations qualify these findings. First, the study is a retrospective analysis of a single public "
     "dataset, and the test partition, although identifier-disjoint, comes from the same source population "
     "and imaging protocol. The metrics are therefore internally validated estimates, not evidence of "
     "transportability, and no external cohort was available.")
para("Second, the identifiers used for grouping were derived from file names and were not independently "
     "linked to the OAI clinical records, so they should not be read as verified participant identifiers; "
     "residual mis-assignment of left and right knees or of participants cannot be excluded.")
para("Third, the KL grades were taken from the folder structure of the release. The number of original "
     "readers, their training and the adjudication procedure are not documented, and the labels were not "
     "re-read or adjudicated for this study, so they are dataset labels rather than a reference standard "
     "established here.")
para("Fourth, the images are downsampled 224 × 224 PNG derivatives. Projection, beam angle, detector and "
     "exposure of the original acquisitions cannot be recovered, and the effect of downsampling on the "
     "visibility of small osteophytes cannot be quantified from the release.")
para("Fifth, no radiologist reader study and no quantitative lesion localisation were performed. The "
     "Grad-CAM analysis is qualitative, covers five correctly classified cases, and at the 7 × 7 resolution "
     "of the target layer cannot resolve individual osteophytes; it should not be read as evidence that the "
     "network segments or localises specific pathological structures.")
para("Sixth, class-specific performance is uneven: KL 1 recall was 0.32 and KL 4 was represented by only 51 "
     "test radiographs, so both the weakest class and the smallest class carry substantial uncertainty.")
para("Seventh, one random seed was used per architecture, so run-to-run variability is not reported; the "
     "confidence intervals account for sampling variability of the test set, not for training variability. "
     "Repeated training with several seeds, as used in other work on this release {{23}}, would be required "
     "to separate architecture effects from seed effects.")
para("Eighth, the backbone comparison is exploratory. Two models reached the early-stopping criterion while "
     "two were stopped by a per-model time limit, so the comparison is not budget-matched, and after "
     "adjustment for multiple comparisons no difference was statistically significant.")
para("Ninth, calibration was fitted and evaluated within the same cohort. Temperature scaling reduced the "
     "calibration error on the internal test set, but calibration on external data, at clinically relevant "
     "decision thresholds, and across subgroups was not assessed; no clinical, laboratory or symptom data "
     "were available for these participants, so a clinically guided extension could not be evaluated either.")

h("5. Conclusion", 1)
para("An explainable ResNet-50 grader evaluated on a single-cohort, identifier-disjoint test set achieved an accuracy of " + ACC + "%, a "
     "quadratic-weighted κ of " + (f3(R["kappa_quadratic"]) if R else "—") + " and a macro AUC of "
     + (f3(R["macro_auc"]) if R else "—") + " for five-class KL grading on an internal test set, with errors "
     "concentrated between adjacent grades and performance lowest at KL 1. The two dichotomies were separated "
     "more accurately than the five-level task, but these analyses were post hoc and were not tested in a "
     "clinical workflow; they describe discrimination at a threshold, not a triage or referral effect. "
     "Because the evidence is internal to a single cohort, external validation and a reader study are the "
     "necessary next steps before any clinical use is considered, and calibration would need to be reassessed "
     "on external data.")

h("Authors' Contributions", 1)
para("Y.W. conceived and designed the study, performed the experiments and data analysis, and wrote the "
     "manuscript. The author read and approved the final manuscript.")
h("Funding", 1)
para("This research received no external funding.")
h("Ethics Approval and Consent to Participate", 1)
para("This study is a secondary analysis of a publicly available, de-identified dataset. No participants "
     "were recruited, contacted or re-identified by the author, and no additional ethical approval was "
     "sought for the analysis of these open, de-identified records. Researchers using the dataset remain "
     "responsible for complying with its terms of use and with their own institutional requirements.")
h("Consent for Publication", 1)
para("Not applicable. No identifiable personal information is included in this manuscript.")
h("Data Availability Statement", 1)
para("The radiographic images analysed in this study are publicly available as the Knee Osteoarthritis "
     "Severity Grading Dataset (Mendeley Data, doi:10.17632/56rmx5bjcr.1). The derived data generated here "
     "— the partition lists, the per-image test predictions, the calibration and architecture-comparison "
     "outputs and the training logs — are provided as Supplementary Material and are also available from the "
     "corresponding author on reasonable request.")
h("Code Availability Statement", 1)
para("The Python scripts implementing preprocessing, training, evaluation, calibration, Grad-CAM and figure "
     "generation are provided as Supplementary Material, together with the trained weights and the random "
     "seeds required to reproduce the reported results. The same files are available from the corresponding "
     "author on reasonable request.")
h("Supplementary Material", 1)
para("The following files accompany the manuscript: Table S1, the partition lists with the file "
     "identifier of every radiograph; File S1, the per-image test predictions and probabilities for all four "
     "architectures; File S2, the training logs of the ResNet-50 model and of the three comparison backbones; "
     "File S3, the trained model weights; and File S4, the analysis code. These materials allow every table, "
     "figure and confidence interval in this article to be regenerated from the original predictions.")
h("Competing Interests", 1)
para("The author declares no competing interests.")

# ---------------------------------------------------------------- references
h("References", 1)
REFS = [
    ("Cross M, Smith E, Hoy D, Nolte S, Ackerman I, Fransen M, et al. The global burden of hip and knee osteoarthritis: estimates from the Global Burden of Disease 2010 study. Annals of the Rheumatic Diseases. 2014;73(7):1323–1330. doi:10.1136/annrheumdis-2013-204763"),
    ("Duong V, Abdel Shaheed C, Ferreira ML, Narayan SW, Venkatesha V, Hunter DJ, et al. Risk factors for the development of knee osteoarthritis across the lifespan: a systematic review and meta-analysis. Osteoarthritis and Cartilage. 2025;33(10):1162–1179. doi:10.1016/j.joca.2025.03.003"),
    ("Kellgren JH, Lawrence JS. Radiological assessment of osteo-arthrosis. Annals of the Rheumatic Diseases. 1957;16(4):494–502. doi:10.1136/ard.16.4.494"),
    ("Goldring SR, Goldring MB. Changes in the osteochondral unit during osteoarthritis: structure, function and cartilage-bone crosstalk. Nature Reviews Rheumatology. 2016;12(11):632–644. doi:10.1038/nrrheum.2016.148"),
    ("Kohn MD, Sassoon AA, Fernando ND. Classifications in brief: Kellgren-Lawrence classification of osteoarthritis. Clinical Orthopaedics and Related Research. 2016;474(8):1886–1893. doi:10.1007/s11999-016-4732-4"),
    ("Tiulpin A, Thevenot J, Rahtu E, Lehenkari P, Saarakkala S. Automatic knee osteoarthritis diagnosis from plain radiographs: a deep learning-based approach. Scientific Reports. 2018;8:1727. doi:10.1038/s41598-018-20132-7"),
    ("Olsson S, Akbarian E, Lind A, Razavian AS, Gordon M. Automating classification of osteoarthritis according to Kellgren-Lawrence in the knee using deep learning in an unfiltered adult population. BMC Musculoskeletal Disorders. 2021;22:844. doi:10.1186/s12891-021-04722-7"),
    ("Tiulpin A, Saarakkala S. Automatic grading of individual knee osteoarthritis features in plain radiographs using deep convolutional neural networks. Diagnostics. 2020;10(11):932. doi:10.3390/diagnostics10110932"),
    ("Yoon JS, Yon CJ, Lee D, Lee JJ, Kang CH, Kang SB, et al. Assessment of a novel deep learning-based software developed for automatic feature extraction and grading of radiographic knee osteoarthritis. BMC Musculoskeletal Disorders. 2023;24:869. doi:10.1186/s12891-023-06951-4"),
    ("Vaattovaara E, Panfilov E, Tiulpin A, Niinimäki T, Niinimäki J, Saarakkala S, et al. Kellgren-Lawrence grading of knee osteoarthritis using deep learning: diagnostic performance with external dataset and comparison with four readers. Osteoarthritis and Cartilage Open. 2025;7(2):100580. doi:10.1016/j.ocarto.2025.100580"),
    ("Zhang H, Kong C, Chang H, Gan Y. Automated Kellgren-Lawrence grading of knee osteoarthritis using a multi-scale attention-based deep learning framework. Frontiers in Medicine. 2026;13:1809768. doi:10.3389/fmed.2026.1809768"),
    ("Alkhatatbeh T, Alkhatatbeh A, Liao Y, Zhang Z, Fang H, Chen W, Zhang R. Cross-institutional "
     "five-class Kellgren–Lawrence grading of knee osteoarthritis via multitask deep learning. Annals of the "
     "New York Academy of Sciences. 2026;1557(1):e70254. doi:10.1111/nyas.70254"),
    ("Chen P. Knee Osteoarthritis Severity Grading Dataset. Mendeley Data. 2018; Version 1. "
     "https://doi.org/10.17632/56rmx5bjcr.1"),
    ("Nevitt MC, Felson DT, Lester G. The Osteoarthritis Initiative: protocol for the cohort study. 2006. "
     "Data available at: https://nda.nih.gov/oai/"),
    ("Shorten C, Khoshgoftaar TM. A survey on image data augmentation for deep learning. Journal of Big Data. 2019;6:60. doi:10.1186/s40537-019-0197-0"),
    ("He K, Zhang X, Ren S, Sun J. Deep residual learning for image recognition. In: Proceedings of the IEEE Conference on Computer Vision and Pattern Recognition (CVPR). 2016. p. 770–778. doi:10.1109/CVPR.2016.90"),
    ("Kim HE, Cosa-Linan A, Santhanam N, Jannesari M, Maros ME, Ganslandt T. Transfer learning for medical image classification: a literature review. BMC Medical Imaging. 2022;22:69. doi:10.1186/s12880-022-00793-7"),
    ("Buda M, Maki A, Mazurowski MA. A systematic study of the class imbalance problem in convolutional neural networks. Neural Networks. 2018;106:249–259. doi:10.1016/j.neunet.2018.07.011"),
    ("Selvaraju RR, Cogswell M, Das A, Vedantam R, Parikh D, Batra D. Grad-CAM: visual explanations from deep networks via gradient-based localization. In: Proceedings of the IEEE International Conference on Computer Vision (ICCV). 2017. p. 618–626. doi:10.1109/ICCV.2017.74"),
    ("Tejani AS, Klontzas ME, Gatti AA, Mongan JT, Moy L, Park SH, Kahn CE Jr; CLAIM 2024 Update Panel. Checklist for artificial intelligence in medical imaging (CLAIM): 2024 update. Radiology: Artificial Intelligence. 2024;6(4):e240300. doi:10.1148/ryai.240300"),
    ("Collins GS, Moons KGM, Dhiman P, Riley RD, Beam AL, Van Calster B, et al. TRIPOD+AI statement: updated guidance for reporting clinical prediction models that use regression or machine learning methods. BMJ. 2024;385:e078378. doi:10.1136/bmj-2023-078378"),
    ("Liu W, Wu M, Liu K, Wu M, Wu Y. A contrastive domain adaptation framework for knee osteoarthritis "
     "severity grading. Bioengineering. 2026;13(9):975. doi:10.3390/bioengineering13090975"),
    ("Yepez KA, Villacreses E, Almeida-Galarraga D, Landázuri K, Meneses FV, Vizcaino FP, et al. Internal "
     "validation of an uncertainty-aware coarse-from-fine deep learning framework for knee osteoarthritis "
     "severity assessment. Bioengineering. 2026;13(11):1290. doi:10.3390/bioengineering13111290"),
]

W_NS = nsdecls("w")
for i, ref in enumerate(REFS, start=1):
    p = doc.add_paragraph()
    fmt = p.paragraph_format
    fmt.left_indent = Cm(0.9)
    fmt.first_line_indent = Cm(-0.9)
    fmt.line_spacing = 1.15
    fmt.space_after = Pt(3)
    fmt.alignment = WD_ALIGN_PARAGRAPH.LEFT
    fmt.tab_stops.add_tab_stop(Cm(0.9))
    bid = 5000 + i
    p._p.append(parse_xml('<w:bookmarkStart %s w:id="%d" w:name="_Ref%08d"/>' % (W_NS, bid, i)))
    r = p.add_run("[%d]" % i); r.font.size = Pt(9.5)
    p._p.append(parse_xml('<w:bookmarkEnd %s w:id="%d"/>' % (W_NS, bid)))
    r = p.add_run("\t" + ref); r.font.size = Pt(9.5)

cp = doc.core_properties
cp.title = ("Automated Kellgren–Lawrence Grading of Knee Osteoarthritis from Plain Radiographs: "
            "Development and Internal Validation with Grad-CAM Explanations")
cp.author = "Youfan Wu"
cp.last_modified_by = "Youfan Wu"
cp.keywords = "knee osteoarthritis; Kellgren-Lawrence grading; deep learning; Grad-CAM"

doc.save(str(OUT))
print("saved", OUT, "paras", len(doc.paragraphs), "tables", len(doc.tables))
