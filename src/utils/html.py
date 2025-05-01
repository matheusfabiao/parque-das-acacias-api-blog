from bs4 import BeautifulSoup

def clean_html(html_content: str) -> str:
    soup = BeautifulSoup(html_content, "html.parser")
    # Get text content and remove explicit newlines
    text = soup.get_text()
    return text.replace('\n', '')
