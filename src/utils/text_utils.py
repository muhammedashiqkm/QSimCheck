from bs4 import BeautifulSoup

def clean_html(text):
    return BeautifulSoup(text or "", "html.parser").get_text()