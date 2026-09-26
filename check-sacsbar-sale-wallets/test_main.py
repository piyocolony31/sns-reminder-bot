import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from main import is_long_wallet, extract_product_id, format_notification_message

class TestSacsBarWalletChecker(unittest.TestCase):

    def test_is_long_wallet(self):
        self.assertTrue(is_long_wallet("kissora キソラ | 長財布 | 50%OFF"))
        self.assertTrue(is_long_wallet("FOWLER | Round zipper long wallet | 50% OFF"))
        self.assertTrue(is_long_wallet("ブランド名 | ラウンドファスナー長財布"))
        self.assertFalse(is_long_wallet("WHITEAGE | Messenger bag M"))
        self.assertFalse(is_long_wallet("GREGORY | Sacoche"))

    def test_extract_product_id(self):
        url = "https://sacsbar.com/c/sale/sale_mens_uni_sex/kipm-020"
        self.assertEqual(extract_product_id(url), "kipm-020")
        
        url_with_query = "https://sacsbar.com/c/sale/sale_mens_uni_sex/aqw-12170122?sort=latest"
        self.assertEqual(extract_product_id(url_with_query), "aqw-12170122")

    def test_format_notification_message(self):
        new_items = [
            {
                "id": "item1",
                "title": "テストブランド | 長財布 | 50% OFF",
                "link": "https://sacsbar.com/c/sale/sale_mens_uni_sex/item1"
            }
        ]
        msg = format_notification_message(new_items)
        self.assertIn("新着の長財布が追加されました！", msg)
        self.assertIn("テストブランド | 長財布", msg)
        self.assertIn("https://sacsbar.com/c/sale/sale_mens_uni_sex/item1", msg)

if __name__ == "__main__":
    unittest.main()
