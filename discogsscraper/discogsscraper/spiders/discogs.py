import scrapy
from scrapy_playwright.page import PageMethod
import json


class DiscogsSpider(scrapy.Spider):
    name = "discogs"

    def start_requests(self):
        yield scrapy.Request(
            url="https://www.discogs.com/",
            meta={
                "playwright": True,
                "playwright_page_methods": [
                    PageMethod("wait_for_load_state", "domcontentloaded", timeout=60000),
                    PageMethod("wait_for_timeout", 5000),
                ],
            },
            callback=self.parse_search,
        )

    def parse_search(self, response):
        next_url = f"https://www.discogs.com/search/?limit=250&genre_exact=Rock&page=1"

        yield scrapy.Request(
            url=next_url,
            meta={
                "playwright": True,
                "playwright_page_methods": [
                    PageMethod("wait_for_load_state", "domcontentloaded", timeout=60000),
                    PageMethod("wait_for_timeout", 5000),
                ],
                "page": 1,
                "primary_key": 0,
            },
            callback=self.parse_album,
        )

    def parse_album(self, response):
        links = response.css('a.search_result_title::attr(href)').getall()

        with open("links.jsonl", "a", encoding="utf-8") as f:
            for l in links:
                f.write(json.dumps({"link": l}, ensure_ascii=False) + "\n")
        f.close()

        # Le links ainda não acessados
        with open('links.jsonl', "r", encoding="utf-8") as f:
            album_links = f.readlines()
        f.close()

        first_objeto = json.loads(album_links[0])
        first_link = first_objeto["link"]

        with open('links.jsonl', "w", encoding="utf-8") as f:
            f.writelines(album_links[1:])
        f.close()

        url = 'https://www.discogs.com' + first_link

        yield scrapy.Request(
            url=url,
            meta={
                "playwright": True,
                "playwright_page_methods": [
                    PageMethod("wait_for_load_state", "domcontentloaded", timeout=60000),
                    PageMethod("wait_for_timeout", 5000),
                ],
                "page": response.meta["page"],
                "primary_key": response.meta["primary_key"],
            },
            callback=self.parse_album_info,
        )

    def parse_album_info(self, response):
        # Id
        primary_key = response.meta["primary_key"] + 1
        # Genre
        genre = response.css('a[href^="/genre/"]::text').get()
        # Artist Name
        artist_name = response.css('a[href^="/artist/"]::text').get()
        # Artist Members Info Link
        artist_members_link = response.css('a[href^="/artist/"]::attr(href)').get()
        # Album Release Year
        album_release_year = response.css('a[href^="/search/"] time::attr(datetime)').get()
        # Album Title
        album_title = response.xpath('//h1/span[a[contains(@href, "/artist/")]]/following-sibling::text()').get()
        album_title = album_title.strip("–- \n\r\t") if album_title else None
        # Album Record Label
        album_record_labels = response.xpath('//th[h2[contains(text(), "Label:")]]/following-sibling::td[1]//a/text()').getall()
        # Album Tracks
        album_tracks = response.css('span[class^="trackTitle"]::text').getall()
        # Track Duration
        track_duration = response.css('td[class^="duration"] span span::text').getall()
        # Album Track Number
        album_track_number = response.css('td[class^="trackPos"] span::text').getall()
        # Album Styles
        album_styles = response.css('a[href^="/style/"]::text').getall()

        url = 'https://www.discogs.com' + artist_members_link

        yield scrapy.Request(
            url=url,
            meta={
                "playwright": True,
                "playwright_page_methods": [
                    PageMethod("wait_for_load_state", "domcontentloaded", timeout=60000),
                    PageMethod("wait_for_timeout", 5000),
                ],
                "album_data": {
                    'id': primary_key,
                    'genre': genre,
                    'artist_name': artist_name,
                    'album_release_year': album_release_year,
                    'album_title': album_title,
                    'album_record_labels': album_record_labels,
                    'album_tracks': album_tracks,
                    'track_duration': track_duration,
                    'album_track_number': album_track_number,
                    'album_styles': album_styles,
                },
                "page": response.meta["page"],
                "primary_key": primary_key,
            },
            callback=self.parse_artist_members,
        )

    def parse_artist_members(self, response):
        album_data = response.meta["album_data"]

        # Artist Members
        artist_members = response.xpath('//th[h2[contains(text(), "Members")]]/following-sibling::td[1]//a[contains(@href, "/artist/")]/span/text()').getall()

        # Artist Websites
        artist_websites = response.xpath('//th[h2[contains(text(), "Sites")]]/following-sibling::td[1]//a/@href').getall()


        resp = {
            'id': album_data['id'],
            'genre': album_data['genre'],
            'artist_name': album_data['artist_name'],
            'artist_members': list(set(artist_members)),
            'artist_websites': list(set(artist_websites)),
            'album_release_year': album_data['album_release_year'],
            'album_title': album_data['album_title'],
            'album_record_label': list(set(album_data['album_record_labels'])),
            'album_styles': list(set(album_data['album_styles'])),
            'album_tracks': []
        }

        for number, name, duration in zip(
            album_data['album_track_number'],
            album_data['album_tracks'],
            album_data['track_duration']
        ):
            resp['album_tracks'].append({
                'number': number,
                'name': name,
                'track_duration': duration
            })

        with open("albums.jsonl", "a", encoding="utf-8") as a:
            a.write(json.dumps(resp, ensure_ascii=False) + "\n")
        a.close()

        with open('links.jsonl', "r", encoding="utf-8") as f:
            album_links = f.readlines()
        f.close()

        # Verifica o JSONL dos links do albums está vazio
        if not album_links:
            if response.meta["page"]:
                page = response.meta["page"] + 1

            next_url = f"https://www.discogs.com/search/?limit=250&genre_exact=Rock&page={page}"

            yield scrapy.Request(
                url=next_url,
                meta={
                    "playwright": True,
                    "playwright_page_methods": [
                        PageMethod("wait_for_load_state", "domcontentloaded", timeout=60000),
                        PageMethod("wait_for_timeout", 5000),
                    ],
                    "page": page,
                    "primary_key": response.meta["primary_key"],
                },
                callback=self.parse_album,
            )
        else:
            first_objeto = json.loads(album_links[0])
            first_link = first_objeto["link"]

            with open('links.jsonl', "w", encoding="utf-8") as f:
                f.writelines(album_links[1:])
            f.close()

            url = 'https://www.discogs.com' + first_link

            yield scrapy.Request(
                url=url,
                meta={
                    "playwright": True,
                    "playwright_page_methods": [
                        PageMethod("wait_for_load_state", "domcontentloaded", timeout=60000),
                        PageMethod("wait_for_timeout", 5000),
                    ],
                    "page": response.meta["page"],
                    "primary_key": response.meta["primary_key"],
                },
                callback=self.parse_album_info,
            )
