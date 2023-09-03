from django.urls import path

from .views import (DownloadFileView, FileMultiView,
                    GenerateDownloadFileLinkView)

# DownloadFileView

# LoginView

urlpatterns = [
    path(
        "file/",
        FileMultiView.as_view(),
        name="file_multi_view",
    ),
    path(
        "genarate_link/<file_id>/",
        GenerateDownloadFileLinkView.as_view(),
        name="download_file_view",
    ),
    path(
        "download_file/<signed_identifier>/",
        DownloadFileView.as_view(),
        name="download_file_view",
    ),
]
