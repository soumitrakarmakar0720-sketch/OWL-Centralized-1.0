import os,unittest
from unittest.mock import patch
from app import app
class PortalTests(unittest.TestCase):
 def setUp(self):self.client=app.test_client()
 def test_health(self):self.assertEqual(self.client.get('/health').status_code,200)
 def test_home(self):self.assertIn(b'OWL FINANCE',self.client.get('/').data)
 def test_store(self):self.assertEqual(self.client.get('/open/store').location,'https://owldigital.shop')
 def test_finance(self):
  with patch.dict(os.environ,{'OWL_FINANCE_URL':'https://finance.test'}):
   self.assertEqual(self.client.get('/open/finance').location,'https://finance.test')
 def test_unknown(self):self.assertEqual(self.client.get('/open/unknown').status_code,404)
 def test_no_open_redirect(self):
  with patch.dict(os.environ,{'OWL_STORE_URL':'https://evil.test@store.test'}):
   self.assertEqual(self.client.get('/open/store').status_code,500)
if __name__=='__main__':unittest.main()
