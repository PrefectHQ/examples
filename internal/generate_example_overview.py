import glob
import re


def get_all_mdx_files() -> list[str]:
    files = glob.glob("*.mdx")
    return [f for f in files if f != "index.mdx"]


def generate_cards(files: list[str]) -> str:
    body = """<CardGroup cols={3}>\n"""

    for file in files:
        path, _ = file.split(".mdx")
        with open(file) as f:
            text = f.read()

        pattern = r"title:\s*(.+)\ndescription:\s*(.+)"
        header_info = re.search(pattern, text)

        if not header_info:
            raise ValueError(f"File {file} does not have a title or description")

        icon_pattern = r"icon:\s*(.+)"
        icon = re.search(icon_pattern, text)

        title = header_info.group(1)
        description = header_info.group(2)

        if icon:
            icon = icon.group(1)
        else:
            icon = "play"

        body += f"""
          <Card title="{title}" icon="{icon}" href="/v3/examples/{path}">
            {description}
          </Card>\n
          """

        print(f"Processed file {file}...")

    body += """</CardGroup>\n"""
    return body


def main():
    files = get_all_mdx_files()
    card_table = generate_cards(files)
    with open("index.mdx", "w") as f:
        f.write("""---\ntitle: Examples\n---\n""")
        f.write(card_table)


if __name__ == "__main__":
    main()
