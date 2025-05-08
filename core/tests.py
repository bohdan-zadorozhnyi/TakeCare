from django.test import TestCase


class DummyTest(TestCase):
    """Simple test case that will always pass"""

    def test_dummy_test_passes(self):
        """Test that True is indeed True"""
        self.assertTrue(True)
        
    def test_dummy_math(self):
        """Test that basic math works"""
        self.assertEqual(1 + 1, 2)
        
    def test_dummy_string(self):
        """Test that string concatenation works"""
        self.assertEqual("Take" + "Care", "TakeCare")
