"""
Copyright (C) 2024 Michael Piazza

This file is part of Smart Notes.

Smart Notes is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

Smart Notes is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with Smart Notes.  If not, see <https://www.gnu.org/licenses/>.
"""

import re
import uuid
from typing import Optional
from urllib.parse import urlparse

import aiohttp
from anki.notes import Note

from .logger import logger
from .media_utils import ext_from_content_type, write_media
from .notes import get_note_type
from .ui.ui_utils import show_message_box
from .utils import run_on_main

IMAGE_EXTENSIONS = r"\.(png|jpg|jpeg|webp|gif)"
MARKDOWN_IMAGE_RE = re.compile(r"!\[([^\]]*)\]\((https?://[^\s)]+)\)")
BARE_IMAGE_URL_RE = re.compile(
    rf"(?<!\()(https?://[^\s\"'<>]+{IMAGE_EXTENSIONS}(\?[^\s\"'<>]*)?)(?!\))",
    re.IGNORECASE,
)


def _media_filename(note: Note, field: str, ext: str) -> str:
    short_id = uuid.uuid4().hex[:8]
    return f"{get_note_type(note)}-{field}-{note.id}-{short_id}.{ext}"


async def _download_image(
    url: str,
) -> tuple[Optional[tuple[bytes, str]], Optional[str]]:
    try:
        parsed = urlparse(url)
        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
            "Accept": "image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8",
            "Referer": f"{parsed.scheme}://{parsed.netloc}/",
        }
        async with (
            aiohttp.ClientSession(headers=headers) as session,
            session.get(url, timeout=aiohttp.ClientTimeout(total=30)) as r,
        ):
            if r.status != 200:
                msg = f"HTTP {r.status}"
                logger.debug(f"Failed to download image {url}: {msg}")
                return None, msg
            content_type = r.content_type or ""
            data = await r.read()
            if not data:
                return None, "Empty response"
            return (data, content_type), None
    except Exception as e:
        msg = str(e) or type(e).__name__
        logger.debug(f"Error downloading image {url}: {msg}")
        return None, msg


def _ext_from_url_or_content_type(url: str, content_type: str) -> str:
    match = re.search(IMAGE_EXTENSIONS, url, re.IGNORECASE)
    if match:
        ext = match.group(1).lower()
        return "jpg" if ext == "jpeg" else ext
    return ext_from_content_type(content_type)


async def download_and_embed_images(
    text: str, note: Note, field: str, show_error_box: bool = True
) -> str:
    urls: list[tuple[str, Optional[str]]] = []

    for match in MARKDOWN_IMAGE_RE.finditer(text):
        urls.append((match.group(2), match.group(0)))

    for match in BARE_IMAGE_URL_RE.finditer(text):
        full_url = match.group(0)
        if not any(full_url == u[0] for u in urls):
            urls.append((full_url, None))

    logger.debug(f"Image detection: found {len(urls)} URLs in response")
    for url, _ in urls:
        logger.debug(f"Image detection: {url}")

    if not urls:
        return text

    for url, original_match in urls:
        logger.debug(f"Downloading image: {url}")
        result, error = await _download_image(url)
        if not result:
            logger.debug(f"Download failed for {url}: {error}")
            if show_error_box:
                run_on_main(
                    lambda url=url, error=error: show_message_box(
                        f"Failed to download image from web search.\n\nURL: {url}\nError: {error}"
                    )
                )
            continue

        data, content_type = result
        logger.debug(f"Downloaded {len(data)} bytes, content_type={content_type}")
        ext = _ext_from_url_or_content_type(url, content_type)
        filename = _media_filename(note, field, ext)
        path = write_media(filename, data)
        if not path:
            logger.debug(f"Failed to write media for: {filename}")
            continue

        logger.debug(f"Saved image as: {path}")
        img_tag = f'<img src="{path}"/>'
        if original_match:
            text = text.replace(original_match, img_tag, 1)
        else:
            text = text.replace(url, img_tag, 1)

    return text
