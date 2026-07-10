# Barcode Label Grid Converter — Uline S-15186

Generates print-ready PDFs precisely matched to the **Uline S-15186 / Avery 6527**
sticky-label sheet specification. Upload a PDF (one barcode per page), set copy
counts, and download output PDFs ready to print directly onto S-15186 label stock.

## Label Sheet Specification (S-15186 / Avery 6527)

| Dimension | Value |
|-----------|-------|
| Sheet size | 8.5" × 11" (Letter) |
| Label size | **4.000" × 2.000"** |
| Labels per sheet | **10 (2 cols × 5 rows)** |
| Top margin | 0.500" (36 pt) |
| Left margin | 0.187" (13.5 pt) |
| Horizontal gutter | 0.125" (9 pt) |
| Vertical gutter | 0.000" (labels touch) |
| Corner style | Rounded (0.1") |

## Run Locally

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Deploy to Streamlit Cloud (free)

1. Push this folder to a **public GitHub repository**
2. Go to [share.streamlit.io](https://share.streamlit.io) → **New app**
3. Select your repo → branch → `app.py`
4. Click **Deploy** ✅

No API keys or environment variables required.

## How to Use

1. **Upload** your PDF (each page = one unique barcode)
2. **Set copy counts** — each barcode shows a thumbnail; enter how many labels you need
3. Click **⚡ Generate PDFs**
4. **Download** the zip (or individual PDFs)
5. Print on Uline S-15186 label stock — set printer to **Letter, Actual Size, no scaling**

## Adjustable Settings (sidebar)

| Setting | Default | Description |
|---------|---------|-------------|
| Render DPI | 200 | Barcode image quality (higher = sharper) |
| Inner padding | 10 pt | Whitespace inside each label |

> The sheet layout (margins, label size, gutter) is **fixed** to the exact S-15186 spec
> and cannot be changed — this ensures pixel-perfect alignment on the label stock.
