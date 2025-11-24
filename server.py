"""MCP server for scraping the main image URL from Echigo Sake Harasho product pages."""

import os
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup
from mcp.server.fastmcp import FastMCP

# streamable_http_path="/" so Cloud Run root URL is the MCP endpoint.
mcp = FastMCP(
    name="EchigoSakeImageServer",
    streamable_http_path="/",
)


@mcp.tool()
def get_product_image_url(product_page_url: str) -> str:
    """
    越後銘門酒会（echigo.sake-harasho.com）の商品ページURLから
    メイン画像のURLを取得して返す MCP ツール。
    """

    # Domain guard (also helps mitigate SSRF).
    if not product_page_url.startswith("https://www.echigo.sake-harasho.com/view/item/"):
        return "Error: unsupported URL. Must be https://www.echigo.sake-harasho.com/view/item/..."

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/91.0.4472.124 Safari/537.36"
        )
    }

    try:
        resp = requests.get(product_page_url, headers=headers, timeout=10)
        resp.raise_for_status()
    except Exception as e:  # noqa: BLE001 - returning error text is acceptable here
        return f"Error: failed to fetch page: {e}"

    soup = BeautifulSoup(resp.content, "html.parser")

    # Primary strategy: provided HTML structure <li id="goods-img-basis"><img src="..."></li>
    img = soup.select_one("#goods-img-basis img")
    if img and img.get("src"):
        img_url = img["src"]
        if not img_url.startswith("http"):
            img_url = urljoin(product_page_url, img_url)
        return img_url

    # Fallback: use og:image when available.
    og = soup.find("meta", property="og:image")
    if og and og.get("content"):
        return og["content"]

    return "Error: image URL not found."


# ASGI app for FastMCP; served by uvicorn.
app = mcp.streamable_http_app()


if __name__ == "__main__":
    import uvicorn

    port = int(os.environ.get("PORT", "8080"))
    uvicorn.run(app, host="0.0.0.0", port=port)
