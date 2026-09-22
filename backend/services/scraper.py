"""Web scraping and DOM text extraction service."""

import re
import functools
from typing import Dict, Optional
import httpx
from bs4 import BeautifulSoup

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
    "Connection": "keep-alive",
}


async def scrape_website(url: str) -> Dict[str, Optional[str]]:
    """Asynchronously fetches target website HTML and extracts DOM text content.

    Args:
        url: The web page URL to scrape.

    Returns:
        Dict containing url, domain, title, content, html_length, and error status.
    """
    if not url.startswith(("http://", "https://")):
        url = "https://" + url

    try:
        async with httpx.AsyncClient(
            headers=HEADERS, timeout=30.0, follow_redirects=True, verify=False
        ) as client:
            response = await client.get(url)
            response.raise_for_status()
            html_content = response.text

        return extract_content(html_content, url)

    except httpx.TimeoutException:
        return {
            "error": "Website took too long to respond (30s timeout)",
            "url": url,
            "content": "",
            "title": "",
            "domain": extract_domain(url),
            "html_length": 0,
        }
    except httpx.HTTPStatusError as e:
        return {
            "error": f"HTTP {e.response.status_code} error accessing website",
            "url": url,
            "content": "",
            "title": "",
            "domain": extract_domain(url),
            "html_length": 0,
        }
    except Exception as e:
        return {
            "error": f"Could not access website: {str(e)[:200]}",
            "url": url,
            "content": "",
            "title": "",
            "domain": extract_domain(url),
            "html_length": 0,
        }


def extract_content(html: str, url: str) -> Dict[str, Optional[str]]:
    """Parses HTML DOM to extract key CTA buttons, forms, prechecked boxes, and prices.

    Args:
        html: Raw HTML string.
        url: Source URL string.

    Returns:
        Structured dictionary containing extracted page text and metadata.
    """
    try:
        soup = BeautifulSoup(html, "html.parser")
    except Exception:
        soup = BeautifulSoup(html, "html.parser")

    # Remove non-content tags
    for tag in soup(["script", "style", "svg", "img", "noscript", "meta", "link"]):
        tag.decompose()

    title = ""
    if soup.title and soup.title.string:
        title = soup.title.string.strip()

    important_elements: list[str] = []

    # Buttons and CTAs
    buttons = soup.find_all(["button", "a"])
    for btn in buttons[:30]:
        text = btn.get_text(strip=True)
        if text and 2 < len(text) < 100:
            important_elements.append(f"[BUTTON] {text}")

    # Forms
    forms = soup.find_all("form")
    for form in forms[:3]:
        form_text = form.get_text(separator=" ", strip=True)
        if form_text:
            important_elements.append(f"[FORM] {form_text[:400]}")

    # Pre-checked checkboxes
    checkboxes = soup.find_all("input", {"type": "checkbox"})
    for cb in checkboxes:
        if cb.get("checked") is not None:
            label = cb.find_next("label")
            label_text = label.get_text(strip=True) if label else "Unknown checkbox"
            important_elements.append(f"[PRE-CHECKED] {label_text}")

    # Price elements
    price_elements = soup.find_all(
        class_=re.compile(r"price|cost|fee|charge|total|amount", re.I)
    )
    for el in price_elements[:10]:
        text = el.get_text(strip=True)
        if text and any(c.isdigit() for c in text):
            important_elements.append(f"[PRICE] {text}")

    # Urgency text
    urgency_keywords = [
        "left",
        "only",
        "hurry",
        "limited",
        "expires",
        "ending",
        "today only",
        "sold out",
        "selling fast",
        "popular",
        "people viewing",
        "watching",
        "countdown",
    ]
    all_text = soup.find_all(string=True)
    for text_node in all_text:
        text = text_node.strip()
        if (
            text
            and any(kw in text.lower() for kw in urgency_keywords)
            and len(text) < 150
        ):
            important_elements.append(f"[URGENCY] {text}")

    # Popups and modals
    popups = soup.find_all(
        class_=re.compile(r"popup|modal|overlay|banner|notification", re.I)
    )
    for popup in popups[:3]:
        text = popup.get_text(separator=" ", strip=True)
        if text:
            important_elements.append(f"[POPUP] {text[:300]}")

    # Footer
    footer = soup.find("footer")
    if footer:
        footer_text = footer.get_text(separator=" ", strip=True)
        important_elements.append(f"[FOOTER] {footer_text[:400]}")

    # General body text
    body_text = soup.get_text(separator="\n", strip=True)
    body_text = re.sub(r"\n{3,}", "\n\n", body_text)[:3000]

    combined = "\n".join(important_elements[:40])
    combined += f"\n\n[PAGE TEXT]\n{body_text}"

    domain = extract_domain(url)

    return {
        "url": url,
        "domain": domain,
        "title": title,
        "content": combined,
        "html_length": len(html),
        "error": None,
    }


@functools.lru_cache(maxsize=1024)
def extract_domain(url: str) -> str:
    """Extracts clean domain name from URL string with LRU caching.

    Args:
        url: Full web address string.

    Returns:
        Clean domain string without protocol or path.
    """
    clean_url = url.replace("https://", "").replace("http://", "").replace("www.", "")
    return clean_url.split("/")[0].split("?")[0]
