import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium_stealth import stealth
from bs4 import BeautifulSoup
from selenium.common.exceptions import ElementNotInteractableException
import time
import os
import logging
from datetime import datetime
from configparser import ConfigParser
from sys import stdout
from pyvirtualdisplay import Display
from ftplib import FTP
from requests import post
import traceback

url = 'https://www.bundesanzeiger.de/pub/en/nlp_history?0'
cookie_file = 'cookie1'
from_input = '0,00'
push_access_token = 'pushtoken'
virtual_display = True
debug_mode = False
ftp_add = 'ftp_add'
ftp_user = 'ftp_user'
ftp_pass = 'ftp_pass'
version_number = '112'
down_wait = 10
ftp_directory = ''


def check_create_dir(dirname):
    '''
    Checks if directory exists and if it doesn't creates a new directory
    :param dirname: Path to directory
    '''
    if not os.path.exists(dirname):
        if '/' in dirname:
            os.makedirs(dirname)
        else:
            os.mkdir(dirname)


def xpath_soup(element):
    """
       Generate xpath from BeautifulSoup4 element.
       :param element: BeautifulSoup4 element.
       :type element: bs4.element.Tag or bs4.element.NavigableString
       :return: xpath as string
       """
    components = []
    child = element if element.name else element.parent
    for parent in child.parents:
        siblings = parent.find_all(child.name, recursive=False)
        components.append(
            child.name if 1 == len(siblings) else '%s[%d]' % (
                child.name,
                next(i for i, s in enumerate(siblings, 1) if s is child)
            )
        )
        child = parent
    components.reverse()
    return '/%s' % '/'.join(components)


def navigator(headless=False):
    logger = logging.getLogger('Navigator')
    logger.info('Initiating driver')
    options = uc.ChromeOptions()
    preferences = {"download.default_directory": os.getcwd() + '/' + download_dir,
                   "download.prompt_for_download": False,
                   "directory_upgrade": True,
                   "safebrowsing.enabled": True}
    options.add_experimental_option('prefs', preferences)
    options.add_argument('--no-first-run --no-service-autorun --password-store=basic')
    options.add_argument('--window-size={}'.format('1920,1080'))
    options.add_argument('--disk-cache-size=1073741824')
    options.add_argument('--no-sandbox')
    options.add_argument("--disable-setuid-sandbox")
    options.add_argument("--disable-extensions")
    options.add_argument('--disable-application-cache')
    options.add_argument('--disable-gpu')
    options.add_argument('--dns-prefetch-disable')
    options.add_argument('--hide-scrollbars')
    options.add_argument("--disable-infobars")
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-browser-side-navigation')
    # options.add_argument('--log-level=0')
    # options.add_argument('--ignore-certificate-errors')
    # options.add_argument("--disable-plugins-discovery")
    # options.add_argument("--start-maximized")
    driver = uc.Chrome(headless=headless, options=options, version_main=version_number, user_data_dir=cookie_file)
    logger.debug('Setting up stealth')
    stealth(driver,
            languages=["en-US", "en"],
            vendor="Google Inc.",
            platform="Win32",
            webgl_vendor="Intel Inc.",
            renderer="Intel Iris OpenGL Engine",
            fix_hairline=True,
            )
    driver.get(url)
    main_soup = BeautifulSoup(driver.page_source, features='html.parser')
    time.sleep(1)
    cookie_dialog = main_soup.find('div', {'class': 'cc_commands'}).find_all('button')[1]
    try:
        logger.info('Cookie dialog found. Clicking accept all')
        driver.find_element(By.XPATH, xpath_soup(cookie_dialog)).click()
        time.sleep(1)
    except ElementNotInteractableException:
        logger.error('Dialog not clickable. Omitting')
    logger.info('Clicking extended search')
    main_soup = BeautifulSoup(driver.page_source, 'html.parser')
    search_options_button = main_soup.find_all('div', {'class': 'search-row'})[1].find('button')
    driver.find_element(By.XPATH, xpath_soup(search_options_button)).click()
    time.sleep(3)
    main_soup = BeautifulSoup(driver.page_source, 'html.parser')
    logger.info('Entering from')
    from_box = main_soup.find_all('div', {'class': 'search-row'})[1].find_all('input')[3]
    driver.find_element(By.XPATH, xpath_soup(from_box)).send_keys(from_input)
    logger.info('Clicking checkbox')
    historicicsed_checkbox = main_soup.find_all('div', {'class': 'search-row'})[1] \
        .find('div', {'class': 'custom-control custom-checkbox'}).find('label')
    driver.find_element(By.XPATH, xpath_soup(historicicsed_checkbox)).click()
    logger.info('Clicking submit')
    submit_button = main_soup.find_all('div', {'class': 'row'})[6].find('input')
    driver.find_element(By.XPATH, xpath_soup(submit_button)).click()
    time.sleep(2)
    logger.info('Clicking download button')
    main_soup = BeautifulSoup(driver.page_source, 'html.parser')
    download_button = main_soup.find('a', {'class': 'btn btn-green argus-A98'})
    driver.find_element(By.XPATH, xpath_soup(download_button)).click()
    time.sleep(5)
    logger.debug('Deleting cookies')
    driver.delete_all_cookies()
    logger.info('Closing driver')
    driver.close()
    driver.quit()


def send_ftp(server_add, username, password, filepath):
    logger = logging.getLogger('SendFileCore')
    if 'http' in server_add:
        logger.debug('Http substring found in address. Correcting')
        server_add = server_add.replace('http://', '').replace('https://', '').strip()
        if server_add[-1] == '/':
            server_add = server_add[:-1]
    logger.info(f'Starting FTP connection to {server_add}')
    with FTP(server_add, username, password) as ftp:
        ftp.encoding = 'utf-8'
        if ftp_directory != '':
            try:
                if ftp_directory not in ftp.nlst():
                    logger.debug('Creating directory')
                    ftp.mkd(ftp_directory)
            except Exception as exc:
                logger.debug('Could not create directory')
                logger.debug(f'Details: {str(exc)}')
        upload_dir = ftp_directory + '/' + filepath.split('/')[-1]
        with open(filepath, 'rb') as f:
            logger.info('Uploading file')
            ftp.storbinary('STOR ' + upload_dir, f)


def send_pushbullet(push_message):
    logger = logging.getLogger('PushbulletCore')
    logger.info('Sending notification to Pushbullet')
    push_url = 'https://api.pushbullet.com/v2/pushes'
    headers = {
        'Access-Token': push_access_token,
        'Content-Type': 'application/json'
    }
    j_data = {
        'body': push_message,
        'title': 'Bundesanzeiger Scraper Notification',
        'type': 'note'
    }
    response = post(push_url, json=j_data, headers=headers)
    if response.status_code != 200 or response.json().get('cat', None):
        logger.error('Could not send push notification')
        logger.error(f'Api response: {response.json()}')


# init logging
rootLogger = logging.getLogger()
consoleHandler = logging.StreamHandler(stdout)
check_create_dir('logs')
log_timestamp = datetime.now()
fileHandler = logging.FileHandler(
    os.path.join('logs', 'HistoricScraper{0}.log'.format(log_timestamp.strftime('%m-%d-%y-%H-%M-%S'))), 'w',
    'utf-8')
fileHandler.setFormatter(logging.Formatter('%(asctime)s:-[%(name)s] - %(levelname)s - %(message)s'))
rootLogger.addHandler(consoleHandler)
rootLogger.addHandler(fileHandler)
rootLogger.setLevel(logging.DEBUG)
logging.getLogger('seleniumwire.handler').setLevel(logging.ERROR)
logging.getLogger('selenium.webdriver.remote.remote_connection').setLevel(logging.ERROR)
logging.getLogger('seleniumwire.server').setLevel(logging.ERROR)
logging.getLogger('hpack.hpack').setLevel(logging.ERROR)
logging.getLogger('hpack.table').setLevel(logging.ERROR)
logging.getLogger('seleniumwire.storage').setLevel(logging.ERROR)
if debug_mode:
    consoleHandler.setLevel(logging.DEBUG)
else:
    consoleHandler.setLevel(logging.INFO)
fileHandler.setLevel(logging.DEBUG)
consoleHandler.setFormatter(logging.Formatter('[%(name)s] - %(levelname)s - %(message)s'))

rootLogger.info('Historic Scraper')
rootLogger.info('Getting conf')
try:
    config = ConfigParser()
    config.read('masterconfig.ini')
    version_number = config.get('browser', 'version')
    virtual_display = config.getboolean('browser', 'virtual_display')
    ftp_add = config.get('ftp', 'address')
    ftp_user = config.get('ftp', 'username')
    ftp_pass = config.get('ftp', 'password')
    ftp_directory = config.get('ftp', 'directory_name')
    push_access_token = config.get('pushbullet', 'push_access_token')
    debug_mode = config.getboolean('misc', 'debug_mode')
    down_wait = int(config['misc']['wait_for_download'])
    headless = config.getboolean('browser', 'headless')
except Exception as exc:
    rootLogger.error('Cannot read conf')
    rootLogger.error(f'Details: {str(exc)}')
    rootLogger.info('Closing process')
    exit(999)

# Reporting config values
rootLogger.debug(f'version_number: {version_number}')
rootLogger.debug(f'virtual_display: {virtual_display}')
rootLogger.debug(f'ftp_add: {ftp_add}')
rootLogger.debug(f'ftp_user: {ftp_user}')
rootLogger.debug(f'ftp_pass: {ftp_pass}')
rootLogger.debug(f'push_acess_token: {push_access_token}')
rootLogger.debug(f'Download wait: {down_wait}')
rootLogger.debug(f'debug_mode: {debug_mode}')

file_timestamp = log_timestamp.strftime('%d-%m-%y-%H-%M-%S')
download_dir = f'dump/{file_timestamp}'
check_create_dir('dump')
check_create_dir(download_dir)
scrape_success = True
now = datetime.now()
error_log = ''
if virtual_display:
    rootLogger.info('Starting virtual display')
    try:
        with Display(visible=False, size=(1920, 1080)) as disp:
            try:
                navigator(headless)
            except Exception as exc:
                rootLogger.error('Cannot navigate website')
                rootLogger.error(f'Details: {str(exc)}')
                rootLogger.debug(f'Traceback: {traceback.format_exc()}')
                scrape_success = False
                error_log = f'Cannot navigate website: {str(exc)}'
            rootLogger.info('Stopping virtual display')
    except Exception as exc:
        rootLogger.error('Error with virtual display')
        rootLogger.error(f'Details: {str(exc)}')
else:
    try:
        navigator(headless)
    except Exception as exc:
        rootLogger.error('Cannot navigate website')
        rootLogger.error(f'Details: {str(exc)}')
        rootLogger.debug(f'Traceback: {traceback.format_exc()}')
        scrape_success = False
        error_log = f'Cannot navigate website: {str(exc)}'
later = datetime.now()
if scrape_success:
    time.sleep(down_wait)
    download_file = os.getcwd() + '/' + download_dir + f'/{os.listdir(download_dir)[0]}'
    for f_add_ele, f_user_ele, f_pass_ele in zip(ftp_add.split(','), ftp_user.split(','), ftp_pass.split(',')):
        try:
            send_ftp(f_add_ele, f_user_ele, f_pass_ele, download_file)
        except Exception as exc:
            rootLogger.error('Could not send file over FTP')
            rootLogger.error(f'Details: {str(exc)}')
            send_pushbullet(f'Could not send file over FTP for address {f_add_ele}: {str(exc)}')
    total_time = (later - now).seconds
    send_pushbullet(f'Scraping process successfully completed. Total time taken: {total_time} second(s)')
else:
    send_pushbullet(error_log)
rootLogger.info('Goodbye')
