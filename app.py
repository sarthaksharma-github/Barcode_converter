import streamlit as st
import fitz  # PyMuPDF
import numpy as np
from PIL import Image
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
import io, math, zipfile, base64

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Barcode Label Grid",
    page_icon="🏷️",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── Styling + full-page drop zone ─────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Manrope:wght@300;400;500;600;700&family=Montserrat:wght@400;500;600;700&display=swap');

*, html, body, [class*="css"] {
    font-family: 'Manrope', sans-serif;
    box-sizing: border-box;
}

/* ── App background ── */
.stApp {
    background-color: #0a0a0a;
    color: #e8e8e8;
}

/* ── Hexagon glow, fades downward ── */
.hex-bg {
    position: fixed;
    top: 0; left: 50%;
    transform: translateX(-50%);
    width: 100%; max-width: 1100px; height: 640px;
    background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='900' height='640'%3E%3Cdefs%3E%3Cpattern id='h' x='0' y='0' width='60' height='52' patternUnits='userSpaceOnUse'%3E%3Cpolygon points='30,1 59,16 59,47 30,62 1,47 1,16' fill='none' stroke='%23ffffff' stroke-width='0.6'/%3E%3C/pattern%3E%3C/defs%3E%3Crect width='900' height='640' fill='url(%23h)'/%3E%3C/svg%3E");
    background-repeat: no-repeat;
    background-position: center top;
    -webkit-mask-image: radial-gradient(ellipse 60% 55% at 50% 0%, black 0%, transparent 100%);
    mask-image: radial-gradient(ellipse 60% 55% at 50% 0%, black 0%, transparent 100%);
    pointer-events: none;
    z-index: 0;
    opacity: 0.11;
}

/* ── Full-page drop overlay ── */
.drop-overlay {
    position: fixed;
    inset: 0;
    background: rgba(10, 10, 10, 0.82);
    border: 2px dashed rgba(255, 237, 213, 0.45);
    z-index: 9999;
    display: none;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    gap: 14px;
    pointer-events: none;
    backdrop-filter: blur(6px);
}
.drop-overlay.active { display: flex; }
.drop-overlay-icon { font-size: 2.8rem; }
.drop-overlay-text {
    font-family: 'Manrope', sans-serif;
    color: #ffedd5;
    font-size: 1.05rem;
    font-weight: 500;
    letter-spacing: -0.01em;
}

/* ── Hero ── */
.hero {
    padding: 64px 24px 52px;
    text-align: center;
    max-width: 580px;
    margin: 0 auto 36px;
}
.hero h1 {
    font-family: 'Manrope', sans-serif;
    font-size: clamp(2rem, 5vw, 3.2rem);
    font-weight: 600;
    color: #ffffff;
    margin: 0 0 14px;
    letter-spacing: -0.025em;
    line-height: 1.1;
}
.hero .highlight {
    font-family: 'Montserrat', sans-serif;
    font-weight: 500;
    color: #ffedd5;
    text-transform: capitalize;
}
.hero p {
    color: #737373;
    font-size: 0.93rem;
    margin: 0 auto;
    line-height: 1.65;
}

/* ── Upload zone ── */
div[data-testid="stFileUploader"] {
    border: 1px dashed rgba(255, 237, 213, 0.22) !important;
    border-radius: 12px !important;
    background: rgba(255, 237, 213, 0.02) !important;
    transition: border-color 0.2s, background 0.2s !important;
}
div[data-testid="stFileUploader"]:hover {
    border-color: rgba(255, 237, 213, 0.42) !important;
    background: rgba(255, 237, 213, 0.04) !important;
}

/* ── Section label (data label — uppercase allowed) ── */
.section-label {
    font-size: 0.70rem;
    color: #525252;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    font-weight: 600;
    margin: 36px 0 14px;
}

/* ── Thin divider ── */
.row-divider {
    border: none;
    border-top: 1px solid rgba(255, 237, 213, 0.07);
    margin: 0;
}

/* ── Sheet count chip ── */
.sheet-chip {
    display: inline-block;
    background: rgba(255, 237, 213, 0.06);
    color: #ffedd5;
    border: 1px solid rgba(255, 237, 213, 0.18);
    border-radius: 4px;
    padding: 2px 9px;
    font-size: 0.76rem;
    font-weight: 500;
    white-space: nowrap;
}

/* ── Totals row ── */
.totals-bar {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 18px 0 22px;
    border-top: 1px solid rgba(255, 237, 213, 0.07);
    flex-wrap: wrap;
    gap: 12px;
}
.totals-text {
    font-size: 0.86rem;
    color: #525252;
}
.totals-text b { color: #e8e8e8; font-weight: 600; }

/* ── Number input ── */
div[data-testid="stNumberInput"] input {
    background: rgba(255, 255, 255, 0.04) !important;
    border: 1px solid rgba(255, 255, 255, 0.09) !important;
    border-radius: 6px !important;
    color: #e8e8e8 !important;
    font-family: 'Manrope', sans-serif !important;
    text-align: center !important;
}

/* ── Progress ── */
.stProgress > div > div > div > div {
    background: #ffffff !important;
}

/* ── Solid button — one per screen, asymmetric corners ── */
.stButton > button {
    background: #ffffff !important;
    color: #0a0a0a !important;
    border: none !important;
    border-radius: 0 !important;
    border-top-right-radius: 8px !important;
    border-bottom-left-radius: 8px !important;
    padding: 9px 28px !important;
    font-weight: 600 !important;
    font-size: 0.88rem !important;
    font-family: 'Montserrat', sans-serif !important;
    letter-spacing: -0.01em !important;
    transition: opacity 0.2s !important;
    white-space: nowrap !important;
}
.stButton > button:hover { opacity: 0.84 !important; }

/* ── Download button — outline, mirrored corners ── */
.stDownloadButton > button {
    background: transparent !important;
    color: #ffffff !important;
    border: 1px solid rgba(255, 255, 255, 0.26) !important;
    border-radius: 0 !important;
    border-top-left-radius: 8px !important;
    border-bottom-right-radius: 8px !important;
    padding: 9px 24px !important;
    font-weight: 600 !important;
    font-family: 'Montserrat', sans-serif !important;
    font-size: 0.88rem !important;
    transition: border-color 0.2s, background 0.2s !important;
}
.stDownloadButton > button:hover {
    border-color: rgba(255, 255, 255, 0.58) !important;
    background: rgba(255, 255, 255, 0.04) !important;
}

/* ── Sidebar ── */
section[data-testid="stSidebar"] {
    background: rgba(10, 10, 10, 0.98) !important;
    border-right: 1px solid rgba(255, 237, 213, 0.09) !important;
}

/* ── Hide Streamlit chrome ── */
#MainMenu, footer, header { visibility: hidden; }
.block-container {
    padding-top: 0 !important;
    padding-bottom: 48px !important;
    max-width: 820px;
    margin: 0 auto;
}
</style>

<div class="hex-bg"></div>

<div class="drop-overlay" id="dropOverlay">
  <div class="drop-overlay-icon">🏷️</div>
  <div class="drop-overlay-text">Drop your PDF anywhere</div>
</div>

<script>
(function() {
  var overlay = document.getElementById('dropOverlay');
  var counter = 0;

  document.addEventListener('dragenter', function(e) {
    counter++;
    if (overlay) overlay.classList.add('active');
  });
  document.addEventListener('dragleave', function(e) {
    counter--;
    if (counter <= 0) { counter = 0; if (overlay) overlay.classList.remove('active'); }
  });
  document.addEventListener('dragover', function(e) { e.preventDefault(); });
  document.addEventListener('drop', function(e) {
    e.preventDefault();
    counter = 0;
    if (overlay) overlay.classList.remove('active');
    var input = document.querySelector('input[type="file"]');
    if (input && e.dataTransfer.files.length > 0) {
      var dt = new DataTransfer();
      for (var i = 0; i < e.dataTransfer.files.length; i++) dt.items.add(e.dataTransfer.files[i]);
      input.files = dt.files;
      input.dispatchEvent(new Event('change', { bubbles: true }));
    }
  });
})();
</script>
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
CORNER_R   = 0.1 * PT      # rounded corner radius ~= 7.2 pt

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
            # Row 0 = topmost row -> highest y.
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

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown(
        "<div style='padding:20px 0 18px;font-size:0.70rem;text-transform:uppercase;"
        "letter-spacing:0.08em;color:#525252;font-weight:600'>Output settings</div>",
        unsafe_allow_html=True
    )
    dpi = st.slider("Render quality (DPI)", 100, 300, 200, 25,
                    help="Higher = sharper, larger file")
    content_pad_in = st.slider("Inner padding (pt)", 4, 30, int(CONTENT_PAD), 1,
                                help="Space between label edge and barcode")
    CONTENT_PAD = float(content_pad_in)

    st.markdown("<hr style='border-color:rgba(255,237,213,0.09);margin:16px 0'>",
                unsafe_allow_html=True)
    st.markdown(
        "<div style='font-size:0.70rem;text-transform:uppercase;letter-spacing:0.08em;"
        "color:#525252;font-weight:600;margin-bottom:12px'>S-15186 spec</div>",
        unsafe_allow_html=True
    )
    st.markdown("""
| | |
|---|---|
| Label | 4" × 2" |
| Grid | 2 × 5 (10 / sheet) |
| Sheet | 8.5" × 11" |
| Top margin | 0.500" |
| H gutter | 0.125" |
| V gutter | 0.000" |
""")

# ── Hero ──────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="hero">
  <h1>Barcode label <span class="highlight">grid</span></h1>
  <p>Converts a PDF of barcodes into print-ready Uline S-15186 label sheets.
     Drop your file anywhere on this page or click below to browse.</p>
</div>
""", unsafe_allow_html=True)

# ── Upload ────────────────────────────────────────────────────────────────────
uploaded = st.file_uploader(
    "Drop a PDF here or click to browse",
    type=["pdf"], label_visibility="collapsed"
)

if uploaded:
    pdf_bytes = uploaded.read()
    with st.spinner("Rendering barcodes…"):
        st.session_state.barcodes    = render_barcodes(pdf_bytes, dpi)
        st.session_state.copy_counts = {i: 10 for i in range(len(st.session_state.barcodes))}
        st.session_state.generated_pdfs = []
        st.session_state.zip_bytes      = None
    st.success(f"{len(st.session_state.barcodes)} barcodes detected.")

# ── Barcode list ──────────────────────────────────────────────────────────────
if st.session_state.barcodes:
    total = len(st.session_state.barcodes)

    st.markdown('<div class="section-label">Copies per barcode</div>', unsafe_allow_html=True)

    for i, img in enumerate(st.session_state.barcodes):
        b64   = pil_to_b64(img, max_h=56)
        n_def = st.session_state.copy_counts.get(i, 10)

        c_img, c_lbl, c_num, c_chip = st.columns([0.7, 2.2, 1.1, 1.3])
        with c_img:
            st.image(f"data:image/png;base64,{b64}", use_container_width=True)
        with c_lbl:
            st.markdown(
                f"<div style='padding-top:6px;font-size:0.86rem;color:#737373'>"
                f"Barcode {i + 1}</div>",
                unsafe_allow_html=True
            )
        with c_num:
            n = st.number_input(
                f"c{i}", min_value=1, max_value=100_000,
                value=n_def, step=1,
                label_visibility="collapsed", key=f"inp_{i}"
            )
            st.session_state.copy_counts[i] = n
        with c_chip:
            sheets = math.ceil(n / CELLS_PP)
            st.markdown(
                f"<div style='padding-top:6px'>"
                f"<span class='sheet-chip'>"
                f"{sheets} sheet{'s' if sheets != 1 else ''}"
                f"</span></div>",
                unsafe_allow_html=True
            )

        st.markdown("<hr class='row-divider'>", unsafe_allow_html=True)

    # ── Totals + Generate ─────────────────────────────────────────────────────
    total_copies = sum(st.session_state.copy_counts[i] for i in range(total))
    total_sheets = sum(math.ceil(st.session_state.copy_counts[i] / CELLS_PP) for i in range(total))

    col_txt, col_btn = st.columns([3, 1])
    with col_txt:
        st.markdown(
            f"<div class='totals-bar'>"
            f"<span class='totals-text'>"
            f"<b>{total_copies:,}</b> labels across <b>{total_sheets}</b> "
            f"sheet{'s' if total_sheets != 1 else ''}"
            f"</span></div>",
            unsafe_allow_html=True
        )
    with col_btn:
        st.markdown("<div style='padding-top:14px'>", unsafe_allow_html=True)
        generate = st.button("Generate ↗")
        st.markdown("</div>", unsafe_allow_html=True)

    if generate:
        progress = st.progress(0, text="Building…")
        pdfs = []
        for i, img in enumerate(st.session_state.barcodes):
            copies = st.session_state.copy_counts[i]
            fname  = f"barcode_{i + 1:03d}_{copies}copies.pdf"
            progress.progress(i / total, text=f"Barcode {i + 1} of {total}…")
            data = build_pdf(img, copies, dpi)
            pdfs.append((fname, data))
        progress.progress(1.0, text="Done.")
        st.session_state.generated_pdfs = pdfs
        st.session_state.zip_bytes      = make_zip(pdfs)
        progress.empty()

    # ── Download ──────────────────────────────────────────────────────────────
    if st.session_state.zip_bytes:
        st.markdown('<div class="section-label">Download</div>', unsafe_allow_html=True)

        col_dl, col_info = st.columns([2, 3])
        with col_dl:
            st.download_button(
                label="Download all PDFs",
                data=st.session_state.zip_bytes,
                file_name="S15186_barcode_grids.zip",
                mime="application/zip",
                use_container_width=True,
            )
        with col_info:
            size_kb = len(st.session_state.zip_bytes) / 1024
            st.markdown(
                f"<div style='padding-top:10px;color:#525252;font-size:0.82rem'>"
                f"{len(st.session_state.generated_pdfs)} PDFs · "
                f"{size_kb:.0f} KB · print on Uline S-15186"
                f"</div>",
                unsafe_allow_html=True
            )

        with st.expander("Individual PDFs"):
            for fname, data in st.session_state.generated_pdfs:
                sheets_f = math.ceil(
                    [st.session_state.copy_counts[i]
                     for i, (fn, _) in enumerate(st.session_state.generated_pdfs)
                     if fn == fname][0] / CELLS_PP
                )
                c1, c2, c3 = st.columns([3, 1, 1])
                with c1: st.caption(fname)
                with c2: st.caption(f"{sheets_f} sheet{'s' if sheets_f != 1 else ''}")
                with c3:
                    st.download_button("↓", data=data, file_name=fname,
                                       mime="application/pdf", key=f"dl_{fname}")

        with st.expander("Preview sheets"):
            prev_cols = st.columns(min(total, 3))
            for i, (fname, data) in enumerate(st.session_state.generated_pdfs):
                doc = fitz.open(stream=data, filetype="pdf")
                pix = doc[0].get_pixmap(matrix=fitz.Matrix(1.4, 1.4), alpha=False)
                pv  = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
                doc.close()
                with prev_cols[i % len(prev_cols)]:
                    st.image(pv, caption=fname, use_container_width=True)

else:
    if not uploaded:
        st.markdown(
            "<div style='text-align:center;color:#2a2a2a;padding:72px 0;"
            "font-size:0.86rem;font-family:Manrope,sans-serif'>"
            "or drop a PDF anywhere on this page"
            "</div>",
            unsafe_allow_html=True
        )
