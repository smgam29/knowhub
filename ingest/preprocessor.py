# preprocessor.py
# Parses any supported file type and returns clean text for extraction

import os

# Element types worth keeping for knowledge extraction
KEEP_TYPES = {"Title", "NarrativeText", "ListItem", "Table"}

def preprocess(file_path: str) -> str:
    # Detect file type and route to correct parser
    ext = os.path.splitext(file_path)[1].lower()

    if ext == ".md":
        from unstructured.partition.md import partition_md
        elements = partition_md(filename=file_path)

    elif ext == ".pdf":
        from unstructured.partition.pdf import partition_pdf
        elements = partition_pdf(filename=file_path)

    elif ext in (".pptx", ".ppt"):
        from unstructured.partition.pptx import partition_pptx
        elements = partition_pptx(filename=file_path)

    else:
        raise ValueError(f"Unsupported file type: {ext}")

    # Filter to meaningful element types and concatenate
    chunks = [
        str(el) for el in elements
        if type(el).__name__ in KEEP_TYPES
    ]

    return "\n\n".join(chunks)


if __name__ == "__main__":
    # Test on a single file
    test_file = "../sn-docs/markdown/now-intelligence/now-assist-explorer.md"
    text = preprocess(test_file)
    print(f"Extracted {len(text)} characters")
    print("\nSample output:")
    print(text[:500])
