from inspect import currentframe, getframeinfo
from sys import exc_info, path
from os.path import join as path_join
from os.path import dirname, abspath

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from lxml.html import fromstring

from datetime import datetime
from pytz import timezone
from dateutil.relativedelta import relativedelta

from re import search

from requests import get

### If you run without robocorp ###
#path.append("..")
#from utils.utilities import _create_dir, save_source_code
#from utils.process_data import _create_excel
###                             ###

#### If you run with robocorp ###
from lib.utils.utilities import _create_dir, save_source_code
from lib.utils.process_data import _create_excel
####                          ###

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
        self._letter_lower = "abcdefghijklmnñopqrstuvwxyz"
        self._letter_upper = "ABCDEFGHIJKLMNÑOPQRSTUVWXYZ "
        frame_info = getframeinfo(currentframe().f_back)
        file_path_parent = dirname(abspath(frame_info.filename))
        self.output_dir = path_join(file_path_parent, self.output_dir)
        #Check if the directories are created, if not, create them.
        self.output_img = _create_dir(
            path_file = [self.output_dir, self.output_img]
        )
        self.output_dir = _create_dir(
            path_file = self.output_dir
        )
        #Datetime in CST
        self.tz = timezone('America/Chicago')
        self.datetime_now = datetime.now(self.tz)
        #Set the max range time in the current date
        self.datetime_now = self.datetime_now.replace(
            hour = 00, minute = 00, second = 1
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
            "intl.accept_languages",
            "es-MX,es;q=0.8,en-US;q=0.5,en;q=0.3"
        )
        self.browser = webdriver.Firefox(
            options=options
        )
        self.browser.maximize_window()
        self.wait = WebDriverWait(self.browser, self.time_wait)

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
                        message = F"Cannot downloand image '{filename}'"
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
        save_source_code(
            source_code = self.browser.page_source,
            filename = self.output_dir
        )
        self._finish_browser()
        print(self.error)

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
                #Finish collect data because months ago completed
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
                        "//*[local-name()='svg' and normalize-space(translate(" \
                        + f"@data-testid, '{self._letter_upper}', " \
                        + f"'{self._letter_lower}'))='svgchevronright']" \
                        + "/ancestor::button"

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
                        "//div[contains(translate(@class, " \
                        + f"'{self._letter_upper}', '{self._letter_lower}'" \
                        + "), 'spinner__spinner__')]"
                    )
                ),
                f"The loading animation did not appears in the set time '{self.time_wait}' seconds"
            )
            self.wait.until(
                EC.invisibility_of_element(
                    (
                        By.XPATH,
                        "//div[contains(translate(@class, " \
                        + f"'{self._letter_upper}', '{self._letter_lower}'" \
                        + "), 'spinner__spinner__')]"
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
                        "//button[normalize-space(translate(@id, "\
                        + f"'{self._letter_upper}', '{self._letter_lower}'))"\
                        + "='sectionfilter']"
                    )
                ),
                f"Not finded element to set 'Section'"
            ).click()
            self.wait.until(
                EC.element_to_be_clickable(
                    (
                        By.XPATH,
                        "//div[normalize-space(translate(@id, " \
                        + f"'{self._letter_upper}', '{self._letter_lower}'))"
                        + f"='sectionfilter']//li/span[normalize-space(" \
                        + f"translate(text(), '{self._letter_upper}', " \
                        + f"'{self._letter_lower}'))" \
                        + f"='{self.section.lower().strip().replace(' ', '')}']"
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
                        "//button[normalize-space(translate(@id, " \
                        + f"'{self._letter_upper}', '{self._letter_lower}'))" \
                        + "='daterangefilter']"
                    )
                ),
                f"Not finded element to set 'Date Range'"
            ).click()
            self.wait.until(
                EC.element_to_be_clickable(
                    (
                        By.XPATH,
                        "//div[normalize-space(translate(@id, " \
                        + f"'{self._letter_upper}', '{self._letter_lower}'))" \
                        + "='daterangefilter']//li/span[normalize-space(" \
                        + f"translate(text(), '{self._letter_upper}', "\
                        + f"'{self._letter_lower}'))" \
                        + f"='{'pastyear' if self.months_ago > 1 else 'pastmonth'}']"
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
                        "//button[normalize-space(translate(@id, " \
                        + f"'{self._letter_upper}', '{self._letter_lower}'))" \
                        + "='sortby']"
                    )
                ),
                f"Not finded element to sort results"
            ).click()
            self.wait.until(
                EC.element_to_be_clickable(
                    (
                        By.XPATH,
                        "//div[normalize-space(translate(@data-testid, " \
                        + f"'{self._letter_upper}', '{self._letter_lower}'))" \
                        + "='select-popup']//li[span[normalize-space(" \
                        + f"translate(text(), '{self._letter_upper}', " \
                        + f"'{self._letter_lower}'))='newest']]"
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
                        "//button[normalize-space(translate(@data-testid, " \
                        + f"'{self._letter_upper}', '{self._letter_lower}'))" \
                        + "='button' and not(@aria-expanded='false')]"
                    )
                ),
                f"Not finded element to search phrase"
            ).click()
            self.wait.until(
                EC.element_to_be_clickable(
                    (
                        By.XPATH,
                        "//input[normalize-space(translate(@data-testid, " \
                        + f"'{self._letter_upper}', '{self._letter_lower}'))" \
                        + "='formfield:input']"
                    )
                ),
                f"Not finded input to search '{self.phrase}'"
            ).send_keys(self.phrase)
            self.wait.until(
                EC.element_to_be_clickable(
                    (
                        By.XPATH,
                        f"//button[normalize-space(translate(@data-testid, " \
                        + f"'{self._letter_upper}', '{self._letter_lower}'))=" \
                        + "'button' and normalize-space(translate(@aria-label, " \
                        + f"'{self._letter_upper}', '{self._letter_lower}'))='search']"
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
                section = new.xpath(
                    ".//span[normalize-space(translate(@data-testid, " \
                    + f"'{self._letter_upper}', '{self._letter_lower}'))" \
                    + "='label']/span"
                )[0].text
                title = new.xpath(
                    ".//header[normalize-space(translate(@class, " \
                    + f"'{self._letter_upper}', '{self._letter_lower}'))" \
                    + "='header']//span"
                )[0].text
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
                    "//div[contains(translate(@class, " \
                    + f"'{self._letter_upper}', " \
                    + f"'{self._letter_lower}'), " \
                    + f"'search-results__sectioncontainer')]//li"
                )
                result = self._save_fields(news = news)
                if result == False:
                    return False
                if number_results > self.count_news and result:
                    if not self._next_page():
                        return False
                else:
                    return _create_excel(
                        phrase = self.phrase,
                        filename = path_join(self.output_dir, self.phrase),
                        data = self.data
                        )
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
                value = "//div[contains(translate(@class, "
                + f"'{self._letter_upper}', '{self._letter_lower}'), " \
                + "'search-results__subtitle')]//span[normalize-space(" \
                + f"translate(@data-testid, '{self._letter_upper}', " \
                + f"'{self._letter_lower}'))='text']"
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

#If you run without robocorp
#result = Scraping(
#    phrase = "Joe Biden",
#    section = "Markets",
#    months_ago = 2
#).start_scraping()
#print(F"Status task: {result}")