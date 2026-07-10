import streamlit as st
import fitz  # PyMuPDF
import numpy as np
from PIL import Image
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
import io, math, zipfile, base64

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Barcode Label Grid — Uline S-15186",
    page_icon="🏷️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Styling ───────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

html, body, [class*="css"] { font-family: 'Inter', sans-serif; }

.stApp {
    background: linear-gradient(135deg, #0f0f1a 0%, #1a1a2e 50%, #16213e 100%);
    color: #e8e8f0;
}
.hero {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    border-radius: 16px;
    padding: 36px 40px;
    margin-bottom: 28px;
    box-shadow: 0 8px 32px rgba(102,126,234,0.35);
}
.hero h1 { color: #fff; font-size: 2rem; font-weight: 700; margin: 0 0 8px; }
.hero p  { color: rgba(255,255,255,0.82); font-size: 0.97rem; margin: 0; }
.spec-box {
    background: rgba(255,255,255,0.06);
    border: 1px solid rgba(255,255,255,0.12);
    border-radius: 12px;
    padding: 18px 22px;
    margin-bottom: 20px;
}
.spec-row { display:flex; gap:32px; flex-wrap:wrap; }
.spec-item { text-align:center; }
.spec-val  { font-size:1.4rem; font-weight:700; color:#a78bfa; }
.spec-key  { font-size:0.75rem; color:#64748b; margin-top:2px; }
.step-card {
    background: rgba(255,255,255,0.05);
    border: 1px solid rgba(255,255,255,0.10);
    border-radius: 14px;
    padding: 24px 28px;
    margin-bottom: 20px;
    backdrop-filter: blur(12px);
}
.step-title {
    font-size: 1.05rem; font-weight: 600; color: #a78bfa;
    margin-bottom: 16px; display: flex; align-items: center; gap: 10px;
}
.step-badge {
    background: linear-gradient(135deg,#667eea,#764ba2);
    color: #fff; border-radius: 50%; width:26px; height:26px;
    display:inline-flex; align-items:center; justify-content:center;
    font-size:0.75rem; font-weight:700; flex-shrink:0;
}
.pill {
    background: rgba(102,126,234,0.18); color: #a5b4fc;
    border-radius: 20px; padding: 3px 12px;
    font-size: 0.78rem; font-weight: 500; white-space: nowrap;
}
section[data-testid="stSidebar"] {
    background: rgba(15,15,26,0.95) !important;
    border-right: 1px solid rgba(255,255,255,0.08) !important;
}
div[data-testid="stNumberInput"] input {
    background: rgba(255,255,255,0.07) !important;
    border: 1px solid rgba(255,255,255,0.15) !important;
    border-radius: 8px !important; color: #e2e8f0 !important;
}
div[data-testid="stFileUploader"] {
    border: 2px dashed rgba(102,126,234,0.45) !important;
    border-radius: 12px !important;
    background: rgba(102,126,234,0.06) !important;
}
.stProgress > div > div > div > div {
    background: linear-gradient(90deg, #667eea, #764ba2) !important;
}
.stButton > button {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
    color: #fff !important; border: none !important;
    border-radius: 10px !important; padding: 10px 28px !important;
    font-weight: 600 !important; font-size: 0.95rem !important;
    transition: opacity .2s !important;
}
.stButton > button:hover { opacity: 0.88 !important; }
.stDownloadButton > button {
    background: linear-gradient(135deg, #10b981 0%, #059669 100%) !important;
    color: #fff !important; border: none !important;
    border-radius: 10px !important; padding: 10px 28px !important;
    font-weight: 600 !important;
}
</style>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
#  Uline S-15186  /  Avery 6527  —  EXACT PHYSICAL SPECIFICATIONS
#  Sheet:  8.5" × 11"  (Letter)
#  Labels: 2 columns × 5 rows = 10 per sheet
#  Label:  4.000" wide  ×  2.000" tall
#  Top margin:    0.500"   (distance from sheet top to first label top edge)
#  Left margin:   0.187"   (distance from sheet left to first label left edge)
#  H gap (gutter): 0.125"  (horizontal gap between two columns)
#  V gap (gutter): 0.000"  (vertical gap between rows — labels touch)
#  Corner radius: 0.1"    (rounded corners — cosmetic)
# ══════════════════════════════════════════════════════════════════════════════

PT = 72.0          # points per inch

# Sheet
SHEET_W   = 8.5   * PT   # 612 pt
SHEET_H   = 11.0  * PT   # 792 pt

# Label grid
COLS      = 2
ROWS      = 5
CELLS_PP  = COLS * ROWS   # 10

# Exact label dimensions (inches → points)
LABEL_W   = 4.000 * PT   # 288 pt
LABEL_H   = 2.000 * PT   # 144 pt

# Sheet margins to first label edge
MARGIN_TOP   = 0.500 * PT   # 36  pt
MARGIN_LEFT  = 0.187 * PT   # 13.5 pt

# Gaps between labels
GAP_H     = 0.125 * PT   # 9 pt  — horizontal gutter between columns
GAP_V     = 0.000 * PT   # 0 pt  — rows touch (no vertical gutter)

# Border styling (cosmetic, printed as crop marks on the label)
BORDER_PT  = 0.75          # thin border line
CORNER_R   = 0.1 * PT      # rounded corner radius ≈ 7.2 pt

# Inner content padding
CONTENT_PAD = 10.0         # pt — whitespace around barcode inside label

# Verify geometry (sanity check)
assert abs((MARGIN_LEFT * 2 + COLS * LABEL_W + (COLS - 1) * GAP_H) - SHEET_W) < 1, \
    "Horizontal geometry mismatch — check left margin / label width / gap"


# ── Helpers ───────────────────────────────────────────────────────────────────

def autocrop_white(img: Image.Image, threshold=245, margin=4) -> Image.Image:
    arr  = np.array(img.convert("L"))
    mask = arr < threshold
    rows = np.where(mask.any(axis=1))[0]
    cols = np.where(mask.any(axis=0))[0]
    if len(rows) == 0 or len(cols) == 0:
        return img
    r0 = max(rows[0]  - margin, 0);  r1 = min(rows[-1] + margin, arr.shape[0])
    c0 = max(cols[0]  - margin, 0);  c1 = min(cols[-1] + margin, arr.shape[1])
    return img.crop((c0, r0, c1, r1))


def pil_to_b64(img: Image.Image, max_h: int = 90) -> str:
    ratio = max_h / img.height
    thumb = img.resize((max(1, int(img.width * ratio)), max_h), Image.LANCZOS)
    buf   = io.BytesIO()
    thumb.save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode()


def render_barcodes(pdf_bytes: bytes, dpi: int) -> list:
    doc  = fitz.open(stream=pdf_bytes, filetype="pdf")
    mat  = fitz.Matrix(dpi / 72, dpi / 72)
    imgs = []
    for page in doc:
        pix = page.get_pixmap(matrix=mat, alpha=False)
        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
        imgs.append(autocrop_white(img))
    doc.close()
    return imgs


def draw_rounded_rect(cv, x, y, w, h, r):
    """Draw a rounded rectangle using ReportLab path commands."""
    p = cv.beginPath()
    p.moveTo(x + r, y)
    p.lineTo(x + w - r, y)
    p.curveTo(x + w - r, y,    x + w, y,       x + w, y + r)
    p.lineTo(x + w, y + h - r)
    p.curveTo(x + w, y + h - r, x + w, y + h,   x + w - r, y + h)
    p.lineTo(x + r, y + h)
    p.curveTo(x + r, y + h,    x, y + h,        x, y + h - r)
    p.lineTo(x, y + r)
    p.curveTo(x, y + r,        x, y,             x + r, y)
    p.close()
    cv.drawPath(p, stroke=1, fill=0)


def build_pdf(barcode_img: Image.Image, num_copies: int, dpi: int) -> bytes:
    """
    Build a PDF matching the Uline S-15186 / Avery 6527 physical layout.

    Each label is positioned using the exact inch-based measurements from the
    S-15186 spec.  The barcode image is scaled to fill the content area inside
    each label, preserving aspect ratio, left-aligned, top-aligned.
    """
    n_pages = math.ceil(num_copies / CELLS_PP)

    # Pre-scale barcode image to content area
    av_w = LABEL_W - 2 * CONTENT_PAD
    av_h = LABEL_H - 2 * CONTENT_PAD
    iw, ih = barcode_img.size
    scale  = min(av_w / iw, av_h / ih)
    dw, dh = iw * scale, ih * scale

    # Encode image once
    img_buf = io.BytesIO()
    barcode_img.save(img_buf, format="PNG")
    img_buf.seek(0)
    reader  = ImageReader(img_buf)

    out_buf   = io.BytesIO()
    cv        = canvas.Canvas(out_buf, pagesize=(SHEET_W, SHEET_H))
    remaining = num_copies

    for _ in range(n_pages):
        cv.setLineWidth(BORDER_PT)
        cv.setStrokeColorRGB(0, 0, 0)

        for cell_idx in range(CELLS_PP):
            row = cell_idx // COLS
            col = cell_idx  % COLS

            # ── Label origin (bottom-left in ReportLab coords) ────────────────
            # ReportLab y=0 is at page bottom.
            # Our MARGIN_TOP is measured from the sheet TOP.
            # Row 0 = topmost row → highest y.
            lx = MARGIN_LEFT + col * (LABEL_W + GAP_H)
            ly = SHEET_H - MARGIN_TOP - (row + 1) * LABEL_H - row * GAP_V

            # Draw rounded label border
            draw_rounded_rect(cv, lx, ly, LABEL_W, LABEL_H, CORNER_R)

            if remaining <= 0:
                continue

            # Barcode: left-aligned, top-aligned inside content padding
            ix = lx + CONTENT_PAD
            iy = ly + LABEL_H - CONTENT_PAD - dh

            img_buf.seek(0)
            cv.drawImage(reader, ix, iy, width=dw, height=dh,
                         preserveAspectRatio=True, anchor="nw")
            remaining -= 1

        cv.showPage()

    cv.save()
    return out_buf.getvalue()


def make_zip(pdfs: list) -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        for name, data in pdfs:
            zf.writestr(name, data)
    return buf.getvalue()


# ── Session state ─────────────────────────────────────────────────────────────
for key, default in {
    "barcodes": [], "copy_counts": {},
    "generated_pdfs": [], "zip_bytes": None,
}.items():
    if key not in st.session_state:
        st.session_state[key] = default

# ── Hero ──────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="hero">
  <h1>🏷️ Barcode Label Grid — Uline S-15186</h1>
  <p>Generates print-ready PDFs precisely matched to the
     <b>Uline S-15186 / Avery 6527</b> sticky-label sheet spec.<br>
     Upload a PDF (one barcode per page), set copies per barcode, download.</p>
</div>
""", unsafe_allow_html=True)

# ── Spec display ──────────────────────────────────────────────────────────────
st.markdown("""
<div class="spec-box">
  <div style="font-size:0.78rem;color:#64748b;font-weight:600;letter-spacing:.05em;
              text-transform:uppercase;margin-bottom:12px;">
    📐 S-15186 Physical Specifications (fixed — exact match)
  </div>
  <div class="spec-row">
    <div class="spec-item"><div class="spec-val">4" × 2"</div>
      <div class="spec-key">Label size</div></div>
    <div class="spec-item"><div class="spec-val">10</div>
      <div class="spec-key">Labels / sheet</div></div>
    <div class="spec-item"><div class="spec-val">2 × 5</div>
      <div class="spec-key">Columns × Rows</div></div>
    <div class="spec-item"><div class="spec-val">8.5" × 11"</div>
      <div class="spec-key">Sheet (Letter)</div></div>
    <div class="spec-item"><div class="spec-val">½"</div>
      <div class="spec-key">Top margin</div></div>
    <div class="spec-item"><div class="spec-val">⅛"</div>
      <div class="spec-key">H gap between cols</div></div>
    <div class="spec-item"><div class="spec-val">0"</div>
      <div class="spec-key">V gap between rows</div></div>
  </div>
</div>
""", unsafe_allow_html=True)

# ── Sidebar — DPI & padding only (layout is fixed to spec) ───────────────────
with st.sidebar:
    st.markdown("### ⚙️ Output Settings")
    st.info("📐 **Sheet layout is fixed** to the exact Uline S-15186 / Avery 6527 spec.\n\n"
            "Only image quality and content padding are adjustable.")
    dpi = st.slider("Render DPI", 100, 300, 200, 25,
                    help="Higher = sharper barcodes, larger file size")
    content_pad_in = st.slider("Inner padding (pt)", 4, 30, int(CONTENT_PAD), 1,
                                help="Whitespace between label border and barcode content")
    CONTENT_PAD = float(content_pad_in)

    st.markdown("---")
    st.markdown("#### 📐 Sheet layout (read-only)")
    st.markdown(f"""
| Dimension | Value |
|-----------|-------|
| Label W | 4.000" (288 pt) |
| Label H | 2.000" (144 pt) |
| Top margin | 0.500" (36 pt) |
| Left margin | 0.187" (13.5 pt) |
| H gutter | 0.125" (9 pt) |
| V gutter | 0.000" |
| Cols × Rows | 2 × 5 |
""")

# ── Step 1 — Upload ───────────────────────────────────────────────────────────
st.markdown("""
<div class="step-card">
  <div class="step-title"><span class="step-badge">1</span>Upload your barcode PDF</div>
</div>
""", unsafe_allow_html=True)

uploaded = st.file_uploader(
    "Each page = one unique barcode",
    type=["pdf"], label_visibility="collapsed"
)

if uploaded:
    pdf_bytes = uploaded.read()
    with st.spinner("Rendering & cropping barcodes…"):
        st.session_state.barcodes     = render_barcodes(pdf_bytes, dpi)
        st.session_state.copy_counts  = {i: 10 for i in range(len(st.session_state.barcodes))}
        st.session_state.generated_pdfs = []
        st.session_state.zip_bytes      = None
    st.success(f"✅ {len(st.session_state.barcodes)} unique barcodes detected.")

# ── Step 2 — Copy counts ──────────────────────────────────────────────────────
if st.session_state.barcodes:
    total = len(st.session_state.barcodes)

    st.markdown(f"""
    <div class="step-card">
      <div class="step-title">
        <span class="step-badge">2</span>
        Set copy counts &nbsp;
        <span style="color:#64748b;font-weight:400;font-size:0.88rem">
          ({total} barcode{"s" if total > 1 else ""} · 10 labels per sheet)
        </span>
      </div>
    </div>
    """, unsafe_allow_html=True)

    for i, img in enumerate(st.session_state.barcodes):
        b64   = pil_to_b64(img, max_h=72)
        n_def = st.session_state.copy_counts.get(i, 10)

        c_img, c_lbl, c_num, c_hint = st.columns([1.2, 2.5, 1.8, 1.8])
        with c_img:
            st.image(f"data:image/png;base64,{b64}", use_container_width=True)
        with c_lbl:
            st.markdown(
                f"<div style='padding-top:10px'>"
                f"<b style='color:#e2e8f0;font-size:0.95rem'>Barcode {i+1}</b>"
                f"<br/><span style='color:#64748b;font-size:0.78rem'>Page {i+1} of source PDF</span>"
                f"</div>",
                unsafe_allow_html=True
            )
        with c_num:
            n = st.number_input(
                f"copies_{i}", min_value=1, max_value=100_000,
                value=n_def, step=1,
                label_visibility="collapsed", key=f"inp_{i}"
            )
            st.session_state.copy_counts[i] = n
        with c_hint:
            sheets = math.ceil(n / CELLS_PP)
            st.markdown(
                f"<div style='padding-top:10px'>"
                f"<span class='pill'>→ {n} labels · {sheets} sheet{'s' if sheets!=1 else ''}</span>"
                f"</div>",
                unsafe_allow_html=True
            )

    # Totals
    total_copies = sum(st.session_state.copy_counts[i] for i in range(total))
    total_sheets  = sum(math.ceil(st.session_state.copy_counts[i] / CELLS_PP) for i in range(total))
    st.markdown(
        f"<div style='color:#64748b;font-size:0.85rem;margin:6px 0 20px'>"
        f"📊 Total: <b style='color:#a5b4fc'>{total_copies:,} labels</b> across "
        f"<b style='color:#a5b4fc'>{total_sheets} sheet{'s' if total_sheets!=1 else ''}</b> "
        f"({total} PDF file{'s' if total>1 else ''})"
        f"</div>",
        unsafe_allow_html=True
    )

    # ── Step 3 — Generate ─────────────────────────────────────────────────────
    st.markdown("""
    <div class="step-card">
      <div class="step-title"><span class="step-badge">3</span>Generate & Download</div>
    </div>
    """, unsafe_allow_html=True)

    if st.button("⚡ Generate PDFs", use_container_width=False):
        progress = st.progress(0, text="Starting…")
        pdfs     = []

        for i, img in enumerate(st.session_state.barcodes):
            copies = st.session_state.copy_counts[i]
            fname  = f"S15186_barcode_{i+1:03d}_{copies}copies.pdf"
            progress.progress(i / total, text=f"Building {fname}…")
            data   = build_pdf(img, copies, dpi)
            pdfs.append((fname, data))

        progress.progress(1.0, text="Zipping…")
        st.session_state.generated_pdfs = pdfs
        st.session_state.zip_bytes      = make_zip(pdfs)
        progress.empty()
        st.success(f"✅ {total} PDF(s) ready — {total_sheets} sheet(s) total.")

    # ── Download ──────────────────────────────────────────────────────────────
    if st.session_state.zip_bytes:
        st.markdown("---")
        col_dl, col_info = st.columns([2, 3])
        with col_dl:
            st.download_button(
                label="⬇️  Download All PDFs (zip)",
                data=st.session_state.zip_bytes,
                file_name="S15186_barcode_grids.zip",
                mime="application/zip",
                use_container_width=True,
            )
        with col_info:
            size_kb = len(st.session_state.zip_bytes) / 1024
            st.markdown(
                f"<div style='padding-top:12px;color:#64748b;font-size:0.85rem'>"
                f"📦 <b style='color:#e2e8f0'>{len(st.session_state.generated_pdfs)} PDFs</b>"
                f" · {size_kb:.0f} KB · {total_sheets} total sheet(s) · "
                f"Print on <b style='color:#a5b4fc'>Uline S-15186</b> label stock"
                f"</div>",
                unsafe_allow_html=True
            )

        # Per-file downloads
        with st.expander("📄 Download individual PDFs"):
            for fname, data in st.session_state.generated_pdfs:
                sheets_f = math.ceil(
                    [st.session_state.copy_counts[i]
                     for i, (fn, _) in enumerate(st.session_state.generated_pdfs)
                     if fn == fname][0] / CELLS_PP
                )
                c1, c2, c3 = st.columns([3, 1, 1])
                with c1: st.caption(fname)
                with c2: st.caption(f"{sheets_f} sheet(s)")
                with c3:
                    st.download_button("⬇️", data=data, file_name=fname,
                                       mime="application/pdf", key=f"dl_{fname}")

        # Preview
        with st.expander("🔍 Preview first sheet of each output"):
            prev_cols = st.columns(min(total, 3))
            for i, (fname, data) in enumerate(st.session_state.generated_pdfs):
                doc = fitz.open(stream=data, filetype="pdf")
                pix = doc[0].get_pixmap(matrix=fitz.Matrix(1.4, 1.4), alpha=False)
                pv  = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
                doc.close()
                with prev_cols[i % len(prev_cols)]:
                    st.image(pv, caption=fname, use_container_width=True)

else:
    st.markdown(
        "<div style='text-align:center;color:#475569;padding:48px 0;font-size:0.95rem;'>"
        "⬆️  Upload a PDF above to get started."
        "</div>",
        unsafe_allow_html=True
    )
