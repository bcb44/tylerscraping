from bs4.element import ResultSet, Tag
from selenium import webdriver
from selenium.webdriver import Chrome, ChromeOptions
from selenium.webdriver.common.by import By
from selenium.webdriver.remote import webelement 
from selenium.webdriver.support import expected_conditions as ec, wait
from selenium.webdriver.support.ui import WebDriverWait
from bs4 import BeautifulSoup as bs
import time
import lxml
from typing import List, Set, Dict, Tuple, Optional
from selenium.webdriver.remote.webelement import WebElement
from provider import Provider
import json
import os.path as path
import csv

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

def newEmail(driver:Chrome) -> WebElement:
    locator = (By.XPATH, f'//button/span/span/span[contains(text(),"New message")]')
    WebDriverWait(driver, 20).until(ec.presence_of_element_located(locator))
    button:WebElement = driver.find_element(*locator)
    button.click()
    locator = (By.XPATH, f'//input[@aria-label="To"]')
    WebDriverWait(driver, 20).until(ec.presence_of_element_located(locator))
    textInput:WebElement = driver.find_element(*locator)
    return textInput
    

def findEmail(doc:Provider):
    textInput.clear()
    name = adjustName(doc.name)
    textInput.send_keys(name)
    textInput.click()
    locator = (By.XPATH, f'//span[contains(text(),"@unchealth.unc.edu") or contains(text(), "@med.unc.edu")]')
    try:
        time.sleep(2)
        WebDriverWait(email_driver, 1).until(ec.presence_of_element_located(locator))
        elements:List[WebElement] = email_driver.find_elements(*locator)
        parseElements(doc, elements)
    except:
        print(f'{name}: notfound')
        doc.email = 'notfound'
    
def parseElements(doc:Provider, elements:List[WebElement]):
    emails = []
    lower:str = doc.name.split(" ")[-1].split('-')[0].lower()
    for element in elements:
        text = element.text
        if lower not in text and lower.capitalize() not in text: 
            print(f'{doc.name}: {text}')
            continue
        emails.append(text)
        if len(emails) == 0:
            doc.email = 'notmatching'
        elif len(emails) == 1:
            doc.email = emails[0]
        else:
            doc.email = f"\"{','.join(emails)}\""
    print(f'{doc.name}: {doc.email}')


def adjustName(name:str) -> str:
    names = name.split(' ')
    i = 0
    while (i < len(names)):
        c = names[i]
        update = c.replace('.', '')
        if len(update) <= 1:
            names.pop(i)
        else:
            i+=1
    if len(names) == 1: 
        return name
    return f'{names[0]} {names[-1]}'
        

email_driver = outlook('tylero@ad.unc.edu')
textInput = newEmail(email_driver)

with open('output.csv', 'w') as output:
    with open('records.csv', 'r') as records:
        reader = csv.reader(records)
        i = 1
        for info in reader:
            if i % 100 == 0:
                print(f"Current Step: {i}")
            doc = Provider()
            doc.name = info[0]
            doc.degree = info[1]
            doc.loc = info[2]
            doc.site = info[5]
            findEmail(doc)
            output.write(f'{doc}\n')
            output.flush()
            i+=1
