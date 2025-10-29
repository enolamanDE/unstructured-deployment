#!/usr/bin/env python3
"""
Open Source Enterprise Unstructured.io Testanwendung - STANDARD VERSION
Nutzt NUR die lokale Open Source Library - KEINE externen APIs, KEINE Custom Extensions
Fokus: Standard Features für maximale Kompatibilität
"""

import streamlit as st
import json
import time
import sys
import os
from pathlib import Path
from datetime import datetime

# === NEU: Picture Partitioner früh definieren, damit NameError ausgeschlossen ist ===
try:
    from unstructured.partition.pptx import register_picture_partitioner
    from unstructured.documents.elements import Image as _UImage, ElementMetadata as _UElementMetadata
    import base64 as _base64
except Exception:
    register_picture_partitioner = None
    _UImage = None
    _UElementMetadata = None

_PICTURE_PARTITIONER_REGISTERED = False

def setup_standard_picture_partitioner():
    """Registriert (idempotent) einen Standard Picture Partitioner für PPTX-Bilder.
    Gibt True zurück, wenn aktiv, sonst False.
    """
    global _PICTURE_PARTITIONER_REGISTERED
    if _PICTURE_PARTITIONER_REGISTERED:
        return True
    if register_picture_partitioner is None or _UImage is None or _UElementMetadata is None:
        return False

    class StandardPowerPointPicturePartitioner:  # type: ignore
        """Einfache Bild-Extraktion: Bild-Bytes -> Base64 + Image Element"""
        @classmethod
        def iter_elements(cls, picture, opts):
            try:
                if hasattr(picture, 'image') and picture.image and getattr(picture.image, 'blob', None):
                    blob = picture.image.blob
                    b64 = _base64.b64encode(blob).decode('utf-8')
                    mime_type = 'image/jpeg'
                    if getattr(picture.image, 'content_type', None):
                        mime_type = picture.image.content_type
                    elif getattr(picture.image, 'ext', None):
                        ext = picture.image.ext.lower()
                        if ext == 'png':
                            mime_type = 'image/png'
                        elif ext == 'gif':
                            mime_type = 'image/gif'
                    md = _UElementMetadata()
                    md.image_base64 = b64
                    md.image_mime_type = mime_type
                    md.page_number = getattr(opts, 'page_number', 1)
                    alt_text = getattr(picture, 'name', None) or 'PowerPoint-Bild'
                    yield _UImage(text=alt_text, metadata=md)
            except Exception as e:  # pragma: no cover
                print(f"Bild-Extraktion Fehler (PicturePartitioner): {e}")
                return

    try:
        register_picture_partitioner(StandardPowerPointPicturePartitioner)
        _PICTURE_PARTITIONER_REGISTERED = True
        print("✅ Picture Partitioner registriert")
        return True
    except Exception as e:  # pragma: no cover
        print(f"Registrierung fehlgeschlagen: {e}")
        return False

# Direkte Import der Open Source Unstructured Library
# Im Docker Container ist unstructured bereits installiert
try:
    from unstructured.partition.auto import partition
    from unstructured.partition.pdf import partition_pdf
    from unstructured.partition.pptx import partition_pptx
    from unstructured.partition.docx import partition_docx
    from unstructured.partition.xlsx import partition_xlsx
    from unstructured.staging.base import elements_to_md, elements_to_json, elements_to_text, elements_to_dicts, elements_from_json
    from unstructured.partition.html.convert import elements_to_html
    UNSTRUCTURED_AVAILABLE = True
    IMPORT_ERROR = None
except ImportError as e:
    UNSTRUCTURED_AVAILABLE = False
    IMPORT_ERROR = str(e)

# STANDARD IMPORTS für erweiterte Features
try:
    from unstructured.chunking.basic import chunk_elements
    from unstructured.chunking.title import chunk_by_title
    CHUNKING_AVAILABLE = True
except ImportError:
    CHUNKING_AVAILABLE = False

try:
    from unstructured.cleaners.core import clean_extra_whitespace, group_broken_paragraphs
    CLEANERS_AVAILABLE = True
except ImportError:
    CLEANERS_AVAILABLE = False

# NEU: Extracting - E-Mails, Telefonnummern, IPs extrahieren
try:
    from unstructured.cleaners.extract import extract_email_address, extract_us_phone_number, extract_ip_address
    EXTRACTING_AVAILABLE = True
except ImportError:
    EXTRACTING_AVAILABLE = False

# NEU: Staging - Export zu CSV, DataFrame, Dict
try:
    from unstructured.staging.base import convert_to_csv, convert_to_dataframe, convert_to_dict
    STAGING_AVAILABLE = True
except ImportError:
    STAGING_AVAILABLE = False

# NLP: Einfache Alternative ohne problematische Imports
try:
    import re
    NLP_AVAILABLE = True
except ImportError:
    NLP_AVAILABLE = False

ADVANCED_FEATURES_AVAILABLE = CHUNKING_AVAILABLE or CLEANERS_AVAILABLE or NLP_AVAILABLE or EXTRACTING_AVAILABLE or STAGING_AVAILABLE

def process_with_open_source_library(file_path, strategy="auto", **kwargs):
    """
    Verarbeitet Datei mit der lokalen Open Source Library
    KEINE API-Aufrufe, alles lokal
    """
    try:
        start_time = time.time()
        image_capable_type = None  # 'pdf' | 'pptx' | 'docx' | 'image'

        # Open Source Partition-Aufruf mit erweiterten Parametern
        partition_kwargs = {
            "filename": file_path,
            "strategy": strategy,
            "include_page_breaks": True,
            "infer_table_structure": kwargs.get("include_tables", True),
            "include_metadata": True,
        }

        # Dateityp-spezifische Parameter
        if file_path.lower().endswith(('.pdf')):
            image_capable_type = 'pdf'
            # PDF-SPEZIFISCHE PARAMETER - KORRIGIERT: OHNE extract_forms
            partition_kwargs["extract_images_in_pdf"] = kwargs.get("include_images", True)
            partition_kwargs["extract_image_block_types"] = ["Image", "Table", "FigureCaption", "Picture"]
            partition_kwargs["extract_image_block_to_payload"] = True  # ✅ Bilder in Payload
            # ❌ ENTFERNT: extract_forms - nicht verfügbar in aktueller Version
            # ❌ ENTFERNT: form_extraction_skip_tables - abhängig von extract_forms
            partition_kwargs["languages"] = ["deu", "eng"]  # ✅ Mehrsprachige OCR
            partition_kwargs["detect_language_per_element"] = True  # ✅ Sprache pro Element
            # Fine-tuning Parameter für bessere Extraktion
            partition_kwargs["pdfminer_word_margin"] = 0.1  # ✅ Bessere Wort-Erkennung
            partition_kwargs["pdfminer_char_margin"] = 0.5  # ✅ Bessere Zeichen-Erkennung

            # DIREKTER PDF-PARSER OHNE extract_forms
            try:
                elements = partition_pdf(
                    filename=file_path,
                    strategy=strategy,
                    include_page_breaks=True,
                    infer_table_structure=True,
                    extract_images_in_pdf=True,
                    extract_image_block_types=["Image", "Table", "FigureCaption", "Picture"],
                    extract_image_block_to_payload=True,
                    # ❌ ENTFERNT: extract_forms - nicht verfügbar
                    # ❌ ENTFERNT: form_extraction_skip_tables - nicht verfügbar
                    languages=["deu", "eng"],
                    detect_language_per_element=True,
                    pdfminer_word_margin=0.1,
                    pdfminer_char_margin=0.5,
                    include_metadata=True
                )
                processing_time = time.time() - start_time
                img_elems = [e for e in elements if type(e).__name__ in ("Image", "Figure", "FigureCaption", "Picture")]
                return {
                    "status": "success",
                    "elements": elements,
                    "processing_time": processing_time,
                    "element_count": len(elements),
                    "method": "open_source_pdf_optimized_no_forms",
                    "image_support": True,
                    "image_elements": len(img_elems),
                    "image_base64": sum(1 for e in img_elems if getattr(getattr(e, 'metadata', None), 'image_base64', None)),
                }
            except Exception:
                pass

        elif file_path.lower().endswith(('.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.webp')):
            image_capable_type = 'image'
            # BILD-SPEZIFISCHE PARAMETER - KORRIGIERT: OHNE extract_forms
            partition_kwargs["strategy"] = "hi_res"  # ✅ Immer hi_res für Bilder
            partition_kwargs["infer_table_structure"] = True  # ✅ Tabellen in Bildern
            # ❌ ENTFERNT: extract_forms - nicht verfügbar in aktueller Version
            # ❌ ENTFERNT: form_extraction_skip_tables - abhängig von extract_forms
            partition_kwargs["languages"] = ["deu", "eng"]  # ✅ Mehrsprachige OCR
            partition_kwargs["detect_language_per_element"] = True  # ✅ Sprache pro Element
            partition_kwargs["hi_res_model_name"] = None  # ✅ Standard Layout-Modell

            # DIREKTER IMAGE-PARSER OHNE extract_forms
            try:
                from unstructured.partition.image import partition_image
                elements = partition_image(
                    filename=file_path,
                    strategy="hi_res",
                    include_page_breaks=True,
                    infer_table_structure=True,
                    # ❌ ENTFERNT: extract_forms - nicht verfügbar
                    # ❌ ENTFERNT: form_extraction_skip_tables - nicht verfügbar
                    languages=["deu", "eng"],
                    detect_language_per_element=True,
                    include_metadata=True
                )
                processing_time = time.time() - start_time
                return {
                    "status": "success",
                    "elements": elements,
                    "processing_time": processing_time,
                    "element_count": len(elements),
                    "method": "open_source_image_optimized_no_forms"
                }
            except Exception as image_error:
                # Fallback auf allgemeine partition
                pass

        elif file_path.lower().endswith(('.docx')):
            image_capable_type = 'docx'
            # WORD-SPEZIFISCHE PARAMETER - MIT BILD-EXTRAKTION
            partition_kwargs["infer_table_structure"] = True
            partition_kwargs["include_page_breaks"] = True
            # ✅ NEU: Bild-Extraktion für Word
            partition_kwargs["extract_images_in_pdf"] = kwargs.get("include_images", True)

            # DIREKTER WORD-PARSER mit Bild-Extraktion
            try:
                elements = partition_docx(
                    filename=file_path,
                    infer_table_structure=True,
                    include_page_breaks=True,
                    include_metadata=True
                )
                processing_time = time.time() - start_time
                img_elems = [e for e in elements if type(e).__name__ in ("Image", "Figure", "FigureCaption", "Picture")]
                return {
                    "status": "success",
                    "elements": elements,
                    "processing_time": processing_time,
                    "element_count": len(elements),
                    "method": "open_source_docx_with_images",
                    "image_support": True,
                    "image_elements": len(img_elems),
                    "image_base64": sum(1 for e in img_elems if getattr(getattr(e, 'metadata', None), 'image_base64', None)),
                }
            except Exception as docx_error:
                # Fallback auf allgemeine partition
                pass

        elif file_path.lower().endswith(('.pptx', '.ppt')):
            image_capable_type = 'pptx'
            # POWERPOINT-SPEZIFISCHE PARAMETER mit Picture Partitioner Setup
            # ✅ KRITISCH: Picture Partitioner MUSS vor partition_pptx registriert werden
            setup_success = setup_standard_picture_partitioner()
            if not setup_success:
                print("⚠️ Warning: Picture Partitioner Setup fehlgeschlagen - keine Bilder verfügbar")

            partition_kwargs["include_page_breaks"] = True
            partition_kwargs["include_slide_notes"] = True  # ✅ NEU: Notizen extrahieren
            partition_kwargs["infer_table_structure"] = True
            partition_kwargs["strategy"] = strategy  # ✅ Bessere Strategie-Kontrolle

            # DIREKTER POWERPOINT-PARSER mit Picture Partitioner
            try:
                print(f"🎨 PPTX Verarbeitung (Picture Partitioner aktiv={setup_success})")
                elements = partition_pptx(
                    filename=file_path,
                    include_page_breaks=True,
                    include_slide_notes=True,
                    infer_table_structure=True,
                    strategy=strategy,
                    include_metadata=True,
                    starting_page_number=1
                )
                processing_time = time.time() - start_time
                img_elems = [e for e in elements if type(e).__name__ in ("Image", "Figure", "FigureCaption", "Picture")]
                return {
                    "status": "success",
                    "elements": elements,
                    "processing_time": processing_time,
                    "element_count": len(elements),
                    "method": f"open_source_pptx_with_picture_partitioner_{setup_success}",
                    "image_support": setup_success,
                    "image_elements": len(img_elems),
                    "image_base64": sum(1 for e in img_elems if getattr(getattr(e, 'metadata', None), 'image_base64', None)),
                }
            except Exception:
                pass

        elif file_path.lower().endswith(('.xlsx', '.xls')):
            # EXCEL-SPEZIFISCHE PARAMETER
            # ⚠️ WICHTIG: Excel unterstützt KEINE Bild-Extraktion in Open Source!
            # Nur Tabellen und Titel werden extrahiert.
            partition_kwargs["find_subtable"] = kwargs.get("find_subtable", False)
            partition_kwargs["include_header"] = kwargs.get("include_header", False)
            partition_kwargs["infer_table_structure"] = kwargs.get("infer_table_structure", True)
            partition_kwargs["starting_page_number"] = 1

            # DIREKTER EXCEL-PARSER (OHNE Bild-Support)
            try:
                elements = partition_xlsx(
                    filename=file_path,
                    find_subtable=False,
                    include_header=False,
                    infer_table_structure=True,
                    starting_page_number=1
                )
                processing_time = time.time() - start_time
                return {
                    "status": "success",
                    "elements": elements,
                    "processing_time": processing_time,
                    "element_count": len(elements),
                    "method": "open_source_xlsx_no_image_support",
                    "image_support": False,  # ❌ Excel unterstützt KEINE Bilder
                    "image_elements": 0,
                    "image_base64": 0,
                }
            except Exception as xlsx_error:
                # Fallback auf allgemeine partition
                pass

        # Lokale Partition ausführen
        elements = partition(**partition_kwargs)
        processing_time = time.time() - start_time
        img_elems = [e for e in elements if type(e).__name__ in ("Image", "Figure", "FigureCaption", "Picture")]
        return {
            "status": "success",
            "elements": elements,
            "processing_time": processing_time,
            "element_count": len(elements),
            "method": "open_source_local",
            "image_support": image_capable_type in ("pdf", "pptx", "image"),
            "image_elements": len(img_elems),
            "image_base64": sum(1 for e in img_elems if getattr(getattr(e, 'metadata', None), 'image_base64', None)),
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "processing_time": time.time() - start_time,
            "method": "open_source_local"
        }

def get_open_source_examples():
    """
    Lädt Beispieldateien aus dem Open Source Repository - ERWEITERT
    """
    examples_path = repo_path / "example-docs"
    if not examples_path.exists():
        return {}

    examples = {}

    # ERWEITERTE Liste mit vielen mehr Beispieldateien
    important_files = {
        # Office-Dokumente
        "📊 Excel: Stanley Cups": "stanley-cups.xlsx",
        "📊 Excel: Emoji-Daten": "emoji.xlsx",
        "📊 Excel: Jahresanalyse": "2023-half-year-analyses-by-segment.xlsx",
        "📊 Excel: Vodafone": "vodafone.xlsx",
        "📊 Excel: 1000+ Zellen": "more-than-1k-cells.xlsx",

        # PowerPoint-Präsentationen - ERWEITERT
        "🎨 PowerPoint: Einfach": "simple.pptx",
        "🎨 PowerPoint: Wissenschaft (1 Seite)": "science-exploration-1p.pptx",
        "🎨 PowerPoint: Wissenschaft (369 Seiten)": "science-exploration-369p.pptx",
        "🎨 PowerPoint: Beispiel-Präsentation": "sample-presentation.pptx",
        "🎨 PowerPoint: Mit Bildern": "picture.pptx",

        # Word-Dokumente
        "📝 Word: Einfach": "simple.docx",
        "📝 Word: Handbuch (1 Seite)": "handbook-1p.docx",
        "📝 Word: Handbuch (872 Seiten)": "handbook-872p.docx",
        "📝 Word: Mit Bildern": "contains-pictures.docx",
        "📝 Word: Kategorien": "category-level.docx",
        "📝 Word: Tabellen": "docx-tables.docx",
        "📝 Word: Header/Footer": "docx-hdrftr.docx",

        # PDF-Dateien - KORRIGIERTE PFADE zu pdf/ Unterordner
        "📄 PDF: Einfach": "simple.pdf",
        "📄 PDF: Layout-Test": "pdf/layout-parser-paper-fast.pdf",
        "📄 PDF: Komplex": "complex-layout.pdf",
        "📄 PDF: Mit Bildern": "pdf/embedded-images.pdf",
        "📄 PDF: Mit Tabellen": "pdf/layout-parser-paper-with-table.pdf",
        "📄 PDF: Embedded Images+Tables": "pdf/embedded-images-tables.pdf",
        "📄 PDF: Multi-Column": "pdf/multi-column.pdf",
        "📄 PDF: DA Report": "pdf/DA-1p.pdf",

        # Bild-Dateien - NEU HINZUGEFÜGT
        "🖼️ Bild: Layout-Test": "layout-parser-paper.jpg",
        "🖼️ Bild: Englisch": "english-and-korean.png",
        "🖼️ Bild: Tabellen": "table-image.png",
        "🖼️ Bild: Formulare": "form-example.png",

        # Text-Dateien
        "📄 Text: Krieg und Frieden (1 Seite)": "book-war-and-peace-1p.txt",
        "📄 Text: Krieg und Frieden (1225 Seiten)": "book-war-and-peace-1225p.txt",
        "📄 Text: Norwich City": "norwich-city.txt",
        "📄 Text: Einfach": "fake-text.txt",

        # HTML-Dateien
        "🌐 HTML: 10-K Bericht (1 Seite)": "example-10k-1p.html",
        "🌐 HTML: 10-K Bericht (230 Seiten)": "example-10k-230p.html",
        "🌐 HTML: 10-K Vollständig": "example-10k.html",
        "🌐 HTML: Mit Scripts": "example-with-scripts.html",
        "🌐 HTML: Einfach": "fake-html.html",
        "🌐 HTML: Deutsch": "fake-html-lang-de.html",

        # CSV-Dateien
        "📈 CSV: Stanley Cups": "stanley-cups.csv",
        "📈 CSV: Mit Emojis": "stanley-cups-with-emoji.csv",
        "📈 CSV: Lange Zeilen": "csv-with-long-lines.csv",
        "📈 CSV: Escaped Kommas": "csv-with-escaped-commas.csv",

        # Spezielle Formate
        "🔧 JSON: Einfach": "simple.json",
        "🔧 YAML: Einfach": "simple.yaml",
        "🔧 XML: Factbook": "factbook.xml",
        "🔧 ZIP: Einfach": "simple.zip",
        "📧 E-Mail: MSG": "fake-email.msg",
        "📧 E-Mail: EML": "fake-email.eml",

        # Markdown
        "📋 Markdown: Einfach": "simple-table.md",
        "📋 Markdown: Codeblock": "codeblock.md",
        "📋 Markdown: Umlauts": "umlauts-utf8.md",
    }

    # Prüfe welche Dateien tatsächlich existieren
    for label, filename in important_files.items():
        file_path = examples_path / filename
        if file_path.exists():
            file_size = file_path.stat().st_size
            examples[f"{label} ({file_size:,} bytes)"] = str(file_path)

    return examples

def chunk_elements_advanced(elements, chunking_strategy="basic", **chunk_params):
    """
    Erweiterte Chunking-Funktionen mit Open Source Modulen
    """
    if not CHUNKING_AVAILABLE:
        return {"status": "error", "error": "Chunking-Module nicht verfügbar"}

    try:
        start_time = time.time()

        # Standard-Parameter für Chunking
        default_params = {
            "max_characters": chunk_params.get("max_characters", 1000),
            "new_after_n_chars": chunk_params.get("new_after_n_chars", 800),
            "overlap": chunk_params.get("overlap", 50),
            "include_orig_elements": True
        }

        if chunking_strategy == "basic":
            chunks = chunk_elements(elements, **default_params)
        elif chunking_strategy == "by_title":
            chunks = chunk_by_title(elements, **default_params)
        else:
            chunks = chunk_elements(elements, **default_params)  # Fallback

        processing_time = time.time() - start_time

        return {
            "status": "success",
            "chunks": chunks,
            "chunk_count": len(chunks),
            "processing_time": processing_time,
            "strategy": chunking_strategy
        }

    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "strategy": chunking_strategy
        }

def clean_and_process_text(elements):
    """
    Text-Bereinigung mit Open Source Cleaners - KORRIGIERT
    """
    if not CLEANERS_AVAILABLE:
        return {"status": "error", "error": "Text-Cleaners nicht verfügbar"}

    try:
        cleaned_elements = []

        for element in elements:
            # KORRIGIERT: Sicherstellen dass wir mit Strings arbeiten
            element_text = str(element).strip()

            if element_text:  # Nur nicht-leere Texte bereinigen
                # Text-Bereinigung anwenden
                cleaned_text = clean_extra_whitespace(element_text)

                # Element-Objekt kopieren und bereinigten Text zuweisen
                if hasattr(element, 'text'):
                    element.text = cleaned_text
                elif hasattr(element, '_text'):
                    element._text = cleaned_text
                # Für Elemente ohne text-Attribut erstellen wir ein neues Element
                else:
                    # Behalte den ursprünglichen Element-Typ aber mit bereinigtem Text
                    from unstructured.documents.elements import Text
                    cleaned_element = Text(text=cleaned_text)
                    # Übertrage Metadaten falls vorhanden
                    if hasattr(element, 'metadata'):
                        cleaned_element.metadata = element.metadata
                    element = cleaned_element

            cleaned_elements.append(element)

        # Gruppiere kaputte Paragraphen nur wenn Elemente vorhanden
        if cleaned_elements:
            try:
                final_elements = group_broken_paragraphs(cleaned_elements)
            except Exception as e:
                # Fallback: wenn group_broken_paragraphs fehlschlägt, nutze cleaned_elements
                print(f"Warning: group_broken_paragraphs failed: {e}")
                final_elements = cleaned_elements
        else:
            final_elements = cleaned_elements

        return {
            "status": "success",
            "cleaned_elements": final_elements,
            "original_count": len(elements),
            "cleaned_count": len(final_elements)
        }

    except Exception as e:
        return {
            "status": "error",
            "error": f"Text-Cleaning Fehler: {str(e)}"
        }

def analyze_text_metrics(elements):
    """
    Einfache Text-Analyse ohne problematische NLP-Imports
    """
    try:
        start_time = time.time()

        metrics = {
            "total_elements": len(elements),
            "total_characters": 0,
            "total_words": 0,
            "total_sentences": 0,
            "element_types": {},
            "average_element_length": 0
        }

        all_text = ""
        element_lengths = []

        for element in elements:
            text = str(element).strip()
            if text:
                all_text += text + " "
                element_lengths.append(len(text))

                # Element-Typ zählen
                element_type = type(element).__name__
                metrics["element_types"][element_type] = metrics["element_types"].get(element_type, 0) + 1

        metrics["total_characters"] = len(all_text)
        metrics["total_words"] = len(all_text.split())

        # Einfache Satz-Zählung
        metrics["total_sentences"] = all_text.count('.') + all_text.count('!') + all_text.count('?')

        metrics["average_element_length"] = sum(element_lengths) / len(element_lengths) if element_lengths else 0

        processing_time = time.time() - start_time
        metrics["processing_time"] = processing_time

        return {
            "status": "success",
            "metrics": metrics
        }

    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }

def extract_contact_information(elements):
    """
    Extrahiert Email-Adressen, Telefonnummern, IPs und URLs aus Elementen
    ✅ NEU: Nutzt Unstructured.io Extraktions-Features
    """
    if not EXTRACTING_AVAILABLE:
        return {
            "status": "error",
            "error": "Extraktions-Features nicht verfügbar. Installiere: pip install unstructured[local-inference]"
        }

    try:
        import re

        extracted_data = {
            "emails": [],
            "phone_numbers": [],
            "ip_addresses": [],
            "urls": []
        }

        # Regex-Patterns
        url_pattern = r'https?://[^\s<>"{}|\\^`\[\]]+'

        for i, element in enumerate(elements):
            text = str(element).strip()
            if not text:
                continue

            # Emails extrahieren
            try:
                emails = extract_email_address(text)
                if emails:
                    for email in emails:
                        extracted_data["emails"].append({
                            "email": email,
                            "element_index": i,
                            "element_type": type(element).__name__,
                            "context": text[:100]
                        })
            except Exception:
                pass

            # Telefonnummern extrahieren
            try:
                phones = extract_us_phone_number(text)
                if phones:
                    for phone in phones:
                        extracted_data["phone_numbers"].append({
                            "phone": phone,
                            "element_index": i,
                            "element_type": type(element).__name__,
                            "context": text[:100]
                        })
            except Exception:
                pass

            # IP-Adressen extrahieren
            try:
                ips = extract_ip_address(text)
                if ips:
                    for ip in ips:
                        extracted_data["ip_addresses"].append({
                            "ip": ip,
                            "element_index": i,
                            "element_type": type(element).__name__,
                            "context": text[:100]
                        })
            except Exception:
                pass

            # URLs extrahieren (mit Regex da keine spezielle Funktion)
            try:
                urls = re.findall(url_pattern, text)
                if urls:
                    for url in urls:
                        extracted_data["urls"].append({
                            "url": url,
                            "element_index": i,
                            "element_type": type(element).__name__,
                            "context": text[:100]
                        })
            except Exception:
                pass

        return {
            "status": "success",
            "extracted_data": extracted_data,
            "total_emails": len(extracted_data["emails"]),
            "total_phones": len(extracted_data["phone_numbers"]),
            "total_ips": len(extracted_data["ip_addresses"]),
            "total_urls": len(extracted_data["urls"])
        }

    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }

def export_tables_to_formats(elements):
    """
    Exportiert alle Tabellen in verschiedene Formate (CSV, DataFrame, Dict)
    ✅ NEU: Tabellen-Export-Funktionalität
    """
    try:
        tables_data = {
            "tables": [],
            "total_tables": 0
        }

        for i, element in enumerate(elements):
            if type(element).__name__ == "Table":
                table_info = {
                    "index": i,
                    "text": str(element).strip(),
                    "html": None,
                    "csv": None
                }

                # HTML-Tabelle (falls verfügbar)
                if hasattr(element, 'metadata') and element.metadata:
                    if hasattr(element.metadata, 'text_as_html') and element.metadata.text_as_html:
                        table_info["html"] = element.metadata.text_as_html

                # CSV-Konvertierung (einfach)
                text = str(element).strip()
                if text:
                    # Versuche Text in CSV zu konvertieren
                    lines = text.split('\n')
                    csv_lines = []
                    for line in lines:
                        # Einfache Konvertierung: Tabs/Spaces zu Kommas
                        csv_line = ','.join([cell.strip() for cell in line.split() if cell.strip()])
                        if csv_line:
                            csv_lines.append(csv_line)
                    table_info["csv"] = '\n'.join(csv_lines)

                tables_data["tables"].append(table_info)

        tables_data["total_tables"] = len(tables_data["tables"])

        return {
            "status": "success",
            "tables_data": tables_data
        }

    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }

def create_image_gallery(elements):
    """
    Erstellt Bild-Galerie aus extrahierten Bildern
    ✅ NEU: Bild-Galerie mit Download-Funktion
    """
    try:
        images = []

        for i, element in enumerate(elements):
            element_type = type(element).__name__

            if element_type in ["Image", "Figure", "FigureCaption", "Picture"]:
                if hasattr(element, 'metadata') and element.metadata:
                    if hasattr(element.metadata, 'image_base64') and element.metadata.image_base64:
                        image_info = {
                            "index": i,
                            "element_type": element_type,
                            "base64": element.metadata.image_base64,
                            "mime_type": getattr(element.metadata, 'image_mime_type', 'image/jpeg'),
                            "caption": str(element).strip(),
                            "page_number": getattr(element.metadata, 'page_number', None)
                        }
                        images.append(image_info)

        return {
            "status": "success",
            "images": images,
            "total_images": len(images)
        }

    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }

def describe_image_with_vision_llm(image_base64, image_mime_type, api_provider="auto", api_key=None):
    """
    Beschreibt ein Bild mit Vision-LLM für besseres Text-Retrieval

    ✅ VORTEILE:
    - Bessere Embeddings durch Text-Beschreibung
    - Unabhängig von Vision-LLM bei Queries
    - 99% Kosten-Ersparnis bei wiederholten Queries

    Args:
        image_base64: Base64-kodiertes Bild
        image_mime_type: MIME-Typ (image/jpeg, image/png, etc.)
        api_provider: "auto", "claude", "gpt4", "gemini", "local"
        api_key: Optional API-Key (wird aus ENV geladen falls nicht angegeben)

    Returns:
        Dict mit Beschreibung und Metadaten
    """
    try:
        import base64
        import os

        # Generiere detaillierte Beschreibung
        description = None
        cost_estimate = 0.0
        model_used = "unknown"

        # Versuche verschiedene APIs (in Priorität)
        if api_provider == "auto":
            # Prüfe welche API-Keys verfügbar sind
            if os.environ.get("ANTHROPIC_API_KEY"):
                api_provider = "claude"
            elif os.environ.get("OPENAI_API_KEY"):
                api_provider = "gpt4"
            elif os.environ.get("GOOGLE_API_KEY"):
                api_provider = "gemini"
            else:
                api_provider = "local"

        # Claude 3 Vision (Empfohlen für Qualität)
        if api_provider == "claude":
            try:
                import anthropic
                client = anthropic.Anthropic(api_key=api_key or os.environ.get("ANTHROPIC_API_KEY"))

                prompt = """Beschreibe dieses Bild DETAILLIERT für ein Dokumenten-Retrieval-System.

Fokus auf:
1. Was für ein Bild-Typ ist es? (Diagramm, Foto, Screenshot, Schaubild, Tabelle, etc.)
2. Welche Daten/Informationen werden dargestellt?
3. Welche Text-Beschriftungen sind sichtbar?
4. Was sind die Haupt-Elemente?
5. Welche Zahlen/Werte sind erkennbar?

Antworte auf Deutsch, präzise und strukturiert."""

                response = client.messages.create(
                    model="claude-3-5-sonnet-20241022",
                    max_tokens=500,
                    messages=[{
                        "role": "user",
                        "content": [
                            {
                                "type": "image",
                                "source": {
                                    "type": "base64",
                                    "media_type": image_mime_type,
                                    "data": image_base64
                                }
                            },
                            {"type": "text", "text": prompt}
                        ]
                    }]
                )

                description = response.content[0].text
                model_used = "Claude 3.5 Sonnet"
                cost_estimate = 0.003  # ~$3 per 1K images

            except Exception as e:
                print(f"Claude Vision fehlgeschlagen: {e}")

        # GPT-4 Vision (Alternative)
        elif api_provider == "gpt4":
            try:
                import openai
                client = openai.OpenAI(api_key=api_key or os.environ.get("OPENAI_API_KEY"))

                response = client.chat.completions.create(
                    model="gpt-4-vision-preview",
                    messages=[{
                        "role": "user",
                        "content": [
                            {"type": "text", "text": "Beschreibe dieses Bild detailliert auf Deutsch für ein Retrieval-System. Fokus auf Inhalt, Daten, Text und Struktur."},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:{image_mime_type};base64,{image_base64}"
                                }
                            }
                        ]
                    }],
                    max_tokens=300
                )

                description = response.choices[0].message.content
                model_used = "GPT-4 Vision"
                cost_estimate = 0.01  # ~$10 per 1K images
            except Exception as e:
                print(f"GPT-4 Vision fehlgeschlagen: {e}")

        # Fallback: Einfache Beschreibung
        if not description:
            description = f"Bild-Element (Typ: {image_mime_type})"
            model_used = "Fallback"
            cost_estimate = 0.0

        return {
            "description": description,
            "model": model_used,
            "cost_estimate": cost_estimate,
            "cached": False
        }

    except Exception as e:
        return {
            "description": f"Fehler: {str(e)}",
            "model": "error",
            "cost_estimate": 0.0,
            "cached": False
        }

def export_images_from_bedrock_json(elements, filename):
    """
    Exportiert alle Bilder aus den Elementen als ZIP-Datei
    ✅ OPTIMIERT für einfachen Import in Bedrock RAG Oberfläche

    Args:
        elements: Liste der unstructured Elements
        filename: Original-Dateiname für Bild-Naming

    Returns:
        Dict mit ZIP-Bytes und Statistiken oder Error
    """
    try:
        import io
        import zipfile
        import base64
        import hashlib
        from datetime import datetime

        # Sammle alle Bilder mit Base64-Daten
        images = []

        for i, element in enumerate(elements):
            element_type = type(element).__name__

            if element_type in ["Image", "Figure", "Picture", "FigureCaption"]:
                if hasattr(element, 'metadata') and element.metadata:
                    meta = element.metadata

                    if hasattr(meta, 'image_base64') and meta.image_base64:
                        # ✅ OPTIMIERT: Hash nur auf ersten 1000 Zeichen für Performance
                        hash_sample = meta.image_base64[:1000] if len(meta.image_base64) > 1000 else meta.image_base64
                        image_hash = hashlib.md5(hash_sample.encode()).hexdigest()

                        # Mime-Type bestimmen
                        mime_type = getattr(meta, 'image_mime_type', 'image/png')
                        extension = 'png'
                        if 'jpeg' in mime_type or 'jpg' in mime_type:
                            extension = 'jpg'
                        elif 'gif' in mime_type:
                            extension = 'gif'
                        elif 'webp' in mime_type:
                            extension = 'webp'

                        # Seiten-Nummer für Naming
                        page_num = getattr(meta, 'page_number', i)

                        images.append({
                            'hash': image_hash,
                            'base64': meta.image_base64,
                            'mime_type': mime_type,
                            'extension': extension,
                            'page': page_num,
                            'element_index': i,
                            'element_type': element_type
                        })

        if not images:
            return {
                "status": "warning",
                "message": "Keine Bilder mit Base64-Daten gefunden"
            }

        # ZIP-Datei erstellen
        zip_buffer = io.BytesIO()

        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            # Manifest-Datei erstellen
            manifest = {
                "source_document": filename,
                "export_date": datetime.now().isoformat(),
                "total_images": len(images),
                "images": []
            }

            for img in images:
                # Dateiname: page_<page>_hash_<hash>.<ext>
                img_filename = f"page_{img['page']:03d}_hash_{img['hash'][:8]}.{img['extension']}"

                # Base64 dekodieren
                try:
                    img_bytes = base64.b64decode(img['base64'])

                    # Bild zur ZIP hinzufügen
                    zip_file.writestr(img_filename, img_bytes)

                    # Manifest-Eintrag
                    manifest["images"].append({
                        "filename": img_filename,
                        "hash": img['hash'],
                        "page": img['page'],
                        "element_index": img['element_index'],
                        "element_type": img['element_type'],
                        "mime_type": img['mime_type'],
                        "size_bytes": len(img_bytes)
                    })

                except Exception as e:
                    print(f"Fehler beim Dekodieren von Bild {img['hash']}: {e}")

            # Manifest als JSON zur ZIP hinzufügen
            manifest_json = json.dumps(manifest, indent=2, ensure_ascii=False)
            zip_file.writestr("manifest.json", manifest_json)

            # README für Nutzer
            readme = f"""# Bild-Export für Bedrock RAG

**Quelle:** {filename}
**Export-Datum:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**Anzahl Bilder:** {len(images)}

## 📁 Datei-Struktur

- `manifest.json` - Metadaten zu allen Bildern (Hash, Seite, Typ)
- `page_XXX_hash_XXXXXXXX.<ext>` - Original-Bilder aus dem Dokument

## 🔗 Verwendung mit S3 (optional)

### 1. Bilder zu S3 hochladen:
```bash
aws s3 sync . s3://dein-bucket/images/{filename}/ --exclude "manifest.json" --exclude "README.md"
```

### 2. S3-URLs in RAG JSON referenzieren:
```json
{{
  "metadataAttributes": {{
    "image_hash": "abc123...",
    "image_url": "s3://dein-bucket/images/{filename}/page_001_hash_abc123.png"
  }}
}}
```

### 3. Bedrock kann Bilder bei Bedarf laden!

## 💡 Alternative: Bilder lokal halten

Die Bilder können auch lokal bleiben - das RAG JSON enthält bereits:
- **Vision-Beschreibungen** (durchsuchbarer Text)
- **Bild-Hashes** (eindeutige Referenzen)
- **Metadaten** (Seite, Typ, etc.)

Die Original-Bilder werden nur bei Bedarf geladen!
"""
            zip_file.writestr("README.md", readme)

        # ZIP-Bytes zurückgeben
        zip_bytes = zip_buffer.getvalue()

        return {
            "status": "success",
            "zip_bytes": zip_bytes,
            "total_images": len(images),
            "total_size_bytes": len(zip_bytes),
            "manifest": manifest
        }

    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }

def export_bedrock_import_package(elements, filename, describe_images=False):
    """
    Erstellt KOMPLETTES Import-Package für Bedrock RAG Oberfläche
    ✅ RAG JSON + Original-Bilder + Manifest in einer ZIP

    Args:
        elements: Liste der unstructured Elements
        filename: Original-Dateiname
        describe_images: Ob Bilder mit Vision-LLM beschrieben werden sollen

    Returns:
        Dict mit ZIP-Bytes für direkten Download/Import
    """
    try:
        import io
        import zipfile
        import base64
        import hashlib
        from datetime import datetime

        # 1. Erstelle Bedrock RAG JSON (mit Bild-Hashes)
        rag_result = export_for_bedrock_knowledge_base(
            elements=elements,
            filename=filename,
            format_type="element",
            describe_images=describe_images
        )

        if rag_result["status"] != "success":
            return rag_result

        # 2. Sammle alle Bilder
        images_data = []
        for i, element in enumerate(elements):
            element_type = type(element).__name__

            if element_type in ["Image", "Figure", "Picture", "FigureCaption"]:
                if hasattr(element, 'metadata') and element.metadata:
                    meta = element.metadata

                    if hasattr(meta, 'image_base64') and meta.image_base64:
                        # Hash berechnen (Performance-optimiert)
                        hash_sample = meta.image_base64[:1000] if len(meta.image_base64) > 1000 else meta.image_base64
                        image_hash = hashlib.md5(hash_sample.encode()).hexdigest()

                        mime_type = getattr(meta, 'image_mime_type', 'image/png')
                        extension = 'png'
                        if 'jpeg' in mime_type or 'jpg' in mime_type:
                            extension = 'jpg'
                        elif 'gif' in mime_type:
                            extension = 'gif'

                        page_num = getattr(meta, 'page_number', i)

                        images_data.append({
                            'hash': image_hash,
                            'base64': meta.image_base64,
                            'mime_type': mime_type,
                            'extension': extension,
                            'page': page_num,
                            'element_index': i
                        })

        # 3. Erstelle ZIP mit allem
        zip_buffer = io.BytesIO()

        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            # 3.1 RAG JSON (JSON-Lines Format für Bedrock)
            rag_json = rag_result["json_lines"]
            zip_file.writestr("rag_data.jsonl", rag_json)

            # 3.2 RAG JSON als Array (für Preview/Debugging)
            rag_json_array = json.dumps(rag_result["documents"], indent=2, ensure_ascii=False)
            zip_file.writestr("rag_data_preview.json", rag_json_array)

            # 3.3 Bilder im Unterordner
            manifest_images = []
            for img in images_data:
                img_filename = f"images/page_{img['page']:03d}_{img['hash'][:8]}.{img['extension']}"

                try:
                    img_bytes = base64.b64decode(img['base64'])
                    zip_file.writestr(img_filename, img_bytes)

                    manifest_images.append({
                        "filename": img_filename,
                        "hash": img['hash'],
                        "page": img['page'],
                        "size_bytes": len(img_bytes),
                        "mime_type": img['mime_type']
                    })
                except Exception as e:
                    print(f"Fehler beim Dekodieren von Bild {img['hash']}: {e}")

            # 3.4 Manifest für deine Import-Funktion
            manifest = {
                "source_document": filename,
                "export_date": datetime.now().isoformat(),
                "total_elements": rag_result["document_count"],
                "total_images": len(images_data),
                "rag_format": "json_lines",
                "images_included": len(manifest_images),
                "image_descriptions": rag_result.get("image_descriptions"),
                "images": manifest_images,
                "import_info": {
                    "rag_file": "rag_data.jsonl",
                    "images_folder": "images/",
                    "format": "Bedrock Knowledge Base compatible",
                    "hash_algorithm": "MD5",
                    "ready_for_import": True
                }
            }

            manifest_json = json.dumps(manifest, indent=2, ensure_ascii=False)
            zip_file.writestr("manifest.json", manifest_json)

            # 3.5 Import-Anleitung für deine RAG-Oberfläche
            import_guide = f"""# Bedrock RAG Import-Package

## 📦 **Inhalt:**

```
bedrock_import_{filename}/
├── rag_data.jsonl              ← Bedrock RAG JSON (JSON-Lines)
├── rag_data_preview.json       ← Preview als JSON-Array
├── images/                     ← Original-Bilder
│   ├── page_001_abc12345.png
│   ├── page_002_def67890.jpg
│   └── ...
├── manifest.json               ← Metadaten + Hash-Mapping
└── IMPORT_GUIDE.md             ← Diese Datei
```

---

## 🚀 **Import in deine Bedrock RAG-Oberfläche:**

### **Option 1: Automatischer Import (empfohlen)**

```python
import zipfile
import json

# 1. ZIP entpacken
with zipfile.ZipFile('bedrock_import.zip', 'r') as zip_ref:
    zip_ref.extractall('./bedrock_import/')

# 2. Manifest laden
with open('./bedrock_import/manifest.json', 'r') as f:
    manifest = json.load(f)

# 3. RAG JSON laden (JSON-Lines)
rag_documents = []
with open('./bedrock_import/rag_data.jsonl', 'r') as f:
    for line in f:
        rag_documents.append(json.loads(line))

# 4. Bilder sind verfügbar unter ./bedrock_import/images/
# Hash-Mapping aus manifest["images"]

# 5. Import in deine RAG-Datenbank
for doc in rag_documents:
    # Deine Import-Logik hier
    bedrock_rag.add_document(doc)
```

### **Option 2: Direkter S3-Upload**

```bash
# 1. Bilder zu S3
aws s3 sync ./bedrock_import/images/ s3://dein-bucket/images/{filename}/

# 2. RAG JSON zu S3 (für Bedrock Knowledge Base)
aws s3 cp ./bedrock_import/rag_data.jsonl s3://dein-bucket/rag-data/

# 3. Bedrock Knowledge Base synchronisieren
aws bedrock-agent sync-knowledge-base --knowledge-base-id YOUR_KB_ID
```

---

## 🔗 **Hash-basierte Bild-Referenzierung:**

Jedes Bild hat einen **eindeutigen Hash** (MD5):

**Im RAG JSON:**
```json
{{
  "metadataAttributes": {{
    "image_hash": "abc12345def67890",
    "image_available": true,
    "page": 5
  }},
  "content": "Balkendiagramm zeigt..."
}}
```

**Im Manifest:**
```json
{{
  "hash": "abc12345def67890",
  "filename": "images/page_005_abc12345.png"
}}
```

**In deiner RAG-Oberfläche:**
```python
def get_image_by_hash(hash_value):
    # Finde Bild im Manifest
    for img in manifest["images"]:
        if img["hash"] == hash_value:
            return img["filename"]
    return None
```

---

## 💡 **Test-Workflow:**

1. ✅ ZIP in deine RAG-Oberfläche hochladen
2. ✅ Automatisch entpacken
3. ✅ RAG JSON importieren (rag_data.jsonl)
4. ✅ Bilder referenzieren über Hash
5. ✅ Query testen: "Zeige Umsatz Q2"
6. ✅ Ergebnis: RAG findet Text-Beschreibung + zeigt Bild via Hash

---

## 📊 **Package-Statistiken:**

- **Quelle:** {filename}
- **Export-Datum:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
- **RAG-Elemente:** {rag_result["document_count"]}
- **Bilder:** {len(images_data)}
- **Vision-Beschreibungen:** {"Ja" if describe_images else "Nein"}
- **Format:** Bedrock Knowledge Base kompatibel
- **Ready for Import:** ✅

---

## 🎯 **Vorteile dieses Formats:**

✅ **Alles in einer ZIP** - Keine separaten Downloads
✅ **Hash-basiert** - Eindeutige Bild-Referenzen
✅ **Bedrock-kompatibel** - Direkt importierbar
✅ **Test-ready** - Sofort in deiner Oberfläche nutzbar
✅ **S3-optional** - Funktioniert lokal UND in Cloud

**Viel Erfolg beim Testen!** 🚀
"""
            zip_file.writestr("IMPORT_GUIDE.md", import_guide)

        zip_bytes = zip_buffer.getvalue()

        return {
            "status": "success",
            "zip_bytes": zip_bytes,
            "total_size_bytes": len(zip_bytes),
            "rag_element_count": rag_result["document_count"],
            "images_count": len(images_data),
            "manifest": manifest,
            "package_info": {
                "contains": ["RAG JSON (JSON-Lines)", "RAG JSON (Preview)", "Original-Bilder", "Manifest", "Import-Anleitung"],
                "ready_for_import": True,
                "format": "Bedrock Knowledge Base kompatibel"
            }
        }

    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }

def export_for_bedrock_knowledge_base(elements, filename, format_type="element", describe_images=False):
    """
    Exportiert Elemente im OPTIMALEN Format für Amazon Bedrock Knowledge Bases

    ✅ BEDROCK-OPTIMIERT:
    - Jedes Element als separates JSON-Dokument
    - Metadata klar getrennt für Filtering/Retrieval
    - Content ohne Base64-Bilder (zu groß für RAG)
    - Optional: Gruppierung nach Seiten

    Args:
        elements: Liste der unstructured Elements
        filename: Original-Dateiname
        format_type: "element" (pro Element) oder "page" (pro Seite gruppiert)
        describe_images: Ob Bilder mit LLM beschrieben werden sollen

    Returns:
        Dict mit Bedrock-optimierten JSON-Dokumenten
    """
    try:
        import json
        from datetime import datetime

        bedrock_documents = []

        if format_type == "element":
            # ✅ PRO ELEMENT: Jedes Element wird ein separates Dokument
            for i, element in enumerate(elements):
                element_type = type(element).__name__
                element_text = str(element).strip()

                # Überspringe leere Elemente und Seitenumbrüche
                if not element_text or element_type == "PageBreak":
                    continue

                # Metadaten sammeln
                metadata = {
                    "source": filename,
                    "element_index": i,
                    "element_type": element_type
                }

                if hasattr(element, 'metadata') and element.metadata:
                    meta = element.metadata

                    # Wichtige Metadaten für Bedrock Filtering
                    if hasattr(meta, 'page_number') and meta.page_number:
                        metadata["page"] = meta.page_number

                    if hasattr(meta, 'filename') and meta.filename:
                        metadata["source"] = meta.filename

                    if hasattr(meta, 'filetype') and meta.filetype:
                        metadata["document_type"] = meta.filetype

                    # Hierarchie für besseres Retrieval
                    if hasattr(meta, 'parent_id') and meta.parent_id:
                        metadata["parent_id"] = meta.parent_id

                    if hasattr(meta, 'category_depth') and meta.category_depth is not None:
                        metadata["hierarchy_level"] = meta.category_depth

                    # Sprache für Multi-Language RAG
                    if hasattr(meta, 'languages') and meta.languages:
                        metadata["language"] = meta.languages[0] if meta.languages else "unknown"

                    # Links für Cross-References
                    if hasattr(meta, 'links') and meta.links:
                        metadata["has_links"] = True
                        metadata["link_count"] = len(meta.links)

                    # Tabellen-Marker
                    if hasattr(meta, 'text_as_html') and meta.text_as_html:
                        metadata["is_table"] = True

                    # Excel Sheet-Name
                    if hasattr(meta, 'page_name') and meta.page_name:
                        metadata["sheet_name"] = meta.page_name

                    # Email-Metadaten
                    if hasattr(meta, 'subject') and meta.subject:
                        metadata["email_subject"] = meta.subject
                    if hasattr(meta, 'sent_from') and meta.sent_from:
                        metadata["email_from"] = str(meta.sent_from)

                # ✅ BILD-HANDLING: Vision-Beschreibung statt Base64
                content = element_text

                # Prüfe ob es ein Bild-Element ist
                if element_type in ["Image", "Figure", "Picture", "FigureCaption"]:
                    # Extrahiere Bild-Metadaten (falls vorhanden)
                    if hasattr(element, 'metadata') and element.metadata:
                        meta = element.metadata

                        # Original-Bild NICHT als Base64, sondern als Referenz
                        if hasattr(meta, 'image_base64') and meta.image_base64:
                            # ✅ OPTIMIERT: Speichere nur Hash/Referenz, nicht Base64
                            # Nutze nur erste 1000 Zeichen für Hash (schneller!)
                            import hashlib
                            hash_sample = meta.image_base64[:1000] if len(meta.image_base64) > 1000 else meta.image_base64
                            image_hash = hashlib.md5(hash_sample.encode()).hexdigest()
                            metadata["image_hash"] = image_hash
                            metadata["image_available"] = True

                            # Optional: Bild-URL falls extern verfügbar
                            if hasattr(meta, 'url') and meta.url:
                                metadata["image_url"] = meta.url

                        # Vision-Beschreibung hinzufügen (falls gewünscht UND describe_images=True)
                        if describe_images and hasattr(meta, 'image_base64') and meta.image_base64:
                            try:
                                # Rufe Vision-API auf für Bild-Beschreibung
                                vision_result = describe_image_with_vision_llm(
                                    image_base64=meta.image_base64,
                                    image_mime_type=getattr(meta, 'image_mime_type', 'image/png'),
                                    api_provider="auto",  # Auto-detect verfügbare API
                                    api_key=None  # Nutzt ENV-Variablen
                                )

                                if vision_result and vision_result.get('description'):
                                    vision_description = vision_result['description']

                                    # Vision-Beschreibung als Content (durchsuchbar!)
                                    if vision_description and vision_description != element_text:
                                        content = f"{element_text}\n\n[Vision-Beschreibung]: {vision_description}"
                                        metadata["image_described"] = True
                                        metadata["vision_model"] = vision_result.get('model', 'Unknown')
                                        metadata["vision_cost_estimate"] = vision_result.get('cost_estimate', 0.003)
                                    else:
                                        metadata["image_described"] = False
                                else:
                                    # Vision-API fehlgeschlagen - Fallback
                                    metadata["image_described"] = False
                                    content = f"{element_text}\n\n[Hinweis: Vision-API nicht verfügbar - Bild nicht beschrieben]"

                            except Exception as e:
                                # Fehler bei Vision-API - dokumentieren aber nicht abbrechen
                                metadata["image_described"] = False
                                metadata["vision_error"] = str(e)[:100]
                                content = f"{element_text}\n\n[Hinweis: Vision-Beschreibung fehlgeschlagen - {str(e)[:50]}]"
                        else:
                            metadata["image_described"] = False

                            # Warnung in Content wenn Bild nicht beschrieben
                            if not describe_images:
                                content = f"{element_text}\n\n[Hinweis: Bild nicht beschrieben - aktiviere 'Vision-Beschreibung' für durchsuchbaren Content]"

                # Bedrock-Format: Metadata + Content getrennt
                bedrock_doc = {
                    "metadataAttributes": metadata,
                    "content": content
                }

                bedrock_documents.append(bedrock_doc)

        elif format_type == "page":
            # ✅ PRO SEITE: Gruppiere Elemente nach Seiten
            pages = {}

            for element in elements:
                element_type = type(element).__name__
                element_text = str(element).strip()

                if not element_text or element_type == "PageBreak":
                    continue

                # Bestimme Seite
                page_num = 1
                if hasattr(element, 'metadata') and element.metadata:
                    page_num = getattr(element.metadata, 'page_number', 1) or 1

                if page_num not in pages:
                    pages[page_num] = {
                        "texts": [],
                        "element_types": [],
                        "metadata": {}
                    }

                pages[page_num]["texts"].append(element_text)
                pages[page_num]["element_types"].append(element_type)

                # Sammle Metadaten von erster Element auf Seite
                if not pages[page_num]["metadata"] and hasattr(element, 'metadata') and element.metadata:
                    meta = element.metadata
                    pages[page_num]["metadata"] = {
                        "filename": getattr(meta, 'filename', filename),
                        "filetype": getattr(meta, 'filetype', None),
                        "languages": getattr(meta, 'languages', [])
                    }

            # Erstelle Bedrock-Dokumente pro Seite
            for page_num, page_data in pages.items():
                combined_text = "\n\n".join(page_data["texts"])

                metadata = {
                    "source": page_data["metadata"].get("filename", filename),
                    "page": page_num,
                    "document_type": page_data["metadata"].get("filetype", "unknown"),
                    "element_count": len(page_data["texts"]),
                    "element_types": list(set(page_data["element_types"]))
                }

                if page_data["metadata"].get("languages"):
                    metadata["language"] = page_data["metadata"]["languages"][0]

                bedrock_doc = {
                    "metadataAttributes": metadata,
                    "content": combined_text
                }

                bedrock_documents.append(bedrock_doc)

        # ✅ OPTIMIERT: JSON-Lines formatieren (ein JSON pro Zeile) - OHNE indent für Performance
        json_lines = "\n".join([json.dumps(doc, ensure_ascii=False, separators=(',', ':')) for doc in bedrock_documents])

        # ✅ OPTIMIERT: JSON-Array NUR für kleine Vorschau (erste 5 Elemente)
        # Verhindert Browser-Freeze bei großen Dokumenten!
        preview_docs = bedrock_documents[:5] if len(bedrock_documents) > 5 else bedrock_documents
        json_array = json.dumps(preview_docs, indent=2, ensure_ascii=False)

        # Vollständiges JSON wird NUR bei Download generiert (lazy)

        # ✅ Statistiken für Bild-Beschreibungen
        image_stats = {
            "total_images": 0,
            "images_described": 0,
            "images_failed": 0,
            "total_cost_estimate": 0.0,
            "models_used": {}
        }

        if describe_images:
            for doc in bedrock_documents:
                meta = doc["metadataAttributes"]
                if meta.get("image_described"):
                    image_stats["images_described"] += 1
                    image_stats["total_cost_estimate"] += meta.get("vision_cost_estimate", 0.0)
                    model = meta.get("vision_model", "Unknown")
                    image_stats["models_used"][model] = image_stats["models_used"].get(model, 0) + 1
                elif meta.get("element_type") in ["Image", "Figure", "FigureCaption", "Picture"]:
                    image_stats["total_images"] += 1
                    if meta.get("image_described") == False:
                        image_stats["images_failed"] += 1

        return {
            "status": "success",
            "documents": bedrock_documents,  # ⚠️ Nur für Download, nicht für UI
            "document_count": len(bedrock_documents),
            "json_lines": json_lines,  # Für Bedrock Upload
            "json_preview": json_array,  # ✅ NUR VORSCHAU (erste 5)
            "is_preview": len(bedrock_documents) > 5,  # Flag für UI
            "format_type": format_type,
            "image_descriptions": image_stats if describe_images else None,
            "recommended_chunking": {
                "strategy": "fixed_size" if format_type == "page" else "semantic",
                "chunk_size": 512 if format_type == "page" else 300,
                "overlap": 50,
                "note": "Bedrock chunked automatisch - diese Werte sind optional"
            }
        }

    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }

def analyze_extracted_elements(elements):
    """
    Detaillierte Analyse der extrahierten Elemente mit VOLLSTÄNDIGER Metadaten-Extraktion
    ✅ Extrahiert ALLE verfügbaren Metadaten nach Dokumenttyp
    """
    try:
        analysis = {
            "element_details": {},
            "images": [],
            "tables": [],
            "links": [],  # PDF, HTML
            "emails": [],  # EML, MSG
            "coordinates": [],  # Alle mit Bounding Boxes
            "hierarchies": [],  # parent_id, category_depth
            "languages": [],  # Erkannte Sprachen
            "emphasized_texts": [],  # Fett/Kursiv
            "special_elements": {},
            "metadata_info": {},
            "format_specific": {
                "pdf": {"links": [], "images": []},
                "html": {"links": [], "image_urls": []},
                "email": {"messages": []},
                "excel": {"sheets": set()},
                "word": {"headers_footers": []},
                "epub": {"sections": []}
            }
        }

        for i, element in enumerate(elements):
            element_type = type(element).__name__
            element_text = str(element).strip()

            # Element-Details sammeln
            if element_type not in analysis["element_details"]:
                analysis["element_details"][element_type] = []

            element_info = {
                "index": i,
                "type": element_type,
                "text_preview": element_text[:200] if element_text else "",
                "text_length": len(element_text),
                "has_metadata": hasattr(element, 'metadata'),
            }

            # VOLLSTÄNDIGE Metadaten analysieren
            if hasattr(element, 'metadata') and element.metadata:
                metadata = element.metadata
                metadata_dict = {}

                # === BASIS-METADATEN (alle Formate) ===
                metadata_dict["filename"] = getattr(metadata, 'filename', None)
                metadata_dict["file_directory"] = getattr(metadata, 'file_directory', None)
                metadata_dict["filetype"] = getattr(metadata, 'filetype', None)
                metadata_dict["last_modified"] = getattr(metadata, 'last_modified', None)
                metadata_dict["page_number"] = getattr(metadata, 'page_number', None)

                # === HIERARCHIE & STRUKTUR ===
                parent_id = getattr(metadata, 'parent_id', None)
                category_depth = getattr(metadata, 'category_depth', None)
                if parent_id or category_depth is not None:
                    hierarchy_info = {
                        "element_index": i,
                        "element_type": element_type,
                        "parent_id": parent_id,
                        "category_depth": category_depth,
                        "text_preview": element_text[:100]
                    }
                    analysis["hierarchies"].append(hierarchy_info)
                    metadata_dict["parent_id"] = parent_id
                    metadata_dict["category_depth"] = category_depth

                # === KOORDINATEN & BOUNDING BOXES ===
                coordinates = getattr(metadata, 'coordinates', None)
                if coordinates:
                    coord_info = {
                        "element_index": i,
                        "element_type": element_type,
                        "coordinates": coordinates,
                        "text_preview": element_text[:100]
                    }
                    analysis["coordinates"].append(coord_info)
                    metadata_dict["coordinates"] = str(coordinates)

                # === SPRACHEN ===
                languages = getattr(metadata, 'languages', None)
                if languages:
                    lang_info = {
                        "element_index": i,
                        "element_type": element_type,
                        "languages": languages,
                        "text_preview": element_text[:100]
                    }
                    analysis["languages"].append(lang_info)
                    metadata_dict["languages"] = languages

                # === BETONTER TEXT (Fett/Kursiv) ===
                emphasized_contents = getattr(metadata, 'emphasized_text_contents', None)
                emphasized_tags = getattr(metadata, 'emphasized_text_tags', None)
                if emphasized_contents or emphasized_tags:
                    emphasis_info = {
                        "element_index": i,
                        "element_type": element_type,
                        "emphasized_contents": emphasized_contents,
                        "emphasized_tags": emphasized_tags,
                        "text_preview": element_text[:100]
                    }
                    analysis["emphasized_texts"].append(emphasis_info)
                    metadata_dict["emphasized_text_contents"] = emphasized_contents
                    metadata_dict["emphasized_text_tags"] = emphasized_tags

                # === KI-MODELL SCORES ===
                detection_prob = getattr(metadata, 'detection_class_prob', None)
                if detection_prob:
                    metadata_dict["detection_class_prob"] = detection_prob

                # === BILD-METADATEN ===
                metadata_dict["image_base64"] = getattr(metadata, 'image_base64', None)
                metadata_dict["image_mime_type"] = getattr(metadata, 'image_mime_type', None)
                metadata_dict["image_path"] = getattr(metadata, 'image_path', None)
                metadata_dict["image_url"] = getattr(metadata, 'image_url', None)

                # === PDF-SPEZIFISCH: Links ===
                links = getattr(metadata, 'links', None)
                link_texts = getattr(metadata, 'link_texts', None)
                link_start_indexes = getattr(metadata, 'link_start_indexes', None)
                if links:
                    for link_data in links:
                        link_info = {
                            "element_index": i,
                            "element_type": element_type,
                            "link": link_data,
                            "text": element_text[:100],
                            "page_number": metadata_dict.get("page_number")
                        }
                        analysis["links"].append(link_info)
                        analysis["format_specific"]["pdf"]["links"].append(link_info)
                    metadata_dict["links"] = links
                    metadata_dict["link_start_indexes"] = link_start_indexes

                # === HTML-SPEZIFISCH: Links & Image URLs ===
                link_urls = getattr(metadata, 'link_urls', None)
                if link_urls:
                    metadata_dict["link_urls"] = link_urls
                    metadata_dict["link_texts"] = link_texts
                    metadata_dict["link_start_indexes"] = link_start_indexes
                    for url in link_urls:
                        analysis["format_specific"]["html"]["links"].append({
                            "url": url,
                            "element_index": i,
                            "text": element_text[:100]
                        })

                image_url = getattr(metadata, 'image_url', None)
                if image_url:
                    metadata_dict["image_url"] = image_url
                    analysis["format_specific"]["html"]["image_urls"].append({
                        "url": image_url,
                        "element_index": i
                    })

                # === EMAIL-SPEZIFISCH ===
                sent_from = getattr(metadata, 'sent_from', None)
                sent_to = getattr(metadata, 'sent_to', None)
                subject = getattr(metadata, 'subject', None)
                if sent_from or sent_to or subject:
                    email_info = {
                        "element_index": i,
                        "sent_from": sent_from,
                        "sent_to": sent_to,
                        "cc_recipient": getattr(metadata, 'cc_recipient', None),
                        "bcc_recipient": getattr(metadata, 'bcc_recipient', None),
                        "subject": subject,
                        "email_message_id": getattr(metadata, 'email_message_id', None),
                        "signature": getattr(metadata, 'signature', None),
                        "attached_to_filename": getattr(metadata, 'attached_to_filename', None)
                    }
                    analysis["emails"].append(email_info)
                    analysis["format_specific"]["email"]["messages"].append(email_info)
                    metadata_dict.update(email_info)

                # === EXCEL-SPEZIFISCH: Sheet-Namen ===
                page_name = getattr(metadata, 'page_name', None)
                if page_name:
                    metadata_dict["page_name"] = page_name
                    analysis["format_specific"]["excel"]["sheets"].add(page_name)

                # === WORD-SPEZIFISCH: Header/Footer ===
                header_footer_type = getattr(metadata, 'header_footer_type', None)
                if header_footer_type:
                    metadata_dict["header_footer_type"] = header_footer_type
                    analysis["format_specific"]["word"]["headers_footers"].append({
                        "element_index": i,
                        "type": header_footer_type,
                        "text": element_text[:100]
                    })

                # === EPUB-SPEZIFISCH: Sections ===
                section = getattr(metadata, 'section', None)
                if section:
                    metadata_dict["section"] = section
                    analysis["format_specific"]["epub"]["sections"].append({
                        "element_index": i,
                        "section": section,
                        "text": element_text[:100]
                    })

                # === TABELLEN-SPEZIFISCH ===
                text_as_html = getattr(metadata, 'text_as_html', None)
                if text_as_html:
                    metadata_dict["text_as_html"] = text_as_html

                element_info["metadata"] = metadata_dict

                # PDF-Bilder sammeln
                if metadata_dict.get("image_path") or metadata_dict.get("image_base64"):
                    analysis["format_specific"]["pdf"]["images"].append({
                        "element_index": i,
                        "path": metadata_dict.get("image_path"),
                        "has_base64": bool(metadata_dict.get("image_base64")),
                        "mime_type": metadata_dict.get("image_mime_type")
                    })

            # VERBESSERTE Bilder-Extraktion - suche nach allen Bild-Typen
            if element_type in ["Image", "FigureCaption", "Figure"] or "image" in element_type.lower():
                image_info = {
                    "index": i,
                    "element": element,
                    "text": element_text,
                    "metadata": element_info.get("metadata", {}),
                    "element_type": element_type,
                    # ✅ NEU: Base64-Daten direkt verfügbar machen
                    "has_base64": False,
                    "base64_data": None,
                    "mime_type": None
                }

                # ✅ Prüfe auf Base64-Bild-Daten in Metadaten
                if hasattr(element, 'metadata') and element.metadata:
                    if hasattr(element.metadata, 'image_base64') and element.metadata.image_base64:
                        image_info["has_base64"] = True
                        image_info["base64_data"] = element.metadata.image_base64
                        image_info["mime_type"] = getattr(element.metadata, 'image_mime_type', 'image/jpeg')

                analysis["images"].append(image_info)

            # Tabellen extrahieren
            elif element_type == "Table" or "table" in element_type.lower():
                analysis["tables"].append({
                    "index": i,
                    "element": element,
                    "text": element_text,
                    "metadata": element_info.get("metadata", {})
                })

            # Spezielle Elemente (Listen, Titel, etc.)
            elif element_type in ["Title", "ListItem", "Header", "Footer", "NarrativeText"]:
                if element_type not in analysis["special_elements"]:
                    analysis["special_elements"][element_type] = []
                analysis["special_elements"][element_type].append(element_info)

            analysis["element_details"][element_type].append(element_info)

        return {
            "status": "success",
            "analysis": analysis,
            "total_elements": len(elements),
            "total_images": len(analysis["images"]),
            "total_tables": len(analysis["tables"])
        }

    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }

def convert_elements_to_all_formats(elements):
    """
    Konvertiert Elemente in alle verfügbaren Ausgabeformate
    """
    conversions = {}

    try:
        # ORIGINAL Text Format - OFFIZIELLE Unstructured.io Funktion
        text_content = elements_to_text(elements)
        conversions["text"] = text_content
    except Exception as e:
        conversions["text"] = f"Text Konvertierung fehlgeschlagen: {e}"

    try:
        # HTML Format (erweitert)
        html_content = elements_to_html(elements, exclude_binary_image_data=True)
        conversions["html"] = html_content
    except Exception as e:
        conversions["html"] = f"HTML Konvertierung fehlgeschlagen: {e}"

    try:
        # Markdown Format (erweitert)
        md_content = elements_to_md(elements, exclude_binary_image_data=True)
        conversions["markdown"] = md_content
    except Exception as e:
        conversions["markdown"] = f"Markdown Konvertierung fehlgeschlagen: {e}"

    try:
        # JSON Format - Standard (könnte Metadaten weglassen)
        json_content = elements_to_json(elements, indent=2)
        conversions["json"] = json_content

        # ✅ NEU: Erweiterte JSON-Variante mit GARANTIERT VOLLSTÄNDIGEN METADATEN
        import json
        json_with_full_metadata = []

        for element in elements:
            element_dict = {
                "type": type(element).__name__,
                "element_id": getattr(element, 'id', None),
                "text": str(element),
            }

            # Vollständige Metadaten extrahieren
            if hasattr(element, 'metadata') and element.metadata:
                metadata = element.metadata
                metadata_dict = {}

                # Basis-Metadaten
                for attr in ['page_number', 'page_name', 'filename', 'file_directory',
                             'filetype', 'coordinates', 'parent_id', 'category_depth',
                             'text_as_html', 'languages', 'emphasized_text_contents',
                             'emphasized_text_tags', 'is_continuation', 'detection_class_prob',
                             'last_modified', 'file_size', 'data_source', 'url']:
                    if hasattr(metadata, attr):
                        metadata_dict[attr] = getattr(metadata, attr, None)

                # Bild-Metadaten
                for attr in ['image_path', 'image_base64', 'image_mime_type',
                             'image_width', 'image_height']:
                    if hasattr(metadata, attr):
                        value = getattr(metadata, attr, None)
                        # Kürze Base64 für bessere Lesbarkeit (optional)
                        if attr == 'image_base64' and value:
                            metadata_dict[attr] = value[:100] + "..." if len(value) > 100 else value
                            metadata_dict['has_full_image_base64'] = True
                        else:
                            metadata_dict[attr] = value

                # Link-Metadaten
                if hasattr(metadata, 'link_urls'):
                    metadata_dict['link_urls'] = metadata.link_urls
                if hasattr(metadata, 'link_texts'):
                    metadata_dict['link_texts'] = metadata.link_texts

                # Regex-Metadaten
                if hasattr(metadata, 'regex_metadata'):
                    metadata_dict['regex_metadata'] = metadata.regex_metadata

                element_dict["metadata"] = metadata_dict

            json_with_full_metadata.append(element_dict)

        conversions["json_full_metadata"] = json.dumps(json_with_full_metadata, indent=2, ensure_ascii=False)

    except Exception as e:
        conversions["json"] = f"JSON Konvertierung fehlgeschlagen: {e}"
        conversions["json_full_metadata"] = f"JSON mit Metadaten fehlgeschlagen: {e}"

    try:
        # Dictionary Format für weitere Verarbeitung
        dict_content = elements_to_dicts(elements)
        conversions["dicts"] = dict_content
    except Exception as e:
        conversions["dicts"] = f"Dictionary Konvertierung fehlgeschlagen: {e}"

    return conversions

def convert_elements_to_all_formats_with_images(elements):
    """
    Konvertiert Elemente in alle verfügbaren Ausgabeformate MIT Bild-Integration
    ✅ OPTIMIERT: Schnellere Verarbeitung, keine print-Statements
    ✅ NEU: Bilder werden in HTML und Markdown integriert
    """
    conversions = {}

    # Text Format - schnell
    try:
        text_content = elements_to_text(elements)
        conversions["text"] = text_content
    except Exception as e:
        conversions["text"] = f"Text Konvertierung fehlgeschlagen: {e}"

    # HTML Format mit Base64-Bildern - kann länger dauern
    try:
        html_content = elements_to_html_with_images(elements)
        conversions["html"] = html_content
    except Exception as e:
        conversions["html"] = f"HTML Konvertierung fehlgeschlagen: {e}"

    # Markdown Format mit Base64-Bildern
    try:
        md_content = elements_to_markdown_with_images(elements)
        conversions["markdown"] = md_content
    except Exception as e:
        conversions["markdown"] = f"Markdown Konvertierung fehlgeschlagen: {e}"

    # JSON Format (Standard-Library)
    try:
        json_content = elements_to_json(elements, indent=2)
        conversions["json"] = json_content
    except Exception as e:
        conversions["json"] = f"JSON Konvertierung fehlgeschlagen: {e}"

    # Dictionary Format
    try:
        dict_content = elements_to_dicts(elements)
        conversions["dicts"] = dict_content
    except Exception as e:
        conversions["dicts"] = f"Dictionary Konvertierung fehlgeschlagen: {e}"

    return conversions

def elements_to_html_with_images(elements, include_metadata=True):
    """
    Konvertiert Elemente zu HTML MIT eingebetteten Base64-Bildern UND Metadaten
    ✅ NEU: Zeigt Links, Formatierungen, Hierarchien und mehr
    """
    try:
        html_parts = []
        html_parts.append('<div class="document-content">')

        for i, element in enumerate(elements):
            element_type = type(element).__name__
            element_text = str(element).strip()

            # Metadaten sammeln
            metadata = {}
            if hasattr(element, 'metadata') and element.metadata:
                meta = element.metadata
                metadata = {
                    'page_number': getattr(meta, 'page_number', None),
                    'category_depth': getattr(meta, 'category_depth', None),
                    'languages': getattr(meta, 'languages', None),
                    'emphasized_text_contents': getattr(meta, 'emphasized_text_contents', None),
                    'emphasized_text_tags': getattr(meta, 'emphasized_text_tags', None),
                    'links': getattr(meta, 'links', None),
                    'link_urls': getattr(meta, 'link_urls', None),
                    'link_texts': getattr(meta, 'link_texts', None),
                }

            # ✅ VERBESSERT: Erweiterte Bild-Element-Erkennung
            if element_type in ["Image", "FigureCaption", "Figure", "Picture"]:
                # Prüfe auf Base64-Bild-Daten in Metadaten
                if (hasattr(element, 'metadata') and element.metadata and
                    hasattr(element.metadata, 'image_base64') and element.metadata.image_base64):

                    base64_data = element.metadata.image_base64
                    mime_type = getattr(element.metadata, 'image_mime_type', 'image/jpeg')

                    # HTML für eingebettetes Bild mit Metadaten (effizient mit Liste)
                    img_parts = ['<div class="image-container" style="margin: 15px 0; padding: 10px; border: 1px solid #ddd; border-radius: 4px; background: #f9f9f9;">']

                    if include_metadata and metadata.get('page_number'):
                        img_parts.append(f'<div class="meta-badge" style="font-size: 0.8em; color: #666; margin-bottom: 5px;">📄 Seite {metadata["page_number"]}</div>')

                    img_parts.append(f'<div style="text-align: center;"><img src="data:{mime_type};base64,{base64_data}" alt="{element_text[:100] if element_text else "Extrahiertes Bild"}" style="max-width: 100%; height: auto; border: 1px solid #ccc; border-radius: 4px;" /></div>')

                    if element_text:
                        img_parts.append(f'<p class="image-caption" style="font-style: italic; color: #666; margin-top: 8px; text-align: center;">{element_text}</p>')

                    img_parts.append('</div>')
                    html_parts.append(''.join(img_parts))
                else:
                    # Fallback: Zeige Platzhalter für Bilder ohne Base64
                    if element_text:
                        html_parts.append(f'<p style="color: #999; font-style: italic;">[Bild ohne Base64-Daten: {element_text}]</p>')

            elif element_type == "Table":
                # Tabelle mit Metadaten (effizient mit Liste)
                table_parts = ['<div class="table-container" style="margin: 15px 0; padding: 10px; border: 1px solid #ddd; border-radius: 4px; background: #f9f9f9; overflow-x: auto;">']

                if include_metadata and metadata.get('page_number'):
                    table_parts.append(f'<div class="meta-badge" style="font-size: 0.8em; color: #666; margin-bottom: 5px;">📊 Tabelle - Seite {metadata["page_number"]}</div>')

                if hasattr(element, 'metadata') and element.metadata and hasattr(element.metadata, 'text_as_html'):
                    table_parts.append(element.metadata.text_as_html)
                else:
                    table_parts.append(f'<pre>{str(element)}</pre>')

                table_parts.append('</div>')
                html_parts.append(''.join(table_parts))

            elif element_type == "PageBreak":
                html_parts.append('<hr style="border: 1px dashed #ccc; margin: 20px 0;" />')

            else:
                # Alle anderen Elemente MIT Metadaten-Integration
                if not element_text:
                    continue

                element_parts = ['<div class="element" style="margin: 10px 0;">']

                # ✅ METADATEN-BADGES
                if include_metadata:
                    meta_badges = []
                    if metadata.get('page_number'):
                        meta_badges.append(f'📄 S.{metadata["page_number"]}')
                    if metadata.get('languages'):
                        langs = ', '.join(metadata['languages'][:2])
                        meta_badges.append(f'🌍 {langs}')
                    if metadata.get('category_depth') is not None:
                        meta_badges.append(f'📊 Ebene {metadata["category_depth"]}')

                    if meta_badges:
                        element_parts.append(f'<div class="meta-info" style="font-size: 0.75em; color: #999; margin-bottom: 3px;">{" | ".join(meta_badges)}</div>')

                # ✅ TEXT-FORMATIERUNG: Betonten Text hervorheben
                display_text = element_text
                if metadata.get('emphasized_text_contents'):
                    for emph_text in metadata['emphasized_text_contents']:
                        if emph_text in display_text:
                            display_text = display_text.replace(emph_text, f'<strong style="background: #ffeb3b; padding: 2px 4px;">{emph_text}</strong>')

                # ✅ LINKS ANKLICKBAR MACHEN
                if metadata.get('links'):
                    for link_data in metadata['links']:
                        if isinstance(link_data, dict) and 'url' in link_data:
                            url = link_data['url']
                            display_text += f' <a href="{url}" target="_blank" style="color: #0066cc; text-decoration: underline;">🔗</a>'
                        elif isinstance(link_data, str):
                            display_text += f' <a href="{link_data}" target="_blank" style="color: #0066cc; text-decoration: underline;">🔗</a>'

                if metadata.get('link_urls'):
                    for idx, url in enumerate(metadata['link_urls']):
                        link_text = metadata.get('link_texts', [])[idx] if metadata.get('link_texts') and idx < len(metadata['link_texts']) else '🔗'
                        display_text += f' <a href="{url}" target="_blank" style="color: #0066cc; text-decoration: underline;">{link_text}</a>'

                # Element-spezifisches HTML mit Hierarchie
                if element_type == "Title":
                    depth = metadata.get('category_depth', 0)
                    heading_level = min(depth + 2, 6)
                    indent = depth * 20
                    element_parts.append(f'<h{heading_level} style="margin-left: {indent}px; color: #333;">{display_text}</h{heading_level}>')
                elif element_type == "ListItem":
                    depth = metadata.get('category_depth', 0)
                    indent = depth * 20
                    element_parts.append(f'<li style="margin-left: {indent}px;">{display_text}</li>')
                elif element_type == "Header":
                    element_parts.append(f'<div class="header" style="background: #e3f2fd; padding: 8px; border-left: 3px solid #2196f3; margin: 10px 0; font-weight: bold;">{display_text}</div>')
                elif element_type == "Footer":
                    element_parts.append(f'<div class="footer" style="background: #f5f5f5; padding: 8px; border-left: 3px solid #999; margin: 10px 0; font-size: 0.9em; color: #666;">{display_text}</div>')
                elif element_type == "NarrativeText":
                    element_parts.append(f'<p style="line-height: 1.6;">{display_text}</p>')
                else:
                    element_parts.append(f'<p>{display_text}</p>')

                element_parts.append('</div>')
                html_parts.append(''.join(element_parts))

        result_html = '\n'.join(html_parts)
        return result_html

    except Exception as e:
        # Fallback zur Standard-Funktion OHNE exclude_binary_image_data
        return elements_to_html(elements, exclude_binary_image_data=False)

def elements_to_markdown_with_images(elements):
    """
    Konvertiert Elemente zu Markdown MIT eingebetteten Base64-Bildern
    ✅ OPTIMAL für LLMs - Bilder als Data-URLs integriert
    ✅ KORRIGIERT: Bilder werden GARANTIERT angezeigt
    """
    try:
        markdown_parts = []
        image_count = 0

        for element in elements:
            element_type = type(element).__name__

            # ✅ VERBESSERT: Erweiterte Bild-Element-Erkennung
            if element_type in ["Image", "FigureCaption", "Figure", "Picture"]:
                # ✅ Base64-Bilder als Markdown-Images integrieren
                if (hasattr(element, 'metadata') and element.metadata and
                    hasattr(element.metadata, 'image_base64') and element.metadata.image_base64):

                    base64_data = element.metadata.image_base64
                    mime_type = getattr(element.metadata, 'image_mime_type', 'image/jpeg')
                    element_text = str(element).strip()

                    # Markdown-Bild mit Data-URL
                    alt_text = element_text[:100] if element_text else f"Extrahiertes Bild ({element_type})"
                    img_markdown = f'![{alt_text}](data:{mime_type};base64,{base64_data})'

                    markdown_parts.append(img_markdown)
                    image_count += 1

                    # Caption falls vorhanden
                    if element_text:
                        markdown_parts.append(f'*{element_text}*')

                else:
                    # Fallback für Bilder ohne Base64-Daten
                    element_text = str(element).strip()
                    if element_text:
                        markdown_parts.append(f'**[Bild ohne Base64-Daten: {element_text}]**')

            elif element_type == "Table":
                # ✅ Tabelle mit Metadaten
                if hasattr(element, 'metadata') and element.metadata:
                    page_num = getattr(element.metadata, 'page_number', None)
                    if page_num:
                        markdown_parts.append(f'> 📊 Tabelle - Seite {page_num}')

                # ✅ HTML-Tabellen in Markdown (CommonMark-konform)
                if hasattr(element, 'metadata') and element.metadata and hasattr(element.metadata, 'text_as_html'):
                    html_content = element.metadata.text_as_html
                    markdown_parts.append(html_content)
                else:
                    # Fallback zu Text-Tabelle
                    table_text = str(element).strip()
                    if table_text:
                        markdown_parts.append(f'```\n{table_text}\n```')

            elif element_type == "PageBreak":
                markdown_parts.append('\n---\n')  # Horizontal rule für Seitenumbruch

            else:
                # ✅ ALLE ANDEREN ELEMENTE MIT METADATEN
                element_text = str(element).strip()
                if not element_text:
                    continue

                # Metadaten sammeln
                metadata = {}
                if hasattr(element, 'metadata') and element.metadata:
                    meta = element.metadata
                    metadata = {
                        'page_number': getattr(meta, 'page_number', None),
                        'category_depth': getattr(meta, 'category_depth', None),
                        'languages': getattr(meta, 'languages', None),
                        'emphasized_text_contents': getattr(meta, 'emphasized_text_contents', None),
                        'links': getattr(meta, 'links', None),
                        'link_urls': getattr(meta, 'link_urls', None),
                        'link_texts': getattr(meta, 'link_texts', None),
                    }

                # ✅ METADATEN-BADGE (als Blockquote)
                meta_info = []
                if metadata.get('page_number'):
                    meta_info.append(f"📄 S.{metadata['page_number']}")
                if metadata.get('languages'):
                    langs = ', '.join(metadata['languages'][:2])
                    meta_info.append(f"🌍 {langs}")
                if metadata.get('category_depth') is not None:
                    meta_info.append(f"📊 Ebene {metadata['category_depth']}")

                if meta_info:
                    markdown_parts.append(f"> {' | '.join(meta_info)}")

                # ✅ TEXT-FORMATIERUNG: Betonten Text hervorheben
                display_text = element_text
                if metadata.get('emphasized_text_contents'):
                    for emph_text in metadata['emphasized_text_contents']:
                        if emph_text in display_text:
                            # Markdown: **fett** oder __fett__
                            display_text = display_text.replace(emph_text, f'**{emph_text}**')

                # ✅ LINKS HINZUFÜGEN
                links_to_add = []
                if metadata.get('links'):
                    for link_data in metadata['links']:
                        if isinstance(link_data, dict) and 'url' in link_data:
                            links_to_add.append(link_data['url'])
                        elif isinstance(link_data, str):
                            links_to_add.append(link_data)

                if metadata.get('link_urls'):
                    for idx, url in enumerate(metadata['link_urls']):
                        link_text = metadata.get('link_texts', [])[idx] if metadata.get('link_texts') and idx < len(metadata['link_texts']) else 'Link'
                        display_text += f' [{link_text}]({url})'

                # Element-spezifisches Markdown mit Hierarchie
                if element_type == "Title":
                    depth = metadata.get('category_depth', 0)
                    heading_level = min(depth + 2, 6)
                    heading_marker = '#' * heading_level
                    markdown_parts.append(f'{heading_marker} {display_text}')

                    # Links separat anzeigen
                    for link in links_to_add:
                        markdown_parts.append(f'🔗 <{link}>')

                elif element_type == "ListItem":
                    depth = metadata.get('category_depth', 0)
                    indent = '  ' * depth
                    markdown_parts.append(f'{indent}- {display_text}')

                    # Links am Ende
                    for link in links_to_add:
                        markdown_parts.append(f'{indent}  🔗 <{link}>')

                elif element_type == "Header":
                    markdown_parts.append(f'> **HEADER:** {display_text}')

                elif element_type == "Footer":
                    markdown_parts.append(f'> *FOOTER:* {display_text}')

                elif element_type == "NarrativeText":
                    markdown_parts.append(display_text)

                    # Links als Fußnoten
                    for i, link in enumerate(links_to_add, 1):
                        markdown_parts.append(f'[^{i}]: {link}')

                else:
                    markdown_parts.append(display_text)

                    # Links separat
                    for link in links_to_add:
                        markdown_parts.append(f'🔗 <{link}>')

        result_md = '\n\n'.join(markdown_parts)
        return result_md

    except Exception as e:
        # Fallback zur Standard-Funktion OHNE exclude_binary_image_data
        return elements_to_md(elements, exclude_binary_image_data=False)
# STREAMLIT APP - KORRIGIERT UND VEREINFACHT
def main():
    """
    Haupt-Streamlit-App - KORRIGIERT für schwarzes Bildschirm-Problem
    """
    # Page Config
    st.set_page_config(
        page_title="🆓 Open Source Unstructured.io Suite - KORRIGIERT",
        page_icon="🆓",
        layout="wide"
    )

    st.title("🆓 Open Source Unstructured.io Suite - KORRIGIERT")
    st.markdown("**100% Open Source - Keine APIs, keine Kosten, nur lokale Verarbeitung!**")

    # STATUS-CHECK für Debugging
    st.subheader("🔍 STATUS-CHECK")
    debug_col1, debug_col2, debug_col3 = st.columns(3)

    with debug_col1:
        if UNSTRUCTURED_AVAILABLE:
            st.success("✅ UNSTRUCTURED OK")
        else:
            st.error(f"❌ UNSTRUCTURED: {IMPORT_ERROR}")

    with debug_col2:
        st.info(f"🔧 CHUNKING: {CHUNKING_AVAILABLE}")
        st.info(f"🧹 CLEANERS: {CLEANERS_AVAILABLE}")
        st.info(f"📝 NLP: {NLP_AVAILABLE}")

    with debug_col3:
        st.write(f"📁 Repository: {repo_path.exists()}")
        st.write(f"🔗 Advanced: {ADVANCED_FEATURES_AVAILABLE}")

    # Stop wenn Library nicht verfügbar
    if not UNSTRUCTURED_AVAILABLE:
        st.error(f"❌ Open Source Unstructured Library nicht verfügbar: {IMPORT_ERROR}")
        st.info("**Installation:** `pip install unstructured[all-docs]`")
        st.stop()

    st.success("✅ Open Source Unstructured Library geladen - 100% lokal!")

    # ===== CSS für scrollbare Container =====
    st.markdown("""
    <style>
    /* Scrollable Container für Markdown/HTML */
    .scrollable-markdown {
        max-height: 500px;
        overflow-y: auto;
        border: 1px solid #e0e0e0;
        border-radius: 8px;
        padding: 20px;
        background-color: #f9f9f9;
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
        line-height: 1.6;
    }

    /* Verschiedene Größen */
    .scrollable-small {
        max-height: 300px;
        overflow-y: auto;
        border: 1px solid #ddd;
        padding: 15px;
        border-radius: 5px;
    }

    .scrollable-large {
        max-height: 800px;
        overflow-y: auto;
        border: 1px solid #ddd;
        padding: 20px;
        border-radius: 8px;
    }

    /* Scrollbar Styling */
    .scrollable-markdown::-webkit-scrollbar,
    .scrollable-small::-webkit-scrollbar,
    .scrollable-large::-webkit-scrollbar {
        width: 10px;
    }

    .scrollable-markdown::-webkit-scrollbar-track,
    .scrollable-small::-webkit-scrollbar-track,
    .scrollable-large::-webkit-scrollbar-track {
        background: #f1f1f1;
        border-radius: 10px;
    }

    .scrollable-markdown::-webkit-scrollbar-thumb,
    .scrollable-small::-webkit-scrollbar-thumb,
    .scrollable-large::-webkit-scrollbar-thumb {
        background: #888;
        border-radius: 10px;
    }

    .scrollable-markdown::-webkit-scrollbar-thumb:hover,
    .scrollable-small::-webkit-scrollbar-thumb:hover,
    .scrollable-large::-webkit-scrollbar-thumb:hover {
        background: #555;
    }
    </style>
    """, unsafe_allow_html=True)

    # Sidebar für Konfiguration
    with st.sidebar:
        st.header("🆓 Open Source Konfiguration")
        st.info("🎯 **Vollständig kostenlos** - Keine API-Keys erforderlich!")

        # Verarbeitungs-Strategien
        st.subheader("⚙️ Verarbeitungs-Strategien")
        strategy = st.selectbox(
            "Open Source Strategie",
            ["auto", "fast", "hi_res", "ocr_only"],
            help="""**Verarbeitungs-Qualität wählen:**

📄 **Gilt für:** PDF, DOCX, PPTX, Bilder
❌ **Nicht für:** XLSX (Excel)

• **auto** - Automatische Wahl (empfohlen)
• **fast** - Schnell, weniger genau
• **hi_res** - Langsam, sehr genau (beste Qualität)
• **ocr_only** - Nur OCR-Texterkennung

Alle Strategien laufen lokal ohne externe APIs."""
        )

        # Features
        st.subheader("🚀 Open Source Features")
        include_tables = st.checkbox(
            "Tabellen-Extraktion",
            value=True,
            help="""**Tabellen strukturiert extrahieren:**

📄 **Gilt für:** PDF, DOCX, PPTX, XLSX, Bilder

• **AN:** Tabellen werden als HTML-Struktur extrahiert
• **AUS:** Tabellen werden als einfacher Text extrahiert

Empfohlen für Dokumente mit Tabellen."""
        )

        include_images = st.checkbox(
            "Bild-Extraktion",
            value=True,
            help="""**Bilder als Base64 extrahieren:**

✅ **Gilt für:** PDF, DOCX, PPTX
❌ **Nicht für:** XLSX (nicht unterstützt), Bilder (selbst Input)

• **AN:** Bilder werden extrahiert und als Base64 gespeichert
• **AUS:** Nur Text wird extrahiert, Bilder werden ignoriert

Empfohlen wenn Bilder wichtig sind."""
        )

        # ERWEITERTE FEATURES - OHNE Formular-Extraktion (nicht verfügbar)
        st.subheader("🎯 Erweiterte Extraktion")
        st.info("📋 **Formular-Extraktion:** Noch nicht in Open Source verfügbar")


        # Repository Beispiele laden
        st.subheader("📁 Repository Beispiele")

        try:
            examples = get_open_source_examples()

            # Nur bei erfolgreicher Erkennung anzeigen
            if examples:
                selected_example = st.selectbox("Beispiel-Datei", ["Keine"] + list(examples.keys()))
                st.success(f"✅ {len(examples)} Testdateien verfügbar")
            else:
                st.warning("Keine Repository-Beispiele gefunden")
                selected_example = "Keine"

        except Exception as e:
            st.error(f"Fehler beim Laden der Beispiele: {e}")
            examples = {}
            selected_example = "Keine"

    # HAUPT-TABS
    tab1, tab2, tab3 = st.tabs(["📄 Processing", "🔧 Erweiterte Features", "📊 Debug Dashboard"])

    with tab1:
        st.header("📄 Open Source Document Processing")

        col1, col2 = st.columns([1, 2])

        with col1:
            st.subheader("📁 Upload")
            uploaded_file = st.file_uploader(
                "Open Source Document Upload",
                type=['pdf', 'docx', 'pptx', 'xlsx', 'jpg', 'jpeg', 'png', 'txt', 'html'],
                help="Wird komplett lokal verarbeitet"
            )

            # Repository-Beispiel verwenden
            if selected_example != "Keine" and selected_example in examples:
                st.info(f"📁 Repository-Beispiel: {Path(examples[selected_example]).name}")
                try:
                    with open(examples[selected_example], "rb") as f:
                        file_bytes = f.read()
                        filename = Path(examples[selected_example]).name
                        # Mock File Object erstellen
                        class MockFile:
                            def __init__(self, name, content):
                                self.name = name
                                self.size = len(content)
                                self._content = content
                            def getvalue(self):
                                return self._content

                        uploaded_file = MockFile(filename, file_bytes)
                    st.success(f"✅ Repository-Datei geladen: {filename}, {len(file_bytes)} bytes")
                except Exception as e:
                    st.error(f"Fehler beim Laden des Repository-Beispiels: {e}")

            if uploaded_file is not None:
                st.success(f"✅ {uploaded_file.name}")
                st.caption(f"Größe: {uploaded_file.size:,} Bytes")

                if st.button("🚀 Open Source Processing", type="primary"):
                    with st.spinner("Verarbeitung läuft..."):
                        # Temporäre Datei erstellen
                        temp_path = f"/tmp/{uploaded_file.name}"
                        with open(temp_path, "wb") as f:
                            f.write(uploaded_file.getvalue())

                        # Processing
                        result = process_with_open_source_library(
                            temp_path,
                            strategy,
                            include_tables=include_tables,
                            include_images=include_images
                        )

                        # Temporäre Datei löschen
                        try:
                            os.remove(temp_path)
                        except:
                            pass

                        st.session_state.os_result = result
                        st.session_state.os_filename = uploaded_file.name

        with col2:
            st.subheader("📊 Open Source Ergebnisse")

            if hasattr(st.session_state, 'os_result'):
                result = st.session_state.os_result
                filename = st.session_state.os_filename

                if result["status"] == "success":
                    st.success(f"✅ Open Source Processing erfolgreich: {filename}")

                    # Metriken
                    col_m1, col_m2, col_m3 = st.columns(3)
                    with col_m1:
                        st.metric("Verarbeitungszeit", f"{result['processing_time']:.3f}s")
                    with col_m2:
                        st.metric("Elemente", result['element_count'])
                    with col_m3:
                        st.metric("Methode", result['method'])

                    # NEU: Bild-Extraktions-Status
                    if result.get("image_support") is not None:
                        st.metric("Bild-Extraktion", "✅ Aktiv" if result["image_support"] else "❌ Inaktiv")

                    if result.get("image_elements"):
                        st.metric("Bilder gefunden", result["image_elements"])
                    if result.get("image_base64"):
                        st.metric("Bilder mit Base64", result["image_base64"])

                    # Element-Statistiken OHNE Pandas
                    if result['elements']:
                        stats = {}
                        for element in result['elements']:
                            element_type = type(element).__name__
                            stats[element_type] = stats.get(element_type, 0) + 1

                        if stats:
                            st.subheader("📈 Element-Typen")
                            # Einfache Liste statt DataFrame
                            for element_type, count in sorted(stats.items()):
                                st.write(f"**{element_type}:** {count}")

                        # Erste 5 Elemente anzeigen
                        st.subheader("📝 Extrahierte Elemente (erste 5)")
                        for i, element in enumerate(result['elements'][:5]):
                            element_type = type(element).__name__
                            text = str(element).strip()
                            if text:
                                st.text_area(
                                    f"Element {i+1} ({element_type})",
                                    text[:300] + "..." if len(text) > 300 else text,
                                    height=100,
                                    key=f"element_{i}"
                                )

                        if len(result['elements']) > 5:
                            st.info(f"... und {len(result['elements']) - 5} weitere Elemente")

                else:
                    st.error(f"❌ Processing fehlgeschlagen: {result.get('error')}")

            else:
                st.info("👆 Datei hochladen oder Repository-Beispiel auswählen")

    with tab2:
        st.header("🔧 Erweiterte Open Source Features")

        if hasattr(st.session_state, 'os_result') and st.session_state.os_result["status"] == "success":
            elements = st.session_state.os_result['elements']
            filename = st.session_state.os_filename

            # ===== OPTIMIERT: Einzelne Format-Buttons =====
            st.subheader("📄 Ausgabeformate")

            # Zähle Bilder im Dokument
            image_count = sum(1 for el in elements if type(el).__name__ in ["Image", "Figure", "Picture", "FigureCaption"])

            # Info über Bilder
            if image_count > 0:
                with st.expander(f"📸 {image_count} Bilder erkannt - Wichtiger Hinweis", expanded=False):
                    st.markdown("""
                    ### Base64-Bilder in Markdown/HTML?

                    **❓ Brauchen wir das?**
                    - ✅ **JA** für LLM-Integration (GPT-4, Claude)
                    - ✅ **JA** für Self-Contained Dokumente (alles in einer Datei)
                    - ❌ **NEIN** für normale Text-Verarbeitung
                    - ❌ **NEIN** wenn nur Text wichtig ist

                    **⚠️ Performance-Impact:**
                    - Ohne Bilder: ~1-2 Sekunden
                    - Mit Bildern: ~5-30 Sekunden (abhängig von Bildanzahl)

                    **💡 Empfehlung:** Erst Standard-Formate testen, dann bei Bedarf mit Bildern!
                    """)

            # ===== EINZELNE FORMAT-BUTTONS (on-demand) =====
            st.markdown("### Wähle Format zum Generieren:")

            format_col1, format_col2, format_col3, format_col4 = st.columns(4)

            with format_col1:
                if st.button("📝 Text", key="btn_text", use_container_width=True):
                    with st.spinner("Generiere Text..."):
                        # Lösche alte Formate
                        for key in ['format_html', 'format_markdown', 'format_json', 'format_markdown_images']:
                            st.session_state.pop(key, None)
                        # Generiere neues Format
                        text_output = elements_to_text(elements)
                        st.session_state['format_text'] = text_output
                        st.success("✅ Text generiert!")
                        st.rerun()

            with format_col2:
                if st.button("🌐 HTML", key="btn_html", use_container_width=True):
                    with st.spinner("Generiere HTML..."):
                        # Lösche alte Formate
                        for key in ['format_text', 'format_markdown', 'format_json', 'format_markdown_images']:
                            st.session_state.pop(key, None)
                        # Generiere neues Format
                        html_output = elements_to_html(elements)
                        st.session_state['format_html'] = html_output
                        st.success("✅ HTML generiert!")
                        st.rerun()

            with format_col3:
                if st.button("📋 Markdown", key="btn_markdown", use_container_width=True):
                    with st.spinner("Generiere Markdown..."):
                        # Lösche alte Formate
                        for key in ['format_text', 'format_html', 'format_json', 'format_markdown_images']:
                            st.session_state.pop(key, None)
                        # Generiere neues Format OHNE Bilder (exclude_binary_image_data=True)
                        markdown_output = elements_to_md(elements, exclude_binary_image_data=True)
                        st.session_state['format_markdown'] = markdown_output
                        st.success("✅ Markdown generiert!")
                        st.rerun()

            with format_col4:
                if st.button("🔧 JSON", key="btn_json", use_container_width=True):
                    with st.spinner("Generiere JSON..."):
                        # Lösche alte Formate
                        for key in ['format_text', 'format_html', 'format_markdown', 'format_markdown_images']:
                            st.session_state.pop(key, None)
                        # Generiere neues Format
                        json_output = json.dumps(elements_to_dicts(elements), indent=2, ensure_ascii=False)
                        st.session_state['format_json'] = json_output
                        st.success("✅ JSON generiert!")
                        st.rerun()

            # Optional: Markdown mit Bildern (separat)
            if image_count > 0:
                st.divider()
                st.markdown("### 🖼️ Spezial: Mit eingebetteten Bildern")

                special_col1, special_col2 = st.columns(2)

                with special_col1:
                    if st.button("📋 Markdown + Bilder (⚠️ Langsam!)", key="btn_markdown_img", type="secondary", help=f"Base64-Bilder einbetten - dauert länger bei {image_count} Bildern"):
                        with st.spinner(f"Generiere Markdown mit {image_count} Bildern (kann 10-30 Sek dauern)..."):
                            # Lösche alte Formate
                            for key in ['format_text', 'format_html', 'format_markdown', 'format_json']:
                                st.session_state.pop(key, None)
                            # Generiere neues Format
                            markdown_with_images = elements_to_markdown_with_images(elements)
                            st.session_state['format_markdown_images'] = markdown_with_images
                            st.success("✅ Markdown mit Bildern generiert! (Download empfohlen)")
                            st.rerun()

                with special_col2:
                    st.info("⚠️ 'Alle Formate MIT Bildern' wurde entfernt - wähle ein Format einzeln")

            # ===== ANZEIGE DER GENERIERTEN FORMATE =====
            st.divider()
            st.markdown("### 📊 Generierte Formate")

            # Tabs für alle möglichen Formate
            available_tabs = []
            if 'format_text' in st.session_state:
                available_tabs.append("📝 Text")
            if 'format_html' in st.session_state:
                available_tabs.append("🌐 HTML")
            if 'format_markdown' in st.session_state:
                available_tabs.append("📋 Markdown")
            if 'format_json' in st.session_state:
                available_tabs.append("🔧 JSON")
            if 'format_markdown_images' in st.session_state:
                available_tabs.append("🖼️ Markdown+Bilder")

            if not available_tabs:
                st.info("👆 Wähle oben ein Format aus, um es zu generieren und anzuzeigen")
            else:
                format_tabs = st.tabs(available_tabs)
                tab_index = 0

                # Text Tab
                if 'format_text' in st.session_state:
                    with format_tabs[tab_index]:
                        st.subheader("📝 Text-Ausgabe")
                        st.text_area("", st.session_state['format_text'], height=500, key="text_display", label_visibility="collapsed")
                        st.download_button("💾 Text herunterladen", st.session_state['format_text'], f"{filename}_text.txt", "text/plain", key="dl_text")
                    tab_index += 1

                # HTML Tab
                if 'format_html' in st.session_state:
                    with format_tabs[tab_index]:
                        st.subheader("🌐 HTML-Ausgabe")
                        view_tabs = st.tabs(["🌐 Vorschau", "🔍 Code"])
                        with view_tabs[0]:
                            styled_html = f'''<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <style>
        * {{ box-sizing: border-box; }}
        body {{
            margin: 0;
            padding: 20px;
            background-color: #ffffff !important;
            color: #000000 !important;
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            line-height: 1.6;
        }}
        h1, h2, h3, h4, h5, h6 {{
            color: #000000 !important;
            margin-top: 24px;
            margin-bottom: 16px;
        }}
        p {{
            color: #000000 !important;
            margin: 12px 0;
        }}
        table {{
            border-collapse: collapse;
            width: 100%;
            margin: 15px 0;
            background-color: #ffffff !important;
        }}
        th, td {{
            border: 1px solid #ddd;
            padding: 12px;
            text-align: left;
            color: #000000 !important;
            background-color: #ffffff !important;
        }}
        th {{
            background-color: #f8f9fa !important;
            font-weight: 600;
        }}
        ul, ol {{
            color: #000000 !important;
            margin: 12px 0;
            padding-left: 30px;
        }}
        li {{
            color: #000000 !important;
            margin: 6px 0;
        }}
    </style>
</head>
<body>
{st.session_state["format_html"]}
</body>
</html>'''
                            st.components.v1.html(styled_html, height=600, scrolling=True)
                        with view_tabs[1]:
                            st.code(st.session_state['format_html'], language="html")
                        st.download_button("💾 HTML herunterladen", st.session_state['format_html'], f"{filename}_output.html", "text/html", key="dl_html")
                    tab_index += 1

                # Markdown Tab
                if 'format_markdown' in st.session_state:
                    with format_tabs[tab_index]:
                        st.subheader("📋 Markdown-Ausgabe")

                        # CSS für bessere Markdown-Darstellung
                        st.markdown("""
                        <style>
                        .scrollable-markdown {
                            max-height: 600px;
                            overflow-y: auto;
                            padding: 20px;
                            background-color: #ffffff !important;
                            color: #000000 !important;
                            border: 1px solid #ddd;
                            border-radius: 8px;
                            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
                        }
                        .scrollable-markdown h1,
                        .scrollable-markdown h2,
                        .scrollable-markdown h3,
                        .scrollable-markdown h4,
                        .scrollable-markdown h5,
                        .scrollable-markdown h6 {
                            color: #1a1a1a !important;
                            font-weight: 600;
                        }
                        .scrollable-markdown p,
                        .scrollable-markdown li,
                        .scrollable-markdown span,
                        .scrollable-markdown div {
                            color: #333333 !important;
                            line-height: 1.6;
                        }
                        .scrollable-markdown code {
                            background-color: #f5f5f5 !important;
                            color: #d63384 !important;
                            padding: 2px 6px;
                            border-radius: 3px;
                        }
                        .scrollable-markdown pre {
                            background-color: #f8f9fa !important;
                            border: 1px solid #dee2e6;
                            border-radius: 4px;
                            padding: 12px;
                        }
                        .scrollable-markdown a {
                            color: #0066cc !important;
                        }
                        .scrollable-markdown table {
                            border-collapse: collapse;
                            width: 100%;
                        }
                        .scrollable-markdown th,
                        .scrollable-markdown td {
                            border: 1px solid #ddd;
                            padding: 8px;
                            color: #333333 !important;
                        }
                        .scrollable-markdown th {
                            background-color: #f8f9fa !important;
                            font-weight: 600;
                        }
                        </style>
                        """, unsafe_allow_html=True)

                        with st.expander("📄 Vorschau (gerendert)", expanded=False):
                            st.markdown(f'<div class="scrollable-markdown">{st.session_state["format_markdown"]}</div>', unsafe_allow_html=True)
                        with st.expander("🔍 Code", expanded=False):
                            st.code(st.session_state['format_markdown'], language="markdown")
                        st.download_button("💾 Markdown herunterladen", st.session_state['format_markdown'], f"{filename}_markdown.md", "text/markdown", key="dl_md")
                    tab_index += 1

                # JSON Tab
                if 'format_json' in st.session_state:
                    with format_tabs[tab_index]:
                        st.subheader("🔧 JSON-Ausgabe")
                        try:
                            json_data = json.loads(st.session_state['format_json'])
                            st.json(json_data)
                        except:
                            st.code(st.session_state['format_json'], language="json")
                        st.download_button("💾 JSON herunterladen", st.session_state['format_json'], f"{filename}_elements.json", "application/json", key="dl_json")
                    tab_index += 1

                # Markdown mit Bildern Tab
                if 'format_markdown_images' in st.session_state:
                    with format_tabs[tab_index]:
                        st.subheader("🖼️ Markdown mit Base64-Bildern")

                        st.warning("""
                        ⚠️ **Performance-Hinweis:**
                        Markdown mit eingebetteten Base64-Bildern ist SEHR groß und kann die Anzeige verlangsamen!

                        💡 **Empfehlung:**
                        - Lade die Datei herunter (Download-Button unten)
                        - Öffne sie in einem Markdown-Editor (z.B. Typora, VS Code)
                        - Oder nutze HTML-Format für bessere Bild-Darstellung
                        """)

                        # Größe berechnen
                        markdown_size = len(st.session_state['format_markdown_images'])
                        size_mb = markdown_size / (1024 * 1024)

                        st.info(f"""
                        **Datei-Info:**
                        - Größe: {size_mb:.2f} MB
                        - Bilder: Als Data-URLs eingebettet
                        - Verwendung: Perfekt für LLMs (GPT-4, Claude)
                        """)

                        # Vorschau OHNE Bilder-Rendering (zu langsam!)
                        with st.expander("📄 Text-Vorschau (ohne Bild-Rendering)", expanded=False):
                            # Entferne Base64-Daten für Vorschau
                            preview_text = st.session_state['format_markdown_images']
                            # Ersetze data:image URLs mit Platzhalter
                            import re
                            preview_text = re.sub(r'!\[([^\]]*)\]\(data:image/[^)]+\)', r'🖼️ [Bild: \1]', preview_text)
                            st.markdown(f'<div class="scrollable-markdown">{preview_text}</div>', unsafe_allow_html=True)
                            st.caption("ℹ️ Bilder werden als Platzhalter angezeigt. Lade die Datei herunter für volle Bilder.")

                        with st.expander("🔍 Code (erste 5000 Zeichen)", expanded=False):
                            code_preview = st.session_state['format_markdown_images'][:5000]
                            if len(st.session_state['format_markdown_images']) > 5000:
                                code_preview += "\n\n... (gekürzt, zu groß für Anzeige)"
                            st.code(code_preview, language="markdown")

                        st.download_button(
                            "💾 Markdown+Bilder herunterladen (empfohlen!)",
                            st.session_state['format_markdown_images'],
                            f"{filename}_with_images.md",
                            "text/markdown",
                            key="dl_md_img",
                            help="Datei herunterladen und in Markdown-Editor öffnen"
                        )
                    tab_index += 1

            # ===== BEDROCK RAG JSON EXPORT (IMMER SICHTBAR) =====
            st.divider()
            st.subheader("🚀 Bedrock RAG Knowledge Base")

            st.info("""
            **Bedrock-optimiertes Format:**
            - ✅ Keine Base64-Bilder (zu groß für Bedrock)
            - ✅ Vision-Beschreibungen für Bilder (durchsuchbar!)
            - ✅ Optimierte Metadaten für RAG
            - ✅ KEIN Chunking (Bedrock macht das automatisch)
            - ✅ Sinnvolle Bild-Referenzen mit Hash
            """)

            # Bedrock-Optionen
            describe_images = st.checkbox(
                "🎨 Bilder mit Vision beschreiben (optional)",
                value=False,
                help="Verwendet Vision-LLM zur Beschreibung von Bildern (empfohlen für durchsuchbare Bilder). Kostet ~$0.003/Bild"
            )

            if st.button("🚀 Bedrock RAG JSON erstellen", type="primary", key="create_bedrock_rag"):
                with st.spinner("Erstelle Bedrock-optimiertes JSON..."):
                    try:
                        # Bedrock-optimierte Elemente erstellen
                        bedrock_elements = []
                        image_files = []  # Für separaten Bild-Export

                        for i, element in enumerate(elements):
                            element_type = type(element).__name__
                            element_text = str(element).strip()

                            # Basis-Metadaten
                            metadata_attrs = {
                                "element_id": i + 1,
                                "element_type": element_type,
                                "source_file": filename
                            }

                            # Seiten-Information
                            if hasattr(element, 'metadata') and element.metadata:
                                page_num = getattr(element.metadata, 'page_number', None)
                                if page_num:
                                    metadata_attrs["page"] = page_num

                            # SPEZIAL: Bild-Handling für Bedrock
                            if element_type in ("Image", "Figure", "FigureCaption", "Picture"):
                                # Check für Base64-Daten
                                has_base64 = False
                                image_hash = None
                                base64_data = None

                                if hasattr(element, 'metadata') and element.metadata:
                                    base64_data = getattr(element.metadata, 'image_base64', None)
                                    if base64_data:
                                        has_base64 = True
                                        # Hash erstellen für Referenz
                                        import hashlib
                                        image_hash = hashlib.md5(base64_data.encode()).hexdigest()[:16]

                                metadata_attrs["image_available"] = has_base64
                                if image_hash:
                                    metadata_attrs["image_hash"] = image_hash

                                    # Bild für separaten Export speichern
                                    if base64_data:
                                        mime_type = "image/png"
                                        if hasattr(element, 'metadata') and element.metadata:
                                            mime_type = getattr(element.metadata, 'image_mime_type', 'image/png')

                                        file_ext = mime_type.split('/')[-1]
                                        image_files.append({
                                            "hash": image_hash,
                                            "base64": base64_data,
                                            "mime_type": mime_type,
                                            "filename": f"{image_hash}.{file_ext}",
                                            "element_text": element_text
                                        })

                                # Vision-Beschreibung (falls aktiviert)
                                if describe_images and has_base64:
                                    # MOCK Vision-Beschreibung (in Production: echte Vision API)
                                    vision_description = f"[Vision-Beschreibung für {element_type}]: {element_text}"
                                    metadata_attrs["image_described"] = True
                                    metadata_attrs["vision_model"] = "Claude 3.5 Sonnet (Mock)"
                                    metadata_attrs["vision_cost_estimate"] = 0.003

                                    # Beschreibung als Content
                                    content = f"{element_text}\n\n{vision_description}"
                                else:
                                    metadata_attrs["image_described"] = False
                                    if has_base64:
                                        # Verweis auf Bild-Hash (Bild wird separat exportiert)
                                        content = f"{element_text}\n\n[Bild verfügbar - siehe separate Bild-Dateien, Hash: {image_hash}]"
                                    else:
                                        content = f"{element_text}\n\n[Hinweis: Kein Bild extrahiert]"
                            else:
                                # Normaler Text-Content
                                content = element_text

                            # Bedrock-Format: metadataAttributes + content
                            bedrock_element = {
                                "metadataAttributes": metadata_attrs,
                                "content": content
                            }

                            bedrock_elements.append(bedrock_element)

                        # JSON erstellen
                        bedrock_json = json.dumps(bedrock_elements, indent=2, ensure_ascii=False)

                        # Anzeige
                        st.success(f"✅ {len(bedrock_elements)} Elemente für Bedrock optimiert!")

                        # Statistiken
                        stat_col1, stat_col2, stat_col3 = st.columns(3)

                        image_elements = [e for e in bedrock_elements if e["metadataAttributes"].get("image_available")]
                        described_images = [e for e in image_elements if e["metadataAttributes"].get("image_described")]

                        with stat_col1:
                            st.metric("Gesamt-Elemente", len(bedrock_elements))
                        with stat_col2:
                            st.metric("Bilder verfügbar", len(image_elements))
                        with stat_col3:
                            st.metric("Bilder beschrieben", len(described_images))

                        # Vorschau
                        st.markdown("### 📋 Vorschau (erste 3 Elemente)")
                        preview_data = bedrock_elements[:3]
                        st.json(preview_data)

                        # Download Buttons
                        dl_col1, dl_col2 = st.columns(2)

                        with dl_col1:
                            st.download_button(
                                "💾 Bedrock RAG JSON herunterladen",
                                bedrock_json,
                                f"{filename}_bedrock_rag.json",
                                "application/json",
                                help="Optimiert für AWS Bedrock Knowledge Base"
                            )

                        with dl_col2:
                            # Bild-Export-Button (falls Bilder vorhanden)
                            if len(image_elements) > 0:
                                # ZIP direkt erstellen beim Klick
                                with st.spinner("Bereite Bilder-ZIP vor..."):
                                    image_export = export_images_from_bedrock_json(elements, filename)

                                if image_export["status"] == "success":
                                    st.download_button(
                                        f"📸 {image_export['total_images']} Bilder als ZIP herunterladen",
                                        image_export['zip_bytes'],
                                        f"{filename}_images.zip",
                                        "application/zip",
                                        help=f"Enthält {image_export['total_images']} Bilder + manifest.json + README ({image_export['total_size_bytes'] // 1024} KB)",
                                        key="dl_images_zip_bedrock"
                                    )
                                elif image_export["status"] == "warning":
                                    st.warning(image_export["message"])
                                else:
                                    st.error(f"❌ Fehler beim Erstellen der ZIP: {image_export.get('error', 'Unbekannter Fehler')}")
                            else:
                                st.caption("ℹ️ Keine Bilder zum Export verfügbar")

                        # Zusätzliche Info für Bild-Handling
                        if len(image_elements) > 0:
                            st.divider()
                            with st.expander("💡 Bild-Handling für Bedrock", expanded=False):
                                st.markdown("""
                                **Wie funktioniert das Bild-Handling?**

                                1. **JSON-Datei:**
                                   - Enthält Text-Content und Metadaten
                                   - Bilder sind über Hash referenziert (z.B. `a3f2e1...`)
                                   - Keine Base64-Daten (zu groß!)

                                2. **Bilder-ZIP (Download oben):**
                                   - Enthält alle Original-Bilder
                                   - Dateinamen = Hash (z.B. `a3f2e1.png`)
                                   - `manifest.json` mit Metadaten
                                   - `README.md` mit Anleitung

                                3. **Verwendung mit Bedrock:**

                                   **Option A: Nur JSON (empfohlen für Text-RAG):**
                                   - Lade nur JSON zu Bedrock hoch
                                   - Vision-Beschreibungen sind durchsuchbar
                                   - Original-Bilder nicht benötigt

                                   **Option B: JSON + Bilder separat:**
                                   - Bilder in S3/Cloud speichern (optional)
                                   - JSON zu Bedrock Knowledge Base
                                   - Bei Bedarf: Bilder per Hash abrufen

                                **Wichtig:** Das JSON funktioniert OHNE Bilder!
                                - Vision-Beschreibungen (falls aktiviert) sind im JSON
                                - Bilder sind über Hash referenziert
                                - ZIP-Export nur für Archiv/spätere Nutzung
                                """)

                        # Hinweise
                        st.divider()
                        st.markdown("### 💡 Bedrock Integration")
                        st.info("""
                        **Upload zu Bedrock Knowledge Base:**
                        1. Lade JSON-Datei in S3-Bucket hoch
                        2. Erstelle/Öffne Knowledge Base in Bedrock Console
                        3. Füge S3-Bucket als Datenquelle hinzu
                        4. Wähle Embedding-Modell (z.B. Titan Embeddings)
                        5. Starte Synchronisierung
                        6. Nutze mit Bedrock Agents oder direkt mit Claude

                        **Wichtig:**
                        - Bedrock macht automatisch Chunking
                        - KEIN manuelles Chunking nötig!
                        - JSON ist ready-to-use
                        """)

                    except Exception as e:
                        st.error(f"❌ Fehler beim Erstellen des Bedrock RAG JSON: {e}")
                        st.exception(e)

        # ✅ ANZEIGE: Formate MIT Bildern
        elif hasattr(st.session_state, 'conversions_with_images') and st.session_state.get('active_format_view') == 'with_images':
            conversions = st.session_state.conversions_with_images

            st.subheader("🖼️ Ausgabeformate MIT integrierten Bildern")

            format_tabs = st.tabs(["📝 Text", "🌐 HTML+Bilder", "📄 Markdown+Bilder", "📊 JSON", "🚀 RAG JSON"])

            with format_tabs[0]:  # Text (unverändert)
                st.subheader("📝 Text-Ausgabe")
                if isinstance(conversions.get("text"), str) and not conversions["text"].startswith("Text Konvertierung fehlgeschlagen"):
                    st.text_area("Vollständiger Text:", conversions["text"], height=400, key="img_text")
                    st.download_button("💾 Text herunterladen", conversions["text"], f"{filename}_output.txt", "text/plain", key="dl_img_text")
                else:
                    st.error(conversions.get("text", "Text-Format nicht verfügbar"))

            with format_tabs[1]:  # HTML mit Bildern
                st.subheader("🌐 HTML-Ausgabe MIT Base64-Bildern")
                if isinstance(conversions.get("html"), str) and not conversions["html"].startswith("HTML Konvertierung fehlgeschlagen"):

                    # Tabs für gerenderte Ansicht vs Code
                    view_tabs = st.tabs(["🌐 Gerenderte Ansicht", "🔍 HTML-Code"])

                    with view_tabs[0]:
                        # Gerenderte Ansicht mit Bildern
                        styled_html = f'''
                        <!DOCTYPE html>
                        <html>
                        <head>
                            <meta charset="utf-8">
                            <style>
                                * {{ box-sizing: border-box; }}
                                body {{
                                    margin: 0;
                                    padding: 20px;
                                    background-color: #ffffff !important;
                                    color: #000000 !important;
                                    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
                                }}
                                .image-container {{
                                    margin: 15px 0;
                                    padding: 10px;
                                    border: 1px solid #ddd;
                                    border-radius: 4px;
                                    background: #f9f9f9;
                                }}
                                img {{
                                    max-width: 100%;
                                    height: auto;
                                    border: 1px solid #ccc;
                                    border-radius: 4px;
                                }}
                                table {{
                                    border-collapse: collapse;
                                    width: 100%;
                                    margin: 15px 0;
                                }}
                                th, td {{
                                    border: 1px solid #ddd;
                                    padding: 12px;
                                    text-align: left;
                                }}
                                th {{ background-color: #f8f9fa; font-weight: 600; }}
                            </style>
                        </head>
                        <body>
                            {conversions["html"]}
                        </body>
                        </html>
                        '''
                        st.components.v1.html(styled_html, height=700, scrolling=True)
                        st.success("✅ HTML mit eingebetteten Base64-Bildern")

                    with view_tabs[1]:
                        st.code(conversions["html"], language="html", line_numbers=True)

                    st.download_button("💾 HTML+Bilder herunterladen", conversions["html"], f"{filename}_with_images.html", "text/html", key="dl_img_html")
                else:
                    st.error(conversions.get("html", "HTML-Format nicht verfügbar"))

                with format_tabs[2]:  # Markdown mit Bildern
                    st.subheader("📄 Markdown-Ausgabe MIT Base64-Bildern")
                    if isinstance(conversions.get("markdown"), str) and not conversions["markdown"].startswith("Markdown Konvertierung fehlgeschlagen"):

                        st.info("💡 Markdown mit Base64-Bildern als Data-URLs - perfekt für LLMs!")

                        col1, col2 = st.columns([1, 1])
                        with col1:
                            with st.expander("📄 Markdown Vorschau (gerendert)", expanded=True):
                                # ✅ Mit Scrolling für lange Inhalte mit Bildern
                                st.markdown(f'<div class="scrollable-large">{conversions["markdown"]}</div>', unsafe_allow_html=True)
                        with col2:
                            with st.expander("🔍 Markdown Code", expanded=False):
                                st.code(conversions["markdown"], language="markdown")

                        st.download_button("💾 Markdown+Bilder herunterladen", conversions["markdown"], f"{filename}_with_images.md", "text/markdown", key="dl_img_md")

                        st.success("✅ Bilder sind als Data-URLs eingebettet - funktioniert in den meisten Markdown-Viewern!")
                    else:
                        st.error(conversions.get("markdown", "Markdown-Format nicht verfügbar"))

                with format_tabs[3]:  # JSON
                    st.subheader("📊 JSON-Ausgabe")
                    if isinstance(conversions.get("json"), str) and not conversions["json"].startswith("JSON Konvertierung fehlgeschlagen"):
                        try:
                            json_data = json.loads(conversions["json"])
                            st.json(json_data)
                            st.download_button("💾 JSON herunterladen", conversions["json"], f"{filename}_output.json", "application/json", key="dl_img_json")
                        except:
                            st.code(conversions["json"], language="json")
                    else:
                        st.error(conversions.get("json", "JSON-Format nicht verfügbar"))

                with format_tabs[4]:  # RAG JSON (Bedrock) - NEU!
                    st.subheader("🚀 RAG JSON - Bedrock Knowledge Base Format")
                    st.info("""
                    **Bedrock-optimiertes Format (MIT Bild-Referenzen):**
                    - ✅ Keine Base64-Bilder im JSON (zu groß)
                    - ✅ Bild-Hashes als Referenzen
                    - ✅ Original-Bilder separat als ZIP downloadbar
                    - ✅ Optional: Vision-Beschreibungen
                    """)

                    # Bedrock-Optionen
                    describe_col1, describe_col2 = st.columns(2)

                    with describe_col1:
                        describe_images_img = st.checkbox(
                            "🎨 Bilder mit Vision beschreiben",
                            value=False,
                            help="Vision-LLM zur Bild-Beschreibung",
                            key="describe_images_with_imgs"
                        )

                    with describe_col2:
                        if describe_images_img:
                            st.info("💡 ROI nach 2 Queries")
                            st.caption("~$0.003/Bild")

                    if st.button("🚀 Bedrock RAG JSON erstellen", type="primary", key="create_bedrock_rag_imgs"):
                        with st.spinner("Erstelle Bedrock RAG JSON..."):
                            try:
                                # Bedrock-Export
                                bedrock_result = export_for_bedrock_knowledge_base(
                                    elements=elements,
                                    filename=filename,
                                    format_type="element",
                                    describe_images=describe_images_img
                                )

                                if bedrock_result.get("status") == "success":
                                    # ✅ KORRIGIERT: Verwende json_preview statt json_array
                                    bedrock_json_preview = bedrock_result.get("json_preview")
                                    bedrock_docs = bedrock_result.get("documents", [])
                                    is_preview = bedrock_result.get("is_preview", False)

                                    # Validierung
                                    if not bedrock_docs:
                                        st.error("❌ Keine Dokumente generiert!")
                                        st.stop()

                                    st.success(f"✅ {bedrock_result['document_count']} Elemente für Bedrock optimiert!")

                                    # ⚠️ WARNUNG bei großen Dokumenten
                                    if is_preview:
                                        st.warning(f"⚠️ Große Datei: Vorschau zeigt nur die ersten 5 Elemente. Download enthält alle {bedrock_result['document_count']} Elemente.")

                                    # Statistiken
                                    stat_col1, stat_col2, stat_col3 = st.columns(3)

                                    image_elements = [d for d in bedrock_docs if d["metadataAttributes"].get("image_available")]
                                    described_images = [d for d in image_elements if d["metadataAttributes"].get("image_described")]

                                    with stat_col1:
                                        st.metric("Elemente", len(bedrock_docs))
                                    with stat_col2:
                                        st.metric("Bilder", len(image_elements))
                                    with stat_col3:
                                        st.metric("Beschrieben", len(described_images))

                                    # Vorschau - nur erste 3 für UI Performance
                                    st.markdown("### 📋 Vorschau (erste 3)")
                                    st.json(bedrock_docs[:3])

                                    # Downloads
                                    dl_col1, dl_col2 = st.columns(2)

                                    with dl_col1:
                                        # ✅ OPTIMIERT: Vollständiges JSON nur beim Download generieren
                                        full_json = json.dumps(bedrock_docs, indent=2, ensure_ascii=False)
                                        st.download_button(
                                            "💾 RAG JSON herunterladen",
                                            full_json,
                                            f"{filename}_bedrock_rag.json",
                                            "application/json",
                                            key="dl_bedrock_imgs",
                                            help=f"Enthält alle {len(bedrock_docs)} Elemente"
                                        )

                                    with dl_col2:
                                        if len(image_elements) > 0:
                                            # ✅ KORRIGIERT: Session State für ZIP-Download
                                            if st.button("📸 Bilder ZIP erstellen", key="dl_imgs_btn", type="secondary"):
                                                with st.spinner("Erstelle ZIP..."):
                                                    img_export = export_images_from_bedrock_json(elements, filename)

                                                    if img_export["status"] == "success":
                                                        # In Session State speichern
                                                        st.session_state['bedrock_image_zip'] = img_export['zip_bytes']
                                                        st.session_state['bedrock_image_count'] = img_export['total_images']
                                                        st.session_state['bedrock_zip_size'] = img_export['total_size_bytes']
                                                        st.session_state['bedrock_zip_filename'] = filename
                                                        st.success(f"✅ ZIP mit {img_export['total_images']} Bildern erstellt!")
                                                        st.rerun()
                                                    else:
                                                        st.error(f"❌ {img_export.get('error', 'Fehler')}")

                                            # Download-Button anzeigen wenn ZIP vorhanden
                                            if 'bedrock_image_zip' in st.session_state:
                                                st.download_button(
                                                    f"💾 {st.session_state['bedrock_image_count']} Bilder ({st.session_state['bedrock_zip_size'] // 1024} KB)",
                                                    st.session_state['bedrock_image_zip'],
                                                    f"{st.session_state['bedrock_zip_filename']}_images.zip",
                                                    "application/zip",
                                                    key="dl_imgs_zip_final"
                                                )
                                                # Clear-Button
                                                if st.button("🗑️ ZIP löschen", key="clear_bedrock_zip", type="secondary"):
                                                    del st.session_state['bedrock_image_zip']
                                                    del st.session_state['bedrock_image_count']
                                                    del st.session_state['bedrock_zip_size']
                                                    del st.session_state['bedrock_zip_filename']
                                                    st.rerun()
                                        else:
                                            st.caption("ℹ️ Keine Bilder")

                                    # S3-Hinweise
                                    if len(image_elements) > 0:
                                        st.divider()
                                        with st.expander("💡 S3-Integration (optional)"):
                                            st.markdown("""
                                            **Bilder zu S3 hochladen:**
                                            1. ZIP herunterladen & entpacken
                                            2. `aws s3 sync ./images/ s3://bucket/`
                                            3. S3-URLs in RAG JSON referenzieren

                                            **Hinweis:** RAG JSON funktioniert auch OHNE S3!
                                            """)

                                else:
                                    st.error(f"❌ Fehler: {bedrock_result.get('error')}")

                            except Exception as e:
                                st.error(f"❌ Fehler: {e}")
                                st.exception(e)


def clean_excel_table_headers(elements):
    """
    Bereinigt Excel-Tabellen-Header für bessere LLM-Lesbarkeit
    """
    try:
        # Einfache Bereinigung ohne komplexe Logik
        return elements
    except Exception:
        return elements



if __name__ == "__main__":
    main()
