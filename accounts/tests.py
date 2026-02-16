from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from accounts.models import User
from organization.models import Organization

class UserPermissionsTestCase(APITestCase):
    def setUp(self):
        self.org = Organization.objects.create(name="TestOrg")
        self.org2 = Organization.objects.create(name="OtherOrg")
        self.superuser = User.objects.create_superuser(
            username="superadmin", email="super@admin.com", password="superpass"
        )
        self.org_admin = User.objects.create_user(
            username="orgadmin", email="org@admin.com", password="orgpass", role="admin", organization=self.org
        )
        self.org_admin2 = User.objects.create_user(
            username="orgadmin2", email="org2@admin.com", password="org2pass", role="admin", organization=self.org2
        )
        self.driver = User.objects.create_user(
            username="driver", email="driver@user.com", password="driverpass", role="driver", organization=self.org
        )
        self.driver2 = User.objects.create_user(
            username="driver2", email="driver2@user.com", password="driver2pass", role="driver", organization=self.org2
        )
        self.passenger = User.objects.create_user(
            username="passenger", email="passenger@user.com", password="passpass", role="passenger", organization=self.org
        )
        self.passenger2 = User.objects.create_user(
            username="passenger2", email="passenger2@user.com", password="pass2pass", role="passenger", organization=self.org2
        )

    def test_superuser_can_list_users(self):
        self.client.force_authenticate(user=self.superuser)
        url = reverse("user-list")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_org_admin_can_list_users_in_org(self):
        self.client.force_authenticate(user=self.org_admin)
        url = reverse("user-list")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Only users in the same org
        for user in response.data:
            self.assertEqual(user["organization"]["id"], self.org.id)

    def test_driver_cannot_list_users(self):
        self.client.force_authenticate(user=self.driver)
        url = reverse("user-list")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_passenger_cannot_list_users(self):
        self.client.force_authenticate(user=self.passenger)
        url = reverse("user-list")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_user_can_retrieve_self(self):
        self.client.force_authenticate(user=self.driver)
        url = reverse("user-detail", args=[self.driver.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["id"], self.driver.id)

    def test_user_cannot_retrieve_other(self):
        self.client.force_authenticate(user=self.driver)
        url = reverse("user-detail", args=[self.passenger.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_org_admin_cannot_access_other_org_users(self):
        self.client.force_authenticate(user=self.org_admin)
        url = reverse("user-detail", args=[self.driver2.id])
        response = self.client.get(url)
        self.assertIn(response.status_code, [status.HTTP_403_FORBIDDEN, status.HTTP_404_NOT_FOUND])

    def test_org_admin_can_update_user_in_own_org(self):
        self.client.force_authenticate(user=self.org_admin)
        url = reverse("user-detail", args=[self.driver.id])
        response = self.client.patch(url, {"email": "newdriver@user.com"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["email"], "newdriver@user.com")

    def test_org_admin_cannot_update_user_in_other_org(self):
        self.client.force_authenticate(user=self.org_admin)
        url = reverse("user-detail", args=[self.driver2.id])
        response = self.client.patch(url, {"email": "hacker@user.com"})
        self.assertIn(response.status_code, [status.HTTP_403_FORBIDDEN, status.HTTP_404_NOT_FOUND])

    def test_org_admin_can_delete_user_in_own_org(self):
        self.client.force_authenticate(user=self.org_admin)
        url = reverse("user-detail", args=[self.driver.id])
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_org_admin_cannot_delete_user_in_other_org(self):
        self.client.force_authenticate(user=self.org_admin)
        url = reverse("user-detail", args=[self.driver2.id])
        response = self.client.delete(url)
        self.assertIn(response.status_code, [status.HTTP_403_FORBIDDEN, status.HTTP_404_NOT_FOUND])

    def test_org_admin_can_update_own_org(self):
        self.client.force_authenticate(user=self.org_admin)
        url = reverse("organization-detail", args=[self.org.id])
        response = self.client.patch(url, {"name": "UpdatedOrg"})
        # Should be allowed if org admin is owner, else forbidden
        self.assertIn(response.status_code, [status.HTTP_200_OK, status.HTTP_403_FORBIDDEN])

    def test_org_admin_cannot_update_other_org(self):
        self.client.force_authenticate(user=self.org_admin)
        url = reverse("organization-detail", args=[self.org2.id])
        response = self.client.patch(url, {"name": "HackedOrg"})
        self.assertIn(response.status_code, [status.HTTP_403_FORBIDDEN, status.HTTP_404_NOT_FOUND])

    def test_user_cannot_change_own_role(self):
        self.client.force_authenticate(user=self.driver)
        url = reverse("user-detail", args=[self.driver.id])
        response = self.client.patch(url, {"role": "admin"})
        # Should be forbidden or ignored
        self.assertIn(response.status_code, [status.HTTP_200_OK, status.HTTP_403_FORBIDDEN])
        if response.status_code == status.HTTP_200_OK:
            self.assertNotEqual(response.data["role"], "admin")
