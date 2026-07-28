from django.urls import path

from api.views import Api


app_name = "api"

urlpatterns = [
    path(
        "getAllImages/",
        Api.as_view({"get": "get_all_images"}),
        name="getAllImages",
    ),
    path(
        "getImage/<int:image_id>/",
        Api.as_view({"get": "get_image"}),
        name="getImage",
    ),
    path(
        "uploadImage/",
        Api.as_view({"post": "upload_image"}),
        name="uploadImage",
    ),
    path(
        "deleteImage/<int:image_id>/",
        Api.as_view({"delete": "delete_image"}),
        name="deleteImage",
    ),
]
