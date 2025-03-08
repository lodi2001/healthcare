from django.urls import path

from .views import ReportListView, ReportDetailView, ReportCreateView, search_report, approve_report

urlpatterns = [
    path('', ReportListView.as_view(), name='report_list'),
    path('create/', ReportCreateView.as_view(), name='report_create'),
    path('detail/<str:report_id>/', ReportDetailView.as_view(), name='report_detail'),
    path('search/', search_report, name='search_report'),
    path('approve/<str:report_id>/', approve_report, name='approve_report'),
]
