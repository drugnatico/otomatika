from robocorp.tasks import task
from robocorp import workitems
from sys import exc_info, argv, _getframe
from os.path import join as path_join, isdir
from os import makedirs

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from lxml.html import fromstring

from datetime import datetime
from pytz import timezone
from dateutil.relativedelta import relativedelta

from re import search, sub
import unicodedata

from openpyxl import Workbook

from requests import get

class Scraping():
    """
    This class contains generic methods for the extractions and save
    them (.xlsx) in the corresponding folders. Additionally, it will
    search images and videos to save.
    """
    def __init__(self, **kwargs) -> None:
        """
        Initialize the class where the section from which the
        information
        Params
        ----------
        Requerid
            phrase: Text to search into the web site
            months_ago: The months you want to consult the news
        Optional
            section: field to filter news by default sets
            'Breakingviews'
        Notes
        ----------
        The result of the execution of this class will be saved in
        excel: '../output/{self.phrase}.xlsx'
        img/video: '../output/img/{filename}'
        """
        self.output_dir = 'output'
        self.output_img = 'img'
        #Check if the directories are created, if not, create them.
        self.output_img = self.create_dir(
            path_file = [self.output_dir, self.output_img]
        )
        self.output_dir = self.create_dir(
            path_file = self.output_dir
        )
        #Datetime in CST
        self.tz = timezone('America/Chicago')
        self.datetime_now = datetime.now(self.tz)
        #Set the max range time in the current date
        self.datetime_now = self.datetime_now.replace(
            hour=00, minute=00, second=1
        )
        self.data = []
        self.count_news = 0
        self.phrase = kwargs.get("phrase")
        self.section = kwargs.get("section")
        self.months_ago = kwargs.get("months_ago")
        self.datetime_finished = self.datetime_now - relativedelta(
            months = self.months_ago
        )
        self.time_wait = 120
        #Save errors
        self.error = None
        options = webdriver.FirefoxOptions()
        options.accept_insecure_certs = True
        options.add_argument('-headless')
        options.set_preference(
            "browser.download.manager.showAlertOnComplete", False
        )
        options.set_preference(
            "browser.aboutConfig.showWarning", False
        )
        options.set_preference(
            "intl.accept_languages", "es-MX,es;q=0.8,en-US;q=0.5,en;q=0.3"
        )
        self.browser = webdriver.Firefox(
            options=options
        )
        self.browser.maximize_window()
        self.wait = WebDriverWait(self.browser, self.time_wait)

    def _save_source_code(self, filename: str = "source_code") -> None:
        """
        Save the source code of the current page to a file
        Params
        ----------
        Optional
            filename: Filename of the source code file
        """
        with open(path_join(self.output_dir, f"{filename}.html"),
                    "w", encoding="utf-8") as tf:
            tf.write(self.browser.page_source)

    def create_dir(self, path_file: str|list) -> str:
        """
        Create dir(s)
        Params
        ----------
        path_file: List or str of the name of folder(s)
        to create or check if exist
        Return
        ----------
        str: path of the folder
        """
        file_path = _getframe(1).__class__.__module__.split(".")[:-1]
        file_path = "/".join(file_path)
        if type(path_file) == list:
            for path in path_file:
                file_path = path_join(file_path, path)
        elif type(path_file) == str:
                file_path = path_join(file_path, path_file)
        if isdir(file_path) == False:
            makedirs(file_path)
        return file_path

    def download_image(self, url: str, filename: str) -> bool:
        """
        Download image from website 
        Params
        ----------
        url: Link to save file
        filename: Filename image/video
        Return
        ----------
        True: If the process is correct
        False: If the process is not correct
        """
        try:
            response = get(
                url = url,
                timeout = self.time_wait
            )
            if not response.status_code:
                #It's not necessary create a complex session
                #with retries beacause range of status code 
                #or dynamic connections, proxies, etc because
                #the security is lower
                cookies_selenium = self.browser.get_cookies()
                cookies_requests = {
                    cookie['name']: cookie['value'] \
                        for cookie in cookies_selenium
                }
                response = get(
                    url = url,
                    cookies = cookies_requests,
                    timeout = self.time_wait
                )
                if not response.status_code:
                    self._handle_exception(
                        message = F"Cannot dowloand image '{filename}'"
                    )
            with open(
                path_join(
                    self.output_img,
                    filename
                ),
                'wb'
            ) as file:
                file.write(response.content)
            return True
        except Exception as e:
            self._handle_exception(e = e)
            return False

    def _finish_browser(self) -> None:
        """
        Finish selenium webdriver
        """
        self.browser.close()
        self.browser.quit()

    def _handle_exception(self, e: Exception = None, message: str = None) -> None:
        """
        Handle exception in the all process
        Params
        ----------
        Optional
            e: Data of exception
            message: Personalized message
        Notes
        ----------
        Is it possible to only send the exception or
        only the message
        """
        if e == None: 
            self.error = message
        elif message == None: 
            self.error = "Error has occurred!!! " \
            + f"- In file '{exc_info()[2].tb_frame.f_code.co_filename}'" \
            + f"- In function '{exc_info()[2].tb_frame.f_code.co_name}' " \
            + f"- No. Line: {exc_info()[2].tb_lineno} - " \
            + f"Error Type: {type(e).__name__} - Error Message: {e}"
        else: 
            self.error = f"{message} - Error has occurred!!! " \
            + f"- In file '{exc_info()[2].tb_frame.f_code.co_filename}'" \
            + f"- In function '{exc_info()[2].tb_frame.f_code.co_name}' " \
            + f"- No. Line: {exc_info()[2].tb_lineno} - " \
            + f"Error Type: {type(e).__name__} - Error Message: {e}"
        self._save_source_code()
        self._finish_browser()
        print(self.error)

    def _normalize_text(self, text: str) -> bool|str:
        """
        Normalize text to improve search
        Params
        ----------
        text: Text to normalize
        Return
        ----------
        str: Normalize text
        False: If the process is not correct
        """
        try:
            text = text.lower()
            text = sub(r'[^\w\s]', '', text)
            text = unicodedata.normalize('NFKD', text).encode('ASCII', 'ignore').decode('utf-8')
            text = ' '.join(text.split())
            return text
        except Exception as e:
            self._handle_exception(e = e)
            return False
    
    def _search_format_amount_money(self, tuple_data: tuple[str, str]) -> bool|None:
        """
        Find amount format of money into the text
        Params
        ----------
        tuple[0]: Title news
        tuple[1]: Description of the image
        Return
        ----------
        Bool:
            True: If found amount format of money
            into the text
            False: If the process is not correct
        None: If not found amount format of money
        into the text
        """
        try:
            #$11.1 | $111,111.11 | 11 dollars | 11 USD
            patter_regex = r'\$\d+(,\d{3})*(\.\d+)?|\b\d+\s*(dollars|USD)\b'
            result = search(patter_regex, tuple_data[0])
            if result:
                return True
            result = search(patter_regex, tuple_data[1])
            if result:
                return True
            else:
                return None
        except Exception as e:
            self._handle_exception(e = e)
            return False
        
    def _count_phares(self, tuple_data: tuple[str, str, str]) -> int|bool:
        """
        Count appers of the phares into the title
        and description of the image/video
        Params
        ----------
        tuple[0]: Phrase to search intothe title and
        description
        tuple[1]: Title
        tuple[2]: Description of image/video
        Return
        ----------
        int: Number of appers into the title and
        description
        False: If the process is not correct
        """
        try:
            phares_normalized = self._normalize_text(tuple_data[0])
            title_normalized = self._normalize_text(tuple_data[1])
            description_picture_normalized = self._normalize_text(tuple_data[2])
            appearances = title_normalized.count(phares_normalized)
            appearances += description_picture_normalized.count(phares_normalized)
            return appearances
        except Exception as e:
            self._handle_exception(e = e)
            return False

    def create_excel(self) -> bool:
        """
        Create file xlsx with all the data
        collected
        Return
        ----------
        True: If the process is correct
        False: If the process is not correct
        """
        try:
            wb = Workbook()
            hoja = wb.active
            headers = ['section', 'title', 'date', 'picture filename', 'description_picture', 'count of search phrases', 'any amount of money']
            hoja.append(headers)
            for row in self.data:
                count_phares = self._count_phares(tuple_data = (self.phrase, row[1], row[4]))
                if count_phares == False and count_phares != 0:
                    return False
                amount_money = self._search_format_amount_money(tuple_data = (row[1], row[4]))
                if amount_money == False:
                    return False
                elif amount_money == None:
                    amount_money = False
                hoja.append(row + (count_phares, amount_money))
            wb.save(path_join(self.output_dir, self.phrase + ".xlsx"))
            return True
        except Exception as e:
            self._handle_exception(e = e)
            return False

    def _evaluated_datetime(self, date: str) -> bool|None:
        """
        Evaluated whether it is necessary to continue collection or
        stop depending on the current news
        Params
        ----------
        date: date/time of the current news
        Return
        ----------
        Bool
            True: If is necessary continue with the process
            False: If the process is not correct
        None: The requested date has been reached and the process
        can be stopped
        """
        try:
            #05:30 PM CST
            if 'CST' in date: 
                time_date = datetime.strptime(date, '%I:%M %p CST')
                date_time = self.datetime_now.replace(
                    hour = time_date.hour, minute = time_date.minute
                )
            #23 min ago
            elif 'min ago' in date:
                minutes_ago = int(date.split()[0])
                date_time = self.datetime_now - relativedelta(minutes = minutes_ago)
            #a few seconds ago
            elif 'seconds ago' in date:
                #Seconds are discarded because they are not
                #a meaningful date range
                date_time = self.datetime_now
            #June 19, 2024
            else:
                date_time = datetime.strptime(
                    date,
                    '%B %d, %Y'
                ).astimezone(tz = self.tz)
            if date_time > self.datetime_finished:
                return True
            else:
                #Finish collect data because month ago completed
                print("News collection will stop because the requested " \
                    + "time range has been met")
                return None
        except Exception as e:
            self._handle_exception(e = e)
            return False

    def _next_page(self) -> bool:
        """
        Request next to collect more news
        Notes
        ----------
        The pages contain 20 news each
        Return
        ----------
        True: If the process is correct
        False: If the process is not correct
        """
        try:
            self.wait.until(
                EC.element_to_be_clickable(
                    (
                        By.XPATH,
                        "//div[contains(@class, 'search-results__pagination')]/button[2]"
                    )
                ),
                f"Could not get next news page"
            ).click()
            return self._wait_icon_loading()
        except Exception as e:
            self._handle_exception(e = e)
            return False

    def _wait_icon_loading(self) -> bool:
        """
        Wait icon loading
        Return
        ----------
        True: If the process is correct
        False: If the process is not correct
        """
        try:
            self.wait.until_not(
                EC.presence_of_element_located(
                    (
                        By.XPATH,
                        "//div[contains(@class, 'spinner__spinner__')]"
                    )
                ),
                f"The loading animation did not appears in the set time '{self.time_wait}' seconds"
            )
            self.wait.until(
                EC.invisibility_of_element(
                    (
                        By.XPATH,
                        "//div[contains(@class, 'spinner__spinner__')]"
                    )
                ),
                f"The loading animation did not disappear in the set time '{self.time_wait}' seconds"
            )
            return True
        except Exception as e:
            self._handle_exception(e = e)
            return False
        
    def _set_filters(self) -> bool:
        """
        Set filters (section, date range, sort by)
        Return
        ----------
        True: If the process is correct
        False: If the process is not correct
        """
        try:
            #Section
            print(f"Set section '{self.section}'")
            if not self._wait_icon_loading():
                return False
            self.wait.until(
                EC.element_to_be_clickable(
                    (
                        By.XPATH,
                        "//button[@id='sectionfilter']"
                    )
                ),
                f"Not finded element to set 'Section'"
            ).click()
            self.wait.until(
                EC.element_to_be_clickable(
                    (
                        By.XPATH,
                        f"//div[@id='sectionfilter']//li/span[text()='{self.section}']" \
                    )
                ),
                f"Not finded Section '{self.section}'"
            ).click()
            #Date Range
            print(
                f"Set date range to collect data '{self.months_ago} month(s) ago'"
            )
            if not self._wait_icon_loading():
                return False
            self.wait.until(
                EC.element_to_be_clickable(
                    (
                        By.XPATH,
                        "//button[@id='daterangefilter']"
                    )
                ),
                f"Not finded element to set 'Date Range'"
            ).click()
            self.wait.until(
                EC.element_to_be_clickable(
                    (
                        By.XPATH,
                        "//div[@id='daterangefilter']//li/span[text()='" \
                        + f"{'Past year' if self.months_ago > 1 else 'Past month'}']"
                    )
                ),
                "Not finded element to set Date Range " \
                + f"{'Past year' if self.months_ago > 1 else 'Past month'}"
            ).click()
            #Sort by
            print(f"Set sort by 'Newest'")
            if not self._wait_icon_loading():
                return False
            self.wait.until(
                EC.element_to_be_clickable(
                    (
                        By.XPATH,
                        "//button[@id='sortby']"
                    )
                ),
                f"Not finded element to sort results"
            ).click()
            self.wait.until(
                EC.element_to_be_clickable(
                    (
                        By.XPATH,
                        "//div[@data-testid='Select-Popup']/ul/li/span[text()='Newest']/.."
                    )
                ),
                "Not finded 'Newest' to sort results"
            ).click()
            if not self._wait_icon_loading():
                return False
            return True
        except Exception as e:
            self._handle_exception(e = e)
            return False
        
    def _search_phrase(self) -> bool:
        """
        Phrase to search
        Return
        ----------
        True: If the process is correct
        False: If the process is not correct
        """
        try:
            self.wait.until(
                EC.element_to_be_clickable(
                    (
                        By.XPATH,
                        #"//button[@data-testid='Button' and not(@aria-expanded='false')]"
                        "//button[@data-testid='Button' and not(@aria-expanded='false') " \
                        + "and not(//div[@class='onetrust-pc-dark-filter ot-fade-in'])]"
                    )
                ),
                f"Not finded element to search phrase"
            ).click()
            self.wait.until(
                EC.element_to_be_clickable(
                    (
                        By.XPATH,
                        "//input[@data-testid='FormField:input']"
                    )
                ),
                f"Not finded input to search '{self.phrase}'"
            ).send_keys(self.phrase)
            self.wait.until(
                EC.element_to_be_clickable(
                    (
                        By.XPATH,
                        "//button[@data-testid='Button' and @aria-label='Search']"
                    )
                ),
                f"Not finded element to do search phrase"
            ).click()
            return True
        except Exception as e:
            self._handle_exception(e = e)
            return False
        
    def _save_fields(self, news: list) -> bool|None:
        """
        Process to extract and save data of each news
        Params
        ----------
        new: list of the nodes of the web page
        Return
        ----------
        True: If the process is correct
        False: If the process is not correct
        """
        try:
            for new in news:
                section = new.xpath(".//span[@data-testid='Label']/span")[0].text
                title = new.xpath(".//header[@class='header']//span")[0].text
                date = new.xpath(".//time")[0].text
                picture_desciption = new.xpath(".//img")[0]
                picture_filename = picture_desciption
                picture_filename = picture_filename.get("src").split(
                    "/")[-1]
                if not self.download_image(
                    url = picture_desciption.get("src"),
                    filename = picture_filename
                ):
                    return False
                picture_desciption = picture_desciption.get("alt", "")
                picture_filename = picture_filename.split(".")[0]
                next = self._evaluated_datetime(date = date)
                if next == None:
                    return None
                elif next == False:
                    return False
                tuple_data = (
                    section,
                    title,
                    date,
                    picture_filename,
                    picture_desciption
                )
                self.data.append(tuple_data)
                self.count_news += 1
                print(F"News visited: {self.count_news}")
            return True
        except Exception as e:
            self._handle_exception(e = e)
            return False
        
    def _process_data_with_lxml(self, number_results: int) -> bool:
        """
        Transfer source code of the page to process with lxml
        Params
        ----------
        number_results: Number of results for the phrase with
        the filters
        Return
        ----------
        True: If the process is correct
        False: If the process is not correct
        """
        try:
            while True:
                content = fromstring(
                    self.browser.page_source
                )
                news = content.xpath(
                    "//div[contains(@class, 'search-results__sectionContainer')]/ul/li"
                )
                result = self._save_fields(news = news)
                if result == False:
                    return False
                if number_results > self.count_news and result:
                    if not self._next_page():
                        return False
                else:
                    return self.create_excel()
        except Exception as e:
            self._handle_exception(e = e)
            return False
        
    def _get_data_news(self) -> bool:
        """
        Handle search and collect data process
        Return
        ----------
        True: If the process is correct
        False: If the process is not correct
        """
        try:
            number_results = self.browser.find_elements(
                by = By.XPATH,
                value = "//h1[@id='main-content']/..//div[contains(@class, " \
                        "'search-results__subtitle')]/span[@data-testid='Text']"
            )
            if len(number_results) == 0:
                self._handle_exception(
                    message = f"No news found for the phrase '{self.phrase}' " \
                    + f"in the section '{self.section}' " \
                    + f"and for the months '{self.months_ago}'"
                )
                return False
            number_results = int(
                search(
                    r'\b\d+\b',
                    number_results[0].text
                ).group()
            )
            print(F"Number of results: {number_results}")
            return self._process_data_with_lxml(number_results = number_results)
        except Exception as e:
            self._handle_exception(e = e)
            return False

    def start_scraping(self) -> bool:
        """
        Handle scraping process
        Return
        ----------
        True: If the process is correct
        False: If the process is not correct
        """
        try:
            print("Requesting 'https://www.reuters.com/'...")
            self.browser.get("https://www.reuters.com/")
            if not self._search_phrase():
                return False
            if not self._set_filters():
                return False
            if not self._get_data_news():
                return False
            self._finish_browser()
            return True
        except Exception as e:
            self._handle_exception(e = e)
            return False

@task
def minimal_task():
    item = workitems.inputs.current
    print("Received payload:", item.payload)
    payload = workitems.outputs.create(payload={"key": "value"})
    print(type(payload))
    result = Scraping(
        phrase = payload.get('phrase'),
        section = payload.get('section', 'Breakingviews'),
        months_ago = payload.get('months_ago')
    ).start_scraping()
    print(F"Status task: {result}")
