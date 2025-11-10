# Discogs

## Sobre

O repositório Discogs é um exemplo de projeto de web scraping voltado para coleta e análise de dados musicais.

O objetivo é percorrer o site Discogs em busca de álbuns do gênero Rock, extraindo informações como nome do artista, ano de lançamento, lista de faixas, duração das músicas, membros da banda e outros detalhes relevantes.

Os dados coletados são estruturados e armazenados no formato JSONL, o que permite sua fácil integração com ferramentas de engenharia de dados e processamento em fluxo, como o Apache Kafka, para análises e pipelines futuros.

## Exemplo de saída de dados

```jsonl
{
    "id": 1,
    "genre": "Rock",
    "artist_name": "Danzig",
    "artist_members": [
        "John Christ",
        "Bevan",
        "Eerie Von",
        "Joseph Bishara",
        "Todd Schofield",
        "Steve Zing",
        "Dave Kushner",
        "Jeff Chambers (2)",
        "Tommy Victor",
        "Joey Castillo",
        "Glenn Anzalone",
        "Johnny Kelly",
        "Josh Lazie",
        "Jerry Montano",
        "Rob Nicholson",
        "Howie Kusten",
        "Charles Montgomery (3)",
        "Charlee Johnson (2)"],
    "artist_websites": [
        "https://www.instagram.com/officialdanzigverotik/",
        "https://twitter.com/DANZlG",
        "https://www.youtube.com/channel/UCj7tShkbc4S5svD_xxO2VvA",
        "https://soundcloud.com/danzig-official",
        "https://www.facebook.com/Danzig",
        "https://myspace.com/danzig",
        "https://danzigsingselvis.bandcamp.com/",
        "http://www.danzig-verotik.com/",
        "https://www.reverbnation.com/danzigsaboath",
        "http://www.the7thhouse.com/"],
    "album_release_year": "2025-10-10",
    "album_title": "Danzig",
    "album_record_label": ["American Recordings"],
    "album_styles": ["Blues Rock", "Heavy Metal"],
    "album_tracks": [
        {"number": "A1", "name": "Twist Of Cain", "track_duration": "4:17"},
        {"number": "A2", "name": "Not Of This World", "track_duration": "3:43"},
        {"number": "A3", "name": "She Rides", "track_duration": "5:11"},
        {"number": "A4", "name": "Soul On Fire", "track_duration": "4:37"},
        {"number": "A5", "name": "Am I Demon", "track_duration": "4:58"},
        {"number": "B1", "name": "Mother", "track_duration": "3:26"},
        {"number": "B2", "name": "Possession", "track_duration": "3:56"},
        {"number": "B3", "name": "End Of Time", "track_duration": "4:02"},
        {"number": "B4", "name": "The Hunter", "track_duration": "3:31"},
        {"number": "B5", "name": "Evil Thing", "track_duration": "3:17"}]
}
```

## Como coletar os dados em JSONL
    git clone https://github.com/Leonardo-Nunes-Armelim/Discogs.git
    cd Discogs
    python -m venv ./venv
    .\venv\Scripts\activate.bat
    python.exe -m pip install --upgrade pip
    pip install -r requirements.txt
    playwright install chromium
    cd discogsscraper
    scrapy crawl discogs

Após executar o comando "scrapy crawl discogs" o arquivo "albums.jsonl" com as informações do site vai ficar salvo no caminho da pasta abaixo.

Discogs > discogsscraper > albums.jsonl

## Como os testes unitários
    git clone https://github.com/Leonardo-Nunes-Armelim/Discogs.git
    cd Discogs
    python -m venv ./venv
    .\venv\Scripts\activate.bat
    python.exe -m pip install --upgrade pip
    pip install -r requirements.txt
    playwright install chromium
    cd discogsscraper
    pytest -k "test"

## Próximos passos

Como próximos passos, o projeto pode evoluir com a criação de um endpoint para expor os dados coletados pelos spiders, permitindo que sejam enviados diretamente para uma ferramenta de streaming de dados, como o Apache Kafka.

Com essa integração, as informações seriam coletadas e disponibilizadas em tempo real, possibilitando o consumo contínuo por pipelines de engenharia de dados e aplicações de análise e visualização.

## Opções

Se quiser rodar o spider de forma a não mostrar as páginas sendo abertas no navegador é só mudar o campo "headless" para True dentro do arquivo "settings.py"

```python
PLAYWRIGHT_LAUNCH_OPTIONS = {
    "headless": True,
    "args": ["--disable-blink-features=AutomationControlled", "--start-maximized"],
}
```

## Detalhes do desenvolvimento

O projeto foi desenvolvido na versão 3.10.11 do Python. Caso alguma funcionalidade não funcionar corretamente é recomendado ultilizar a mesma versão do desenvolvida do projeto.

````.python-version
3.10.11
```