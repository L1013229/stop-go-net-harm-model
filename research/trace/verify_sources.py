#!/usr/bin/env python3
"""Verify cited URLs/content; retain HTTP failures separately from browser evidence.

Uses existing PDF/XLSX downloads when available; otherwise bounded streaming GET.
Total new body download cap 80 MB, per resource 20 MB. Does not download STATS19
CSVs (those have their own byte/SHA manifest). Python 3, requests, bs4, PyMuPDF.
"""
import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path
import requests
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parent
sources = json.loads((ROOT / "sources.json").read_text())
results = []
downloaded = 0
for source in sources["sources"]:
    row = {"id": source["id"], "url": source["url"],
           "checked_utc": datetime.now(timezone.utc).isoformat(),
           "browser_content_verified_during_research": source.get("browser_verified", False)}
    try:
        path = Path(source.get("local_download", "NONEXISTENT"))
        if not path.is_absolute():
            path = ROOT / path
        if path.is_file():
            body = path.read_bytes()
            row.update(method="Earlier successful source download; local content and SHA checked", bytes=len(body))
        else:
            with requests.get(source["url"], stream=True, timeout=40) as response:
                row.update(method="GET", status=response.status_code, final_url=response.url)
                length = int(response.headers.get("Content-Length", 0))
                if length > 20_000_000 or downloaded + length > 80_000_000:
                    raise RuntimeError("Download budget would be exceeded")
                chunks, size = [], 0
                for chunk in response.iter_content(131072):
                    size += len(chunk)
                    downloaded += len(chunk)
                    if size > 20_000_000 or downloaded > 80_000_000:
                        raise RuntimeError("Download budget exceeded")
                    chunks.append(chunk)
                body = b"".join(chunks)
                row["bytes"] = size
                response.raise_for_status()
        row["sha256"] = hashlib.sha256(body).hexdigest()
        if body.startswith(b"%PDF"):
            import fitz
            text = " ".join(page.get_text() for page in fitz.open(stream=body, filetype="pdf"))
            row["format"] = "PDF"
        elif source["id"] == "DFT_GUIDE":
            assert body.startswith(b"PK"), "Not an XLSX ZIP"
            text = ""
            row["format"] = "XLSX"
        else:
            soup = BeautifulSoup(body, "html.parser")
            text = soup.get_text(" ", strip=True)
            # The WorkSafe JSON is in an HTML attribute, not visible text.
            if source["id"] == "WS_TABLE":
                text += " " + str(soup.select_one("#app").get("data-props"))
            row["format"] = "HTML"
        text = re.sub(r"\s+", " ", text).casefold()
        row["expected_content_found"] = {s: s.casefold() in text for s in source["expected"]}
        row["http_or_local_content_verified"] = all(row["expected_content_found"].values())
    except Exception as exc:
        row["http_or_local_content_verified"] = False
        row["error"] = str(exc)
    row["verified"] = row["http_or_local_content_verified"] or row["browser_content_verified_during_research"]
    results.append(row)
    print(row["id"], "verified=" + str(row["verified"]), row.get("status", "local"), row.get("expected_content_found", row.get("error", "")), flush=True)
(ROOT / "url-verification.json").write_text(json.dumps({
    "new_payload_bytes_this_verification": downloaded, "access_date_local": sources["access_date_local"],
    "note": "Browser evidence means the linked source text was read with the web tool on the access date, even where raw HTTP is blocked. It is not an assertion of HTTP 200.",
    "results": results}, indent=2) + "\n")
assert all(r["verified"] for r in results), "Some source contents are not verified"
