import unicodedata
from openpyxl import Workbook
from re import sub, search
from sys import exc_info

def _handle_exception(e: Exception = None, message: str = None) -> None:
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
        error = message
    elif message == None: 
        error = "Error has occurred!!! " \
        + f"- In file '{exc_info()[2].tb_frame.f_code.co_filename}'" \
        + f"- In function '{exc_info()[2].tb_frame.f_code.co_name}' " \
        + f"- No. Line: {exc_info()[2].tb_lineno} - " \
        + f"Error Type: {type(e).__name__} - Error Message: {e}"
    else: 
        error = f"{message} - Error has occurred!!! " \
        + f"- In file '{exc_info()[2].tb_frame.f_code.co_filename}'" \
        + f"- In function '{exc_info()[2].tb_frame.f_code.co_name}' " \
        + f"- No. Line: {exc_info()[2].tb_lineno} - " \
        + f"Error Type: {type(e).__name__} - Error Message: {e}"
    print(error)

def _normalize_text(text: str) -> bool|str:
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
        _handle_exception(e = e)
        return False

def _search_format_amount_money(tuple_data: tuple[str, str]) -> bool|None:
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
        _handle_exception(e = e)
        return False
        
def _count_phares(tuple_data: tuple[str, str, str]) -> int|bool:
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
        phares_normalized = _normalize_text(tuple_data[0])
        title_normalized = _normalize_text(tuple_data[1])
        description_picture_normalized = _normalize_text(tuple_data[2])
        appearances = title_normalized.count(phares_normalized)
        appearances += description_picture_normalized.count(phares_normalized)
        return appearances
    except Exception as e:
        _handle_exception(e = e)
        return False

def _create_excel(phrase: str, filename: str, data: list) -> bool:
    """
    Create file xlsx with all the data
    collected
    Params
    ----------
    phrase: Phrase searched into web page
    filename: Filename of file to save
    data: data extracted from web page
    Return
    ----------
    True: If the process is correct
    False: If the process is not correct
    """
    try:
        wb = Workbook()
        sheet = wb.active
        headers = ['section', 'title', 'date', 'picture filename', 'description_picture',
                   'count of search phrases', 'any amount of money']
        sheet.append(headers)
        for row in data:
            count_phares = _count_phares(tuple_data = (phrase, row[1], row[4]))
            if count_phares == False and count_phares != 0:
                return False
            amount_money = _search_format_amount_money(tuple_data = (row[1], row[4]))
            if amount_money == False:
                return False
            elif amount_money == None:
                amount_money = False
            sheet.append(row + (count_phares, amount_money))
        wb.save(f"{filename}.xlsx")
        return True
    except Exception as e:
        _handle_exception(e = e)
        return False