from bs4 import BeautifulSoup
import bs4
from selenium import webdriver
from webdriver_manager.firefox import GeckoDriverManager
from selenium.webdriver import FirefoxOptions
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from markdownify import markdownify
import time
import os.path
from selenium.common.exceptions import TimeoutException

# Utilize headless browser
opts = FirefoxOptions()
opts.add_argument("--incognito")
opts.add_argument("--headless")
driver = webdriver.Firefox(
    executable_path=GeckoDriverManager().install(), options=opts)

# Function to update superscripts recursively


def update_sup(soup):
    if soup.name == "sup":
        if any(not isinstance(i, bs4.element.NavigableString) for i in soup.contents):
            soup.extract()
        else:
            soup.string = f'[{soup.get_text(strip=True)}]'
    for i in filter(lambda x: not isinstance(x, bs4.element.NavigableString), soup.contents):
        update_sup(i)


# Select input TXT file
with open("linklist.txt", "r") as f_in:
    for line in map(str.strip, f_in):
        if not line:
            continue

        try:
            driver.get(line)
            time.sleep(20)  # standard delay

            # Wait until necessary elements are present
            delay = 60  # Max delay in seconds until element is present
            WebDriverWait(driver, delay).until(
                EC.visibility_of_element_located((By.CLASS_NAME, "srnummer")))
            WebDriverWait(driver, delay).until(
                EC.visibility_of_element_located((By.CLASS_NAME, "erlasstitel")))
            WebDriverWait(driver, delay).until(
                EC.visibility_of_element_located((By.ID, "lawcontent")))
            html = driver.page_source
            soup = BeautifulSoup(html, "html.parser")

            # Remove toolbar
            soup.find(id="toolbar").decompose()

            # Remove footnotes
            for div in soup.find_all("div", "footnotes"):
                div.decompose()

            # Call function to handle superscripts
            update_sup(soup)

            # Isolate descriptive lists to paragraphs
            for dl_list in soup.find_all("dl"):
                dl_list.name = "p"

            for dt_list in soup.find_all("dt"):
                dt_list.insert_after(" ")  # Add whitespace after tag
                dt_list.insert(0, "|    ")  # Add nonbreaking spaces as indent
                dt_list.name = "br"

            # Replace articles with bold paragraphs
            for article in soup.find_all("h6", "heading"):
                article.name = "p"

            # Replace div headings with corresponding <h> tag
            for div in soup.select("div[aria-level]"):
                if div["aria-level"] > "6":  # Capp at max lvl 6
                    div.name = f'h6'
                else:
                    div.name = f'h{div["aria-level"]}'
                del div.attrs

            # Get norms
            lawtext = soup.find(id="lawcontent")

            # Add disclaimer according to Art. 49 PublV
            disclaimer = """
            **Disclaimer**  

            EN: This MD file was generated automatically through conversion of the HTML source served by the Federal Publishing Platform [Fedlex](https://www.fedlex.admin.ch/).
            During this process, certain elements of the original source such as footnotes, tables or pictures can be lost or transformed incorrectly. Any inaccuracies present in the HTML source will be carried over to the MD file.  

            DE: Diese MD Datei wurde durch automatische Konvertierung des auf der Publikationsplattform des Bundes [Fedlex](https://www.fedlex.admin.ch/) publizierten HTML Quelltextes erstellt.
            Dieser Konvertierungsprozess kann dazu führen, dass gewisse Elemente wie bspw. Fussnoten, Tabellen oder Bilder falsch dargestellt werden oder verloren gehen.
            Allfällige inkorrekte Passagen im HTML Quelltext werden in die MD Datei übernommen.  

            EN: This is not an official publication. Only the official publication by the [Federal Chancellery](https://www.bk.admin.ch/bk/en/home.html) is authorative and legally binding.  
            DE: Dies ist keine amtliche Veröffentlichung. Massgebend ist allein die Veröffentlichung durch die [Bundeskanzlei](https://www.bk.admin.ch/bk/de/home.html).  
            FR: Ceci n’est pas une publication officielle. Seule la publication opérée par la [Chancellerie fédérale](https://www.bk.admin.ch/bk/fr/home.html) fait foi.  
            IT: presente documento non è una pubblicazione ufficiale. Fa unicamente fede la pubblicazione della [Cancelleria federale](https://www.bk.admin.ch/bk/it/home.html).  

            &nbsp;

            ----

            &nbsp;
            
            """

            # Convert to markdown
            raw_markdown = disclaimer + \
                markdownify(str(lawtext), heading_style='ATX')

            # Strip whitespace left of text
            clean_markdown = '\n'.join(
                _.lstrip() for _ in raw_markdown.split('\n'))

            # Fetch SR number
            sr_num = soup.find("p", "srnummer")
            if not sr_num:  # <== check for NoneType
                print('element not found')
                sr_num = 'no_sr_num'
            else:
                sr_num = sr_num.text

            # Fetch law title
            law_title = soup.find("h1", "erlasstitel")
            if not law_title:  # <== check for NoneType
                print('element not found')
                law_title = 'no_title'
            else:
                law_title = law_title.text

            # Define categories and match with sr number
            sr_num_string = str(sr_num)
            sr_digits = ["1", "2", "3", "4", "5", "6", "7", "8", "9"]
            
            # Set categories according to language
            if "/en" in line:
                categories = ["State - People - Authorities",
                            "Private law - Administration of Civil Justice - Enforcement",
                            "Criminal law - Administration of Criminal Justice - Execution of Sentences",
                            "Education - Science - Culture",
                            "National defence",
                            "Finance",
                            "Public works - Energy - Transport",
                            "Health - Employment - Social Security",
                            "Economy - Technical Cooperation"]
            else:
                categories = ["Staat - Volk - Behörden",
                            "Privatrecht - Zivilrechtspflege - Vollstreckung",
                            "Strafrecht - Strafrechtspflege - Strafvollzug",
                            "Schule - Wissenschaft - Kultur",
                            "Landesverteidigung",
                            "Finanzen",
                            "Öffentliche Werke - Energie - Verkehr",
                            "Gesundheit - Arbeit - Soziale Sicherheit",
                            "Wirtschaft - Technische Zusammenarbeit"]
            
            # Link SR num to category according to the first digit
            if sr_num_string[0] in sr_digits:
                category = categories[sr_digits.index(sr_num_string[0])]
            else:
                category = "no category"

            # Write to markdown file in subdirectory according to language
            if "/en" in line:
                directory = "./federal_law/en/" + category + "/"
            else:
                directory = "./federal_law/de/" + category + "/"
            file_name = sr_num + "_" + law_title + ".md"
            file_path = os.path.join(directory, file_name)
            if not os.path.isdir(directory):
                os.mkdir(directory)
            with open(file_path, "w+") as f_out:
                f_out.write(clean_markdown)

        # Handle timeout exception
        except TimeoutException:
            print("Timeout Exception:", line)
