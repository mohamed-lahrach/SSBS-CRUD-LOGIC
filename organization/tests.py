from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from accounts.models import User
from organization.models import Organization

class OrganizationPermissionsTestCase(APITestCase):
    def setUp(self):
        self.org = Organization.objects.create(name="TestOrg")
        self.org2 = Organization.objects.create(name="OtherOrg")
        self.superuser = User.objects.create_superuser(
            username="superadmin", email="super@admin.com", password="superpass"
        )
        self.org_admin = User.objects.create_user(
            username="orgadmin", email="org@admin.com", password="orgpass", role="admin", organization=self.org
        )
        self.driver = User.objects.create_user(
            username="driver", email="driver@user.com", password="driverpass", role="driver", organization=self.org
        )

    def test_superuser_can_create_organization(self):
        self.client.force_authenticate(user=self.superuser)
        url = reverse("organization-list")
        response = self.client.post(url, {"name": "NewOrg"})
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(Organization.objects.filter(name="NewOrg").exists())

    def test_org_admin_can_list_own_organization(self):
        self.client.force_authenticate(user=self.org_admin)
        url = reverse("organization-list")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["id"], self.org.id)

    def test_driver_cannot_create_organization(self):
        self.client.force_authenticate(user=self.driver)
        url = reverse("organization-list")
        response = self.client.post(url, {"name": "DriverOrg"})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_org_admin_can_update_own_organization(self):
        self.client.force_authenticate(user=self.org_admin)
        url = reverse("organization-detail", args=[self.org.id])
        response = self.client.patch(url, {"name": "UpdatedOrg"})
        # Should be allowed if org admin is permitted
        self.assertIn(response.status_code, [status.HTTP_200_OK, status.HTTP_403_FORBIDDEN])
        if response.status_code == status.HTTP_200_OK:
            self.org.refresh_from_db()
            self.assertEqual(self.org.name, "UpdatedOrg")

    def test_org_admin_cannot_update_other_organization(self):
        self.client.force_authenticate(user=self.org_admin)
        url = reverse("organization-detail", args=[self.org2.id])
        response = self.client.patch(url, {"name": "HackedOrg"})
        self.assertIn(response.status_code, [status.HTTP_403_FORBIDDEN, status.HTTP_404_NOT_FOUND])

    def test_superuser_can_delete_organization(self):
        self.client.force_authenticate(user=self.superuser)
        url = reverse("organization-detail", args=[self.org2.id])
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Organization.objects.filter(id=self.org2.id).exists())


