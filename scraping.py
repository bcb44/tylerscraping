from bs4.element import ResultSet, Tag
from selenium import webdriver
from selenium.webdriver import Chrome, ChromeOptions
from selenium.webdriver.common.by import By 
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.support.ui import WebDriverWait
from bs4 import BeautifulSoup as bs
import time
import lxml
from typing import List, Set, Dict, Tuple, Optional
from selenium.webdriver.remote.webelement import WebElement
from provider import Provider
import json
import os.path as path

def findResults(content:str) -> List[Provider]:
    soup = soup = bs(content, features='lxml')
    docs:List[Provider] = []
    search_params = {'class', 'CustomProfessional-card custom-professional'}
    results:ResultSet[Tag] = soup.find_all('div', attrs=search_params)
    for result in results:
        if type(result) is not Tag: continue
        info = Provider(result)
        info.name, info.degree, info.site = findNameDegSite(result)
        info.loc = findLoc(result)
        info.addr = findLoc(result)
        docs.append(info)
    return docs

def findNameDegSite(section:Tag) -> Tuple[str | None, str | None, str | None]:
    attr = {"class", "CustomProfessional-titleLink"}
    result = getElements(section, 'a', attr)[0]
    if type(result) is not Tag:
        return (None, None, None)
    split = result.text.split(',')
    name = split[0].strip()
    deg = result.text.replace(f'{name}, ', '').strip()
    site = result.attrs.get('href', None).strip()
    return (name, deg, site)

def findLoc(section:Tag) -> str | None:
    attr = {'class', 'CustomProfessional-locationName'}
    result = getElements(section, 'div', attr)[0]
    if type(result) is not Tag:
        return None
    return result.text.strip()

def findAddr(section:Tag) -> str | None:
    attr = {'class', 'CustomProfessional-address'}
    results:List[Tag] = getElements(section, 'div', attr, 2)
    if type(results) is not List[Tag]:
        return None
    local = results[0].text.strip()
    city = results[1].text.strip()
    return f'{local}, {city}'


def getElements(section:Tag, name:str, attr:Dict[str, str], maxsize:int = 1) -> List[Tag]:
    results:ResultSet[Tag] = section.find_all(name, attrs=attr)
    index = 0
    new:List[Tag] = []
    while index < len(results):
        if type(results[index]) is Tag: 
            new.append(results[index])
            index += 1
    if index > maxsize:
        results = results[:maxsize + 1]
    return results

def nextPage(driver:Chrome) -> None:
    #driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    #time.sleep(2)
    locator = (By.CLASS_NAME, 'js-yxt-Pagination-next')
    element:WebElement = driver.find_element(*locator)
    element.click()
    time.sleep(2)
    
def firstPage() -> Chrome:
    subpage = "https://answers-embed.unchealthcare.org.pagescdn.com/?=&amp;referrerPageUrl=&query=&referrerPageUrl=&facetFilters=%7B%7D&filters=%7B%7D"
    driver = Chrome()
    driver.get(subpage)
    time.sleep(10)
    return driver

def outlook(email:str) -> Chrome:
    page = 'https://outlook.office.com/mail/'
    options_path = path.join(path.dirname(__file__), 'chromeprofile/')
    options = ChromeOptions()
    options.add_argument(f'user-data-dir={options_path}')
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    driver = Chrome(options=options)
    driver.get(page)
    #confirmIdentity(driver, email)
    return driver

def confirmIdentity(driver:Chrome, email:str):
    time.sleep(2)
    if driver.current_url == 'https://outlook.office.com/mail/':
        return
    locator = (By.XPATH, f"//div[@data-test-id='{email}']")
    WebDriverWait(driver, 5).until(ec.presence_of_element_located(locator))
    with open("login.html", "w") as file:
        file.write(driver.page_source)
    locator = (By.XPATH, f"//div[@data-test-id='{email}']")
    profile:WebElement = driver.find_element(*locator)
    profile.click()

def newEmail(driver:Chrome):
    locator = (By.XPATH, f'//button/span/span/span[contains(text(),"New message")]')
    WebDriverWait(driver, 20).until(ec.presence_of_element_located(locator))
    button:WebElement = driver.find_element(*locator)
    button.click()

def findEmail(driver:Chrome, doc:Provider) -> str:
    locator = (By.XPATH, f'//input[@aria-label="To"]')
    WebDriverWait(driver, 20).until(ec.presence_of_element_located(locator))
    textInput:WebElement = driver.find_element(*locator)
    textInput.clear()
    textInput.send_keys(doc.name)
    with open("outlook.html", "w") as file:
        file.write(email_driver.page_source)
    locator = (By.XPATH, f'//span[contains(.,"{doc.name}")]')
    try:
        WebDriverWait(driver, 5).until(ec.presence_of_element_located(locator))
    except:
        return 'notfound'
    form:WebElement = driver.find_element(*locator)
    for child in form.parent.find_elements(By.XPATH, "./child::*"):
        if doc.name in child.text: continue
        doc.email = child.text
        break
    if doc.email == '':
        print('error')

email_driver = outlook('tylero@ad.unc.edu')
newEmail(email_driver)

unc_driver = firstPage()
with open('output.csv', 'w') as file:
    for page in range(352):
        docs:List[Provider] = findResults(unc_driver.page_source)
        for doc in docs:
            doc.email = findEmail(email_driver, doc)
            print(f'{doc}')
            file.write(f'{doc}\n')
            file.flush()
        nextPage(unc_driver)