import json

from django.test import TestCase
try:
    from django.urls import reverse
except ImportError:
    from django.core.urlresolvers import reverse
from django.core.exceptions import ImproperlyConfigured

from rest_framework_gis import serializers as gis_serializers

from .models import BoxedLocation, Location
from .serializers import LocationGeoSerializer


class TestRestFrameworkGisBBox(TestCase):
    """
    unit tests for bbox support in restframework_gis
    """
    def setUp(self):
        self.geojson_boxedlocation_list_url = reverse('api_geojson_boxedlocation_list')
        self.geojson_location_bbox_list_url = reverse('api_geojson_location_bbox_list')

    def _create_locations(self):
        self.bl1 = BoxedLocation.objects.create(id=1, name='l1', slug='l1', geometry='POINT (13.007 42.423)',
                bbox_geometry='POLYGON((12.997 42.413,12.997 42.433,13.017 42.433,13.017 42.413,12.997 42.413))')
        self.bl2 = BoxedLocation.objects.create(id=2, name='l2', slug='l2', geometry='POINT (12.007 43.423)',
                bbox_geometry='POLYGON((11.997 43.413,11.997 43.433,12.017 43.433,12.017 43.413,11.997 43.413))')
        self.l1 = Location.objects.create(id=1, name='l1', slug='l1',
                geometry='POLYGON((12.997 42.413,12.997 42.433,13.017 42.433,13.017 42.413,12.997 42.413))')

    def test_list(self):
        self._create_locations()
        response = self.client.get(self.geojson_boxedlocation_list_url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['features']), 2)
        for feature in response.data['features']:
            self.assertIn('bbox', feature)
            fid = feature['id']
            if fid==1:
                self.assertEqual(feature['bbox'], self.bl1.bbox_geometry.extent)
            elif fid==2:
                self.assertEqual(feature['bbox'], self.bl2.bbox_geometry.extent)
            else:
                self.fail("Unexpected id: {0}".format(fid))
        BoxedLocation.objects.all().delete()

    def test_post_location_list_geojson(self):
        self.assertEqual(BoxedLocation.objects.count(), 0)
        data = {
            "properties": {
                "name": "geojson input test",
            },
            "geometry": {
                "type": "Point",
                "coordinates": [
                    12.49,
                    41.89
                ]
            },
            "bbox": [11.0, 40.0, 13.0, 42.0]
        }
        response = self.client.post(self.geojson_boxedlocation_list_url, data=json.dumps(data), content_type='application/json')
        self.assertEqual(response.status_code, 201)
        self.assertEqual(BoxedLocation.objects.count(), 1)
        self.assertEqual(BoxedLocation.objects.all()[0].bbox_geometry.extent, (11.0,40.0,13.0,42.0))

    def test_get_autogenerated_location_bbox_geojson(self):
        self._create_locations()
        response = self.client.get(self.geojson_location_bbox_list_url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['features']), 1)
        self.assertEqual(response.data['features'][0]['bbox'], self.l1.geometry.extent)

    def test_bbox_improperly_configured(self):
        self._create_locations()
        class LocationGeoFeatureSerializer(gis_serializers.GeoFeatureModelSerializer):
            class Meta:
                model = Location
                geo_field = 'geometry'
                bbox_geo_field  = 'geometry'
                auto_bbox = True
        with self.assertRaises(ImproperlyConfigured):
            LocationGeoFeatureSerializer(instance=self.l1)
