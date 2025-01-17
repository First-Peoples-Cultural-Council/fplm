from django.test import TestCase
from rest_framework.test import APITestCase
from rest_framework import status

from users.models import User, Administrator
from django.contrib.gis.geos import GEOSGeometry

import json

from language.models import (
    Language, 
)


class BaseTestCase(APITestCase):
    def setUp(self):
        self.user = User.objects.create(
            username="testuser001",
            first_name="Test",
            last_name="user 001",
            email="test@countable.ca",
            is_staff=True,
            is_superuser=True,
        )
        self.user.set_password("password")
        self.user.save()

        self.FAKE_GEOM = """
            {
                "type": "Polygon",
                "coordinates": [
                    [
                        [
                        -126.69158935546875,
                        54.629338216555766
                        ],
                        [
                        -126.91406249999999,
                        54.746820492190885
                        ],
                        [
                        -126.95526123046875,
                        54.57683778006274
                        ],
                        [
                        -126.69158935546875,
                        54.629338216555766
                        ]
                    ]
                ]
            }"""


class LanguageAPITests(BaseTestCase):

    ###### ONE TEST TESTS ONLY ONE SCENARIO ######

    def test_language_detail_route_exists(self):
        """
		Ensure language Detail API route exists
		"""
        response = self.client.get("/api/language/0/", format="json")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_language_detail(self):
        """
		Ensure we can retrieve a newly created language object.
		"""
        poly = GEOSGeometry(self.FAKE_GEOM)
        
        test_language = Language(name="Test language 001")
        test_language.geom = poly
        test_language.save()

        response = self.client.get(
            "/api/language/{}/".format(test_language.id), format="json"
        )

        # import pdb
        # pdb.set_trace()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["id"], test_language.id)
        self.assertEqual(response.data["name"], "Test language 001")

    def test_language_list_route_exists(self):
        """
		Ensure language list API route exists
		"""
        response = self.client.get("/api/language/", format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_language_list(self):
        """
		Ensure we can retrieve newly created language objects.
		"""
        poly = GEOSGeometry(self.FAKE_GEOM)
        
        test_language = Language(name="Test language 001")
        test_language.geom = poly
        test_language.save()

        response = self.client.get("/api/language/", format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)


class LanguageGeoAPITests(APITestCase):

    ###### ONE TEST TESTS ONLY ONE SCENARIO ######

    def test_language_geo_list_route_exists(self):
        """
		Ensure language list API route exists
		"""
        response = self.client.get("/api/language-geo/", format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    # Only the LIST operations exists in this API.
