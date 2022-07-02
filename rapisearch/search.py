import json, time
from datetime import datetime
from urllib.parse import urlparse, parse_qs
from requests import session
from bs4 import BeautifulSoup
from bs4.element import Tag

USER_AGENT = {"User-Agent": 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/102.0.0.0 Safari/537.36'}

class SearchResults:
    def __init__(self, Data: dict[str], resp: BeautifulSoup) -> None:
        self.Data = Data
        self.__resp = resp
    
    def writeRawHTML(self, path: str) -> None:
        with open(path, "w", encoding="utf-8") as f:
            f.write(self.__resp.prettify())

    def writeJSON(self, path: str) -> None:
        with open(path, 'w') as f:
            f.write(json.dumps(self.Data, indent=4, sort_keys=True))

def searchgoogle(q: str, hl: str = "en", gl: str = "us", allow_to_get_answer: bool = False, **kwargs) -> SearchResults:
    """
    Args:
        q (str): query to search
        hl (str, optional): Change google search language. Defaults to "en".
        gl (str, optional): Country search. Defaults to "us".
        allow_to_get_answer (bool, optional): Getting answers from "People also ask" may take sometime to get due to each response, Allowing this may take around .2s - .1s for single response. Defaults to False.
        
    """

    def dapatinJawabanbox(so: BeautifulSoup) -> dict[str]:
        answerbox_element = so.find("div", {"class": "V3FYCf"}) or so.find("div", {"class": "TrpAt kp-rgc"})
        artiKata_element = so.find("div", {"class": "lr_container yc7KLc mBNN3d"}) #Cek kalau jawaban itu arti dari kata
        jawaban = {}

        if answerbox_element:
            listJawaban_element = answerbox_element.find_all("li", {"class": "TrT0Xe"}) #Cek kalau jawaban itu list, Contohnya: 1. Ke kamar mandi 2. **** 3. Tidur
            tableJawaban_element = answerbox_element.select('[class="Crs1tb"] tbody > tr > *')
            description = answerbox_element.find("span", {"class": "hgKElc"}) or answerbox_element.find("div", {"class": "iKJnec"})
            # with open("index.html", 'w', encoding="utf-8") as f: #Ini untuk debug, kalau ada error waktu mengambil jawaban maka halaman jawaban akan di tulis
            #     f.write(so.prettify())

            if listJawaban_element:
                description = [i.text for i in listJawaban_element]

            if tableJawaban_element:
                # print(answerbox_element.find("div", {"class": "Crs1tb"}).find_all("tr")[0].select('*'))
                description = [i.text for i in tableJawaban_element]

            if answerbox_element.find("div", {"class": 'N6Sb2c i29hTd'}): #Cek kalau answerbox itu umur
                jawaban = {
                    "type": "age",
                    "title": answerbox_element.find("div", {"class": "N6Sb2c i29hTd"}).text,
                    "answer": answerbox_element.find("div", {"class": "Z0LcW"}).text,
                    "passed": answerbox_element.find("div", {"class": 'yxAsKe kZ91ed'}).text if answerbox_element.find("div", {"class": 'yxAsKe kZ91ed'}) else "",
                }
                
                search_lainnya = answerbox_element.find("div", {"class": "Ss2Faf zbA8Me qLYAZd q8U8x"})
                if search_lainnya:
                    jawaban[search_lainnya.find("a").text.replace(" ", "_").lower()] = [{
                        "name": i.text, 
                        "link": i['href']
                    } for i in answerbox_element.select('div[class="zVvuGd MRfBrb"] > div > a')]
            else:
                jawaban = {
                    "type": "search",
                    "answer": answerbox_element.find("div", {"class": "IZ6rdc"}).text if answerbox_element.find("div", {"class": "IZ6rdc"}) else "",
                    "description": description.text if isinstance(description, Tag) else description,
                    "title": answerbox_element.find("h3", {"class": "LC20lb MBeuO DKV0Md"}).text,
                    "link": answerbox_element.find("h3", {"class": "LC20lb MBeuO DKV0Md"}).parent['href'],
                    "displayed_link": answerbox_element.find("cite").text,
                }

                jawabanTable_element = answerbox_element.find("table")
                if jawabanTable_element:
                    jawaban["table"] = [k.text for j in jawabanTable_element.find_all("tr") for k in j.select("tr > *")]

        elif artiKata_element:
            child_div = artiKata_element.select('[class="bqVbBf jfFgAc CqMNyc"] > div')
            posisi_similar = child_div.index(next((z for z in child_div if z.text == "Similar:")))
            posisi_opposite = child_div.index(next((z for z in child_div if z.text == "Opposite:")))

            similar  = [child_div[i].text for i in range(posisi_similar, posisi_opposite) if child_div[i].get("role") and child_div[i].text]
            opposite = [child_div[i].text for i in range(posisi_opposite, len(child_div)) if child_div[i].get("role") and child_div[i].text]

            # print(similar)
            # print(opposite)
            jawaban = {
                "type": "meaning",
                "word": artiKata_element.select_one('[class*="c8d6zd xWMiCc"]').text,
                "pronounce": artiKata_element.find("span", {"class": "LTKOO"}).text if artiKata_element.find("span", {"class": "LTKOO"}) else "",
                "word_type": artiKata_element.select_one('[class*="YrbPuc vdBwhd"]').text,
                "definition": [x.text for x in artiKata_element.find_all("div", {"data-dobid": "dfn"})],
                "similar" : similar,
                "opposite": opposite
            }
        
        return jawaban

    s = session()
    s.headers.update(kwargs.get("User-Agent", USER_AGENT))

    data = {
        "results_request": {
            "created_on": "",
            "google_url": "",
            "time_needed": 0
        },
        "search_parameters": {
            "q": q,
            "country": gl,
            "language": hl,
        },
        "search_information": {
            "displayed_query": "",
            "total_search": 0,
            "time_results_needed": 0
        },
        "page_information": {
            "title": "",
            "description_source": {
                "description": "",
                "source": "",
                "source_link": ""
            },
        },
        "displayed_video": {
            "video": [],
        },
        "search_links": [],
        "related_questions": [],
        "related_searches": []
    }

    mulai = time.time()

    url = f"https://www.google.com/search?q={q}&hl={hl}&gl={gl}&aqs=chrome.0.69i59j69i61l2j69i60.792j0j7&sourceid=chrome&ie=UTF-8"
    resp = s.get(url)
    soup = BeautifulSoup(resp.content, 'lxml')

    # writeRawHTML("index.html")

    data["search_information"]["displayed_query"] = soup.find("input", {"class": "gLFyf gsfi"})['value']
    data["search_information"]["total_search"] = int("".join(x for x in soup.find("div", {"id": "result-stats"}).text.split(" ")[1] if x.isdigit()))
    data["search_information"]["time_results_needed"] = float(soup.find("div", {"id": "result-stats"}).text.split(" ")[3].replace("(", "").replace(",","."))

    informasi_halaman_element = soup.find("div", {"jscontroller": "cSX9Xe"})
    judul_informasi_halaman = soup.select_one("[data-attrid=title]")

    if judul_informasi_halaman and informasi_halaman_element:
        subtitle = soup.find("div", {"data-attrid": "subtitle"})
        deskripsi = soup.find("div", {"class": "kno-rdesc"})
        
        data["page_information"]["title"] = judul_informasi_halaman.text
        
        if subtitle:
            data["page_information"]["type"] = subtitle.text

        data["page_information"]["description_source"]["description"] = deskripsi.find_all("span")[0].text if deskripsi else "No description"
        if deskripsi:
            data["page_information"]["description_source"]["source"] = deskripsi.find("a").text if deskripsi.find("a") else ""
            data["page_information"]["description_source"]["source_link"] = deskripsi.find("a")['href'] if deskripsi.find("a") else ""

        #cek kalau ada vidio klip seperti trailer
        klip_element = soup.find("div", {"class": "eSsNob"})
        if klip_element:
            data["page_information"]["clip"] = {
                "title": klip_element.find("div", {"class": "ellip"}).text,
                "link": klip_element.parent['href'],
                "duration": klip_element.find("span", {"class": "MPavMc"}).text,
            }

        #Dapatin rating
        rate = soup.select_one('div[class*="zr7Aae"]')
        if rate:
            data["page_information"]["rating"] = [{
                "title": i.parent.find("span", {"class": "wDgjf"}).text if i.parent.find("span", {"class": "wDgjf"}) else i.parent.find("span", {"class": "rhsB pVA7K"}).text, 
                "rating": i.text, 
                "link": i.parent['href']} 
            for i in rate.select('span[class*=gsrt]')]

        rate_googleuser = soup.find("div", {"class": "srBp4 Vrkhme"})
        if rate_googleuser:
            data["page_information"]["rating_googleuser"] = {
                "description": rate_googleuser.find("div", {"class": "a19vA"}).text,
                "platform": rate_googleuser.find("div", {"class": "OZ8wsd"}).text
            }

        #Dapatin informasi singkat, contohnya "Designed by: Guido van rossum"
        i: Tag
        for i in soup.find_all("span", {"class": "w8qArf"}):
            lebih_link = i.parent.find("span", {"class": "LrzXr kno-fv wHYlTd z8gr9e"}).find_all("a", {"class": "fl"})

            nama = i.text.strip().replace(" ", "_").replace(":", "").lower()
            if len(lebih_link) <= 1:
                data["page_information"][nama] = {
                    "text": lebih_link[0].parent.text if len(lebih_link) == 1 else i.parent.find("span", {"class": "LrzXr kno-fv wHYlTd z8gr9e"}).text,
                    "link": "https://google.com"+lebih_link[0]['href'] if lebih_link else ""
                } 
            else:
                data["page_information"][nama+"_links"] = []

                k : Tag
                for k in lebih_link:
                    data["page_information"][nama+"_links"].append({
                        "text": k.text,
                        "link": "https://google.com"+k["href"]
                    })
        
        #Dapatin table informasi
        informasi_table_element = soup.find_all("table", {"class": "AYBNrd"})
        if informasi_table_element:
            data["page_information"]["information_table"] = {}
            j : Tag
            for c, j in enumerate(informasi_table_element):
                # Bad code tapi berjalan dengan mulus
                if c == 0:
                    for v in j.find_all("td"):
                        data["page_information"]["information_table"][v.find("span", {"class": "V6Ytv"}).text.replace(" ", "_").lower()] = v.find_all("span")[1].text
                elif c == 1:
                    for v in j.find_all("tr", {"class": "kno-nf-nr"}):
                        if len(v.find_all("span")) < 3: break

                        text_span = v.find_all("span")
                        data["page_information"]["information_table"][text_span[0].text.replace(" ", "_").lower()] = [text_span[1].text, text_span[2].text]
                elif c == 2:
                    tr = j.find_all("tr")
                    for x in tr:
                        td = x.find_all("td")
                        for b in range(0, len(td), 2):
                            if td[b].text == "": continue
                            data["page_information"]["information_table"][td[b].text.replace(" ", "_").lower()] = td[b+1].text            

        # peringkat penonton seperti jumlah rating 5 ke 1 / Audience rating summary
        rating_summary = soup.find("div", {"class": "jYcvae kY5Gde"})
        if rating_summary:
            total_rating = int(rating_summary.find("div", {"class": "H5xxEd"}).text.split(" ")[0])
            data["page_information"]["rating_summary"] = {
                "rating": float(rating_summary.find("div", {"class": "xt8Uw q8U8x"}).text),
                "total_ratings": total_rating,
            }

            elemen_bintang = rating_summary.find_all("div", {"class": "l2gNXd"})
            # Bad code, realy bad code but this is what i can do 
            # timer_rate = time.time()
            x : Tag
            for i, x in enumerate(elemen_bintang): #Bintang rating 5 -> 1
                hasil_width = float(x['style'].replace("width:", "").replace("%", ""))
                for j in range(1, total_rating+1):
                    hasil = (total_rating - j)/total_rating*100
                    if hasil == hasil_width:
                        data["page_information"]["rating_summary"][str(len(elemen_bintang)-i)] = total_rating - j
                        break
            # print(time.time() - timer_rate)

        #reviews orang lain
        komentar_element = soup.find_all("div", {"jsname": "HeNW9"})
        if komentar_element:
            data["page_information"]["user_reviews"] = [{
                "rating": i.find("star-rating")['data-ir'], 
                "review": i.find("span").text} 
            for i in komentar_element]

        #List informasi lain yang ada di paling bawah
        i : Tag
        for i in informasi_halaman_element.select('[class*="LuVEUc XleQBd CGCvRb B03h3d"]'):
            judul = i.parent.parent.find("div", {"class": "HnYYW"}).text if i.parent.parent.find("div", {"class": "HnYYW"}) else i.find("div", {"class": 'Ss2Faf zbA8Me qLYAZd q8U8x'}).find("div", {"class": "VLkRKc"}).text
            elements = i.select('[class*="PZPZlf"]') or i.select('td[class="ellip"]')
            data["page_information"][judul.replace(" ", "_").lower()] = [{
                "nama": c.text if c.name == "a" else c.find("a").text,
                "link": "https://google.com"+(c['href'] if c.name == "a" else c.find("a")['href'])
            } for c in elements]

        #liat tentang hasil (See results about)
        listliatresult = soup.select('[data-md="62"]')
        if listliatresult:
            data["page_information"][soup.find("h2", {"class": "qrShPb garHBe q8U8x"}).text.replace(" ", "_").lower()] = [{
                "title": i.select_one('div[class*="RJn8N"]').text,
                "type": i.find("span", {"class": "rhsl5 rhsg3"}).text,
                "link": "https://google.com"+i.find("a")['href']
            } for i in listliatresult]

    #dapatin element yang dipenuhi dengan list karakter, seperti "cast, characters"
    list_element_cast = soup.select('div[class*="LuVEUc XleQBd CGCvRb B03h3d V14nKc EN1f2d"]')
    for i in list_element_cast:
        data[i.parent.parent.find("div", {"class": "HnYYW"}).text.replace(" ", "_").lower()] = [{
            "name": v.find("div", {"class": "oyj2db"}).text.strip(),
            "description": v.find("div", {"class": "wwLdc"}).text if v.find("div", {"class": "wwLdc"}) else "",
            "link": "https://google.com"+v['href']
        } for v in i.find_all("a", {"class": "ttwCMe"})]

    #Dapatin jawaban box element
    dapatinJawaban = dapatinJawabanbox(soup)
    if dapatinJawaban:
        data["answers"] = dapatinJawaban

    # Dapatin informasi bola
    bola_element = soup.find_all("div", {"jsaction": "rcuQ6b:npT2md;JqlOve"})
    if bola_element:
        namaTim = soup.find("div", {"class": "ofy7ae"}).text

        data.setdefault("soccer", {})['match'] = []
        data["soccer"]["team"] = namaTim
        data["soccer"]["position"] = soup.find("span", {"class": "mKwiob imso-ani"}).text

        i : Tag
        for i in bola_element:
            timElements = i.select('[class*="ellipsisize"]')
            timElement = timElements[timElements.index(next((x for x in timElements if x.text in namaTim)))]
            enemyElement = timElements[timElements.index(next((x for x in timElements if x.text not in namaTim)))]

            started = i.select('[class="imso-hide-overflow"] > span')[1] if i.select('[class="imso-hide-overflow"] > span') else i.find("div", {"class": "imspo_mt__ns-pm-s"})
            started = started or i.find("div", {"class": "imspo_mt__cmd"})

            # print(enemyElement.text)
            data["soccer"]["match"].append({
                "team": timElement.text,
                "enemy": enemyElement.text,
                "started": started.text,
                "matchday": i.find("div", {"class": "imso_mh_s__lg-st-srs"}).text if i.find("div", {"class": "imso_mh_s__lg-st-srs"}) else i.find("div", {"class": "imspo_mt__lg-st-co"}).text
            })

            cekKalauSudahSelesai = i.find("div", {"class": "AfwOkb imso_gs__gs-cont imso-medium-font imso_gs__gs-cont-ed"}) #Cek kalau pertanding sudah selesai
            if cekKalauSudahSelesai:
                data["soccer"]["match"][-1]["enemy_goal"] = {}
                data["soccer"]["match"][-1]["team_goal"] = {}

                data["soccer"]["match"][-1]["enemy_goal"]["goal"] = int(i.find("div", {"class": "imso_mh__ma-sc-cont"}).find_all("div")[0].text)
                data["soccer"]["match"][-1]["team_goal"]["goal"] = int(i.find("div", {"class": "imso_mh__ma-sc-cont"}).find_all("div")[2].text)

                data["soccer"]["match"][-1]["enemy_goal"]["player_goal"] = [x.text for x in i.find("div", {"class": "imso_gs__tgs imso_gs__left-team"}).find_all("div")]
                data["soccer"]["match"][-1]["team_goal"]["player_goal"] = [x.text for x in i.find("div", {"class": "imso_gs__tgs imso_gs__right-team"}).find_all("div")]
            
            cekKalauSudahSelesai = i.find("div")

    #GPS lokasi
    lokasi = soup.find("div", {"class": "H93uF"})
    if lokasi:
        link = lokasi.find("a")
        if "rllag" in link['href']:
            data["lokasi"] = {}
            gps: list[str] = parse_qs(urlparse(link['href']).query)["rllag"][0].split(",")
            
            data["lokasi"]["gps"] = {
                "latitude": int(gps[0]) * .000001,
                "longtitude": int(gps[1]) * .000001,
                "altitude": int(gps[2])
            }
            data["lokasi"]["link"] = "https://google.com"+link['href']

    #Tempat warung lokasi
    tempat_element = soup.select('div[class*=w7Dbne]')
    if tempat_element:
        data["tempat_lokasi"] = {}
        data["tempat_lokasi"]["lokasi"] = []
        i : Tag
        for i in tempat_element:
            rllt: str = i.find("div", {"class": "rllt__details"}).find_all("div")
            data["tempat_lokasi"]["lokasi"].append({
                "title": i.find("div", {"class": "dbg0pd"}).text,
                "address": rllt[2].text,
                "description": i.find("div", {"class": "dXnVAb"}).text.replace("·", " - ") if i.find("div", {"class": "dXnVAb"}) else "No description",
                "tipe": rllt[1].text[rllt[1].text.find(")")+4:] if rllt[1].text.find(")") != -1 else rllt[1].text,
                "hasil_rating": {
                    "rating": float(i.find("span", {"class": "YDIN4c YrbPuc"}).text.replace(",",".")) if i.find("span", {"class": "YDIN4c YrbPuc"}) else rllt[1].text,
                    "people_rating": i.find("span", {"class": "HypWnf YrbPuc"}).text.replace("(","").replace(")","") if i.find("span", {"class": "HypWnf YrbPuc"}) else rllt[1].text
                },
            })
        data["tempat_lokasi"]["lokasi_lainnya"] = "https://google.com"+soup.find("div", {"class": "iNTie"}).find("a", {"class": "tiS4rf Q2MMlc"})['href']

    #Hasil Resep
    Resep_element = soup.find_all("a", {"class": "a-no-hover-decoration"})
    if Resep_element:
        resep: list[dict] = [{
            "judul": i.find("div", {"class": "hfac6d LviCwe tNxQIb ynAwRc"}).text,
            "source": i.find("cite", {"class": "KuNgxf"}).text,
            "time_taken": i.find("div", {"class": "wHYlTd z8gr9e mr8ekd tbeioe"}).text if i.find("div", {"class": "wHYlTd z8gr9e mr8ekd tbeioe"}) else "No time taken",
            "link": i['href'],
            "rating_result": {
                "rating": float(i.find("span", {"class": "YDIN4c YrbPuc"}).text) if i.find("span", {"class": "YDIN4c YrbPuc"}) else i.find("div", {"class": "RbkJtf"}).text,
                "people_rating": int(i.find("span", {"class": "HypWnf YrbPuc"}).text.replace("(", "").replace(")", "")) if i.find("span", {"class": "HypWnf YrbPuc"}) else i.find("div", {"class": "RbkJtf"}).text
            },
            "ingredients": [j.strip() for j in i.find("div", {"class": "LDr9cf L5KuY tbeioe CqqFGf"}).text.split(',')]
        } for i in Resep_element if i.find("div", {"class": "hfac6d LviCwe tNxQIb ynAwRc"}) != None]
        if resep:
            data["recipe"] = resep

    #Link iklan
    link_iklan = soup.find_all("div", {"data-text-ad": "1"})
    if link_iklan:
        data["iklan"] = []
        i: Tag
        for i in link_iklan:
            situs_sama = [{
                "judul": j.find("h3").text,
                "deskripsi": j.find("div", {"class": "MUxGbd yDYNvb lyLwlc aLF0Z OSrXXb"}).text,
                "link": j.find("a")['href'],
            } for j in i.find_all("div", {"class": "MhgNwc"})]

            data["iklan"].append({
                "judul": i.find("div", {"role": "heading"}).text,
                "deskripsi": i.find("div", {"class": "MUxGbd yDYNvb lyLwlc"}).text,
                "link": i.find("a", {"class": "sVXRqc"})['href'],
            })

            if situs_sama:
                data["iklan"][-1]["situs_sama"] = situs_sama

    #Produk
    produk_element = soup.find_all("div", {"class": "Xhm3Sb a-no-hover-decoration"})
    if produk_element:
        data["product"] = [{
            "title": i.find("div", {"class": "GJfQob"}).text,
            "price": i.find("div", {"class": "z235y jAPStb"}).text,
            "currency": i.find("div", {"class": "z235y jAPStb"}).text[0],
            "store": i.find("div", {"class": "ix5OZc"}).text,
            "rating": i.find("span", {"class": "Fam1ne QjH6g"})['aria-label'].split(" ")[1] if i.find("span", {"class": "Fam1ne QjH6g"}) else "",
            "people_rating": i.find("span", {"class": "xdUCw"}).text.replace("(", "").replace(")", "") if i.find("span", {"class": "xdUCw"}) else "",
            "platform": i.find("div", {"class": "oYFFnd yXy5c"}).text
        } for i in produk_element]
        
    #Hasil link 
    x : Tag
    for x in soup.find_all("div", {"class": "g"}):
        tampilan_link = x.find("cite", {"role": "text"}) #Cek kalau ada tampilan_link (atau display link)
        deskripsi = x.select_one('div[class*="VwiC3b"]')
        
        if tampilan_link:
            judul_link = x.find("h3").text
            # Cek kalau ada judul yang sama di data link pencarian
            betul = False 

            if data.get("answers"): #cek kalau link sudah ada di jawaban dictionary
                betul = data["answers"].get("title") == judul_link

            for j in data["search_links"]:
                if j["title"] == judul_link:
                    betul = True
            
            if betul: continue

            #Situs tambahan ada 2 jenis, table dan list
            list_situstambahan = []
            tabledata = x.find("table", {"class": "jmjoTe"})
            uldata = x.find("ul", {"class": "FxLDp"})
            if tabledata:
                list_situstambahan = [{
                    "title": v.find("a").text,
                    "description": v.find("div", {"class": "zz3gNc"}).text if v.find("div", {"class": "zz3gNc"}) else "No description",
                    "link": v.find("a")['href'] if "/search?" not in v.find("a")['href'] else "https://google.com"+v.find("a")['href'] 
                } for v in tabledata.find_all("td") if v.find("form") == None]
            elif uldata:
                list_situstambahan = [{
                    "title": v.find("h3").text,
                    "description": v.find("div", {"style": "-webkit-line-clamp:2"}).text,
                    "link": v.find("a")['href']
                } for v in uldata.find_all("li")]

            situs_lain = x.find("div", {"class": "HiHjCd"})
            list_situslain = [{"title": v.text, "link": v['href']} for v in situs_lain.find_all("a")] if situs_lain else []

            potongansingkat = x.find_all("div", {"class": "rEYMH OSrXXb"})
            list_potongansingkat = []
            
            if potongansingkat:
                v: Tag
                for v in potongansingkat:
                    soal = v.find("span", {"class": "YrbPuc WGKbId BBwThe"}).text.replace(" ", "_").replace(":", "").lower()
                    soal = soal[0:len(soal)-1]
                    jawaban_element = v.find("span", {"class": "wHYlTd z8gr9e"})
                    jawaban_link = []
                    jawaban = ""

                    if jawaban_element.find_all("a"):
                        j: Tag
                        for j in jawaban_element.find_all("a"):
                            jawaban += j.text + " "
                            jawaban_link.append({
                                "title": j.text,
                                "link": j['href']
                            })
                    else:
                        jawaban = jawaban_element.text

                    list_potongansingkat.append({
                        "title": soal,
                        "snippet": jawaban.strip(),
                    })
                    if jawaban_link:
                        list_potongansingkat[-1]["snippet_link"] = jawaban_link

            #Rating link
            hasil_rating = []
            rating_links = x.find("div", {"class": "fG8Fp uo4vr"})
            if rating_links:
                hasil_rating = [i.text for i in rating_links.select('[class="fG8Fp uo4vr"] > span')]

            resep_deskripsi = x.select('div[class*="xeBVJe OSrXXb uYZpsf U09Jxd"]')
            list_resep_deskripis = [z.text for z in resep_deskripsi] if resep_deskripsi else []

            data["search_links"].append({
                "title": judul_link,
                "description": deskripsi.text if deskripsi else list_resep_deskripis,
                "link": x.find("a")['href'],
                "link_displayed": tampilan_link.text,
                # "more_links": list_situstambahan,
                # "another_links": list_situslain,
                # "shortcut": list_potongansingkat,
                # "rating": hasil_rating,
            })

            if list_situstambahan:
                data["search_links"][-1]["more_links"] = list_situstambahan
            if list_situslain:
                data["search_links"][-1]["another_links"] = list_situslain
            if potongansingkat:
                data["search_links"][-1]["shortcut"] = list_potongansingkat
            if hasil_rating:
                data["search_links"][-1]["rating"] = hasil_rating
    
        #Cek kalau ada link twitter, kita tidak bisa gabungkan dengan "Hasil link" karena variabel classnya berubah dengan link lainnya
        tweetselement = x.find("div", {"class": "e2BEnf otisdd"})
        if tweetselement:
            # gua suka singkatkan kode
            data["search_links"].append({
                "title": tweetselement.find("h3").text,
                "link": tweetselement.find("a")['href'],
                "link_displayed" : tweetselement.find("cite").text,
                "tweets": [{
                    "description": j.find("div", {"class": "xcQxib eadHV YBEXSb wHYlTd"}).text,
                    "link": j.find("a", {"class": "h4kbcd"})['href'],
                    "upload_date": j.find_all("span", {"class": "f"})[1].text,
                    "username": j.find("span", {"class": "jUVTC s3dYDc"}).text if j.find("span", {"class": "jUVTC s3dYDc"}) else "",
                    "nickname": j.find("div", {"class": "zTpPx s3dYDc"}).text.strip()[:j.find("div", {"class": "zTpPx s3dYDc"}).text.strip().index("@")] if j.find("div", {"class": "zTpPx s3dYDc"}) else "",
                } for j in tweetselement.parent.find_all("div", {"class": "aMAfLd"})]
            })

    #Pertanyaan yang terkait
    i: Tag
    for i in soup.find_all("div", {"class": "z9gcx SVyP1c"}):
        soal = i['data-q']
        jawaban = {
            "question": soal,
            "answer": "No answer",
            "title": "",
            "link": "",
        }

        if allow_to_get_answer:
            #Baris ini lebih banyak memakan waktu, dikarenakan 1 request pertanyaan bisa memakan .2 detik, kemungkinan harus ditambahakan parameter untuk memperbolehkan dapatkan pertanyaan atau tidak, depending to it user
            so = BeautifulSoup(s.get(f"https://www.google.com/search?q={soal.replace(' ', '+')}&hl={hl}&gl={gl}&aqs=chrome.0.69i59j69i61l2j69i60.792j0j7&sourceid=chrome&ie=UTF-8", headers=USER_AGENT).content, 'lxml') 
            data_jawaban = dapatinJawabanbox(so)
            
            if data_jawaban:
                jawaban = {
                    "question": soal,
                    "answer": data_jawaban.get("description") or data_jawaban.get("answer", ""),
                    "title": data_jawaban.get("title", ""),
                    "link": data_jawaban.get("link", "")
                }

        data["related_questions"].append(jawaban)

    #Vidio link seperti youtube twitch dan lain lain
    vidio_link_element = soup.find_all("div", {"class": "mnr-c"})
    if vidio_link_element:
        data["video_link"] = []
        i : Tag
        for i in vidio_link_element:
            vidio_list_element = i.find_all("a", {"class": "irqWwf"})
            
            if vidio_list_element:
                data["video_link"].append({
                    "title": i.find("h3").text,
                    "link": i.find("a")['href'],
                    "link_displayed": i.find("cite").text,
                    "video": [{
                        "title": j.find("div", {"class": "w18VHb YVgRyb tNxQIb ynAwRc OSrXXb"}).text,
                        "link": j['href'],
                        "platform": j.find("cite").text,
                        "channel": j.find("span", {"class": "gipoFf OSrXXb"}).text,
                        "upload_date": j.find_all("div", {"class": "gipoFf OSrXXb"})[1].text,
                        "duration": j.find("div", {"class": "J1mWY"}).text
                    } for j in i.find_all("a", {"class": "irqWwf"})]
                })

    #Vidio yang ditunjukkin
    list_video = soup.find_all("div", {"class": "RzdJxc"})
    if list_video:
        data["displayed_video"]["video"] = [{
            "title": i.find("div", {"class": "fc9yUc tNxQIb ynAwRc OSrXXb"}).text, 
            "link": i.find("a", {"class": "X5OiLe"})['href'], 
            "platform": i.find("cite").text, 
            "channel": i.find("span", {"class": "pcJO7e"}).find("span").text[3:] if i.find("span", {"class": "pcJO7e"}).find("span") else "No channel", 
            "duration": i.find("div", {"class": "J1mWY"}).text if i.find("div", {"class": "J1mWY"}) else "Live", 
            "date": i.find("div", {"class": "hMJ0yc"}).text if i.find("div", {"class": "hMJ0yc"}) else ""
            } for i in list_video]
        
        data["displayed_video"]["more_video"] = "https://google.com"+soup.find("div", {"class": "aEkOAd"}).find("a")['href']

    #Berita utama
    berita = soup.find_all("a", {"class": "WlydOe"})
    if berita:
        data["news"] = {}
        data["news"]["news_list"] = [{
            "title": i.find("div", {"class": "mCBkyc tNxQIb ynAwRc nDgy9d"}).text, 
            "source": i.select_one('img[class*="YQ4gaf zr758c"]')['alt'] if i.select_one('img[class*="YQ4gaf zr758c"]')['alt'] != "" else i.find("div", {"class": "CEMjEf NUnG9d"}).text, 
            "link": i['href'],
            "upload_date": i.find("div", {"class": "OSrXXb ZE0LJd"}).text
        } for i in berita]
        
        # data["news"]["news_list"] = "https://google.com"+(soup.find("div", {"class": "e2BEnf U7izfe hWIMdd axf3qc q8U8x"}).parent.find("a", {"class": "tiS4rf Q2MMlc"})['href'] if soup.find("div", {"class": "e2BEnf U7izfe hWIMdd axf3qc q8U8x"}) else soup.find("div", {"class": "e2BEnf U7izfe hWIMdd q8U8x"})).parent.find("a", {"class": "tiS4rf Q2MMlc"})['href'] # saya tidak tau kalau "berita_lain" ini perlu digunakan atau tidak bagi saya tidak jadi saya tidak mau tambahin

    #terkait_penelusuran
    i: Tag
    for i in soup.find_all("div", {"class": "s75CSd OhScic AB4Wff"}):
        data["related_searches"].append({
            "judul": i.text,
            "link": "https://google.com"+i.parent['href']
        })

    selesai = time.time()

    data["results_request"]["created_on"] = datetime.now().strftime("%A, %B %d, %Y, %H:%M")
    data["results_request"]["google_url"] = url
    data["results_request"]["time_needed"] = float("{:.2f}".format(selesai - mulai))

    # writeJSON("test.json")
    return SearchResults(data, soup)