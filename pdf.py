from PyPDF2 import PdfMerger, PdfReader, PdfWriter
import click

from glob import glob
import os

def _check_pdfs(pdfs: list[str]) -> list[str]:
    """Checks if a list of PDF files exists.

    Args:
        pdfs (list[str]): List of PDF files

    Returns:
        list[str]: List of PDF files that exist
    """
    # TODO Check if PDF is encrypted
    return [pdf for pdf in pdfs if os.path.isfile(pdf) and pdf.endswith(".pdf")]

def _display_pdfs(pdfs: list[str]) -> None:
    """Displays a list of PDF files.

    Args:
        pdfs (list[str]): List of PDF files
    """
    click.echo(click.style(f"Found {len(pdfs)} PDFs to merge:", fg="blue"))
    for index, pdf in enumerate(pdfs):
        click.echo(f"{index+1:>3} {pdf}")

def _merge_pdfs(files: list[str], output_file: str) -> tuple[str, int]:
    """Merges a list of PDF files into one PDF file.

    Args:
        files (list[str]): List of PDF files to merge
        output_file (str): Name of the output PDF file

    Returns:
        tuple[str, int]: Name of the output PDF file, and the number of PDF files
    """
    merged_count = 0
    merger = PdfMerger()
    for file in files:
        try:
            merger.append(file)
            click.echo(click.style(f"Appended `{file}`", fg="green"))
            merged_count += 1
        except FileNotFoundError:
            click.echo(click.style(f"File `{file}` not found. Skipping", fg="red"))
            continue
        except Exception as e:
            click.echo(click.style(f"Error appending `{file}: {e}`. Skipping", fg="red"))
            continue
            
    if merger.pages:
        click.style(f"Merging PDFs...")
        merger.write(output_file)
        merger.close()

    return (output_file, merged_count)

def _sort_pdfs(files: list[str], sort_option: str = None) -> list[str]:
    """Sorts a list of PDF files based on a given option.

    Args:
        files (list[str]): List of files to sort
        sort_option (str): Sort option. Options are:
            - name: Sort by file name
            - date: Sort by file modification date
            - size: Sort by file size
            - ^name: Sort by file name in descending order
            - ^date: Sort by file modification date in descending order
            - ^size: Sort by file size in descending order
            - None: Do not sort the files. Return the original list.

    Returns:
        list[str]: Sorted list of files.
    """

    sort_key = None
    reverse_order = False

    if sort_option:
        if sort_option.startswith("^"):
            reverse_order = True
            sort_option = sort_option[1:]

        if sort_option == 'name':
            sort_key = lambda name: name.lower()
        elif sort_option == 'date':
            sort_key = os.path.getmtime
        elif sort_option == 'size':
            sort_key = os.path.getsize

        if sort_key:
            click.echo(click.style(f"Sorting PDFs by {sort_option} in " \
                f"{'descending' if reverse_order else 'ascending'} order.", 
                fg="yellow"))
            files.sort(key=sort_key, reverse=reverse_order)

    return files

def _compress_pdf(file: str, output_file: str = "compressed.pdf") -> tuple[str, int]:
    """Compresses a PDF file.

    Args:
        file (str): Name of the input PDF file
        output_file (str): Name of the output PDF file

    Returns:
        tuple[str, int]: Name of the output compressed PDF file and the file size
                         after compression
    """
    reader = PdfReader(file)
    writer = PdfWriter()

    for page in reader.pages:
        page.compress_content_streams()
        writer.add_page(page)

    with open(output_file, "wb") as f:
        writer.write(f)

    return (output_file, os.path.getsize(output_file))

# * Merge PDFs
# Merge a list of PDF files into one PDF file.
@click.command()
@click.argument(
    "files",
    nargs=-1,
    type=click.Path(exists=True, dir_okay=False),
)
@click.option(
    "--dir", "-d", 
    help="Directory containing PDF files to merge. " \
         "Defaults to current working directory.",
    default=os.getcwd(), 
    type=click.Path(exists=True, dir_okay=True), 
)
@click.option(
    "--pattern", "-p",
    help="Filename pattern to match. Wildcards (*, ?, [ranges]) are accepted.",
    default="*.pdf",
    show_default=True,
)
@click.option(
    "--from-list", "-L",
    help="File containing a list of PDF files to merge.",
    type=click.Path(exists=True, dir_okay=False),
)
@click.option(
    "--sort", "-s",
    help="Sort PDFs by a given option.",
    type=click.Choice([
        'name', 'date', 'size',
        '^name', '^date', '^size'
    ], 
    case_sensitive=False),
)
@click.option(
    "--output", "-o", 
    help="Output filename.",
    default="merged.pdf", 
    show_default=True, 
)
@click.option(
    "--yes", "-y",
    is_flag=True,
    help="Skip confirmation prompt."
)
def merge(yes, files, dir, pattern, from_list, sort, output) -> None:
    """Merges a list of PDF files into one PDF file."""

    if files:
        pdfs = [ os.path.join(dir, file) for file in files ]
    elif from_list:
        with open(from_list, "r") as f:
            pdfs = [ 
                line.strip() 
                for line in f.readlines() 
                if line.strip().endswith(".pdf")
            ]
    else:
        pdfs = glob(os.path.join(dir, pattern))

    pdfs = _check_pdfs(pdfs)
    _display_pdfs(pdfs)

    if sort:
        pdfs = _sort_pdfs(pdfs, sort)

    if not pdfs:
        click.echo(click.style("No PDFs found.", fg="red"))
        return

    if not yes:
        click.confirm(click.style("Are you sure you want to merge these PDFs?", 
            fg="yellow"), abort=True)

    output_file, merged_count = _merge_pdfs(pdfs, output)

    if merged_count:
        click.echo(click.style(f"Merged {merged_count} PDFs to `{output_file}`.", 
            fg="blue"))
    else:
        click.echo(click.style("No valid PDFs found to merge.", fg="red"))

# * Split PDF
# Split a PDF file into multiple PDF files.
@click.command()
def split():
    """Split a PDF file into multiple PDF files."""
    # TODO Implement split command
    # ! Not implemented yet
    click.echo(click.style("PDF split not yet implemented.", fg="yellow"))

# * Compress PDF
# Compress a PDF file. 
@click.command()
@click.argument(
    "file",
    type=click.Path(exists=True, dir_okay=False),
    nargs=1,
)
@click.option(
    "--output", "-o",
    help="Output filename.",
    default="compressed.pdf",
    show_default=True,
)
def compress(file, output):
    """Compress a PDF file."""
    # TODO Implement compress command
    # ! Not implemented yet
    size_before = os.path.getsize(file)
    output_file, size_after = _compress_pdf(file, output)

    click.echo(click.style(f"Compressed `{file}` to `{output_file}`.", fg="blue"))
    click.echo(click.style(f"File size before: {size_before} bytes", fg="blue"))
    click.echo(click.style(f"File size after: {size_after} bytes "
                           f"({(size_before - size_after) / size_before * 100:.2f}%)",
                           fg="blue"))

@click.group()
def cli():
    """PDF tools"""
    # ? Function to group the commands
    pass

# ? Add commands to the group here
cli.add_command(merge)
cli.add_command(split)
cli.add_command(compress)

if __name__ == '__main__':
    cli()