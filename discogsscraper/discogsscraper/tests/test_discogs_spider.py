import os
import json
import pytest
import tempfile
import scrapy
from scrapy.http import TextResponse, Request
from scrapy_playwright.page import PageMethod
from discogsscraper.spiders.discogs import DiscogsSpider


def fake_response_from_html(html_or_file: str, url: str):
    if os.path.exists(html_or_file):
        with open(html_or_file, encoding="utf-8") as f:
            html = f.read()
    else:
        html = html_or_file

    request = Request(url=url)
    return TextResponse(url=url, request=request, body=html, encoding='utf-8')

def test_start_requests():
    spider = DiscogsSpider()
    results = list(spider.start_requests())

    # Should generate exactly one request
    assert len(results) == 1
    req = results[0]

    # Verify type and target
    assert isinstance(req, scrapy.Request)
    assert req.url == "https://www.discogs.com/"
    assert req.callback == spider.parse_search

    # Verify that Playwright is enabled
    meta = req.meta
    assert meta["playwright"] is True
    assert isinstance(meta["playwright_page_methods"], list)

    # Confirm that both expected PageMethods are present
    load_state = meta["playwright_page_methods"][0]
    wait_timeout = meta["playwright_page_methods"][1]
    assert isinstance(load_state, PageMethod)
    assert isinstance(wait_timeout, PageMethod)
    assert load_state.method == "wait_for_load_state"
    assert wait_timeout.method == "wait_for_timeout"

def test_parse_search():
    spider = DiscogsSpider()

    # Create a fake response simulating the homepage
    request = Request(url="https://www.discogs.com/")
    response = TextResponse(url=request.url, request=request, body=b"", encoding="utf-8")

    results = list(spider.parse_search(response))

    # Should generate one new request
    assert len(results) == 1
    req = results[0]
    assert isinstance(req, scrapy.Request)

    # Verify if the URL is correct
    expected_url = "https://www.discogs.com/search/?limit=250&genre_exact=Rock&page=1"
    assert req.url == expected_url

    # Confirm that the callback is correct
    assert req.callback == spider.parse_album

    # Verify meta data
    meta = req.meta
    assert meta["playwright"] is True
    assert meta["page"] == 1
    assert meta["primary_key"] == 0

    # Verify PageMethods
    page_methods = meta["playwright_page_methods"]
    assert len(page_methods) == 2
    assert page_methods[0].method == "wait_for_load_state"
    assert page_methods[1].method == "wait_for_timeout"

def test_parse_album(tmp_path):
    spider = DiscogsSpider()

    # Fake HTML
    html = """
    <html>
        <body>
            <a class="search_result_title" href="/release/111">Album 1</a>
            <a class="search_result_title" href="/release/222">Album 2</a>
            <a class="search_result_title" href="/release/333">Album 3</a>
        </body>
    </html>
    """

    # Creates the temporary file
    html_file = tmp_path / "sample.html"
    html_file.write_text(html, encoding="utf-8")

    # Create the fake response
    response = fake_response_from_html(str(html_file), "https://www.discogs.com/search/")
    response.meta["page"] = 1
    response.meta["primary_key"] = 0

    # Change to the temporary directory
    cwd = os.getcwd()
    os.chdir(tmp_path)

    try:
        results = list(spider.parse_album(response))
    finally:
        os.chdir(cwd)

    # Verify that the links.json file was created
    links_file = tmp_path / "links.jsonl"
    assert links_file.exists(), "O arquivo links.jsonl deve existir"
    lines = links_file.read_text(encoding="utf-8").splitlines()

    # It should contain the links, except for the first one (since it's removed in the code)
    assert len(lines) == 2
    assert json.loads(lines[0])["link"] == "/release/222"
    assert json.loads(lines[1])["link"] == "/release/333"

    # Checks if a scrapy.Request yielded a result
    assert len(results) == 1
    req = results[0]
    assert isinstance(req, Request)
    assert req.url == "https://www.discogs.com/release/111"
    assert req.meta["page"] == 1
    assert req.meta["primary_key"] == 0
    assert req.callback == spider.parse_album_info

def test_parse_album_info():
    spider = DiscogsSpider()

    html = """
    <html>
      <body>
        <a href="/artist/260202">Danzig</a>
        <a href="/genre/Rock">Rock</a>
        <a href="/search/?q=2025-10-10"><time datetime="2025-10-10"></time></a>

        <h1>
          <span>
            <a href="/artist/260202">Danzig</a>
          </span>
          – Danzig
        </h1>

        <th><h2>Label:</h2></th>
        <td><a>American Recordings</a></td>

        <span class="trackTitle">Twist Of Cain</span>
        <span class="trackTitle">Mother</span>

        <td class="duration"><span><span>4:17</span></span></td>
        <td class="duration"><span><span>3:43</span></span></td>

        <td class="trackPos"><span>A1</span></td>
        <td class="trackPos"><span>A2</span></td>

        <a href="/style/Heavy-Metal">Heavy Metal</a>
      </body>
    </html>
    """

    response = fake_response_from_html(html, "https://www.discogs.com/release/12345")
    response.meta["primary_key"] = 0
    response.meta["page"] = 1

    results = list(spider.parse_album_info(response))

    assert len(results) == 1
    next_req = results[0]
    assert next_req.callback == spider.parse_artist_members
    assert "album_data" in next_req.meta
    album_data = next_req.meta["album_data"]

    assert album_data["artist_name"] == "Danzig"
    assert "Twist Of Cain" in album_data["album_tracks"]

def test_parse_artist_members(tmp_path):
    spider = DiscogsSpider()

    # Fake HTML
    html = """
    <html>
        <body>
            <th><h2>Members</h2></th>
            <td>
                <a href="/artist/260202"><span>Bevan</span></a>
                <a href="/artist/812930"><span>Charlee Johnson</span></a>
            </td>
            <th><h2>Sites</h2></th>
            <td>
                <a href="http://www.danzig-verotik.com/">danzig-verotik</a>
                <a href="http://www.the7thhouse.com/">the7thhouse</a>
            </td>
        </body>
    </html>
    """

    # Saves the temporary HTML
    html_file = tmp_path / "sample.html"
    html_file.write_text(html, encoding="utf-8")

    response = fake_response_from_html(str(html_file), "https://www.discogs.com/artist/123")
    response.meta["page"] = 1
    response.meta["primary_key"] = 0
    response.meta["album_data"] = {
        "id": 1,
        "genre": "Rock",
        "artist_name": "Danzig",
        "album_release_year": "1988",
        "album_title": "Danzig",
        "album_record_labels": ["Def American"],
        "album_styles": ["Heavy Metal"],
        "album_tracks": ["Twist of Cain"],
        "track_duration": ["3:11"],
        "album_track_number": ["A1"]
    }

    # Temporary "links.jsonl"
    links_file = tmp_path / "links.jsonl"
    links_file.write_text(json.dumps({"link": "/release/999"}) + "\n", encoding="utf-8")

    # Redirects execution to the temporary folder
    cwd = os.getcwd()
    os.chdir(tmp_path)

    try:
        results = list(spider.parse_artist_members(response))
    finally:
        os.chdir(cwd)

    # Read the output file
    output_file = tmp_path / "albums.jsonl"
    assert output_file.exists(), "O arquivo albums.jsonl deve ter sido criado"

    data = json.loads(output_file.read_text(encoding="utf-8"))
    assert data["artist_name"] == "Danzig"
    assert sorted(data["artist_members"]) == ["Bevan", "Charlee Johnson"]
    assert "http://www.the7thhouse.com/" in data["artist_websites"]
    assert "http://www.danzig-verotik.com/" in data["artist_websites"]

    # Checks if a Request for the next link was rendered
    assert len(results) == 1
    assert "https://www.discogs.com/release/999" in results[0].url
