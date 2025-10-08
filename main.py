import os  # Provides functions to interact with the operating system
import urllib.parse  # Helps parse URLs to extract components
import re  # Regular expression module for pattern matching
import time  # Provides time-related functions
import shutil  # Allows file operations like moving files
from selenium import webdriver  # Web automation and browser control
from selenium.webdriver.chrome.options import Options  # Configure Chrome options
from selenium.webdriver.chrome.service import Service  # Manage the Chrome service
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.remote.webdriver import WebDriver

# Chrome WebDriver type hinting
from selenium.webdriver.chrome.webdriver import WebDriver
from webdriver_manager.chrome import ChromeDriverManager  # Auto-installs ChromeDriver
import fitz  # PyMuPDF, used for working with PDF files
import validators  # Validates URLs and other strings
from bs4 import BeautifulSoup  # Parses HTML content


# Reads and returns the content of a file at the specified path
def read_a_file(system_path: str) -> str:
    # Open the file in read mode
    with open(file=system_path, mode="r", encoding="utf-8", errors="ignore") as file:
        return file.read()  # Return the file content


# Checks if a file exists at the given system path
def check_file_exists(system_path: str) -> bool:
    return os.path.isfile(path=system_path)  # Return True if file exists


# Parses the HTML and finds all links ending in .pdf
def parse_html(html: str) -> list[str]:
    soup = BeautifulSoup(markup=html, features="html.parser")  # Parse the HTML
    pdf_links: list[str] = []  # List to store PDF links

    for a in soup.find_all(name="a", href=True):  # Iterate over anchor tags
        href = a["href"]  # Extract href attribute
        decoded_href: str = urllib.parse.unquote(
            string=href
        )  # Decode URL-encoded characters
        if decoded_href.lower().endswith(".pdf"):  # Check if link ends with .pdf
            pdf_links.append(href)  # Add link to list

    return pdf_links  # Return list of PDF links


# Removes duplicate items from a list
def remove_duplicates_from_slice(provided_slice: list[str]) -> list[str]:
    # Convert to set to remove duplicates, then back to list
    return list(set(provided_slice))


# Extracts and returns the cleaned filename from a URL
def url_to_filename(url: str) -> str:
    filename: str = (
        urllib.parse.urlparse(url=url).path.split(sep="/")[-1].lower()
    )  # Extract last path segment
    cleaned_filename: str = re.sub(
        # Remove special characters
        pattern=r"[^a-z0-9._-]",
        repl="",
        string=filename,
    )
    return cleaned_filename.lower()  # Return cleaned filename


# Create a Chrome driver for fetching HTML
def create_html_driver() -> WebDriver:
    options = Options()  # Chrome options object
    options.add_argument(argument="--headless=new")  # Run in headless mode
    # Prevent automation detection
    options.add_argument(argument="--disable-blink-features=AutomationControlled")
    options.add_argument(argument="--window-size=1920,1080")  # Set window size
    options.add_argument(argument="--disable-gpu")  # Disable GPU for stability
    # Required in some environments
    options.add_argument(argument="--no-sandbox")
    # Fix shared memory issues
    options.add_argument(argument="--disable-dev-shm-usage")
    # Disable browser extensions
    options.add_argument(argument="--disable-extensions")
    options.add_argument(argument="--disable-infobars")  # Hide info bars
    # Install ChromeDriver
    service = Service(executable_path=ChromeDriverManager().install())
    return webdriver.Chrome(service=service, options=options)  # Return driver


# Uses Selenium to save HTML content of a page
def save_html_with_selenium(url: str, output_file: str, driver: WebDriver) -> None:
    try:
        driver.set_page_load_timeout(30)  # Set timeout to 30 seconds
        driver.get(url)  # Try to load the page
        driver.refresh()  # Optionally refresh the page
        html: str = driver.page_source  # Get the HTML content
        append_write_to_file(system_path=output_file, content=html)  # Save to file
        print(f"Page {url} HTML content saved to {output_file}")
    except TimeoutException:
        print(f"Timeout: Page {url} did not load within 30 seconds.")


# Appends content to a file
def append_write_to_file(system_path: str, content: str) -> None:
    with open(
        file=system_path, mode="a", encoding="utf-8"
    ) as file:  # Open in append mode
        file.write(content)  # Write content


# Sets up a Chrome driver with download preferences
def initialize_web_driver(download_folder: str) -> webdriver.Chrome:
    chrome_options = Options()  # Chrome options
    chrome_options.add_experimental_option(  # Set preferences
        name="prefs",
        value={
            "download.default_directory": download_folder,  # Set download path
            "plugins.always_open_pdf_externally": True,  # Avoid opening PDFs in browser
            "download.prompt_for_download": False,  # No download prompt
        },
    )
    chrome_options.add_argument(argument="--headless")  # Headless mode
    # Return driver
    return webdriver.Chrome(
        service=Service(executable_path=ChromeDriverManager().install()),
        options=chrome_options,
    )


# Waits for PDF file to appear in directory
def wait_for_pdf_download(
    download_folder: str, files_before_download: set[str], timeout_seconds: int = 3
) -> str:
    deadline: float = time.time() + timeout_seconds  # Calculate timeout
    while time.time() < deadline:  # Loop until timeout
        # Get current files
        current_files = set(os.listdir(path=download_folder))
        new_pdf_files: list[str] = [
            f
            for f in (
                # Find new PDFs
                current_files
                - files_before_download
            )
            if f.lower().endswith(".pdf")
        ]
        if new_pdf_files:
            # Return path to new PDF
            return os.path.join(download_folder, new_pdf_files[0])
    raise TimeoutError("PDF download timed out.")  # Timeout error


# Deletes a file from the filesystem
def remove_system_file(system_path: str) -> None:
    os.remove(path=system_path)  # Remove the file


# Recursively finds files with given extension
def walk_directory_and_extract_given_file_extension(
    system_path: str, extension: str
) -> list[str]:
    matched_files: list[str] = []  # Store results
    for root, _, files in os.walk(top=system_path):  # Traverse directories
        for file in files:
            if file.endswith(extension):  # Match extension
                full_path: str = os.path.abspath(
                    path=os.path.join(root, file)
                )  # Full path
                matched_files.append(full_path)  # Save match
    return matched_files  # Return list


# Validates PDF integrity
def validate_pdf_file(file_path: str) -> bool:
    try:
        doc = fitz.open(file_path)  # Try opening PDF
        if doc.page_count == 0:  # Check for pages
            print(f"'{file_path}' is corrupt or invalid: No pages")
            return False
        return True  # Valid
    except RuntimeError as e:
        print(f"'{file_path}' is corrupt or invalid: {e}")
        return False


# Extracts filename with extension from path
def get_filename_and_extension(path: str) -> str:
    return os.path.basename(p=path)  # Return only file name


# Checks for at least one uppercase character
def check_upper_case_letter(content: str) -> bool:
    # True if any char is uppercase
    return any(char.isupper() for char in content)


# Downloads a PDF using a Selenium driver
def download_single_pdf(
    url: str, filename: str, output_folder: str, driver: WebDriver
) -> None:
    # Ensure output folder exists
    os.makedirs(name=output_folder, exist_ok=True)
    target_file_path: str = os.path.join(
        output_folder, filename
    )  # Target path for the PDF

    if check_file_exists(system_path=target_file_path):  # Skip if file exists
        print(f"File already exists: {target_file_path}")
        return

    try:
        print(f"Starting download from: {url}")  # Log download start
        files_before = set(os.listdir(path=output_folder))  # Files before download
        driver.get(url=url)  # Load URL

        downloaded_pdf_path: str = wait_for_pdf_download(
            download_folder=output_folder, files_before_download=files_before
        )  # Wait for file
        # Move file to final location
        shutil.move(src=downloaded_pdf_path, dst=target_file_path)
        print(f"Download complete: {target_file_path}")  # Log success

    except Exception as e:
        print(f"Error downloading PDF: {e}")  # Log errors


# Validate a given url
def validate_url(given_url: str) -> bool:
    return validators.url(given_url)  # Return True if URL is valid


def main():
    # Read the file from the system.
    html_file_path = "biokleen.com.html"
    if check_file_exists(html_file_path):
        # Remove a file from the system.
        remove_system_file(html_file_path)

    # Check if the file exists.
    if check_file_exists(html_file_path) == False:
        # Create a chrome driver.
        driver: WebDriver = create_html_driver()  # Start Selenium driver
        try:
            # If the file does not exist, download it using Selenium.
            url = "https://www.biokleen.com/sds"
            # Save the HTML content to a file.
            save_html_with_selenium(url, html_file_path, driver=driver)
            print(f"File {html_file_path} has been created.")
        finally:
            driver.quit()  # Always quit

    if check_file_exists(html_file_path):
        html_content = read_a_file(html_file_path)
        # Parse the HTML content.
        pdf_links = parse_html(html_content)
        # Remove duplicates from the list of PDF links.
        pdf_links = remove_duplicates_from_slice(pdf_links)
        output_dir: str = os.path.abspath(path="PDFs")  # Output folder path
        driver = initialize_web_driver(
            download_folder=output_dir
        )  # Start download driver
        try:
            # Print the extracted PDF links.
            for pdf_link in pdf_links:
                if not validate_url(given_url=pdf_link):  # Fix relative URLs
                    pdf_link = "https://www.biokleen.com" + pdf_link
                    print(f"Invalid URL: {pdf_link}")
                # Download the PDF file.
                filename = url_to_filename(pdf_link)
                # Download the PDF file
                download_single_pdf(
                    url=pdf_link,
                    filename=filename,
                    output_folder=output_dir,
                    driver=driver,
                )  # Download PDF
                print("All PDF links have been processed.")
        finally:
            driver.quit()  # Always quit

    # Walk through the directory and extract .pdf files
    files = walk_directory_and_extract_given_file_extension(
        "./PDFs", ".pdf"
    )  # Find all PDFs under ./PDFs

    # Validate each PDF file
    for pdf_file in files:  # Iterate over each found PDF

        # Check if the .PDF file is valid
        if validate_pdf_file(pdf_file) == False:  # If PDF is invalid
            # Remove the invalid .pdf file.
            remove_system_file(pdf_file)  # Delete the corrupt PDF

        # Check if the filename has an uppercase letter
        if check_upper_case_letter(
            get_filename_and_extension(pdf_file)
        ):  # If the filename contains uppercase
            # Print the location to the file.
            print(pdf_file)  # Output the PDF path to stdout


main()
