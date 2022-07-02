# rapisearch

rapisearch is a python library for scraping google search

## Installation
Download as a zip file or clone this repository
```bash
git clone https://github.com/rafiathallah3/rapisearch.git
```

Install the libraries
```bash
pip install requirements.txt
```

## Usage

```py
from rapisearch import searchgoogle

result = searchgoogle("Cow")
print(result.Data["results_request"]["time_needed"])

result.writeRawHTML("Cow.html")
result.writeJSON("Cow.json")
```

## Translate

# rapisearch

rapisearch adalah library untuk mengambil data google

## Instalasi
Download sebagai zip file atau clone repository ini
```bash
git clone https://github.com/rafiathallah3/rapisearch.git
```

Install libraries
```bash
pip install requirements.txt
```

## Penggunaan

```py
from rapisearch import searchgoogle

result = searchgoogle("Anjing")
print(result.Data["results_request"]["time_needed"])

result.writeRawHTML("Anjing.html")
result.writeJSON("Anjing.json")
```