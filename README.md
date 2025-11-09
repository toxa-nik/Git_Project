# Books Scraper

## Цель проекта

Учебный проект по парсингу данных с веб-сайтов. 
Программа собирает информацию о книгах с сайта Books to Scrape, включая названия, рейтинги, описания, цены и другие характеристики.

## Список используемых библиотек
- requests
- beautifulsoup4
- schedule
- pytest


## Инструкции по запуску

### Установка зависимостей
```bash
pip install -r requirements.txt
```

### Использование

```python
from scraper import scrape_books

# Парсинг всех книг с первой страницы
data = scrape_books(
    catalog_url="http://books.toscrape.com/catalogue/page-1.html",
    page_count=1,
    return_json=True
)

# Сохранение в файл
data = scrape_books(
    catalog_url="http://books.toscrape.com/catalogue/page-1.html",
    is_save=True,
    page_count=2
)
```

### Тестирование
```bash
# Запуск всех тестов
pytest tests/ -v
```


### Пример вывода JSON
```JSON
[
  {
    "Name": "A Light in the Attic",
    "Rating": "3",
    "Description": "It's hard to imagine a world without A Light in the Attic. ...more",
    "UPC": "a897fe39b1053632",
    "Product Type": "Books",
    "Price (excl. tax)": "£51.77",
    "Price (incl. tax)": "£51.77",
    "Tax": "£0.00",
    "Availability": "In stock (22 available)",
    "Number of reviews": "0"
  }
]
```

Проект создан в учебных целях.
