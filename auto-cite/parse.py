import yaml
import os
from util import *
from importlib import import_module
from dict_hash import sha256

directory = os.path.dirname(os.path.realpath(__file__))

# config info for input/output files and plugins
config = {}
try:
    config = load_data("_config.yaml", type_check=False).get("auto-cite")
    if not config:
        raise Exception("Couldn't find auto-cite key in config")
except Exception as e:
    log(e, 3, "red")
    exit(1)

def format_authors(authors):
    return ", ".join(f"***{author}***" if "Qian Dong" in author else author for author in authors)

def get_year_from_date(date):
    return date.split("-")[0]

def parse_yaml_to_markdown(yaml_data):
    markdown_text = ""
    sorted_data = sorted(yaml_data, key=lambda x: x['date'], reverse=True)
    
    # Group data by year
    grouped_data = {}
    for entry in sorted_data:
        year = get_year_from_date(entry['date'])
        if year not in grouped_data:
            grouped_data[year] = []
        grouped_data[year].append(entry)

    # Generate Markdown text with grouped data
    for year, entries in grouped_data.items():
        # markdown_text += f"## {year}\n\n"
        markdown_text += f"<h2 align='center'>{year}</h2>\n\n"
        for entry in entries:
            title = entry['title']
            authors = format_authors(entry['authors'])
            link = entry['link']
            doi = entry['id']
            publisher = entry.get('publisher', '')
            # Combine publisher and link as a single string with a hyperlink
            publisher_with_link = f"[{publisher}]({link})"
            markdown_text += f"| **{title}** |\n"
            markdown_text += "| :------ |\n"
            markdown_text += f"| {authors} |\n"
            markdown_text += f"| {publisher}. [\\[Paper\\]]({link}) [\\[BibTeX\\]](_data/bibtexs/{doi}) |\n\n"

    return markdown_text

def replace_publications_and_awards_content(input_file_path, new_content):
    with open(input_file_path, "r", encoding="utf-8") as file:
        about_content = file.read()

    # Find the positions of "Publications" and "Honor and Awards" sections
    publications_start = about_content.find("Publications\n======")
    awards_start = about_content.find("Honor and Awards\n======")

    # Get the part before "Publications" and after "Honor and Awards"
    before_publications = about_content[:publications_start]
    after_awards = about_content[awards_start:]

    # Replace the content between "Publications" and "Honor and Awards" with new content
    updated_about_content = before_publications + "Publications\n======\n\n" + new_content + "\n\n" + after_awards

    return updated_about_content

yaml_data = open(os.path.join(directory, config["output"]), encoding="utf8")
parsed_data = yaml.safe_load(yaml_data)
parsed_data = parse_yaml_to_markdown(parsed_data)

file_path = "../_pages/about.md"
file_path = os.path.join(directory, file_path)
markdown_text = replace_publications_and_awards_content(file_path, parsed_data)
print(markdown_text)
# Save the final Markdown output to "output.md" file
with open(file_path, "w", encoding="utf-8") as file:
    file.write(markdown_text)
