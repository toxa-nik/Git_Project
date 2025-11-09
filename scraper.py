import time
import re
import json
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import requests
import schedule
from bs4 import BeautifulSoup
import pytest


def get_book_data(book_url: str) -> dict:
    """
    Парсит данные о книге с указанного Url.

    Функция загружает HTML-страницу книги и извлекает информацию.

    Args:
        book_url (str): URL-адрес страницы книги для парсинга

    Returns:
        dict: Словарь с данными о книге, содержащий следующие ключи:
            - Name (str): Название книги
            - Rating (str): Рейтинг от 1 до 5
            - Description (str): Описание книги или "No description available"
            - UPC (str): Код книги
            - Product Type (str): Тип продукта
            - Price (excl. tax) (str): Цена без налога
            - Price (incl. tax) (str): Цена с налогом
            - Tax (str): Размер налога
            - Availability (str): Информация о наличии
            - Number of reviews (str): Количество отзывов

    Raises:
        requests.RequestException: В случае ошибки сетевого запроса

    Note:
        В случае ошибки при загрузке страницы возвращает пустой словарь {}
        и выводит сообщение об ошибке.
    """

    session = requests.Session()

    try:
        page = session.get(book_url)
        page.raise_for_status()
        page.encoding = "utf-8"
        soup = BeautifulSoup(page.text, "html.parser")

        product_dict = {}

        name = soup.find("div", class_="col-sm-6 product_main").find("h1").get_text()
        product_dict["Name"] = name

        stars = (
            soup.find("p", class_="star-rating")
            .get("class")[1]
            .replace("One", "1")
            .replace("Two", "2")
            .replace("Three", "3")
            .replace("Four", "4")
            .replace("Five", "5")
        )
        product_dict["Rating"] = stars

        description_element = soup.find(
            "div", id="product_description", class_="sub-header"
        )
        if description_element and description_element.find_next_sibling():
            description = (
                soup.find("div", id="product_description", class_="sub-header")
                .find_next_sibling()
                .get_text()
                .replace("\xa0", "")
            )
            product_dict["Description"] = description
        else:
            product_dict["Description"] = "No description available"

        table = soup.find("table", class_="table table-striped").find_all("tr")
        for row in table:
            product_dict[row.find("th").get_text().strip()] = (
                row.find("td").get_text().strip()
            )

        return product_dict

    except requests.RequestException as e:
        print(f"Ошибка при загрузке страницы: {e}")
        return {}

    finally:
        session.close()


def _get_url_list(catalog_url: str, page_count: int = 0) -> list:
    """
    Генерирует список URL всех книг из каталога.
    Внутренняя вспомогательная функция для извлечения ссылок на книги
    со страниц каталога.

    Args:
        catalog_url (str): URL начальной страницы каталога
        page_count (int, optional): Количество страниц для парсинга.
            При значении 0 обрабатываются все страницы. По умолчанию 0.

    Returns:
        list: Список абсолютных URL отдельных книг

    Raises:
        requests.RequestException: В случае ошибки сетевого запроса

    Note:
        Функция выводит прогресс обработки в консоль и измеряет время выполнения.
        При отрицательном page_count возвращает пустой список.
    """

    get_url_list_start_time = time.time()
    session = requests.Session()
    big_list = []

    try:
        if page_count < 0:
            print(f"Введено отрицательное число страниц: {page_count}")
            return big_list

        page_url = catalog_url
        upper_page_url = "/".join(catalog_url.split("/")[:-1])
        pages_processed = 0
        max_pages = None

        while True:
            current_page = session.get(page_url)
            current_page.raise_for_status()
            current_page.encoding = "utf-8"
            soup = BeautifulSoup(current_page.text, "html.parser")

            current_page_numb = int(
                soup.find("li", class_="current").get_text().split()[1]
            )

            if max_pages is None:
                max_pages = int(
                    soup.find("li", class_="current").get_text().split()[-1]
                )
                if page_count == 0:
                    page_count = max_pages
                else:
                    page_count = min(page_count, max_pages)

            current_page_link_list = []
            links = soup.find_all("a", title=True)
            for link in links:
                href = link.get("href")
                if href:
                    absolute_url = upper_page_url + "/" + href
                    current_page_link_list.append(absolute_url)

            big_list.extend(current_page_link_list)  ########
            pages_processed += 1
            print(f"Обработаны ссылки со страницы №{current_page_numb}")

            if pages_processed >= page_count:
                print(f"Достигнуто заданное количество страниц: {page_count}")
                break

            if current_page_numb >= max_pages:
                print("Достигнута последняя страница каталога")
                break

            page_url = re.sub(r"\d+", str(int(current_page_numb) + 1), page_url)

        get_url_list_end_time = time.time()
        get_url_list_execution_time = get_url_list_end_time - get_url_list_start_time
        print(f"Время обработки ссылок: {round(get_url_list_execution_time, 2)} сек.")

        return big_list

    finally:
        session.close()


def scrape_books(
    catalog_url: str,
    is_save: bool = False,
    return_json: bool = True,
    page_count: int = 0,
) -> list:
    """
    Парсит данные о книгах из каталога.

    Основная функция для сбора данных о книгах. Использует многопоточность
    для параллельного парсинга страниц книг. Поддерживает сохранение результатов
    в файл и различные форматы вывода.

    Args:
        catalog_url (str): URL каталога книг
        is_save (bool, optional): Сохранять ли результат в файл.
            По умолчанию False.
        return_json (bool, optional): Возвращать результат в формате JSON.
            При False возвращает список словарей. По умолчанию True.
        page_count (int, optional): Количество страниц для парсинга.
            При значении 0 обрабатываются все страницы. По умолчанию 0.

    Returns:
        list or str: Данные о книгах. При return_json=True возвращает JSON-строку,
            при return_json=False возвращает список словарей.

    Raises:
        requests.RequestException: В случае ошибки сетевого запроса
        Exception: В случае других ошибок при парсинге

    Note:
        Функция выводит прогресс выполнения и время работы в консоль.
        При is_save=True создает файл 'books_data.txt' в папке artifacts.
    """

    scrape_books_start_time = time.time()

    url_list = _get_url_list(catalog_url, page_count)
    print(f"Всего найдено URL книг для парсинга: {len(url_list)}")
    print("Начинаю парсинг")

    with ThreadPoolExecutor(max_workers=10) as executor:
        results = executor.map(get_book_data, url_list)
        big_data = [book_data for book_data in results if book_data]

    if return_json:
        big_data_json = json.dumps(big_data, ensure_ascii=False, indent=2)

    if is_save:
        script_dir = Path.cwd()
        artifacts_dir = (
            script_dir.parent / "artifacts"
        )  # Изменить для скрипта на /"artifacts" и проверить обязательно!!!
        file_path = artifacts_dir / "books_data.txt"
        with open(file_path, "w", encoding="utf-8") as f:
            if return_json:
                f.write(big_data_json)
            else:
                for line in big_data:
                    f.write(str(line) + "\n\n")

    scrape_books_end_time = time.time()
    scrape_books_execution_time = scrape_books_end_time - scrape_books_start_time
    print(f"Время парсинга книг: {round(scrape_books_execution_time, 2)} сек.")
    print(f"Обработано книг: {len(big_data)}")
    print(
        f"Средняя скорость: {len(big_data) / scrape_books_execution_time:.2f} книг/сек"
    )

    if return_json:
        return big_data_json
    else:
        return big_data
