from util import *
from importlib import import_module
from dict_hash import sha256
import os

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

log("Compiling list of sources to cite")

# compile master list of sources from various plugins
sources = []

# error exit flag
will_exit = False

# loop through plugins
for plugin in config.get("plugins", []):
    # get plugin props
    name = plugin.get("name", "[no name]")
    files = plugin.get("input", [])

    # show progress
    log(f"Running {name} plugin")

    # loop through plugin input files
    for file in files:
        # show progress
        log(file, 2)

        plugin_sources = []
        try:
            # get data in file
            data = load_data(file)
            # run plugin
            plugin_sources = import_module(f"plugins.{name}").main(data)
        except Exception as e:
            log(e, 3, "red")
            will_exit = True

        log(f"Got {len(plugin_sources)} sources", 2, "green")

        for source in plugin_sources:
            # include meta info about plugin and source
            source["_plugin"] = name
            source["_input"] = file
            # make unique key for cache matching
            source["_cache"] = sha256(source)
            # add source
            sources.append(source)

# exit at end of loop if error occurred
if will_exit:
    log("One or more input files or plugins failed", 3, "red")
    exit(1)

log("Generating citations for sources")

# load existing citations
citations = []
try:
    citations = load_data(config["output"])
except Exception as e:
    log(e, 2, "yellow")

# error exit flag
will_exit = False

# list of new citations to overwrite existing citations
new_citations = []

# go through sources
for index, source in enumerate(sources):
    # show progress
    log(f"Source {index + 1} of {len(sources)} - {source.get('id', '[no ID]')}", 2)

    # new citation for source
    new_citation = {}

    # find same source in existing citations
    cached = get_cached(source, citations)

    if cached:
        # use existing citation to save time
        log("Using existing citation", 3)
        new_citation = cached

    elif source.get("id", "").strip():
        # use Manubot to generate new citation
        log("Using Manubot to generate new citation", 3)
        try:
            new_citation = cite_with_manubot(source)
        # if Manubot couldn't cite source
        except Exception as e:
            log(e, 3, "red")
            # if manually-entered source, throw error on cite failure
            if source.get("_plugin") == "sources":
                will_exit = True
            continue
    else:
        # pass source through untouched
        log("Passing source through", 3)

    # merge in properties from input source
    new_citation.update(source)
    # ensure date in proper format for correct date sorting
    new_citation["date"] = clean_date(new_citation.get("date"))

    # remove unwanted keys
    new_citation.pop("_plugin")
    new_citation.pop("_input")

    # add new citation to list
    new_citations.append(new_citation)

# exit at end of loop if error occurred
if will_exit:
    log("One or more sources failed to be cited", 3, "red")
    exit(1)

log("Exporting citations")

# save new citations
try:
    save_data(config["output"], new_citations)
except Exception as e:
    log(e, 2, "red")
    exit(1)

log(f"Exported {len(new_citations)} citations", 2, "green")

import yaml

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
        markdown_text += f"## {year}\n\n"
        for entry in entries:
            title = entry['title']
            authors = format_authors(entry['authors'])
            link = entry['link']
            publisher = entry.get('publisher', '')
            # Combine publisher and link as a single string with a hyperlink
            publisher_with_link = f"[{publisher}]({link})"
            markdown_text += f"| **{title}** |\n"
            markdown_text += "| :------ |\n"
            markdown_text += f"| {authors} |\n"
            markdown_text += f"| {publisher}. [\\[Paper\\]]({link}) |\n\n"

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

# Save the final Markdown output to "output.md" file
with open(file_path, "w", encoding="utf-8") as file:
    file.write(markdown_text)
