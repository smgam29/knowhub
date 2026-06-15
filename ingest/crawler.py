import os

def get_markdown_files(docs_path):
    markdown_files = []

    for root, dirs, files in os.walk(docs_path):
        for file in files:
            if file.endswith('.md'):
              full_path = os.path.join(root, file)
              markdown_files.append(full_path)
    
    return markdown_files


if __name__ == "__main__":
    docs_path = os.path.expanduser("~/Documents/github/sn-docs/markdown")

    files = get_markdown_files(docs_path)
    print(f"Found {len(files)} markdown files:")
    print("\nFirst 5 files:")
    for file in files[:5]:
        print(file)