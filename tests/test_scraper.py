import sys
import os
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from scraper import get_book_data, scrape_books


class TestGetBookData:
    """Тесты для функции get_book_data"""

    def test_returns_dict_with_required_keys(self):
        """Проверяем, что функция возвращает словарь с нужными ключами"""
        test_url = (
            "http://books.toscrape.com/catalogue/a-light-in-the-attic_1000/index.html"
        )
        result = get_book_data(test_url)

        assert isinstance(result, dict), "Функция должна возвращать словарь"

        required_keys = [
            "Name",
            "Rating",
            "Description",
            "UPC",
            "Product Type",
            "Price (excl. tax)",
            "Price (incl. tax)",
            "Tax",
            "Availability",
            "Number of reviews",
        ]
        for key in required_keys:
            assert key in result, f"В словаре должен быть ключ '{key}'"

    def test_book_title_not_empty(self):
        """Проверяем, что название книги не пустое"""
        test_url = (
            "http://books.toscrape.com/catalogue/a-light-in-the-attic_1000/index.html"
        )
        result = get_book_data(test_url)

        assert "Name" in result, "Должен быть ключ 'Name'"
        assert result["Name"] != "", "Название книги не должно быть пустым"

    def test_rating_is_valid(self):
        """Проверяем, что рейтинг находится в допустимом диапазоне (должен быть числом от 1 до 5)"""
        test_url = (
            "http://books.toscrape.com/catalogue/a-light-in-the-attic_1000/index.html"
        )
        result = get_book_data(test_url)

        assert "Rating" in result, "Должен быть ключ 'Rating'"

        rating = result["Rating"]

        assert rating in ["1", "2", "3", "4", "5"], (
            f"Рейтинг {rating} должен быть от 1 до 5"
        )


class TestScrapeBooks:
    """Тесты для функции scrape_books"""

    def test_returns_list_of_books(self):
        """Проверяем, что функция возвращает список книг, тестируем на одной странице для скорости"""
        #
        catalog_url = "http://books.toscrape.com/catalogue/page-1.html"
        result = scrape_books(catalog_url, page_count=1, return_json=False)
        assert isinstance(result, list), "Функция должна возвращать список"
        assert len(result) > 0, "Список книг не должен быть пустым"

    def test_books_have_required_fields(self):
        """Проверяем, что у всех книг есть обязательные поля на одной книге"""
        catalog_url = "http://books.toscrape.com/catalogue/page-1.html"
        books = scrape_books(catalog_url, page_count=1, return_json=False)

        if len(books) > 0:
            first_book = books[0]
            required_keys = [
                "Name",
                "Rating",
                "Description",
                "UPC",
                "Product Type",
                "Price (excl. tax)",
                "Price (incl. tax)",
                "Tax",
                "Availability",
                "Number of reviews",
            ]

            for key in required_keys:
                assert key in first_book, f"У книги должен быть ключ '{key}'"
                assert first_book[key] != "", f"Поле '{key}' не должно быть пустым"

    def test_json_output_format(self):
        """Проверяем работу с JSON форматом, должна возвращается строка"""

        catalog_url = "http://books.toscrape.com/catalogue/page-1.html"
        result = scrape_books(catalog_url, page_count=1, return_json=True)
        assert isinstance(result, str), "При return_json=True должен возвращаться str"


def test_bad_page_count_handling():
    """Проверяем обработку неверного page_count"""
    catalog_url = "http://books.toscrape.com/catalogue/page-1.html"
    result = scrape_books(catalog_url, page_count=-1, return_json=False)
    assert result == [], "Должен возвращаться пустой список"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
